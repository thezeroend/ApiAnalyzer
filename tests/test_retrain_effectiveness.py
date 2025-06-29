#!/usr/bin/env python3
"""
Script para testar a eficácia do retreinamento com feedback
"""

import requests
import json
import time
from datetime import datetime, timedelta

# Configurações
API_BASE = "http://localhost:8000"
API_ID = "test_retrain_api"

def add_test_logs():
    """Adiciona logs de teste"""
    print("📝 Adicionando logs de teste...")
    
    # Logs normais
    normal_logs = [
        {
            "requestId": f"normal_{i}",
            "apiId": API_ID,
            "clientId": "client_normal",
            "ip": "192.168.1.100",
            "path": "/api/users",
            "method": "GET",
            "status": 200,
            "responseTime": 150,
            "timestamp": datetime.now().isoformat()
        }
        for i in range(10)
    ]
    
    # Logs que serão marcados como falsos positivos
    false_positive_logs = [
        {
            "requestId": f"false_pos_{i}",
            "apiId": API_ID,
            "clientId": "client_suspicious",
            "ip": "10.0.0.50",
            "path": "/api/admin",
            "method": "POST",
            "status": 200,
            "responseTime": 500,
            "timestamp": datetime.now().isoformat()
        }
        for i in range(3)
    ]
    
    # Enviar logs
    for log in normal_logs + false_positive_logs:
        response = requests.post(f"{API_BASE}/logs", json=log)
        if response.status_code != 200:
            print(f"❌ Erro ao adicionar log: {response.text}")
    
    print(f"✅ {len(normal_logs + false_positive_logs)} logs adicionados")

def train_initial_model():
    """Treina o modelo inicial"""
    print("🎯 Treinando modelo inicial...")
    
    response = requests.post(f"{API_BASE}/ml/train?apiId={API_ID}")
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Modelo inicial treinado: {result}")
    else:
        print(f"❌ Erro ao treinar modelo inicial: {response.text}")

def detect_initial_anomalies():
    """Detecta anomalias iniciais"""
    print("🔍 Detectando anomalias iniciais...")
    
    response = requests.get(f"{API_BASE}/ml/detect?apiId={API_ID}")
    if response.status_code == 200:
        result = response.json()
        print(f"📊 Anomalias iniciais detectadas: {result.get('anomalies_detected', 0)}")
        return result
    else:
        print(f"❌ Erro ao detectar anomalias: {response.text}")
        return None

def mark_false_positives(anomalies_result):
    """Marca anomalias como falsos positivos"""
    if not anomalies_result or 'anomalies' not in anomalies_result:
        print("❌ Nenhuma anomalia para marcar")
        return
    
    print("🏷️ Marcando anomalias como falsos positivos...")
    
    for anomaly in anomalies_result['anomalies']:
        feedback_data = {
            "log_id": anomaly['requestId'],
            "api_id": API_ID,
            "user_comment": "Teste de retreinamento",
            "anomaly_score": anomaly['anomaly_score'],
            "features": anomaly.get('features', {})
        }
        
        response = requests.post(f"{API_BASE}/feedback/false-positive", json=feedback_data)
        if response.status_code == 200:
            print(f"✅ Falso positivo marcado para {anomaly['requestId']}")
        else:
            print(f"❌ Erro ao marcar falso positivo: {response.text}")

def retrain_model():
    """Retreina o modelo com feedback"""
    print("🔄 Retreinando modelo com feedback...")
    
    retrain_data = {"api_id": API_ID}
    response = requests.post(f"{API_BASE}/feedback/retrain", json=retrain_data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Modelo retreinado: {result}")
        return result
    else:
        print(f"❌ Erro ao retreinar: {response.text}")
        return None

def test_retrain_effectiveness():
    """Testa se o retreinamento foi efetivo"""
    print("🧪 Testando eficácia do retreinamento...")
    
    # Adicionar os mesmos logs novamente
    add_test_logs()
    
    # Detectar anomalias novamente
    response = requests.get(f"{API_BASE}/ml/detect?apiId={API_ID}")
    if response.status_code == 200:
        result = response.json()
        print(f"📊 Anomalias após retreinamento: {result.get('anomalies_detected', 0)}")
        
        # Verificar se os logs marcados como falsos positivos ainda aparecem
        if 'anomalies' in result:
            false_positive_ids = [f"false_pos_{i}" for i in range(3)]
            still_anomalous = [a for a in result['anomalies'] if a['requestId'] in false_positive_ids]
            
            if still_anomalous:
                print(f"⚠️ {len(still_anomalous)} logs ainda aparecem como anomalias após retreinamento")
                for anomaly in still_anomalous:
                    print(f"   - {anomaly['requestId']}: score {anomaly['anomaly_score']:.3f}")
            else:
                print("✅ Retreinamento efetivo! Logs marcados como falsos positivos não aparecem mais")
        
        return result
    else:
        print(f"❌ Erro ao testar retreinamento: {response.text}")
        return None

def get_feedback_stats():
    """Obtém estatísticas de feedback"""
    print("📈 Obtendo estatísticas de feedback...")
    
    response = requests.get(f"{API_BASE}/feedback/stats?api_id={API_ID}")
    if response.status_code == 200:
        result = response.json()
        print(f"📊 Estatísticas: {result}")
        return result
    else:
        print(f"❌ Erro ao obter estatísticas: {response.text}")
        return None

def main():
    """Executa o teste completo"""
    print("🚀 Iniciando teste de eficácia do retreinamento")
    print("=" * 50)
    
    # Limpar logs existentes
    print("🧹 Limpando logs existentes...")
    response = requests.delete(f"{API_BASE}/logs")
    if response.status_code == 200:
        print("✅ Logs limpos")
    else:
        print(f"❌ Erro ao limpar logs: {response.text}")
    
    # Etapa 1: Adicionar logs e treinar modelo inicial
    add_test_logs()
    train_initial_model()
    
    # Etapa 2: Detectar anomalias iniciais
    initial_result = detect_initial_anomalies()
    
    if not initial_result:
        print("❌ Não foi possível detectar anomalias iniciais")
        return
    
    # Etapa 3: Marcar falsos positivos
    mark_false_positives(initial_result)
    
    # Etapa 4: Retreinar modelo
    retrain_result = retrain_model()
    
    if not retrain_result:
        print("❌ Não foi possível retreinar o modelo")
        return
    
    # Etapa 5: Testar eficácia
    final_result = test_retrain_effectiveness()
    
    # Etapa 6: Mostrar estatísticas
    get_feedback_stats()
    
    print("\n" + "=" * 50)
    print("🏁 Teste concluído!")
    
    if final_result:
        initial_count = initial_result.get('anomalies_detected', 0)
        final_count = final_result.get('anomalies_detected', 0)
        
        print(f"📊 Resumo:")
        print(f"   - Anomalias iniciais: {initial_count}")
        print(f"   - Anomalias após retreinamento: {final_count}")
        print(f"   - Redução: {initial_count - final_count} anomalias")

if __name__ == "__main__":
    main() 