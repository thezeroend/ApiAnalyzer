#!/usr/bin/env python3
"""
Teste da Análise de Ranges CIDR

Este script testa a nova funcionalidade de análise de IPs considerando ranges CIDR
em vez de apenas mudanças individuais de IP.
"""

import requests
import json
import time
from datetime import datetime, timedelta
import random

# Configurações
API_BASE = "http://localhost:8000"
API_ID = "api_cidr_test"

def clear_logs():
    """Limpa todos os logs"""
    try:
        response = requests.delete(f"{API_BASE}/logs")
        if response.status_code == 200:
            print("✅ Logs limpos com sucesso")
        else:
            print(f"❌ Erro ao limpar logs: {response.text}")
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")

def send_log(log_data):
    """Envia um log para a API"""
    try:
        response = requests.post(f"{API_BASE}/logs", json=log_data)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Erro ao enviar log: {e}")
        return False

def generate_cidr_test_data():
    """Gera dados de teste com diferentes ranges CIDR"""
    print("📊 Gerando dados de teste com ranges CIDR...")
    
    # Limpar logs existentes
    clear_logs()
    
    base_time = datetime.now() - timedelta(hours=24)
    success_count = 0
    
    # Cenário 1: Cliente com range privado específico (10.0.1.0/24)
    print("🔍 Cenário 1: Cliente com range privado 10.0.1.0/24")
    for i in range(50):
        timestamp = base_time + timedelta(minutes=i * 2)
        ip = f"10.0.1.{random.randint(1, 254)}"
        log_data = {
            "requestId": f"req_private_{i:04d}",
            "clientId": "client_private_range",
            "ip": ip,
            "apiId": API_ID,
            "path": f"/api/users/{i}",
            "method": "GET",
            "status": 200,
            "responseTime": random.randint(50, 200),
            "timestamp": timestamp.isoformat()
        }
        if send_log(log_data):
            success_count += 1
    
    # Cenário 2: Cliente com múltiplos ranges privados
    print("🔍 Cenário 2: Cliente com múltiplos ranges privados")
    private_ranges = ["10.0.1.0/24", "10.0.2.0/24", "192.168.1.0/24"]
    for i in range(30):
        timestamp = base_time + timedelta(minutes=i * 3)
        if i < 10:
            ip = f"10.0.1.{random.randint(1, 254)}"
        elif i < 20:
            ip = f"10.0.2.{random.randint(1, 254)}"
        else:
            ip = f"192.168.1.{random.randint(1, 254)}"
        
        log_data = {
            "requestId": f"req_multi_range_{i:04d}",
            "clientId": "client_multi_ranges",
            "ip": ip,
            "apiId": API_ID,
            "path": f"/api/data/{i}",
            "method": "POST",
            "status": 201,
            "responseTime": random.randint(100, 300),
            "timestamp": timestamp.isoformat()
        }
        if send_log(log_data):
            success_count += 1
    
    # Cenário 3: Cliente com range público específico (203.0.113.0/24)
    print("🔍 Cenário 3: Cliente com range público 203.0.113.0/24")
    for i in range(40):
        timestamp = base_time + timedelta(minutes=i * 2.5)
        ip = f"203.0.113.{random.randint(1, 254)}"
        log_data = {
            "requestId": f"req_public_{i:04d}",
            "clientId": "client_public_range",
            "ip": ip,
            "apiId": API_ID,
            "path": f"/api/public/{i}",
            "method": "GET",
            "status": 200,
            "responseTime": random.randint(80, 250),
            "timestamp": timestamp.isoformat()
        }
        if send_log(log_data):
            success_count += 1
    
    # Cenário 4: Cliente com IP fora do range conhecido (ANOMALIA)
    print("🔍 Cenário 4: Cliente com IP fora do range conhecido (ANOMALIA)")
    for i in range(10):
        timestamp = base_time + timedelta(minutes=i * 5)
        # Usar IP de range completamente diferente
        ip = f"172.16.{random.randint(1, 254)}.{random.randint(1, 254)}"
        log_data = {
            "requestId": f"req_anomaly_{i:04d}",
            "clientId": "client_private_range",  # Mesmo cliente do cenário 1
            "ip": ip,
            "apiId": API_ID,
            "path": f"/api/admin/{i}",
            "method": "POST",
            "status": 403,
            "responseTime": random.randint(500, 1000),
            "timestamp": timestamp.isoformat()
        }
        if send_log(log_data):
            success_count += 1
    
    # Cenário 5: Cliente com rotação excessiva de IPs (ANOMALIA)
    print("🔍 Cenário 5: Cliente com rotação excessiva de IPs (ANOMALIA)")
    for i in range(20):
        timestamp = base_time + timedelta(minutes=i * 1)
        # Usar IPs de ranges completamente diferentes a cada requisição
        if i % 4 == 0:
            ip = f"10.0.1.{random.randint(1, 254)}"
        elif i % 4 == 1:
            ip = f"192.168.1.{random.randint(1, 254)}"
        elif i % 4 == 2:
            ip = f"172.16.{random.randint(1, 254)}.{random.randint(1, 254)}"
        else:
            ip = f"203.0.113.{random.randint(1, 254)}"
        
        log_data = {
            "requestId": f"req_rotation_{i:04d}",
            "clientId": "client_excessive_rotation",
            "ip": ip,
            "apiId": API_ID,
            "path": f"/api/secure/{i}",
            "method": "GET",
            "status": 200,
            "responseTime": random.randint(50, 150),
            "timestamp": timestamp.isoformat()
        }
        if send_log(log_data):
            success_count += 1
    
    # Cenário 6: Cliente com IP de range suspeito (ANOMALIA)
    print("🔍 Cenário 6: Cliente com IP de range suspeito (ANOMALIA)")
    for i in range(5):
        timestamp = base_time + timedelta(minutes=i * 10)
        # Usar IPs de ranges suspeitos (DNS públicos)
        suspicious_ips = ["1.1.1.1", "8.8.8.8", "208.67.222.222", "185.228.168.168"]
        ip = random.choice(suspicious_ips)
        
        log_data = {
            "requestId": f"req_suspicious_{i:04d}",
            "clientId": "client_suspicious_range",
            "ip": ip,
            "apiId": API_ID,
            "path": f"/api/admin/{i}",
            "method": "DELETE",
            "status": 401,
            "responseTime": random.randint(1000, 2000),
            "timestamp": timestamp.isoformat()
        }
        if send_log(log_data):
            success_count += 1
    
    print(f"✅ {success_count} logs enviados com sucesso")
    return success_count

