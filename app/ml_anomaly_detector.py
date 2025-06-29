"""
Módulo para detecção de anomalias usando PyOD e machine learning
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import json

# PyOD imports
from pyod.models.iforest import IForest
from pyod.models.lof import LOF
from pyod.models.cblof import CBLOF
from pyod.models.knn import KNN
from pyod.models.ocsvm import OCSVM
from pyod.models.auto_encoder import AutoEncoder
from pyod.utils.utility import standardizer

# Scikit-learn imports
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.feature_extraction.text import TfidfVectorizer

from .models import LogEntry
from .storage import get_logs_by_api, get_all_logs
from .model_storage import save_trained_models, load_trained_model, get_available_models

class MLAnomalyDetector:
    """Detector de anomalias usando machine learning"""
    
    def __init__(self):
        self.models = {
            'iforest': IForest(contamination=0.1, random_state=42),
            'lof': LOF(contamination=0.1),
            'knn': KNN(contamination=0.1),
            'ocsvm': OCSVM(contamination=0.1),
            'cblof': CBLOF(contamination=0.1, random_state=42)
        }
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.tfidf_vectorizer = TfidfVectorizer(max_features=50, stop_words='english')
        self.is_fitted = False
        self.current_model_name = None
        
    def extract_features(self, logs: List[LogEntry]) -> pd.DataFrame:
        """
        Extrai características dos logs para análise de anomalias
        
        Características extraídas:
        - Temporais: hora, dia da semana, minuto
        - Requisição: status code, método HTTP, tamanho do path
        - IP: conversão numérica do IP
        - Cliente: ID codificado
        - Path: flags para APIs, admin, auth
        - Status: flags para erros, sucessos, redirecionamentos
        """
        if not logs:
            return pd.DataFrame()
        
        features = []
        
        for log in logs:
            # Características temporais
            hour = log.timestamp.hour
            day_of_week = log.timestamp.weekday()
            minute = log.timestamp.minute
            
            # Características da requisição
            status_code = log.status
            method_encoded = self._encode_categorical('method', log.method)
            path_length = len(log.path)
            path_depth = log.path.count('/')
            
            # Características do IP
            ip_parts = log.ip.split('.')
            ip_numeric = sum(int(part) * (256 ** (3-i)) for i, part in enumerate(ip_parts))
            
            # Características do cliente
            client_id_encoded = self._encode_categorical('clientId', log.clientId)
            
            # Características do path
            is_api_path = 1 if '/api/' in log.path else 0
            is_admin_path = 1 if '/admin' in log.path else 0
            is_auth_path = 1 if any(x in log.path.lower() for x in ['/login', '/auth', '/token']) else 0
            
            # Características de erro
            is_error = 1 if status_code >= 400 else 0
            is_server_error = 1 if status_code >= 500 else 0
            is_client_error = 1 if 400 <= status_code < 500 else 0
            
            # Características de sucesso
            is_success = 1 if 200 <= status_code < 300 else 0
            is_redirect = 1 if 300 <= status_code < 400 else 0
            
            # Ajustar peso dos erros de servidor (não são anomalias do cliente)
            # Reduzir o impacto dos erros de servidor nas features
            if is_server_error:
                # Para erros de servidor, usar valores mais próximos do normal
                status_code_normalized = 200  # Tratar como se fosse sucesso
                is_error = 0  # Não considerar como erro para análise de anomalia
            else:
                status_code_normalized = status_code
            
            feature_vector = [
                hour, day_of_week, minute,
                status_code_normalized, method_encoded, path_length, path_depth,
                ip_numeric, client_id_encoded,
                is_api_path, is_admin_path, is_auth_path,
                is_error, is_server_error, is_client_error,
                is_success, is_redirect
            ]
            
            features.append(feature_vector)
        
        # Criar DataFrame
        feature_names = [
            'hour', 'day_of_week', 'minute',
            'status_code', 'method_encoded', 'path_length', 'path_depth',
            'ip_numeric', 'client_id_encoded',
            'is_api_path', 'is_admin_path', 'is_auth_path',
            'is_error', 'is_server_error', 'is_client_error',
            'is_success', 'is_redirect'
        ]
        
        df = pd.DataFrame(features, columns=feature_names)
        return df
    
    def _encode_categorical(self, field: str, value: str) -> int:
        """Codifica valores categóricos usando LabelEncoder"""
        if field not in self.label_encoders:
            self.label_encoders[field] = LabelEncoder()
            # Inicializar com valores conhecidos
            if field == 'method':
                known_values = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']
            else:
                known_values = [value]
            self.label_encoders[field].fit(known_values)
        
        try:
            return self.label_encoders[field].transform([value])[0]
        except ValueError:
            # Se o valor não foi visto antes, retornar -1
            return -1
    
    def train_models(self, logs: List[LogEntry], save_models: bool = True) -> Dict:
        """
        Treina os modelos de detecção de anomalias
        
        Args:
            logs: Lista de logs para treinamento
            save_models: Se deve salvar os modelos treinados
        
        Returns:
            Dict com resultados do treinamento
        """
        if len(logs) < 10:
            return {"error": "Poucos dados para treinar (mínimo 10 logs)"}
        
        try:
            # Extrair características
            features_df = self.extract_features(logs)
            
            if features_df.empty:
                return {"error": "Não foi possível extrair características dos logs"}
            
            # Normalizar características
            features_scaled = self.scaler.fit_transform(features_df)
            
            # Treinar modelos
            results = {}
            for name, model in self.models.items():
                try:
                    model.fit(features_scaled)
                    results[name] = "treinado"
                except Exception as e:
                    results[name] = f"erro: {str(e)}"
            
            self.is_fitted = True
            
            # Preparar metadados
            metadata = {
                "trained_at": datetime.now().isoformat(),
                "features_count": len(features_df.columns),
                "samples_count": len(features_df),
                "feature_names": list(features_df.columns),
                "models_trained": results,
                "feature_stats": {
                    "mean": features_df.mean().to_dict(),
                    "std": features_df.std().to_dict(),
                    "min": features_df.min().to_dict(),
                    "max": features_df.max().to_dict()
                }
            }
            
            # Salvar modelos se solicitado
            if save_models:
                save_results = save_trained_models(
                    models=self.models,
                    scaler=self.scaler,
                    label_encoders=self.label_encoders,
                    metadata=metadata
                )
                metadata["save_results"] = save_results
            
            return {
                "status": "sucesso",
                "models_trained": results,
                "features_count": len(features_df.columns),
                "samples_count": len(features_df),
                "feature_names": list(features_df.columns),
                "metadata": metadata
            }
            
        except Exception as e:
            return {"error": f"Erro no treinamento: {str(e)}"}
    
    def load_trained_model(self, model_name: str) -> bool:
        """
        Carrega um modelo treinado salvo
        
        Args:
            model_name: Nome do modelo a carregar
        
        Returns:
            True se carregado com sucesso
        """
        try:
            model_data = load_trained_model(model_name)
            if not model_data:
                return False
            
            # Carregar modelo e preprocessadores
            self.models[model_name] = model_data['model']
            self.scaler = model_data['scaler']
            self.label_encoders = model_data['label_encoders']
            self.is_fitted = True
            self.current_model_name = model_name
            
            print(f"✅ Modelo {model_name} carregado com sucesso!")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao carregar modelo {model_name}: {e}")
            return False
    
    def _analyze_ip_changes(self, current_log: LogEntry, all_logs: List[LogEntry], hours_back: int = 24) -> List[str]:
        """
        Analisa mudanças de IP considerando ranges CIDR e padrões por cliente
        
        Args:
            current_log: Log atual sendo analisado
            all_logs: Lista de todos os logs
            hours_back: Horas para trás para analisar histórico
        
        Returns:
            Lista de descrições de mudanças de IP suspeitas
        """
        try:
            # Obter logs do mesmo cliente nas últimas horas
            cutoff_time = datetime.now() - timedelta(hours=hours_back)
            client_logs = [log for log in all_logs 
                          if log.clientId == current_log.clientId 
                          and log.timestamp >= cutoff_time
                          and log.timestamp < current_log.timestamp]
            
            if len(client_logs) < 2:
                return []
            
            # Coletar IPs únicos usados pelo cliente
            unique_ips = list(set([log.ip for log in client_logs]))
            current_ip = current_log.ip
            
            ip_changes = []
            
            # Analisar padrões de IP por cliente
            client_ip_patterns = self._analyze_client_ip_patterns(client_logs)
            
            # Verificar se o IP atual está dentro dos ranges conhecidos do cliente
            if client_ip_patterns['known_ranges']:
                ip_in_known_range = False
                for cidr_range in client_ip_patterns['known_ranges']:
                    if self._ip_in_cidr_range(current_ip, cidr_range):
                        ip_in_known_range = True
                        break
                
                if not ip_in_known_range:
                    ip_changes.append(f"IP fora dos ranges conhecidos do cliente ({current_ip})")
            
            # Verificar se o cliente está usando muitos ranges diferentes
            if len(client_ip_patterns['known_ranges']) > 3:
                ip_changes.append(f"Cliente usando muitos ranges de IP ({len(client_ip_patterns['known_ranges'])} ranges)")
            
            # Verificar mudanças recentes de range (últimas 2 horas)
            recent_cutoff = datetime.now() - timedelta(hours=2)
            recent_logs = [log for log in client_logs if log.timestamp >= recent_cutoff]
            recent_ranges = self._analyze_client_ip_patterns(recent_logs)['known_ranges']
            
            if len(recent_ranges) > 2:
                ip_changes.append("Mudanças frequentes de ranges de IP (últimas 2 horas)")
            
            # Verificar se o IP atual é de uma faixa suspeita
            if self._is_suspicious_ip_range(current_ip):
                ip_changes.append(f"IP de range suspeito detectado ({current_ip})")
            
            # Verificar mudança de tipo de rede (privada/pública)
            if client_ip_patterns['network_types']:
                current_network_type = self._get_network_type(current_ip)
                if current_network_type not in client_ip_patterns['network_types']:
                    ip_changes.append(f"Mudança de tipo de rede ({current_network_type})")
            
            # Verificar se o cliente está usando IPs de diferentes provedores/regiões
            if len(client_ip_patterns['asn_ranges']) > 2:
                ip_changes.append("IPs de múltiplos provedores/regiões detectados")
            
            # Verificar padrão de uso de IPs
            if client_ip_patterns['ip_rotation_frequency'] > 0.5:  # Mais de 50% de rotação
                ip_changes.append("Rotação excessiva de IPs detectada")
            
            return ip_changes
            
        except Exception as e:
            print(f"Erro ao analisar mudanças de IP: {e}")
            return []
    
    def _analyze_client_ip_patterns(self, client_logs: List[LogEntry]) -> Dict:
        """
        Analisa padrões de IP para um cliente específico
        
        Args:
            client_logs: Logs do cliente para análise
        
        Returns:
            Dicionário com padrões de IP identificados
        """
        try:
            unique_ips = list(set([log.ip for log in client_logs]))
            
            if not unique_ips:
                return {
                    'known_ranges': [],
                    'network_types': [],
                    'asn_ranges': [],
                    'ip_rotation_frequency': 0.0
                }
            
            # Identificar ranges CIDR que cobrem os IPs
            known_ranges = self._identify_cidr_ranges(unique_ips)
            
            # Identificar tipos de rede
            network_types = set()
            for ip_str in unique_ips:
                network_types.add(self._get_network_type(ip_str))
            
            # Simular identificação de ASN ranges (baseado em primeiros octetos)
            asn_ranges = self._identify_asn_ranges(unique_ips)
            
            # Calcular frequência de rotação de IPs
            ip_rotation_frequency = self._calculate_ip_rotation_frequency(client_logs)
            
            return {
                'known_ranges': known_ranges,
                'network_types': list(network_types),
                'asn_ranges': asn_ranges,
                'ip_rotation_frequency': ip_rotation_frequency
            }
            
        except Exception as e:
            print(f"Erro ao analisar padrões de IP: {e}")
            return {
                'known_ranges': [],
                'network_types': [],
                'asn_ranges': [],
                'ip_rotation_frequency': 0.0
            }
    
    def _identify_cidr_ranges(self, ip_list: List[str]) -> List[str]:
        """
        Identifica ranges CIDR que cobrem os IPs fornecidos
        
        Args:
            ip_list: Lista de IPs para análise
        
        Returns:
            Lista de ranges CIDR identificados
        """
        try:
            if not ip_list:
                return []
            
            # Ordenar IPs
            sorted_ips = sorted(ip_list, key=lambda x: [int(i) for i in x.split('.')])
            
            # Tentar identificar ranges comuns
            ranges = []
            
            # Verificar ranges privados comuns
            private_ranges = [
                "10.0.0.0/8",
                "172.16.0.0/12", 
                "192.168.0.0/16"
            ]
            
            for cidr in private_ranges:
                ips_in_range = [ip for ip in sorted_ips if self._ip_in_cidr_range(ip, cidr)]
                if len(ips_in_range) >= 2:  # Pelo menos 2 IPs no range
                    ranges.append(cidr)
            
            # Verificar ranges públicos por subnets
            public_ips = [ip for ip in sorted_ips if not self._is_private_ip(ip)]
            
            if public_ips:
                # Agrupar por primeiros octetos (simulando ASN)
                first_octet_groups = {}
                for ip in public_ips:
                    first_octet = ip.split('.')[0]
                    if first_octet not in first_octet_groups:
                        first_octet_groups[first_octet] = []
                    first_octet_groups[first_octet].append(ip)
                
                # Criar ranges para grupos com múltiplos IPs
                for first_octet, ips in first_octet_groups.items():
                    if len(ips) >= 2:
                        # Tentar criar um range /8 para o primeiro octeto
                        range_cidr = f"{first_octet}.0.0.0/8"
                        ranges.append(range_cidr)
            
            return list(set(ranges))
            
        except Exception as e:
            print(f"Erro ao identificar ranges CIDR: {e}")
            return []
    
    def _ip_in_cidr_range(self, ip: str, cidr: str) -> bool:
        """
        Verifica se um IP está dentro de um range CIDR
        
        Args:
            ip: IP para verificar
            cidr: Range CIDR (ex: "192.168.1.0/24")
        
        Returns:
            True se o IP está no range
        """
        try:
            ip_parts = [int(x) for x in ip.split('.')]
            cidr_parts = cidr.split('/')
            cidr_ip = [int(x) for x in cidr_parts[0].split('.')]
            mask = int(cidr_parts[1])
            
            # Calcular máscara de rede
            mask_bits = (0xFFFFFFFF << (32 - mask)) & 0xFFFFFFFF
            
            # Converter IPs para inteiros
            ip_int = (ip_parts[0] << 24) + (ip_parts[1] << 16) + (ip_parts[2] << 8) + ip_parts[3]
            cidr_int = (cidr_ip[0] << 24) + (cidr_ip[1] << 16) + (cidr_ip[2] << 8) + cidr_ip[3]
            
            # Verificar se está no range
            return (ip_int & mask_bits) == (cidr_int & mask_bits)
            
        except Exception as e:
            print(f"Erro ao verificar IP em range CIDR: {e}")
            return False
    
    def _is_private_ip(self, ip: str) -> bool:
        """
        Verifica se um IP é privado
        
        Args:
            ip: IP para verificar
        
        Returns:
            True se o IP é privado
        """
        try:
            parts = [int(x) for x in ip.split('.')]
            
            # Ranges privados
            if parts[0] == 10:
                return True
            elif parts[0] == 172 and 16 <= parts[1] <= 31:
                return True
            elif parts[0] == 192 and parts[1] == 168:
                return True
            
            return False
            
        except Exception as e:
            print(f"Erro ao verificar IP privado: {e}")
            return False
    
    def _get_network_type(self, ip: str) -> str:
        """
        Identifica o tipo de rede de um IP
        
        Args:
            ip: IP para análise
        
        Returns:
            String com o tipo de rede
        """
        try:
            if self._is_private_ip(ip):
                return "private"
            elif ip.startswith("127."):
                return "loopback"
            elif ip.startswith("169.254."):
                return "link_local"
            elif ip.startswith("224.") or ip.startswith("225.") or ip.startswith("226.") or ip.startswith("227.") or ip.startswith("228.") or ip.startswith("229.") or ip.startswith("230.") or ip.startswith("231.") or ip.startswith("232.") or ip.startswith("233.") or ip.startswith("234.") or ip.startswith("235.") or ip.startswith("236.") or ip.startswith("237.") or ip.startswith("238.") or ip.startswith("239."):
                return "multicast"
            else:
                return "public"
        except:
            return "unknown"
    
    def _identify_asn_ranges(self, ip_list: List[str]) -> List[str]:
        """
        Identifica ranges de ASN baseados em primeiros octetos
        
        Args:
            ip_list: Lista de IPs para análise
        
        Returns:
            Lista de ranges de ASN identificados
        """
        try:
            asn_ranges = set()
            
            for ip in ip_list:
                if not self._is_private_ip(ip):
                    # Simular identificação de ASN baseado no primeiro octeto
                    first_octet = ip.split('.')[0]
                    asn_ranges.add(f"ASN_{first_octet}")
            
            return list(asn_ranges)
            
        except Exception as e:
            print(f"Erro ao identificar ranges ASN: {e}")
            return []
    
    def _calculate_ip_rotation_frequency(self, client_logs: List[LogEntry]) -> float:
        """
        Calcula a frequência de rotação de IPs
        
        Args:
            client_logs: Logs do cliente para análise
        
        Returns:
            Float com a frequência de rotação (0.0 a 1.0)
        """
        try:
            if len(client_logs) < 2:
                return 0.0
            
            # Ordenar logs por timestamp
            sorted_logs = sorted(client_logs, key=lambda x: x.timestamp)
            
            # Contar mudanças de IP
            ip_changes = 0
            previous_ip = sorted_logs[0].ip
            
            for log in sorted_logs[1:]:
                if log.ip != previous_ip:
                    ip_changes += 1
                previous_ip = log.ip
            
            # Calcular frequência
            total_requests = len(sorted_logs)
            rotation_frequency = ip_changes / (total_requests - 1) if total_requests > 1 else 0.0
            
            return min(rotation_frequency, 1.0)
            
        except Exception as e:
            print(f"Erro ao calcular frequência de rotação: {e}")
            return 0.0
    
    def _is_suspicious_ip_range(self, ip: str) -> bool:
        """
        Verifica se um IP está em um range suspeito
        
        Args:
            ip: IP para verificação
        
        Returns:
            True se o IP está em range suspeito
        """
        try:
            # Ranges conhecidos de VPNs, proxies, etc.
            suspicious_ranges = [
                "1.1.1.0/24",  # Cloudflare DNS
                "8.8.8.0/24",  # Google DNS
                "208.67.222.0/24",  # OpenDNS
                "185.228.168.0/24",  # CleanBrowsing
                "176.103.130.0/24",  # AdGuard
            ]
            
            for cidr in suspicious_ranges:
                if self._ip_in_cidr_range(ip, cidr):
                    return True
            
            # Verificar IPs de datacenters conhecidos
            datacenter_patterns = [
                "aws", "amazon", "google", "azure", "cloudflare", "digitalocean",
                "linode", "vultr", "ovh", "hetzner", "rackspace"
            ]
            
            # Simular verificação de datacenter (em produção, usar API de geolocalização)
            # Por enquanto, apenas verificar ranges específicos
            if self._is_private_ip(ip):
                return False  # IPs privados geralmente não são suspeitos
            
            return False
            
        except Exception as e:
            print(f"Erro ao verificar range suspeito: {e}")
            return False
    
    def generate_anomaly_description(self, features: dict, score: float, model_name: str = 'iforest', 
                                   current_log: LogEntry = None, all_logs: List[LogEntry] = None) -> str:
        """
        Gera descrição inteligente da anomalia usando ML
        """
        try:
            # Importa o sistema de ML de descrições
            from .anomaly_description_ml import description_ml
            
            if current_log is None or all_logs is None:
                # Fallback para descrição básica se não houver contexto
                return f"Anomalia detectada pelo modelo {model_name} (Score: {score:.3f})"
            
            # Converte LogEntry para dict para compatibilidade
            log_dict = {
                'requestId': current_log.requestId,
                'clientId': current_log.clientId,
                'ip': current_log.ip,
                'apiId': current_log.apiId,
                'method': current_log.method,
                'path': current_log.path,
                'status': current_log.status,
                'timestamp': current_log.timestamp.isoformat()
            }
            
            # Converte todos os logs para dict
            all_logs_dict = []
            for log in all_logs:
                all_logs_dict.append({
                    'requestId': log.requestId,
                    'clientId': log.clientId,
                    'ip': log.ip,
                    'apiId': log.apiId,
                    'method': log.method,
                    'path': log.path,
                    'status': log.status,
                    'timestamp': log.timestamp.isoformat()
                })
            
            # Gera descrição usando ML
            description = description_ml.generate_ml_description(log_dict, score, all_logs_dict)
            
            return description
            
        except Exception as e:
            # Fallback em caso de erro
            print(f"Erro ao gerar descrição ML: {e}")
            return f"Anomalia detectada pelo modelo {model_name} (Score: {score:.3f})"
    
    def detect_anomalies(self, logs: List[LogEntry], model_name: str = 'iforest', threshold: float = None) -> Dict:
        """
        Detecta anomalias usando o modelo especificado
        
        Args:
            logs: Lista de logs para análise
            model_name: Nome do modelo a usar
            threshold: Score mínimo para considerar como anomalia (opcional)
        
        Returns:
            Dict com anomalias detectadas
        """
        if not self.is_fitted:
            return {"error": "Modelos não foram treinados. Execute train_models primeiro."}
        
        if model_name not in self.models:
            return {"error": f"Modelo '{model_name}' não encontrado"}
        
        try:
            # Extrair características
            features_df = self.extract_features(logs)
            
            if features_df.empty:
                return {"error": "Não foi possível extrair características dos logs"}
            
            # Normalizar características
            features_scaled = self.scaler.transform(features_df)
            
            # Detectar anomalias
            model = self.models[model_name]
            anomaly_scores = model.decision_function(features_scaled)
            anomaly_labels = model.predict(features_scaled)
            
            # Organizar resultados
            anomalies = []
            normal_logs = []
            
            for i, (log, score, is_anomaly) in enumerate(zip(logs, anomaly_scores, anomaly_labels)):
                log_info = {
                    "index": i,
                    "requestId": log.requestId,
                    "clientId": log.clientId,
                    "ip": log.ip,
                    "apiId": log.apiId,
                    "method": log.method,
                    "path": log.path,
                    "status": log.status,
                    "timestamp": log.timestamp.isoformat(),
                    "anomaly_score": float(score),
                    "is_anomaly": bool(is_anomaly),
                    "features": features_df.iloc[i].to_dict()
                }
                
                if is_anomaly:
                    # Gerar descrição da anomalia
                    log_info["anomaly_description"] = self.generate_anomaly_description(
                        features_df.iloc[i].to_dict(), 
                        float(score), 
                        model_name,
                        log,
                        logs
                    )
                    anomalies.append(log_info)
                else:
                    normal_logs.append(log_info)
            
            # Aplicar threshold de score se fornecido
            if threshold is not None:
                anomalies = [a for a in anomalies if a["anomaly_score"] >= threshold]
            
            # Calcular estatísticas
            total_logs = len(logs)
            anomalies_detected = len(anomalies)
            anomaly_rate = (anomalies_detected / total_logs * 100) if total_logs > 0 else 0
            
            # Estatísticas dos scores
            if anomaly_scores.size > 0:
                score_stats = {
                    "min": float(np.min(anomaly_scores)),
                    "max": float(np.max(anomaly_scores)),
                    "mean": float(np.mean(anomaly_scores)),
                    "std": float(np.std(anomaly_scores)),
                    "median": float(np.median(anomaly_scores))
                }
            else:
                score_stats = {"min": 0, "max": 0, "mean": 0, "std": 0, "median": 0}
            
            # Organizar resultado final
            result = {
                "model_used": model_name,
                "logs_analyzed": total_logs,
                "anomalies_detected": anomalies_detected,
                "anomaly_rate": round(anomaly_rate, 2),
                "score_statistics": score_stats,
                "anomalies": anomalies,
                "normal_logs": normal_logs,
                "threshold_used": threshold
            }
            
            return result
            
        except Exception as e:
            return {"error": f"Erro na detecção: {str(e)}"}
    
    def compare_models(self, logs: List[LogEntry]) -> Dict:
        """
        Compara diferentes modelos de detecção de anomalias
        
        Args:
            logs: Lista de logs para comparação
        
        Returns:
            Dict com comparação dos modelos
        """
        if not self.is_fitted:
            return {"error": "Modelos não foram treinados. Execute train_models primeiro."}
        
        try:
            comparison = {}
            
            for model_name in self.models.keys():
                if model_name in self.models:
                    result = self.detect_anomalies(logs, model_name)
                    if "error" not in result:
                        comparison[model_name] = {
                            "anomalies_detected": result["anomalies_detected"],
                            "anomaly_rate": result["anomaly_rate"],
                            "score_statistics": result["score_statistics"]
                        }
                    else:
                        comparison[model_name] = {"error": result["error"]}
            
            return {
                "total_logs": len(logs),
                "models_comparison": comparison
            }
            
        except Exception as e:
            return {"error": f"Erro na comparação: {str(e)}"}

# Funções de conveniência para uso externo
def train_ml_models_with_collection(apiId: str = None, hours_back: int = 24, save_models: bool = True) -> Dict:
    """
    Treina modelos ML usando a coleção de treinamento (com feedback aplicado)
    
    Args:
        apiId: ID da API (None para todas)
        hours_back: Horas para trás para buscar logs (não usado quando há coleção de treinamento)
        save_models: Se deve salvar os modelos treinados
    
    Returns:
        Dict com resultados do treinamento
    """
    try:
        from .db import db
        
        # Verificar se existe coleção de treinamento
        training_collection = db.training_logs
        training_docs = list(training_collection.find())
        
        if not training_docs:
            return {"error": "Nenhum log de treinamento encontrado. Execute o retreinamento primeiro."}
        
        # Converter documentos para LogEntry
        logs = []
        for doc in training_docs:
            try:
                # Remover _id do MongoDB se presente
                if '_id' in doc:
                    del doc['_id']
                logs.append(LogEntry(**doc))
            except Exception as e:
                print(f"Erro ao processar log de treinamento: {e}")
                continue
        
        if not logs:
            return {"error": "Nenhum log válido encontrado na coleção de treinamento"}
        
        # Treinar modelos
        detector = MLAnomalyDetector()
        result = detector.train_models(logs, save_models)
        
        if "error" not in result:
            result["logs_used"] = len(logs)
            result["training_source"] = "feedback_enhanced"
            result["message"] = f"Modelo treinado com {len(logs)} logs (incluindo feedback)"
        
        return result
        
    except Exception as e:
        return {"error": f"Erro no treinamento com coleção: {str(e)}"}

def train_ml_models(apiId: str = None, hours_back: int = 24, save_models: bool = True) -> Dict:
    """
    Treina modelos ML com logs de uma API específica ou todos
    
    Args:
        apiId: ID da API (None para todas)
        hours_back: Horas para trás para buscar logs
        save_models: Se deve salvar os modelos treinados
    
    Returns:
        Dict com resultados do treinamento
    """
    try:
        # Obter logs
        if apiId:
            logs = get_logs_by_api(apiId)
        else:
            logs = get_all_logs()
        
        if not logs:
            return {"error": "Nenhum log encontrado"}
        
        # Filtrar logs recentes
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        recent_logs = [log for log in logs if log.timestamp >= cutoff_time]
        
        if not recent_logs:
            return {"error": f"Nenhum log encontrado nas últimas {hours_back} horas"}
        
        # Treinar modelos
        detector = MLAnomalyDetector()
        result = detector.train_models(recent_logs, save_models)
        
        if "error" not in result:
            result["logs_used"] = len(recent_logs)
            result["time_range"] = f"Últimas {hours_back} horas"
        
        return result
        
    except Exception as e:
        return {"error": f"Erro no treinamento: {str(e)}"}

def detect_ml_anomalies(apiId: str = None, model_name: str = 'iforest', hours_back: int = 24, threshold: float = None) -> Dict:
    """
    Detecta anomalias usando ML
    
    Args:
        apiId: ID da API (None para todas)
        model_name: Nome do modelo a usar
        hours_back: Horas para trás para buscar logs
        threshold: Score mínimo para considerar como anomalia (opcional)
    
    Returns:
        Dict com anomalias detectadas
    """
    try:
        # Obter threshold das configurações se não fornecido
        if threshold is None:
            try:
                from .config_manager import config_manager
                ml_config = config_manager.get_config("ml_detection")
                threshold = ml_config.get("threshold", 0.12)
                print(f"🔧 Usando threshold das configurações: {threshold}")
            except Exception as e:
                print(f"⚠️ Erro ao obter threshold das configurações: {e}")
                threshold = 0.12  # Valor padrão
        
        # Obter logs
        if apiId:
            logs = get_logs_by_api(apiId)
        else:
            logs = get_all_logs()
        
        if not logs:
            return {"error": "Nenhum log encontrado"}
        
        # Filtrar logs recentes
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        recent_logs = [log for log in logs if log.timestamp >= cutoff_time]
        
        if not recent_logs:
            return {"error": f"Nenhum log encontrado nas últimas {hours_back} horas"}
        
        # Filtrar logs que já foram marcados com feedback
        from .feedback_system import feedback_system
        processed_false_positives = feedback_system.get_processed_false_positives(apiId)
        
        if processed_false_positives:
            # Filtrar apenas logs que foram marcados como falsos positivos E processados
            filtered_logs = [log for log in recent_logs if log.requestId not in processed_false_positives]
            print(f"Filtrando {len(processed_false_positives)} falsos positivos processados. Restaram {len(filtered_logs)} logs para análise.")
        else:
            filtered_logs = recent_logs
            print(f"Nenhum falso positivo processado encontrado. Analisando todos os {len(filtered_logs)} logs.")
        
        if not filtered_logs:
            return {
                "error": "Todos os logs recentes foram marcados como falsos positivos processados",
                "total_logs": len(recent_logs),
                "processed_false_positives": len(processed_false_positives),
                "logs_available": 0
            }
        
        # Criar detector e carregar modelo treinado
        detector = MLAnomalyDetector()
        
        # Tentar carregar modelo treinado
        if not detector.load_trained_model(model_name):
            # Se não conseguir carregar, retornar erro em vez de treinar
            return {"error": f"Modelo {model_name} não encontrado. Execute o treinamento primeiro via endpoint /ml/train"}
        
        # Verificar se o modelo específico está disponível
        if model_name not in detector.models:
            return {"error": f"Modelo {model_name} não está disponível. Modelos disponíveis: {list(detector.models.keys())}"}
        
        # Detectar anomalias
        result = detector.detect_anomalies(filtered_logs, model_name, threshold=threshold)
        
        if "error" not in result:
            result["logs_analyzed"] = len(filtered_logs)
            result["total_logs"] = len(recent_logs)
            result["processed_false_positives"] = len(processed_false_positives)
            result["logs_available"] = len(filtered_logs)
            result["time_range"] = f"Últimas {hours_back} horas"
            result["threshold_used"] = threshold
        
        return result
        
    except Exception as e:
        return {"error": f"Erro na detecção: {str(e)}"}

def compare_ml_models(apiId: str = None, hours_back: int = 24) -> Dict:
    """
    Compara diferentes modelos ML
    
    Args:
        apiId: ID da API (None para todas)
        hours_back: Horas para trás para buscar logs
    
    Returns:
        Dict com comparação dos modelos
    """
    try:
        # Obter threshold das configurações
        threshold = None
        try:
            from .config_manager import config_manager
            ml_config = config_manager.get_config("ml_detection")
            threshold = ml_config.get("threshold", 0.12)
            print(f"🔧 Compare usando threshold das configurações: {threshold}")
        except Exception as e:
            print(f"⚠️ Erro ao obter threshold das configurações: {e}")
            threshold = 0.12  # Valor padrão
        
        # Obter logs
        if apiId:
            logs = get_logs_by_api(apiId)
        else:
            logs = get_all_logs()
        
        if not logs:
            return {"error": "Nenhum log encontrado"}
        
        # Filtrar logs recentes
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        recent_logs = [log for log in logs if log.timestamp >= cutoff_time]
        
        if not recent_logs:
            return {"error": f"Nenhum log encontrado nas últimas {hours_back} horas"}
        
        # Filtrar logs que já foram marcados com feedback
        from .feedback_system import feedback_system
        processed_false_positives = feedback_system.get_processed_false_positives(apiId)
        
        if processed_false_positives:
            # Filtrar apenas logs que foram marcados como falsos positivos E processados
            filtered_logs = [log for log in recent_logs if log.requestId not in processed_false_positives]
            print(f"Compare: Filtrando {len(processed_false_positives)} falsos positivos processados. Restaram {len(filtered_logs)} logs para análise.")
        else:
            filtered_logs = recent_logs
            print(f"Compare: Nenhum falso positivo processado encontrado. Analisando todos os {len(filtered_logs)} logs.")
        
        if not filtered_logs:
            return {
                "error": "Todos os logs recentes foram marcados como falsos positivos processados",
                "total_logs": len(recent_logs),
                "processed_false_positives": len(processed_false_positives),
                "logs_available": 0
            }
        
        # Criar detector e carregar modelos treinados
        detector = MLAnomalyDetector()
        
        # Tentar carregar todos os modelos treinados
        models_loaded = []
        for model_name in ['iforest', 'lof', 'ocsvm']:
            if detector.load_trained_model(model_name):
                models_loaded.append(model_name)
        
        if not models_loaded:
            return {"error": "Nenhum modelo treinado encontrado. Execute o treinamento primeiro via endpoint /ml/train"}
        
        print(f"Modelos carregados para comparação: {models_loaded}")
        
        # Comparar modelos com threshold
        comparison = {}
        
        for model_name in models_loaded:
            if model_name in detector.models:
                result = detector.detect_anomalies(filtered_logs, model_name, threshold=threshold)
                if "error" not in result:
                    comparison[model_name] = {
                        "anomalies_detected": result["anomalies_detected"],
                        "anomaly_rate": result["anomaly_rate"],
                        "score_statistics": result["score_statistics"],
                        "threshold_used": threshold
                    }
                else:
                    comparison[model_name] = {"error": result["error"]}
        
        result = {
            "total_logs": len(recent_logs),
            "logs_analyzed": len(filtered_logs),
            "processed_false_positives": len(processed_false_positives),
            "logs_available": len(filtered_logs),
            "time_range": f"Últimas {hours_back} horas",
            "threshold_used": threshold,
            "models_comparison": comparison
        }
        
        return result
        
    except Exception as e:
        return {"error": f"Erro na comparação: {str(e)}"}

def get_anomalies_timeline_data(apiId: str = None, model_name: str = 'iforest', hours_back: int = 24, interval_minutes: int = 30) -> Dict:
    """
    Gera dados temporais de anomalias para gráficos
    
    Args:
        apiId: ID da API (None para todas)
        model_name: Nome do modelo a usar
        hours_back: Horas para trás para buscar logs
        interval_minutes: Intervalo em minutos para agrupar dados
    
    Returns:
        Dict com dados temporais de anomalias
    """
    try:
        from .storage import get_logs_by_api, get_all_logs
        
        # Obter threshold das configurações
        threshold = None
        try:
            from .config_manager import config_manager
            ml_config = config_manager.get_config("ml_detection")
            threshold = ml_config.get("threshold", 0.12)
            print(f"🔧 Timeline usando threshold das configurações: {threshold}")
        except Exception as e:
            print(f"⚠️ Erro ao obter threshold das configurações: {e}")
            threshold = 0.12  # Valor padrão
        
        # Obter logs
        if apiId:
            logs = get_logs_by_api(apiId)
        else:
            logs = get_all_logs()
        
        if not logs:
            return {"error": "Nenhum log encontrado"}
        
        # Filtrar logs recentes
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        recent_logs = [log for log in logs if log.timestamp >= cutoff_time]
        
        if not recent_logs:
            return {"error": f"Nenhum log encontrado nas últimas {hours_back} horas"}
        
        # Filtrar logs que já foram marcados com feedback
        from .feedback_system import feedback_system
        processed_false_positives = feedback_system.get_processed_false_positives(apiId)
        
        if processed_false_positives:
            # Filtrar apenas logs que foram marcados como falsos positivos E processados
            filtered_logs = [log for log in recent_logs if log.requestId not in processed_false_positives]
            print(f"Timeline: Filtrando {len(processed_false_positives)} falsos positivos processados. Restaram {len(filtered_logs)} logs para análise.")
        else:
            filtered_logs = recent_logs
            print(f"Timeline: Nenhum falso positivo processado encontrado. Analisando todos os {len(filtered_logs)} logs.")
        
        if not filtered_logs:
            return {
                "error": "Todos os logs recentes foram marcados como falsos positivos processados",
                "total_logs": len(recent_logs),
                "processed_false_positives": len(processed_false_positives),
                "logs_available": 0
            }
        
        # Carregar modelo treinado
        detector = MLAnomalyDetector()
        if not detector.load_trained_model(model_name):
            return {"error": f"Modelo {model_name} não encontrado. Treine o modelo primeiro."}
        
        # Detectar anomalias com threshold
        result = detector.detect_anomalies(filtered_logs, model_name, threshold=threshold)
        if "error" in result:
            return result
        
        anomalies = result.get("anomalies", [])
        
        # Agrupar anomalias por intervalos de tempo
        timeline_data = {}
        
        for anomaly in anomalies:
            # Converter timestamp para datetime se necessário
            if isinstance(anomaly["timestamp"], str):
                timestamp = datetime.fromisoformat(anomaly["timestamp"].replace('Z', '+00:00'))
            else:
                timestamp = anomaly["timestamp"]
            
            # Arredondar para o intervalo especificado
            interval_seconds = interval_minutes * 60
            rounded_timestamp = timestamp.replace(
                second=0, 
                microsecond=0
            ).replace(
                minute=(timestamp.minute // interval_minutes) * interval_minutes
            )
            
            time_key = rounded_timestamp.isoformat()
            
            if time_key not in timeline_data:
                timeline_data[time_key] = {
                    "timestamp": time_key,
                    "anomaly_count": 0,
                    "avg_score": 0.0,
                    "total_score": 0.0,
                    "anomalies": []
                }
            
            timeline_data[time_key]["anomaly_count"] += 1
            timeline_data[time_key]["total_score"] += anomaly["anomaly_score"]
            timeline_data[time_key]["avg_score"] = timeline_data[time_key]["total_score"] / timeline_data[time_key]["anomaly_count"]
            timeline_data[time_key]["anomalies"].append({
                "requestId": anomaly["requestId"],
                "clientId": anomaly["clientId"],
                "ip": anomaly["ip"],
                "method": anomaly["method"],
                "path": anomaly["path"],
                "status": anomaly["status"],
                "score": anomaly["anomaly_score"],
                "description": anomaly.get("anomaly_description", "")
            })
        
        # Converter para lista ordenada por timestamp
        timeline_list = sorted(timeline_data.values(), key=lambda x: x["timestamp"])
        
        # Gerar dados para gráfico
        chart_data = {
            "labels": [item["timestamp"] for item in timeline_list],
            "datasets": [
                {
                    "label": "Número de Anomalias",
                    "data": [item["anomaly_count"] for item in timeline_list],
                    "borderColor": "#e74c3c",
                    "backgroundColor": "rgba(231, 76, 60, 0.1)",
                    "yAxisID": "y"
                },
                {
                    "label": "Score Médio",
                    "data": [round(item["avg_score"], 3) for item in timeline_list],
                    "borderColor": "#f39c12",
                    "backgroundColor": "rgba(243, 156, 18, 0.1)",
                    "yAxisID": "y1"
                }
            ]
        }
        
        return {
            "status": "success",
            "model_used": model_name,
            "total_anomalies": len(anomalies),
            "time_interval_minutes": interval_minutes,
            "hours_back": hours_back,
            "threshold_used": threshold,
            "timeline_data": timeline_list,
            "chart_data": chart_data,
            "summary": {
                "total_intervals": len(timeline_list),
                "max_anomalies_per_interval": max([item["anomaly_count"] for item in timeline_list]) if timeline_list else 0,
                "avg_anomalies_per_interval": sum([item["anomaly_count"] for item in timeline_list]) / len(timeline_list) if timeline_list else 0,
                "max_score": max([item["avg_score"] for item in timeline_list]) if timeline_list else 0,
                "avg_score": sum([item["avg_score"] for item in timeline_list]) / len(timeline_list) if timeline_list else 0
            }
        }
        
    except Exception as e:
        return {"error": f"Erro ao gerar dados temporais: {str(e)}"} 