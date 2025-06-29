#!/usr/bin/env python3
"""
Teste rápido para verificar se a funcionalidade de anomalias está funcionando
"""

import requests
import json
from datetime import datetime, timedelta

API_BASE = "http://localhost:8000"

def quick_test():
    print("🧪 Teste Rápido da Funcionalidade de Anomalias")
    print("=" * 50)
    
    # 1. Limpar logs existentes
    print("1. Limpando logs existentes...")
    try:
        response = requests.delete(f"{API_BASE}/logs")
        print(f"   ✅ {response.json()}")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return
    
    # 2. Criar logs de teste simples
    print("\n2. Criando logs de teste...")
    
    test_logs = [
        # Cliente normal
        {
            "requestId": "test_001", "clientId": "client_a", "ip": "192.168.1.100",
            "apiId": "test_api", "path": "/users", "method": "GET", "status": 200,
            "timestamp": (datetime.now() - timedelta(hours=2)).isoformat()
        },
        # Cliente com IP novo (anomalia)
        {
            "requestId": "test_002", "clientId": "client_a", "ip": "8.8.8.8",  # IP novo!
            "apiId": "test_api", "path": "/admin", "method": "GET", "status": 403,
            "timestamp": (datetime.now() - timedelta(hours=1)).isoformat()
        },
        # Cliente com múltiplos IPs
        {
            "requestId": "test_003", "clientId": "client_b", "ip": "10.0.0.1",
            "apiId": "test_api", "path": "/data", "method": "POST", "status": 200,
            "timestamp": (datetime.now() - timedelta(hours=2)).isoformat()
        },
        {
            "requestId": "test_004", "clientId": "client_b", "ip": "10.0.0.2",
            "apiId": "test_api", "path": "/data", "method": "POST", "status": 200,
            "timestamp": (datetime.now() - timedelta(hours=1)).isoformat()
        },
        {
            "requestId": "test_005", "clientId": "client_b", "ip": "10.0.0.3",
            "apiId": "test_api", "path": "/data", "method": "POST", "status": 200,
            "timestamp": datetime.now().isoformat()
        }
    ]
    
    success_count = 0
    for log in test_logs:
        try:
            response = requests.post(f"{API_BASE}/logs", json=log)
            if response.status_code == 200:
                success_count += 1
        except Exception as e:
            print(f"   ❌ Erro ao enviar log: {e}")
    
    print(f"   ✅ {success_count}/{len(test_logs)} logs enviados")
    
    # 3. Testar estatísticas básicas
    print("\n3. Testando estatísticas básicas...")
    try:
        response = requests.get(f"{API_BASE}/stats/test_api")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Total de logs: {data.get('total_logs', 0)}")
            print(f"   ✅ Clientes: {list(data.get('requests_by_client', {}).keys())}")
        else:
            print(f"   ❌ Erro: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    # 4. Testar detecção de anomalias de IP
    print("\n4. Testando detecção de anomalias de IP...")
    try:
        response = requests.get(f"{API_BASE}/ip-anomalies?hours_back=24")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Clientes analisados: {data.get('summary', {}).get('total_clients_analyzed', 0)}")
            print(f"   ✅ Anomalias detectadas: {data.get('summary', {}).get('total_anomalies', 0)}")
            
            if data.get('new_ips'):
                print(f"   🆕 IPs novos: {list(data['new_ips'].keys())}")
            if data.get('multiple_ips'):
                print(f"   🌐 Múltiplos IPs: {list(data['multiple_ips'].keys())}")
            if data.get('suspicious_activity'):
                print(f"   ⚠️ Atividade suspeita: {list(data['suspicious_activity'].keys())}")
                
        else:
            print(f"   ❌ Erro: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Teste concluído! Verifique o frontend para ver os resultados.")

if __name__ == "__main__":
    quick_test() 