#!/usr/bin/env python3
"""
Teste para verificar se a funcionalidade de ML de descrições está funcionando
"""

import requests
import json
import time
from datetime import datetime, timedelta

# Configurações
base_url = "http://localhost:8000"

def test_descriptions_functionality():
    """Testa todas as funcionalidades de ML de descrições"""
    print("🧪 Testando funcionalidade de ML de descrições...")
    
    # 1. Teste de treinamento
    print("\n1️⃣ Testando treinamento do modelo...")
    try:
        response = requests.post(f"{base_url}/ml/descriptions/train")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Treinamento bem-sucedido: {result.get('message', 'N/A')}")
            print(f"   Logs utilizados: {result.get('logs_used', 'N/A')}")
        else:
            result = response.json()
            print(f"❌ Erro no treinamento: {result.get('error', 'Erro desconhecido')}")
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
    
    # 2. Teste de análise de padrões
    print("\n2️⃣ Testando análise de padrões...")
    try:
        response = requests.get(f"{base_url}/ml/descriptions/analyze")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if "error" not in result:
                print(f"✅ Análise bem-sucedida: {result.get('total_anomalies', 0)} anomalias analisadas")
                if result.get('pattern_analysis'):
                    for anomaly_type, analysis in result['pattern_analysis'].items():
                        print(f"   {anomaly_type}: {analysis['count']} anomalias ({analysis['percentage']:.1f}%)")
                else:
                    print("   Nenhum padrão encontrado")
            else:
                print(f"❌ Erro na análise: {result.get('error', 'Erro desconhecido')}")
        else:
            result = response.json()
            print(f"❌ Erro na análise: {result.get('error', 'Erro desconhecido')}")
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
    
    # 3. Teste de geração de descrição
    print("\n3️⃣ Testando geração de descrição...")
    
    # Dados de teste
    test_data = {
        "requestId": "test_req_001",
        "clientId": "test_client",
        "ip": "192.168.1.100",
        "apiId": "test_api",
        "method": "POST",
        "path": "/api/admin/users",
        "status": 403,
        "timestamp": datetime.now().isoformat(),
        "score": 0.85
    }
    
    try:
        response = requests.post(
            f"{base_url}/ml/descriptions/generate",
            json=test_data,
            headers={'Content-Type': 'application/json'}
        )
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if "error" not in result:
                print(f"✅ Descrição gerada com sucesso!")
                print(f"   Descrição: {result.get('description', 'N/A')}")
                print(f"   Tipo: {result.get('analysis', {}).get('anomaly_type', 'N/A')}")
                print(f"   Severidade: {result.get('analysis', {}).get('severity', 'N/A')}")
            else:
                print(f"❌ Erro na geração: {result.get('error', 'Erro desconhecido')}")
        else:
            result = response.json()
            print(f"❌ Erro na geração: {result.get('error', 'Erro desconhecido')}")
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
    
    # 4. Teste com dados de exemplo mais realistas
    print("\n4️⃣ Testando com dados realistas...")
    
    realistic_scenarios = [
        {
            "name": "Tentativa de acesso administrativo",
            "data": {
                "requestId": "req_admin_001",
                "clientId": "unknown_client",
                "ip": "203.0.113.45",
                "apiId": "api_admin",
                "method": "POST",
                "path": "/api/admin/system",
                "status": 403,
                "timestamp": datetime.now().isoformat(),
                "score": 0.92
            }
        },
        {
            "name": "Erro de servidor",
            "data": {
                "requestId": "req_error_001",
                "clientId": "known_client",
                "ip": "10.0.0.100",
                "apiId": "api_users",
                "method": "GET",
                "path": "/api/users/profile",
                "status": 500,
                "timestamp": datetime.now().isoformat(),
                "score": 0.78
            }
        },
        {
            "name": "Atividade em horário atípico",
            "data": {
                "requestId": "req_night_001",
                "clientId": "regular_client",
                "ip": "192.168.1.50",
                "apiId": "api_data",
                "method": "GET",
                "path": "/api/data/export",
                "status": 200,
                "timestamp": (datetime.now() - timedelta(hours=3)).isoformat(),  # 3h atrás
                "score": 0.65
            }
        }
    ]
    
    for scenario in realistic_scenarios:
        print(f"\n   Testando: {scenario['name']}")
        try:
            response = requests.post(
                f"{base_url}/ml/descriptions/generate",
                json=scenario["data"],
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                result = response.json()
                if "error" not in result:
                    print(f"   ✅ {result.get('description', 'Descrição gerada')}")
                else:
                    print(f"   ❌ {result.get('error', 'Erro')}")
            else:
                result = response.json()
                print(f"   ❌ {result.get('error', 'Erro HTTP')}")
        except Exception as e:
            print(f"   ❌ Erro: {e}")
    
    print("\n🎯 Teste concluído!")

if __name__ == "__main__":
    test_descriptions_functionality() 