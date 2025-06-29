#!/usr/bin/env python3
"""
Teste do sistema de ML para geração de descrições de anomalias
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import json
from datetime import datetime, timedelta

def test_description_ml():
    """Testa o sistema de ML de descrições"""
    print("🤖 Testando sistema de ML de descrições...")
    
    base_url = "http://localhost:8000"
    
    # Teste 1: Treinar modelo
    print("\n1️⃣ Treinando modelo de descrições...")
    try:
        response = requests.post(f"{base_url}/ml/descriptions/train")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Modelo treinado com sucesso!")
            print(f"   - Logs utilizados: {result.get('logs_used', 0)}")
            print(f"   - Modelos salvos: {', '.join(result.get('models_saved', []))}")
        else:
            print(f"❌ Erro ao treinar modelo: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
        return False
    
    # Teste 2: Analisar padrões
    print("\n2️⃣ Analisando padrões de anomalias...")
    try:
        response = requests.get(f"{base_url}/ml/descriptions/analyze")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Análise de padrões concluída!")
            print(f"   - Total de anomalias: {result.get('total_anomalies', 0)}")
            print(f"   - Tipos detectados: {', '.join(result.get('summary', {}).get('types_detected', []))}")
            print(f"   - Tipo mais comum: {result.get('summary', {}).get('most_common_type', 'N/A')}")
            
            # Exibe detalhes dos padrões
            pattern_analysis = result.get('pattern_analysis', {})
            for anomaly_type, analysis in pattern_analysis.items():
                print(f"   📊 {anomaly_type.upper()}:")
                print(f"      - Quantidade: {analysis.get('count', 0)}")
                print(f"      - Percentual: {analysis.get('percentage', 0):.1f}%")
                print(f"      - Score médio: {analysis.get('avg_score', 0):.3f}")
        else:
            print(f"❌ Erro na análise: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
        return False
    
    # Teste 3: Gerar descrição personalizada
    print("\n3️⃣ Gerando descrição personalizada...")
    try:
        test_log = {
            "requestId": "test_req_001",
            "clientId": "suspicious_client",
            "ip": "203.0.113.45",
            "apiId": "api_admin",
            "method": "POST",
            "path": "/api/admin/users",
            "status": 403,
            "score": 0.85,
            "timestamp": datetime.now().isoformat()
        }
        
        response = requests.post(f"{base_url}/ml/descriptions/generate", json=test_log)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Descrição gerada com sucesso!")
            print(f"   📝 Descrição: {result.get('description', 'N/A')}")
            print(f"   🔍 Tipo: {result.get('analysis', {}).get('anomaly_type', 'N/A')}")
            print(f"   ⚠️ Severidade: {result.get('analysis', {}).get('severity', 'N/A')}")
        else:
            print(f"❌ Erro na geração: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
        return False
    
    # Teste 4: Testar diferentes cenários
    print("\n4️⃣ Testando diferentes cenários...")
    test_scenarios = [
        {
            "name": "Ataque de Força Bruta",
            "data": {
                "requestId": "brute_force_001",
                "clientId": "unknown_client",
                "ip": "192.168.1.100",
                "apiId": "api_auth",
                "method": "POST",
                "path": "/api/auth/login",
                "status": 401,
                "score": 0.92,
                "timestamp": datetime.now().isoformat()
            }
        },
        {
            "name": "Erro de Servidor",
            "data": {
                "requestId": "server_error_001",
                "clientId": "normal_client",
                "ip": "10.0.0.50",
                "apiId": "api_users",
                "method": "GET",
                "path": "/api/users",
                "status": 500,
                "score": 0.78,
                "timestamp": datetime.now().isoformat()
            }
        },
        {
            "name": "Acesso Administrativo",
            "data": {
                "requestId": "admin_access_001",
                "clientId": "regular_user",
                "ip": "172.16.0.25",
                "apiId": "api_admin",
                "method": "GET",
                "path": "/api/admin/system",
                "status": 403,
                "score": 0.88,
                "timestamp": datetime.now().isoformat()
            }
        }
    ]
    
    for scenario in test_scenarios:
        try:
            response = requests.post(f"{base_url}/ml/descriptions/generate", json=scenario["data"])
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ {scenario['name']}:")
                print(f"      - Descrição: {result.get('description', 'N/A')[:80]}...")
                print(f"      - Tipo: {result.get('analysis', {}).get('anomaly_type', 'N/A')}")
                print(f"      - Severidade: {result.get('analysis', {}).get('severity', 'N/A')}")
            else:
                print(f"   ❌ {scenario['name']}: Erro na geração")
        except Exception as e:
            print(f"   ❌ {scenario['name']}: Erro de conexão - {e}")
    
    print("\n🎉 Teste do sistema de ML de descrições concluído!")
    return True

def test_detection_with_ml_descriptions():
    """Testa a detecção de anomalias com descrições ML"""
    print("\n🔍 Testando detecção com descrições ML...")
    
    base_url = "http://localhost:8000"
    
    try:
        # Detecta anomalias
        response = requests.get(f"{base_url}/ml/detect")
        if response.status_code == 200:
            result = response.json()
            
            if "error" in result:
                print(f"❌ Erro na detecção: {result['error']}")
                return False
            
            anomalies = result.get("anomalies", [])
            print(f"✅ {len(anomalies)} anomalias detectadas")
            
            # Exibe algumas descrições geradas
            for i, anomaly in enumerate(anomalies[:3]):  # Mostra apenas as 3 primeiras
                description = anomaly.get("anomaly_description", "Sem descrição")
                score = anomaly.get("anomaly_score", 0)
                print(f"   📝 Anomalia {i+1}:")
                print(f"      - Score: {score:.3f}")
                print(f"      - Descrição: {description}")
                print()
            
            return True
        else:
            print(f"❌ Erro na detecção: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando testes do sistema de ML de descrições...")
    
    # Testa o sistema de ML de descrições
    success1 = test_description_ml()
    
    # Testa a detecção com descrições ML
    success2 = test_detection_with_ml_descriptions()
    
    if success1 and success2:
        print("\n✅ Todos os testes passaram!")
        sys.exit(0)
    else:
        print("\n❌ Alguns testes falharam!")
        sys.exit(1) 