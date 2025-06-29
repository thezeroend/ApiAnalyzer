#!/usr/bin/env python3
"""
Script para testar o filtro de logs com feedback
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_feedback_filter():
    """Testa se o filtro de logs com feedback está funcionando"""
    
    print("🧪 Testando filtro de logs com feedback...")
    
    # 1. Gerar logs de teste
    print("\n1. Gerando logs de teste...")
    api_id = "api_feedback_filter_test"
    
    # Gerar logs normais
    for i in range(8):
        log_data = {
            "requestId": f"test_normal_{i}_{int(time.time())}",
            "apiId": api_id,
            "clientId": f"client_{i}",
            "ip": "192.168.1.100",
            "method": "GET",
            "path": "/api/test",
            "status": 200,
            "responseTime": 150 + i * 10,
            "timestamp": "2024-01-15T10:00:00Z"
        }
        
        try:
            response = requests.post(f"{BASE_URL}/logs", json=log_data)
            if response.status_code == 200:
                print(f"✅ Log normal {i+1} enviado")
            else:
                print(f"❌ Erro ao enviar log {i+1}: {response.text}")
        except Exception as e:
            print(f"❌ Erro de conexão: {e}")
    
    # Gerar logs anômalos (erros 500, IPs diferentes, etc.)
    anomalous_logs = [
        {
            "requestId": f"test_anomaly_1_{int(time.time())}",
            "apiId": api_id,
            "clientId": "client_0",
            "ip": "10.0.0.1",  # IP diferente
            "method": "POST",
            "path": "/api/admin",
            "status": 500,  # Erro de servidor
            "responseTime": 5000,  # Tempo muito alto
            "timestamp": "2024-01-15T10:00:00Z"
        },
        {
            "requestId": f"test_anomaly_2_{int(time.time())}",
            "apiId": api_id,
            "clientId": "client_0",
            "ip": "192.168.1.100",
            "method": "DELETE",
            "path": "/api/users/123",
            "status": 404,  # Erro de cliente
            "responseTime": 50,  # Tempo muito baixo
            "timestamp": "2024-01-15T10:00:00Z"
        },
        {
            "requestId": f"test_anomaly_3_{int(time.time())}",
            "apiId": api_id,
            "clientId": "client_0",
            "ip": "192.168.1.100",
            "method": "GET",
            "path": "/api/test",
            "status": 200,
            "responseTime": 10000,  # Tempo extremamente alto
            "timestamp": "2024-01-15T10:00:00Z"
        }
    ]
    
    for i, log_data in enumerate(anomalous_logs):
        try:
            response = requests.post(f"{BASE_URL}/logs", json=log_data)
            if response.status_code == 200:
                print(f"✅ Log anômalo {i+1} enviado")
            else:
                print(f"❌ Erro ao enviar log anômalo {i+1}: {response.text}")
        except Exception as e:
            print(f"❌ Erro de conexão: {e}")
    
    # 2. Treinar modelo
    print("\n2. Treinando modelo...")
    try:
        response = requests.post(f"{BASE_URL}/ml/train?apiId={api_id}&hours_back=24")
        if response.status_code == 200:
            print("✅ Modelo treinado")
        else:
            print(f"❌ Erro ao treinar: {response.text}")
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
    
    # 3. Primeira detecção (sem feedback)
    print("\n3. Primeira detecção (sem feedback)...")
    try:
        response = requests.get(f"{BASE_URL}/ml/detect?apiId={api_id}&model_name=iforest&hours_back=24")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Primeira detecção: {data.get('anomalies_detected', 0)} anomalias")
            print(f"📊 Logs analisados: {data.get('logs_analyzed', 0)}")
            print(f"📊 Logs com feedback: {data.get('logs_with_feedback', 0)}")
            
            # Salvar anomalias para feedback
            anomalies = data.get('anomalies', [])
            if anomalies:
                first_anomaly = anomalies[0]
                print(f"🎯 Primeira anomalia: {first_anomaly.get('requestId', 'N/A')}")
        else:
            print(f"❌ Erro na detecção: {response.text}")
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
    
    # 4. Marcar algumas anomalias como falso positivo
    print("\n4. Marcando anomalias como falso positivo...")
    if anomalies:
        for i, anomaly in enumerate(anomalies[:3]):  # Marcar 3 primeiras
            feedback_data = {
                "log_id": anomaly['requestId'],
                "api_id": api_id,
                "user_comment": f"Teste de filtro {i+1}",
                "anomaly_score": anomaly.get('anomaly_score', 0.5),
                "features": anomaly.get('features', {})
            }
            
            try:
                response = requests.post(f"{BASE_URL}/feedback/false-positive", json=feedback_data)
                if response.status_code == 200:
                    print(f"✅ Falso positivo {i+1} registrado: {anomaly['requestId']}")
                else:
                    print(f"❌ Erro ao registrar feedback {i+1}: {response.text}")
            except Exception as e:
                print(f"❌ Erro de conexão: {e}")
    
    # 5. Segunda detecção (com feedback)
    print("\n5. Segunda detecção (com feedback)...")
    try:
        response = requests.get(f"{BASE_URL}/ml/detect?apiId={api_id}&model_name=iforest&hours_back=24")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Segunda detecção: {data.get('anomalies_detected', 0)} anomalias")
            print(f"📊 Total de logs: {data.get('total_logs', 0)}")
            print(f"📊 Logs com feedback: {data.get('logs_with_feedback', 0)}")
            print(f"📊 Logs disponíveis: {data.get('logs_available', 0)}")
            
            # Verificar se as anomalias marcadas não aparecem mais
            new_anomalies = data.get('anomalies', [])
            marked_ids = [anomaly['requestId'] for anomaly in anomalies[:3]]
            
            for marked_id in marked_ids:
                if any(a['requestId'] == marked_id for a in new_anomalies):
                    print(f"❌ Anomalia marcada ainda aparece: {marked_id}")
                else:
                    print(f"✅ Anomalia marcada filtrada corretamente: {marked_id}")
                    
        else:
            print(f"❌ Erro na detecção: {response.text}")
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
    
    # 6. Verificar logs com feedback
    print("\n6. Verificando logs com feedback...")
    try:
        response = requests.get(f"{BASE_URL}/feedback/logs-with-feedback?api_id={api_id}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Logs com feedback: {data.get('count', 0)}")
            print(f"📋 IDs: {data.get('logs_with_feedback', [])}")
        else:
            print(f"❌ Erro ao buscar logs com feedback: {response.text}")
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")

if __name__ == "__main__":
    print("🚀 Iniciando teste de filtro de feedback...")
    test_feedback_filter()
    print("\n✅ Teste concluído!") 