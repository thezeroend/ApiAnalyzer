#!/usr/bin/env python3
"""
Script para testar a interface de feedback
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_feedback_endpoints():
    """Testa todos os endpoints de feedback"""
    
    print("🧪 Testando endpoints de feedback...")
    
    # Teste 1: Estatísticas de feedback
    print("\n1. Testando estatísticas de feedback...")
    try:
        response = requests.get(f"{BASE_URL}/feedback/stats?api_id=api_realistic")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Estatísticas: {json.dumps(data, indent=2)}")
        else:
            print(f"❌ Erro: {response.text}")
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
    
    # Teste 2: Histórico de feedback
    print("\n2. Testando histórico de feedback...")
    try:
        response = requests.get(f"{BASE_URL}/feedback/history?api_id=api_realistic&limit=5")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Histórico: {json.dumps(data, indent=2)}")
        else:
            print(f"❌ Erro: {response.text}")
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
    
    # Teste 3: Marcar falso positivo
    print("\n3. Testando marcação de falso positivo...")
    try:
        feedback_data = {
            "log_id": "test_log_123",
            "api_id": "api_realistic",
            "user_comment": "Teste de falso positivo",
            "anomaly_score": 0.85,
            "features": {"response_time": 150, "status": 200}
        }
        response = requests.post(f"{BASE_URL}/feedback/false-positive", json=feedback_data)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Falso positivo registrado: {json.dumps(data, indent=2)}")
        else:
            print(f"❌ Erro: {response.text}")
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
    
    # Teste 4: Marcar verdadeiro positivo
    print("\n4. Testando marcação de verdadeiro positivo...")
    try:
        feedback_data = {
            "log_id": "test_log_456",
            "api_id": "api_realistic",
            "user_comment": "Teste de verdadeiro positivo",
            "anomaly_score": 0.95,
            "features": {"response_time": 5000, "status": 500}
        }
        response = requests.post(f"{BASE_URL}/feedback/true-positive", json=feedback_data)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Verdadeiro positivo registrado: {json.dumps(data, indent=2)}")
        else:
            print(f"❌ Erro: {response.text}")
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")

def test_ml_detection_with_feedback():
    """Testa detecção ML e simula feedback"""
    
    print("\n🔍 Testando detecção ML com feedback...")
    
    # Primeiro, detectar anomalias
    try:
        response = requests.get(f"{BASE_URL}/ml/detect?apiId=api_realistic&model_name=iforest&hours_back=24")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Anomalias detectadas: {data.get('anomalies_detected', 0)}")
            
            # Simular feedback para algumas anomalias
            if data.get('anomalies') and len(data['anomalies']) > 0:
                anomaly = data['anomalies'][0]
                print(f"📝 Simulando feedback para anomalia: {anomaly.get('requestId', 'N/A')}")
                
                # Marcar como falso positivo
                feedback_data = {
                    "log_id": anomaly['requestId'],
                    "api_id": "api_realistic",
                    "user_comment": "Teste via interface - falso positivo",
                    "anomaly_score": anomaly.get('anomaly_score', 0.5),
                    "features": anomaly.get('features', {})
                }
                
                feedback_response = requests.post(f"{BASE_URL}/feedback/false-positive", json=feedback_data)
                if feedback_response.status_code == 200:
                    print("✅ Feedback de falso positivo registrado com sucesso!")
                else:
                    print(f"❌ Erro no feedback: {feedback_response.text}")
        else:
            print(f"❌ Erro na detecção: {response.text}")
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")

if __name__ == "__main__":
    print("🚀 Iniciando testes da interface de feedback...")
    
    # Testar endpoints básicos
    test_feedback_endpoints()
    
    # Testar detecção ML com feedback
    test_ml_detection_with_feedback()
    
    print("\n✅ Testes concluídos!")
    print("\n📋 Para usar a interface:")
    print("1. Abra o frontend.html no navegador")
    print("2. Use a seção 'Feedback de Anomalias'")
    print("3. Execute detecção ML primeiro")
    print("4. Clique nos botões de feedback nas anomalias detectadas") 