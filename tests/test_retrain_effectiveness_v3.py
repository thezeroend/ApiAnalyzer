#!/usr/bin/env python3
"""
Script para testar a eficácia do retreinamento com feedback - Versão 3
Marca como falsos positivos as anomalias que realmente foram detectadas
"""

import requests
import json
import time
from datetime import datetime, timedelta
import random

# Configurações
API_BASE = "http://localhost:8000"
API_ID = "test_retrain_api_v3"

def add_diverse_test_logs():
    """Adiciona logs de teste mais diversos"""
    print("📝 Adicionando logs de teste diversos...")
    
    # Logs normais (padrão)
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
        for i in range(20)
    ]
    
    # Logs normais com variações
    normal_variations = [
        {
            "requestId": f"normal_var_{i}",
            "apiId": API_ID,
            "clientId": "client_normal",
            "ip": "192.168.1.101",
            "path": "/api/products",
            "method": "GET",
            "status": 200,
            "responseTime": random.randint(100, 300),
            "timestamp": datetime.now().isoformat()
        }
        for i in range(15)
    ]
    
    # Logs que podem ser detectados como anomalias
    potential_anomalies = [
        {
            "requestId": f"potential_anomaly_{i}",
            "apiId": API_ID,
            "clientId": "client_suspicious",
            "ip": "10.0.0.50",
            "path": "/api/admin/users",
            "method": "POST",
            "status": 200,
            "responseTime": 800,  # Tempo de resposta alto
            "timestamp": datetime.now().isoformat()
        }
        for i in range(5)
    ]
    
    # Logs claramente anômalos (que devem ser detectados)
    anomalous_logs = [
        {
            "requestId": f"anomaly_{i}",
            "apiId": API_ID,
            "clientId": "client_attack",
            "ip": "192.168.1.999",  # IP suspeito
            "path": "/api/admin/delete",
            "method": "DELETE",
            "status": 403,  # Status de erro
            "responseTime": 2000,  # Tempo muito alto
            "timestamp": datetime.now().isoformat()
        }
        for i in range(3)
    ]
    
    # Logs com padrões muito diferentes
    very_anomalous_logs = [
        {
            "requestId": f"very_anomaly_{i}",
            "apiId": API_ID,
            "clientId": "client_very_suspicious",
            "ip": "10.10.10.10",
            "path": "/api/internal/system/reboot",
            "method": "PUT",
            "status": 500,  # Erro de servidor
            "responseTime": 5000,  # Tempo extremamente alto
            "timestamp": datetime.now().isoformat()
        }
        for i in range(2)
    ]
    
    all_logs = normal_logs + normal_variations + potential_anomalies + anomalous_logs + very_anomalous_logs
    
    # Enviar logs
    for log in all_logs:
        response = requests.post(f"{API_BASE}/logs", json=log)
        if response.status_code != 200:
            print(f"❌ Erro ao adicionar log: {response.text}")
    
    print(f"✅ {len(all_logs)} logs adicionados (normais: {len(normal_logs + normal_variations)}, potenciais: {len(potential_anomalies)}, anômalos: {len(anomalous_logs + very_anomalous_logs)})")
    
    return {
        'normal_ids': [log['requestId'] for log in normal_logs + normal_variations],
        'potential_ids': [log['requestId'] for log in potential_anomalies],
        'anomalous_ids': [log['requestId'] for log in anomalous_logs + very_anomalous_logs]
    }

def train_initial_model():
    """Treina o modelo inicial"""
    print("🎯 Treinando modelo inicial...")
    
    response = requests.post(f"{API_BASE}/ml/train?apiId={API_ID}")
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Modelo inicial treinado com {result.get('logs_used', 0)} logs")
    else:
        print(f"❌ Erro ao treinar modelo inicial: {response.text}")

def detect_initial_anomalies():
    """Detecta anomalias iniciais"""
    print("🔍 Detectando anomalias iniciais...")
    
    response = requests.get(f"{API_BASE}/ml/detect?apiId={API_ID}")
    if response.status_code == 200:
        result = response.json()
        print(f"📊 Anomalias iniciais detectadas: {result.get('anomalies_detected', 0)}")
        
        if 'anomalies' in result and result['anomalies']:
            print("📋 Anomalias detectadas:")
            for i, anomaly in enumerate(result['anomalies']):
                print(f"   {i+1}. {anomaly['requestId']}: score {anomaly['anomaly_score']:.3f}")
        
        return result
    else:
        print(f"❌ Erro ao detectar anomalias: {response.text}")
        return None

