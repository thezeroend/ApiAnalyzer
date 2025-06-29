#!/usr/bin/env python3
"""
Script de teste para a funcionalidade de detecção de anomalias
"""

import requests
import json
from datetime import datetime, timedelta
import random

# Configuração
API_BASE = "http://localhost:8000"

def create_test_logs():
    """Cria logs de teste para demonstrar as anomalias"""
    
    # Dados de teste
    test_data = [
        # Cliente normal com IP consistente
        {
            "requestId": "req_001", "clientId": "client_normal", "ip": "192.168.1.100",
            "apiId": "api_test", "path": "/users", "method": "GET", "status": 200,
            "timestamp": (datetime.now() - timedelta(hours=2)).isoformat()
        },
        {
            "requestId": "req_002", "clientId": "client_normal", "ip": "192.168.1.100",
            "apiId": "api_test", "path": "/users/1", "method": "GET", "status": 200,
            "timestamp": (datetime.now() - timedelta(hours=1)).isoformat()
        },
        
        # Cliente com IP novo (anomalia)
        {
            "requestId": "req_003", "clientId": "client_suspicious", "ip": "192.168.1.101",
            "apiId": "api_test", "path": "/users", "method": "GET", "status": 200,
            "timestamp": (datetime.now() - timedelta(hours=25)).isoformat()
        },
        {
            "requestId": "req_004", "clientId": "client_suspicious", "ip": "8.8.8.8",  # IP novo!
            "apiId": "api_test", "path": "/admin", "method": "GET", "status": 403,
            "timestamp": (datetime.now() - timedelta(hours=1)).isoformat()
        },
        
        # Cliente com múltiplos IPs
        {
            "requestId": "req_005", "clientId": "client_multiple_ips", "ip": "10.0.0.1",
            "apiId": "api_test", "path": "/api/data", "method": "POST", "status": 200,
            "timestamp": (datetime.now() - timedelta(hours=3)).isoformat()
        },
        {
            "requestId": "req_006", "clientId": "client_multiple_ips", "ip": "10.0.0.2",
            "apiId": "api_test", "path": "/api/data", "method": "POST", "status": 200,
            "timestamp": (datetime.now() - timedelta(hours=2)).isoformat()
        },
        {
            "requestId": "req_007", "clientId": "client_multiple_ips", "ip": "10.0.0.3",
            "apiId": "api_test", "path": "/api/data", "method": "POST", "status": 200,
            "timestamp": (datetime.now() - timedelta(hours=1)).isoformat()
        },
        
        # Cliente com alta taxa de erro
        {
            "requestId": "req_008", "clientId": "client_high_errors", "ip": "172.16.0.1",
            "apiId": "api_test", "path": "/login", "method": "POST", "status": 401,
            "timestamp": (datetime.now() - timedelta(hours=2)).isoformat()
        },
        {
            "requestId": "req_009", "clientId": "client_high_errors", "ip": "172.16.0.1",
            "apiId": "api_test", "path": "/login", "method": "POST", "status": 401,
            "timestamp": (datetime.now() - timedelta(hours=1, minutes=30)).isoformat()
        },
        {
            "requestId": "req_010", "clientId": "client_high_errors", "ip": "172.16.0.1",
            "apiId": "api_test", "path": "/login", "method": "POST", "status": 401,
            "timestamp": (datetime.now() - timedelta(hours=1)).isoformat()
        },
        {
            "requestId": "req_011", "clientId": "client_high_errors", "ip": "172.16.0.1",
            "apiId": "api_test", "path": "/users", "method": "GET", "status": 200,
            "timestamp": (datetime.now() - timedelta(minutes=30)).isoformat()
        },
        
        # Cliente com muitas requisições
        {
            "requestId": "req_012", "clientId": "client_high_volume", "ip": "203.0.113.1",
            "apiId": "api_test", "path": "/api/test", "method": "GET", "status": 200,
            "timestamp": (datetime.now() - timedelta(hours=1)).isoformat()
        }
    ]
    
    # Adicionar mais requisições para o cliente de alto volume
    for i in range(25):
        test_data.append({
            "requestId": f"req_volume_{i}", "clientId": "client_high_volume", "ip": "203.0.113.1",
            "apiId": "api_test", "path": f"/api/test/{i}", "method": "GET", "status": 200,
            "timestamp": (datetime.now() - timedelta(minutes=i)).isoformat()
        })
    
    print("Enviando logs de teste...")
    
    success_count = 0
    for log_data in test_data:
        try:
            response = requests.post(f"{API_BASE}/logs", json=log_data)
            if response.status_code == 200:
                success_count += 1
            else:
                print(f"Erro ao enviar log {log_data['requestId']}: {response.status_code}")
        except Exception as e:
            print(f"Erro de conexão: {e}")
    
    print(f"✅ {success_count}/{len(test_data)} logs enviados com sucesso!")

def test_anomalies():
    """Testa a funcionalidade de detecção de anomalias"""
    
    print("\n🧪 Testando detecção de anomalias...")
    
    try:
        # Testar anomalias gerais
        response = requests.get(f"{API_BASE}/ip-anomalies")
        if response.status_code == 200:
            data = response.json()
            print("✅ Anomalias detectadas:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(f"❌ Erro ao obter anomalias: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")

def test_basic_stats():
    """Testa estatísticas básicas"""
    
    print("\n📊 Testando estatísticas básicas...")
    
    try:
        response = requests.get(f"{API_BASE}/stats/api_test")
        if response.status_code == 200:
            data = response.json()
            print("✅ Estatísticas básicas:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(f"❌ Erro ao obter estatísticas: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")

if __name__ == "__main__":
    print("🚀 Iniciando testes da funcionalidade de anomalias...")
    
    # Verificar se o servidor está rodando
    try:
        response = requests.get(f"{API_BASE}/docs")
        print("✅ Servidor está rodando!")
    except:
        print("❌ Servidor não está rodando. Execute: python main.py")
        exit(1)
    
    # Criar dados de teste
    create_test_logs()
    
    # Aguardar um pouco para processar
    import time
    time.sleep(2)
    
    # Testar funcionalidades
    test_basic_stats()
    test_anomalies()
    
    print("\n🎉 Testes concluídos! Verifique o frontend para ver os resultados.") 