#!/usr/bin/env python3
"""
Script para testar a correção do erro 422 no feedback
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_feedback_with_features():
    """Testa o feedback com features para verificar se o erro 422 foi corrigido"""
    
    print("🧪 Testando correção do erro 422 no feedback...")
    
    # Primeiro, vamos gerar alguns logs para ter dados para testar
    print("\n1. Gerando logs de teste...")
    for i in range(5):
        log_data = {
            "requestId": f"test_feedback_{i}_{int(time.time())}",
            "apiId": "api_feedback_test",
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
                print(f"✅ Log {i+1} enviado com sucesso")
            else:
                print(f"❌ Erro ao enviar log {i+1}: {response.text}")
        except Exception as e:
            print(f"❌ Erro de conexão: {e}")
    
    # Agora vamos treinar o modelo
    print("\n2. Treinando modelo...")
    try:
        response = requests.post(f"{BASE_URL}/ml/train?apiId=api_feedback_test&hours_back=24")
        if response.status_code == 200:
            print("✅ Modelo treinado com sucesso")
        else:
            print(f"❌ Erro ao treinar modelo: {response.text}")
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
    
    # Detectar anomalias
    print("\n3. Detectando anomalias...")
    try:
        response = requests.get(f"{BASE_URL}/ml/detect?apiId=api_feedback_test&model_name=iforest&hours_back=24")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Anomalias detectadas: {data.get('anomalies_detected', 0)}")
            
            # Testar feedback com as anomalias detectadas
            if data.get('anomalies') and len(data['anomalies']) > 0:
                anomaly = data['anomalies'][0]
                print(f"\n4. Testando feedback para anomalia: {anomaly.get('requestId', 'N/A')}")
                
                # Testar falso positivo
                feedback_data = {
                    "log_id": anomaly['requestId'],
                    "api_id": "api_feedback_test",
                    "user_comment": "Teste de correção do erro 422",
                    "anomaly_score": anomaly.get('anomaly_score', 0.5),
                    "features": anomaly.get('features', {})
                }
                
                print(f"📤 Enviando feedback com features: {type(feedback_data['features'])}")
                print(f"📋 Features: {feedback_data['features']}")
                
                response = requests.post(f"{BASE_URL}/feedback/false-positive", json=feedback_data)
                print(f"📥 Status da resposta: {response.status_code}")
                
                if response.status_code == 200:
                    print("✅ Feedback enviado com sucesso! Erro 422 corrigido!")
                    result = response.json()
                    print(f"📊 Resultado: {result}")
                else:
                    print(f"❌ Erro no feedback: {response.status_code}")
                    print(f"📄 Resposta: {response.text}")
                    
                    # Tentar novamente com features como string para testar o parse
                    print("\n🔄 Testando com features como string JSON...")
                    feedback_data_string = {
                        "log_id": anomaly['requestId'],
                        "api_id": "api_feedback_test",
                        "user_comment": "Teste com features como string",
                        "anomaly_score": anomaly.get('anomaly_score', 0.5),
                        "features": json.dumps(anomaly.get('features', {}))
                    }
                    
                    response2 = requests.post(f"{BASE_URL}/feedback/false-positive", json=feedback_data_string)
                    print(f"📥 Status da resposta (string): {response2.status_code}")
                    
                    if response2.status_code == 200:
                        print("✅ Feedback com string JSON enviado com sucesso!")
                    else:
                        print(f"❌ Erro mesmo com string: {response2.text}")
            else:
                print("⚠️ Nenhuma anomalia detectada para testar")
        else:
            print(f"❌ Erro na detecção: {response.text}")
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")

def test_direct_feedback():
    """Testa feedback diretamente com dados simulados"""
    
    print("\n🧪 Teste direto de feedback...")
    
    # Simular features como string JSON (como estava causando erro)
    features_string = '{"hour":18,"day_of_week":5,"minute":55,"status_code":200,"method_encoded":1,"path_length":12,"path_depth":3,"ip_numeric":3232235786,"client_id_encoded":0,"is_api_path":1,"is_admin_path":0,"is_auth_path":0,"is_error":0,"is_server_error":0,"is_client_error":0,"is_success":1,"is_redirect":0}'
    
    feedback_data = {
        "log_id": "test_log_422_fix",
        "api_id": "api_feedback_test",
        "user_comment": "Teste direto de correção do erro 422",
        "anomaly_score": 0.85,
        "features": features_string
    }
    
    print(f"📤 Enviando feedback com features como string...")
    print(f"📋 Features (tipo): {type(feedback_data['features'])}")
    
    try:
        response = requests.post(f"{BASE_URL}/feedback/false-positive", json=feedback_data)
        print(f"📥 Status da resposta: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Teste direto bem-sucedido! Erro 422 corrigido!")
            result = response.json()
            print(f"📊 Resultado: {result}")
        else:
            print(f"❌ Erro no teste direto: {response.status_code}")
            print(f"📄 Resposta: {response.text}")
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")

if __name__ == "__main__":
    print("🚀 Iniciando testes de correção do erro 422...")
    
    # Teste com dados reais
    test_feedback_with_features()
    
    # Teste direto
    test_direct_feedback()
    
    print("\n✅ Testes concluídos!")
    print("\n📋 Para testar na interface:")
    print("1. Abra o frontend.html ou feedback.html")
    print("2. Carregue anomalias detectadas")
    print("3. Clique nos botões de feedback")
    print("4. Verifique se não há mais erro 422") 