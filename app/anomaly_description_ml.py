#!/usr/bin/env python3
"""
Módulo de Machine Learning para geração de descrições precisas de anomalias
Usa técnicas de NLP e análise de padrões para criar descrições mais inteligentes
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import json
from collections import Counter, defaultdict
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import joblib
import os

class AnomalyDescriptionML:
    """
    Sistema de ML para gerar descrições precisas de anomalias
    """
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=100, stop_words='english')
        self.scaler = StandardScaler()
        self.pca = PCA(n_components=10)
        self.cluster_model = KMeans(n_clusters=8, random_state=42)
        self.pattern_templates = self._load_pattern_templates()
        self.severity_classifier = self._load_severity_classifier()
        self.models_dir = "models"
        os.makedirs(self.models_dir, exist_ok=True)
        
    def _load_pattern_templates(self) -> Dict[str, List[str]]:
        """Carrega templates de padrões para diferentes tipos de anomalias"""
        return {
            "network": [
                "Detectada atividade de rede anômala: {details}",
                "Padrão de tráfego suspeito identificado: {details}",
                "Anomalia de conectividade de rede: {details}",
                "Comportamento de rede fora do padrão: {details}"
            ],
            "security": [
                "Possível tentativa de segurança: {details}",
                "Atividade suspeita detectada: {details}",
                "Padrão de acesso anômalo: {details}",
                "Comportamento de segurança atípico: {details}"
            ],
            "performance": [
                "Degradação de performance identificada: {details}",
                "Anomalia de performance detectada: {details}",
                "Comportamento de sistema anômalo: {details}",
                "Padrão de performance suspeito: {details}"
            ],
            "behavioral": [
                "Mudança de comportamento detectada: {details}",
                "Padrão de uso anômalo: {details}",
                "Comportamento atípico identificado: {details}",
                "Anomalia comportamental: {details}"
            ]
        }
    
    def _load_severity_classifier(self) -> Dict[str, float]:
        """Classificador de severidade baseado em scores"""
        return {
            "critical": 0.8,
            "high": 0.6,
            "medium": 0.4,
            "low": 0.2
        }
    
    def extract_contextual_features(self, log_data: Dict, all_logs: List[Dict]) -> Dict:
        """Extrai features contextuais para análise ML"""
        features = {}
        
        # Features temporais
        timestamp = datetime.fromisoformat(log_data['timestamp'].replace('Z', '+00:00'))
        features['hour'] = timestamp.hour
        features['day_of_week'] = timestamp.weekday()
        features['is_business_hours'] = 8 <= timestamp.hour <= 18
        features['is_weekend'] = timestamp.weekday() >= 5
        
        # Features de rede
        features['ip_numeric'] = self._ip_to_numeric(log_data['ip'])
        features['is_private_ip'] = self._is_private_ip(log_data['ip'])
        features['ip_frequency'] = self._calculate_ip_frequency(log_data['ip'], all_logs)
        
        # Features de comportamento
        features['client_frequency'] = self._calculate_client_frequency(log_data['clientId'], all_logs)
        features['api_frequency'] = self._calculate_api_frequency(log_data['apiId'], all_logs)
        features['method_frequency'] = self._calculate_method_frequency(log_data['method'], all_logs)
        
        # Features de status
        features['status_code'] = log_data['status']
        features['is_error'] = 400 <= log_data['status'] < 600
        features['is_server_error'] = 500 <= log_data['status'] < 600
        features['is_client_error'] = 400 <= log_data['status'] < 500
        
        # Features de path
        features['path_length'] = len(log_data['path'])
        features['path_depth'] = log_data['path'].count('/')
        features['is_api_path'] = '/api/' in log_data['path']
        features['is_admin_path'] = '/admin/' in log_data['path']
        features['is_auth_path'] = '/auth/' in log_data['path']
        
        return features
    
    def _ip_to_numeric(self, ip: str) -> int:
        """Converte IP para valor numérico"""
        try:
            parts = ip.split('.')
            return sum(int(part) * (256 ** (3 - i)) for i, part in enumerate(parts))
        except:
            return 0
    
    def _is_private_ip(self, ip: str) -> bool:
        """Verifica se é IP privado"""
        try:
            parts = [int(part) for part in ip.split('.')]
            return (parts[0] == 10 or 
                   (parts[0] == 172 and 16 <= parts[1] <= 31) or
                   (parts[0] == 192 and parts[1] == 168))
        except:
            return False
    
    def _calculate_ip_frequency(self, ip: str, all_logs: List[Dict]) -> float:
        """Calcula frequência do IP nos logs"""
        ip_count = sum(1 for log in all_logs if log['ip'] == ip)
        return ip_count / len(all_logs) if all_logs else 0
    
    def _calculate_client_frequency(self, client_id: str, all_logs: List[Dict]) -> float:
        """Calcula frequência do cliente nos logs"""
        client_count = sum(1 for log in all_logs if log['clientId'] == client_id)
        return client_count / len(all_logs) if all_logs else 0
    
    def _calculate_api_frequency(self, api_id: str, all_logs: List[Dict]) -> float:
        """Calcula frequência da API nos logs"""
        api_count = sum(1 for log in all_logs if log['apiId'] == api_id)
        return api_count / len(all_logs) if all_logs else 0
    
    def _calculate_method_frequency(self, method: str, all_logs: List[Dict]) -> float:
        """Calcula frequência do método nos logs"""
        method_count = sum(1 for log in all_logs if log['method'] == method)
        return method_count / len(all_logs) if all_logs else 0
    
    def classify_anomaly_type(self, features: Dict, score: float) -> str:
        """Classifica o tipo de anomalia baseado nas features"""
        # Análise de padrões para classificação
        if features.get('is_server_error', False):
            return "performance"
        elif features.get('is_client_error', False):
            return "security"
        elif features.get('ip_frequency', 0) < 0.01:  # IP muito raro
            return "security"
        elif features.get('client_frequency', 0) < 0.01:  # Cliente muito raro
            return "security"
        elif features.get('is_admin_path', False):
            return "security"
        elif features.get('is_auth_path', False):
            return "security"
        elif not features.get('is_private_ip', True):  # IP público
            return "network"
        elif features.get('hour', 0) < 6 or features.get('hour', 0) > 22:  # Horário atípico
            return "behavioral"
        else:
            return "behavioral"
    
    def determine_severity(self, score: float, features: Dict) -> str:
        """Determina a severidade da anomalia"""
        # Ajusta severidade baseado em fatores contextuais
        adjusted_score = score
        
        # Aumenta severidade para erros de servidor
        if features.get('is_server_error', False):
            adjusted_score += 0.2
        
        # Aumenta severidade para IPs públicos
        if not features.get('is_private_ip', True):
            adjusted_score += 0.1
        
        # Aumenta severidade para horários atípicos
        if not features.get('is_business_hours', True):
            adjusted_score += 0.05
        
        # Aumenta severidade para paths administrativos
        if features.get('is_admin_path', False):
            adjusted_score += 0.15
        
        # Classifica severidade
        if adjusted_score >= self.severity_classifier["critical"]:
            return "critical"
        elif adjusted_score >= self.severity_classifier["high"]:
            return "high"
        elif adjusted_score >= self.severity_classifier["medium"]:
            return "medium"
        else:
            return "low"
    
    def generate_contextual_details(self, log_data: Dict, features: Dict, anomaly_type: str) -> str:
        """Gera detalhes contextuais específicos para o tipo de anomalia"""
        details = []
        
        if anomaly_type == "security":
            if features.get('is_admin_path', False):
                details.append("acesso a área administrativa")
            if features.get('is_auth_path', False):
                details.append("tentativa de autenticação")
            if not features.get('is_private_ip', True):
                details.append(f"IP público ({log_data['ip']})")
            if features.get('client_frequency', 0) < 0.01:
                details.append("cliente não reconhecido")
            if features.get('method_frequency', 0) < 0.05:
                details.append(f"método HTTP incomum ({log_data['method']})")
                
        elif anomaly_type == "network":
            if not features.get('is_private_ip', True):
                details.append(f"origem externa ({log_data['ip']})")
            if features.get('ip_frequency', 0) < 0.01:
                details.append("IP não reconhecido")
            if features.get('is_weekend', False):
                details.append("atividade em fim de semana")
            if not features.get('is_business_hours', True):
                details.append("atividade fora do horário comercial")
                
        elif anomaly_type == "performance":
            if features.get('is_server_error', False):
                details.append(f"erro de servidor ({log_data['status']})")
            if features.get('api_frequency', 0) > 0.5:
                details.append("alta frequência de requisições")
            if features.get('path_depth', 0) > 3:
                details.append("path muito profundo")
                
        elif anomaly_type == "behavioral":
            if not features.get('is_business_hours', True):
                details.append("horário atípico")
            if features.get('is_weekend', False):
                details.append("atividade em fim de semana")
            if features.get('method_frequency', 0) < 0.1:
                details.append(f"método raramente usado ({log_data['method']})")
            if features.get('client_frequency', 0) < 0.01:
                details.append("cliente com padrão incomum")
        
        return ", ".join(details) if details else "padrão anômalo detectado"
    
    def generate_ml_description(self, log_data: Dict, score: float, all_logs: List[Dict]) -> str:
        """Gera descrição usando ML e análise contextual"""
        # Extrai features contextuais
        features = self.extract_contextual_features(log_data, all_logs)
        
        # Classifica tipo de anomalia
        anomaly_type = self.classify_anomaly_type(features, score)
        
        # Determina severidade
        severity = self.determine_severity(score, features)
        
        # Gera detalhes contextuais
        details = self.generate_contextual_details(log_data, features, anomaly_type)
        
        # Seleciona template apropriado
        templates = self.pattern_templates.get(anomaly_type, self.pattern_templates["behavioral"])
        template = np.random.choice(templates)
        
        # Constrói descrição
        description = template.format(details=details)
        
        # Adiciona informações de severidade
        severity_indicators = {
            "critical": "🚨 CRÍTICO",
            "high": "⚠️ ALTO",
            "medium": "⚡ MÉDIO", 
            "low": "ℹ️ BAIXO"
        }
        
        severity_indicator = severity_indicators.get(severity, "ℹ️")
        
        # Adiciona contexto temporal
        timestamp = datetime.fromisoformat(log_data['timestamp'].replace('Z', '+00:00'))
        time_context = timestamp.strftime("%d/%m/%Y %H:%M")
        
        # Monta descrição final
        final_description = f"{severity_indicator} - {description} (Score: {score:.3f}, {time_context})"
        
        return final_description
    
    def analyze_patterns(self, anomalies: List[Dict]) -> Dict:
        """Analisa padrões entre múltiplas anomalias"""
        if not anomalies:
            return {}
        
        # Agrupa anomalias por tipo
        type_groups = defaultdict(list)
        for anomaly in anomalies:
            features = self.extract_contextual_features(anomaly, [a for a in anomalies])
            anomaly_type = self.classify_anomaly_type(features, anomaly.get('anomaly_score', 0))
            type_groups[anomaly_type].append(anomaly)
        
        # Analisa padrões por grupo
        pattern_analysis = {}
        for anomaly_type, group in type_groups.items():
            pattern_analysis[anomaly_type] = {
                'count': len(group),
                'percentage': len(group) / len(anomalies) * 100,
                'avg_score': np.mean([a.get('anomaly_score', 0) for a in group]),
                'common_ips': Counter([a['ip'] for a in group]).most_common(3),
                'common_clients': Counter([a['clientId'] for a in group]).most_common(3),
                'common_apis': Counter([a['apiId'] for a in group]).most_common(3),
                'time_distribution': self._analyze_time_distribution(group)
            }
        
        return pattern_analysis
    
    def _analyze_time_distribution(self, anomalies: List[Dict]) -> Dict:
        """Analisa distribuição temporal das anomalias"""
        hours = []
        for anomaly in anomalies:
            timestamp = datetime.fromisoformat(anomaly['timestamp'].replace('Z', '+00:00'))
            hours.append(timestamp.hour)
        
        hour_counts = Counter(hours)
        return {
            'peak_hours': hour_counts.most_common(3),
            'total_hours': len(set(hours)),
            'hourly_distribution': dict(hour_counts)
        }
    
    def train_description_model(self, training_data: List[Dict]) -> bool:
        """Treina modelo de descrição com dados históricos"""
        try:
            # Extrai features de todos os logs
            all_features = []
            for log in training_data:
                features = self.extract_contextual_features(log, training_data)
                all_features.append(features)
            
            # Converte para DataFrame
            df = pd.DataFrame(all_features)
            
            # Normaliza features
            scaled_features = self.scaler.fit_transform(df)
            
            # Reduz dimensionalidade
            reduced_features = self.pca.fit_transform(scaled_features)
            
            # Treina modelo de clustering
            self.cluster_model.fit(reduced_features)
            
            # Salva modelos treinados
            self._save_models()
            
            return True
            
        except Exception as e:
            print(f"Erro ao treinar modelo de descrição: {e}")
            return False
    
    def _save_models(self):
        """Salva modelos treinados"""
        try:
            joblib.dump(self.scaler, os.path.join(self.models_dir, 'description_scaler.pkl'))
            joblib.dump(self.pca, os.path.join(self.models_dir, 'description_pca.pkl'))
            joblib.dump(self.cluster_model, os.path.join(self.models_dir, 'description_cluster.pkl'))
        except Exception as e:
            print(f"Erro ao salvar modelos: {e}")
    
    def load_models(self) -> bool:
        """Carrega modelos treinados"""
        try:
            self.scaler = joblib.load(os.path.join(self.models_dir, 'description_scaler.pkl'))
            self.pca = joblib.load(os.path.join(self.models_dir, 'description_pca.pkl'))
            self.cluster_model = joblib.load(os.path.join(self.models_dir, 'description_cluster.pkl'))
            return True
        except Exception as e:
            print(f"Erro ao carregar modelos: {e}")
            return False

# Instância global
description_ml = AnomalyDescriptionML() 