def mark_detected_anomalies_as_false_positives(anomalies_result, max_to_mark=3):
    """Marca as primeiras anomalias detectadas como falsos positivos"""
    if not anomalies_result or 'anomalies' not in anomalies_result:
        print("❌ Nenhuma anomalia para marcar")
        return []
    
    print(f"🏷️ Marcando até {max_to_mark} anomalias como falsos positivos...")
    
    marked_ids = []
    for i, anomaly in enumerate(anomalies_result['anomalies'][:max_to_mark]):
        feedback_data = {
            "log_id": anomaly['requestId'],
            "api_id": API_ID,
            "user_comment": f"Teste de retreinamento - falso positivo #{i+1}",
            "anomaly_score": anomaly['anomaly_score'],
            "features": anomaly.get('features', {})
        }
        
        response = requests.post(f"{API_BASE}/feedback/false-positive", json=feedback_data)
        if response.status_code == 200:
            print(f"✅ Falso positivo marcado para {anomaly['requestId']} (score: {anomaly['anomaly_score']:.3f})")
            marked_ids.append(anomaly['requestId'])
        else:
            print(f"❌ Erro ao marcar falso positivo: {response.text}")
    
    print(f"📊 Total de falsos positivos marcados: {len(marked_ids)}")
    return marked_ids

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

def test_retrain_effectiveness(marked_ids):
    """Testa se o retreinamento foi efetivo"""
    print("🧪 Testando eficácia do retreinamento...")
    
    # Adicionar os mesmos logs novamente
    add_diverse_test_logs()
    
    # Detectar anomalias novamente
    response = requests.get(f"{API_BASE}/ml/detect?apiId={API_ID}")
    if response.status_code == 200:
        result = response.json()
        print(f"📊 Anomalias após retreinamento: {result.get('anomalies_detected', 0)}")
        
        # Verificar se os logs marcados como falsos positivos ainda aparecem
        if 'anomalies' in result:
            still_anomalous = [a for a in result['anomalies'] if a['requestId'] in marked_ids]
            
            if still_anomalous:
                print(f"⚠️ {len(still_anomalous)} logs ainda aparecem como anomalias após retreinamento:")
                for anomaly in still_anomalous:
                    print(f"   - {anomaly['requestId']}: score {anomaly['anomaly_score']:.3f} (era falso positivo)")
            else:
                print("✅ Retreinamento efetivo! Logs marcados como falsos positivos não aparecem mais")
            
            # Mostrar outras anomalias detectadas
            other_anomalies = [a for a in result['anomalies'] if a['requestId'] not in marked_ids]
            if other_anomalies:
                print(f"📋 Outras anomalias detectadas ({len(other_anomalies)}):")
                for i, anomaly in enumerate(other_anomalies[:3]):  # Mostrar apenas as primeiras 3
                    print(f"   {i+1}. {anomaly['requestId']}: score {anomaly['anomaly_score']:.3f}")
        
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
    print("🚀 Iniciando teste de eficácia do retreinamento - Versão 3")
    print("=" * 60)
    
    # Limpar logs existentes
    print("🧹 Limpando logs existentes...")
    response = requests.delete(f"{API_BASE}/logs")
    if response.status_code == 200:
        print("✅ Logs limpos")
    else:
        print(f"❌ Erro ao limpar logs: {response.text}")
    
    # Etapa 1: Adicionar logs diversos e treinar modelo inicial
    log_ids = add_diverse_test_logs()
    train_initial_model()
    
    # Etapa 2: Detectar anomalias iniciais
    initial_result = detect_initial_anomalies()
    
    if not initial_result or initial_result.get('anomalies_detected', 0) == 0:
        print("❌ Não foram detectadas anomalias iniciais. Tentando com mais logs...")
        # Adicionar mais logs anômalos
        add_diverse_test_logs()
        train_initial_model()
        initial_result = detect_initial_anomalies()
        
        if not initial_result or initial_result.get('anomalies_detected', 0) == 0:
            print("❌ Ainda não foram detectadas anomalias. O modelo pode estar muito permissivo.")
            return
    
    # Etapa 3: Marcar as anomalias detectadas como falsos positivos
    marked_ids = mark_detected_anomalies_as_false_positives(initial_result, max_to_mark=3)
    
    if not marked_ids:
        print("❌ Nenhum falso positivo foi marcado. Não há o que retreinar.")
        return
    
    # Etapa 4: Retreinar modelo
    retrain_result = retrain_model()
    
    if not retrain_result:
        print("❌ Não foi possível retreinar o modelo")
        return
    
    # Etapa 5: Testar eficácia
    final_result = test_retrain_effectiveness(marked_ids)
    
    # Etapa 6: Mostrar estatísticas
    get_feedback_stats()
    
    print("\n" + "=" * 60)
    print("🏁 Teste concluído!")
    
    if final_result:
        initial_count = initial_result.get('anomalies_detected', 0)
        final_count = final_result.get('anomalies_detected', 0)
        
        print(f"📊 Resumo:")
        print(f"   - Anomalias iniciais: {initial_count}")
        print(f"   - Anomalias após retreinamento: {final_count}")
        print(f"   - Falsos positivos marcados: {len(marked_ids)}")
        print(f"   - Redução: {initial_count - final_count} anomalias")
        
        # Verificar se os logs marcados ainda aparecem
        if 'anomalies' in final_result:
            still_anomalous = [a for a in final_result['anomalies'] if a['requestId'] in marked_ids]
            if still_anomalous:
                print(f"   - Logs marcados que ainda aparecem: {len(still_anomalous)}")
            else:
                print(f"   - ✅ Todos os logs marcados foram removidos das anomalias!")

if __name__ == "__main__":
    main() 