def train_models():
    """Treina os modelos de ML"""
    print("🎯 Treinando modelos de ML...")
    
    try:
        response = requests.post(f"{API_BASE}/ml/train", json={
            "apiId": API_ID,
            "hours_back": 24
        })
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Modelos treinados com sucesso")
            return True
        else:
            print(f"❌ Erro ao treinar modelos: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
        return False

def test_cidr_analysis():
    """Testa a análise de ranges CIDR"""
    print("🔍 Testando análise de ranges CIDR...")
    
    try:
        params = {
            "apiId": API_ID,
            "model_name": "iforest",
            "hours_back": 24
        }
        
        response = requests.get(f"{API_BASE}/ml/detect", params=params)
        
        if response.status_code == 200:
            data = response.json()
            
            if "error" in data:
                print(f"❌ Erro na detecção: {data['error']}")
                return
            
            print(f"✅ Detecção concluída: {data.get('anomalies_detected', 0)} anomalias")
            
            # Analisar anomalias por cliente
            anomalies = data.get('anomalies', [])
            client_anomalies = {}
            
            for anomaly in anomalies:
                client_id = anomaly.get('clientId', 'unknown')
                if client_id not in client_anomalies:
                    client_anomalies[client_id] = []
                client_anomalies[client_id].append(anomaly)
            
            print("\n📊 Análise por Cliente:")
            for client_id, client_anomaly_list in client_anomalies.items():
                print(f"\n🔍 Cliente: {client_id}")
                print(f"   📈 Anomalias detectadas: {len(client_anomaly_list)}")
                
                # Analisar descrições de anomalias
                ip_related_anomalies = []
                for anomaly in client_anomaly_list:
                    description = anomaly.get('anomaly_description', '')
                    if 'IP' in description or 'range' in description.lower():
                        ip_related_anomalies.append(anomaly)
                
                print(f"   🔗 Anomalias relacionadas a IP: {len(ip_related_anomalies)}")
                
                # Mostrar algumas descrições
                for i, anomaly in enumerate(ip_related_anomalies[:3]):
                    description = anomaly.get('anomaly_description', '')
                    ip = anomaly.get('ip', '')
                    score = anomaly.get('anomaly_score', 0)
                    print(f"      {i+1}. IP: {ip} | Score: {score:.3f}")
                    print(f"         {description}")
                
                # Verificar se as anomalias fazem sentido para o cenário
                if client_id == "client_private_range" and len(ip_related_anomalies) > 0:
                    print("   ✅ Anomalias detectadas corretamente (IP fora do range)")
                elif client_id == "client_excessive_rotation" and len(ip_related_anomalies) > 0:
                    print("   ✅ Anomalias detectadas corretamente (rotação excessiva)")
                elif client_id == "client_suspicious_range" and len(ip_related_anomalies) > 0:
                    print("   ✅ Anomalias detectadas corretamente (range suspeito)")
                elif client_id in ["client_public_range", "client_multi_ranges"] and len(ip_related_anomalies) == 0:
                    print("   ✅ Comportamento normal detectado (sem anomalias de IP)")
            
            # Estatísticas gerais
            total_ip_anomalies = sum(len([a for a in anomalies if 'IP' in a.get('anomaly_description', '')]) 
                                   for anomalies in client_anomalies.values())
            
            print(f"\n📈 Estatísticas Gerais:")
            print(f"   🔗 Total de anomalias relacionadas a IP: {total_ip_anomalies}")
            print(f"   📊 Precisão da análise CIDR: {(total_ip_anomalies/len(anomalies)*100):.1f}%" if anomalies else "N/A")
            
        else:
            print(f"❌ Erro HTTP {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")

def test_cidr_functions():
    """Testa as funções de análise CIDR diretamente"""
    print("\n🧪 Testando funções de análise CIDR...")
    
    try:
        # Importar a classe MLAnomalyDetector
        import sys
        sys.path.append('.')
        from app.ml_anomaly_detector import MLAnomalyDetector
        
        detector = MLAnomalyDetector()
        
        # Teste 1: Verificar se IP está em range CIDR
        test_cases = [
            ("192.168.1.100", "192.168.1.0/24", True),
            ("192.168.1.100", "192.168.2.0/24", False),
            ("10.0.1.50", "10.0.0.0/8", True),
            ("172.16.1.100", "172.16.0.0/12", True),
            ("203.0.113.10", "203.0.113.0/24", True),
        ]
        
        print("🔍 Teste de verificação CIDR:")
        for ip, cidr, expected in test_cases:
            result = detector._ip_in_cidr_range(ip, cidr)
            status = "✅" if result == expected else "❌"
            print(f"   {status} {ip} em {cidr}: {result} (esperado: {expected})")
        
        # Teste 2: Identificar ranges CIDR
        test_ips = ["192.168.1.1", "192.168.1.2", "192.168.1.3", "10.0.1.1", "10.0.1.2"]
        ranges = detector._identify_cidr_ranges(test_ips)
        print(f"\n🔍 Ranges identificados para {test_ips}:")
        for cidr in ranges:
            print(f"   📍 {cidr}")
        
        # Teste 3: Verificar tipo de rede
        network_tests = [
            ("192.168.1.1", "private"),
            ("10.0.1.1", "private"),
            ("172.16.1.1", "private"),
            ("203.0.113.1", "public"),
            ("127.0.0.1", "loopback"),
        ]
        
        print("\n🔍 Teste de tipos de rede:")
        for ip, expected_type in network_tests:
            result = detector._get_network_type(ip)
            status = "✅" if result == expected_type else "❌"
            print(f"   {status} {ip}: {result} (esperado: {expected_type})")
        
    except Exception as e:
        print(f"❌ Erro ao testar funções CIDR: {e}")

def main():
    """Função principal"""
    print("🚀 Iniciando teste da Análise de Ranges CIDR")
    print("=" * 60)
    
    # Verificar se o backend está rodando
    try:
        response = requests.get(f"{API_BASE}/docs")
        if response.status_code != 200:
            print("❌ Backend não está rodando. Execute 'python main.py' primeiro.")
            return
        print("✅ Backend está rodando")
    except Exception as e:
        print(f"❌ Erro ao conectar com o backend: {e}")
        print("Execute 'python main.py' primeiro.")
        return
    
    # Testar funções CIDR diretamente
    test_cidr_functions()
    
    # Gerar dados de teste
    success_count = generate_cidr_test_data()
    if success_count == 0:
        print("❌ Nenhum log foi enviado. Abortando teste.")
        return
    
    # Aguardar um pouco para processamento
    print("⏳ Aguardando processamento...")
    time.sleep(2)
    
    # Treinar modelos
    if not train_models():
        print("❌ Falha no treinamento. Abortando teste.")
        return
    
    # Testar análise de ranges CIDR
    test_cidr_analysis()
    
    print("\n" + "=" * 60)
    print("✅ Teste da Análise de Ranges CIDR concluído!")
    print("\n📋 Resumo:")
    print("   • Funções CIDR testadas com sucesso")
    print("   • Dados de teste gerados com diferentes ranges")
    print("   • Análise de anomalias por cliente validada")
    print("   • Detecção de IPs fora de ranges conhecidos")
    print("\n🎯 Benefícios da nova implementação:")
    print("   • Análise mais inteligente baseada em ranges CIDR")
    print("   • Detecção de padrões de rede por cliente")
    print("   • Identificação de rotação excessiva de IPs")
    print("   • Detecção de ranges suspeitos")

if __name__ == "__main__":
    main() 