#!/usr/bin/env python3
"""
Script para testar se falsos positivos são filtrados corretamente
"""

import sys
import os
# Adicionar o diretório pai ao path de forma mais robusta
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

import requests
import json
from datetime import datetime, timedelta
import random
from app.models import LogEntry
from app.storage import insert_log, clear_logs, get_all_logs
from app.ml_anomaly_detector import train_ml_models, detect_ml_anomalies
from app.feedback_system import feedback_system

# Configuração
API_BASE = "http://localhost:8000"
API_ID = "test_false_positive_filter"

def create_test_logs():
    """Cria logs de teste com padrões anômalos"""
    
    print("📊 Criando logs de teste...")
    
    # Limpar logs existentes
    try:
        clear_logs()
        print("   ✅ Logs limpos do MongoDB")
    except Exception as e:
        print(f"   ❌ Erro ao limpar logs: {e}")
        return 0
    
    test_logs = []
    
    # 1. Logs normais
    print("   📝 Criando logs normais...")
    for i in range(20):
        log = LogEntry(
            requestId=f"normal_{i:03d}",
            clientId="client_normal",
            ip="192.168.1.100",
            apiId=API_ID,
            path=f"/api/users/{i}", 
            method="GET",
            status=200,
            responseTime=150,
            timestamp=datetime.now() - timedelta(hours=2, minutes=i)
        )
        test_logs.append(log)
    
    # 2. Logs que serão marcados como FALSOS positivos (padrão específico)
    print("   🚫 Criando logs para falsos positivos...")
    for i in range(8):
        log = LogEntry(
            requestId=f"false_pos_{i:03d}",
            clientId="client_false_positive",
            ip="192.168.1.101",
            apiId=API_ID,
            path=f"/api/data/{i}",
            method="GET",
            status=200,
            responseTime=2500,  # Tempo muito alto para ser detectado como anomalia
            timestamp=datetime.now() - timedelta(hours=1, minutes=i*5)
        )
        test_logs.append(log)
    
    # 3. Logs que serão marcados como VERDADEIROS positivos
    print("   🚨 Criando logs para verdadeiros positivos...")
    for i in range(5):
        log = LogEntry(
            requestId=f"true_pos_{i:03d}",
            clientId="client_true_positive",
            ip="8.8.8.8",  # IP público suspeito
            apiId=API_ID,
            path="/api/admin/delete",
            method="DELETE",
            status=403,  # Acesso negado
            responseTime=2000,  # Tempo muito alto
            timestamp=datetime.now() - timedelta(minutes=i*3)
        )
        test_logs.append(log)
    
    print(f"   📝 Inserindo {len(test_logs)} logs no MongoDB...")
    
    success_count = 0
    for log in test_logs:
        try:
            insert_log(log)
            success_count += 1
        except Exception as e:
            print(f"   ❌ Erro ao inserir log: {e}")
    
    print(f"   ✅ {success_count}/{len(test_logs)} logs inseridos com sucesso!")
    return success_count

def train_and_detect_initial():
    """Treina modelo e detecta anomalias iniciais"""
    print("\n🎯 Treinando modelo inicial...")
    
    result = train_ml_models(apiId=API_ID, hours_back=24, save_models=True)
    if "error" in result:
        print(f"❌ Erro no treinamento: {result['error']}")
        return None
    
    print("✅ Modelo treinado com sucesso!")
    
    print("\n🔍 Detectando anomalias iniciais...")
    result = detect_ml_anomalies(apiId=API_ID, model_name='iforest', hours_back=24)
    
    if "error" in result:
        print(f"❌ Erro na detecção: {result['error']}")
        return None
    
    print(f"📊 Anomalias detectadas: {result.get('anomalies_detected', 0)}")
    
    # Mostrar detalhes das anomalias
    if 'anomalies' in result:
        print("\n📋 Anomalias detectadas:")
        for i, anomaly in enumerate(result['anomalies']):
            log_id = anomaly['requestId']
            score = anomaly.get('anomaly_score', 0)
            print(f"   {i+1}. {log_id} (score: {score:.3f})")
    
    return result

def mark_false_positives(anomalies_result):
    """Marca falsos positivos nos logs detectados"""
    if not anomalies_result or 'anomalies' not in anomalies_result:
        print("❌ Nenhuma anomalia para marcar feedback")
        return 0
    
    print("\n🏷️ Marcando falsos positivos...")
    
    false_positive_count = 0
    
    for anomaly in anomalies_result['anomalies']:
        log_id = anomaly['requestId']
        
        # Marcar como falso positivo se for do cliente false_positive
        if log_id.startswith('false_pos_'):
            feedback_data = {
                "log_id": log_id,
                "api_id": API_ID,
                "user_comment": "Falso positivo - padrão normal para este cliente",
                "anomaly_score": anomaly['anomaly_score'],
                "features": anomaly.get('features', {})
            }
            
            response = requests.post(f"{API_BASE}/feedback/false-positive", json=feedback_data)
            if response.status_code == 200:
                print(f"✅ Falso positivo marcado: {log_id}")
                false_positive_count += 1
            else:
                print(f"❌ Erro ao marcar falso positivo: {response.text}")
    
    print(f"📊 Falsos positivos marcados: {false_positive_count}")
    return false_positive_count

def retrain_model():
    """Retreina o modelo com feedback"""
    print("\n🔄 Retreinando modelo com feedback...")
    
    retrain_data = {"api_id": API_ID}
    response = requests.post(f"{API_BASE}/feedback/retrain", json=retrain_data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Modelo retreinado: {result}")
        return result
    else:
        print(f"❌ Erro ao retreinar: {response.text}")
        return None

def test_detection_after_retrain():
    """Testa se falsos positivos foram filtrados após retreinamento"""
    print("\n🧪 Testando detecção após retreinamento...")
    
    # Adicionar os mesmos logs novamente
    create_test_logs()
    
    # Detectar anomalias novamente
    result = detect_ml_anomalies(apiId=API_ID, model_name='iforest', hours_back=24)
    
    if "error" in result:
        print(f"❌ Erro na detecção: {result['error']}")
        return None
    
    print(f"📊 Anomalias detectadas após retreinamento: {result.get('anomalies_detected', 0)}")
    
    # Analisar resultados
    if 'anomalies' in result:
        false_positives_still_detected = []
        true_positives_still_detected = []
        new_anomalies = []
        
        for anomaly in result['anomalies']:
            log_id = anomaly['requestId']
            
            if log_id.startswith('false_pos_'):
                false_positives_still_detected.append(log_id)
            elif log_id.startswith('true_pos_'):
                true_positives_still_detected.append(log_id)
            else:
                new_anomalies.append(log_id)
        
        print(f"\n📋 Análise dos resultados:")
        print(f"   ❌ Falsos positivos que ainda aparecem: {len(false_positives_still_detected)}")
        if false_positives_still_detected:
            print(f"      - {false_positives_still_detected}")
        
        print(f"   ✅ Verdadeiros positivos que continuam sendo detectados: {len(true_positives_still_detected)}")
        if true_positives_still_detected:
            print(f"      - {true_positives_still_detected}")
        
        print(f"   🆕 Novas anomalias detectadas: {len(new_anomalies)}")
        if new_anomalies:
            print(f"      - {new_anomalies}")
    
    return result

def show_feedback_stats():
    """Mostra estatísticas de feedback"""
    print("\n📈 Estatísticas de feedback:")
    
    response = requests.get(f"{API_BASE}/feedback/stats?api_id={API_ID}")
    if response.status_code == 200:
        result = response.json()
        stats = result.get('stats', {})
        print(f"   📊 Falsos positivos: {stats.get('false_positives', 0)}")
        print(f"   📊 Verdadeiros positivos: {stats.get('true_positives', 0)}")
        print(f"   📊 Não processados: {stats.get('unprocessed', 0)}")
        print(f"   📊 Total: {stats.get('total', 0)}")
    else:
        print(f"❌ Erro ao obter estatísticas: {response.text}")

def main():
    """Função principal"""
    print("🚀 TESTE DE FILTRO DE FALSOS POSITIVOS")
    print("=" * 50)
    
    try:
        # 1. Criar logs de teste
        logs_created = create_test_logs()
        if logs_created == 0:
            print("❌ Falha ao criar logs de teste")
            return
        
        # 2. Treinar e detectar anomalias iniciais
        initial_result = train_and_detect_initial()
        if not initial_result:
            print("❌ Falha na detecção inicial")
            return
        
        # 3. Marcar falsos positivos
        false_count = mark_false_positives(initial_result)
        
        if false_count == 0:
            print("❌ Nenhum falso positivo foi marcado")
            return
        
        # 4. Retreinar modelo
        retrain_result = retrain_model()
        if not retrain_result:
            print("❌ Falha no retreinamento")
            return
        
        # 5. Testar detecção após retreinamento
        final_result = test_detection_after_retrain()
        
        # 6. Mostrar estatísticas
        show_feedback_stats()
        
        print("\n" + "=" * 50)
        print("🏁 TESTE CONCLUÍDO!")
        
        if final_result:
            initial_count = initial_result.get('anomalies_detected', 0)
            final_count = final_result.get('anomalies_detected', 0)
            
            print(f"\n📊 RESUMO:")
            print(f"   - Anomalias iniciais: {initial_count}")
            print(f"   - Anomalias após retreinamento: {final_count}")
            print(f"   - Falsos positivos marcados: {false_count}")
            
            # Verificar se o comportamento está correto
            if false_count > 0:
                print(f"   - ✅ Falsos positivos devem ter sido reduzidos após retreinamento")
                if final_count < initial_count:
                    print(f"   - ✅ SUCCESS: Falsos positivos foram filtrados!")
                else:
                    print(f"   - ⚠️  WARNING: Falsos positivos ainda aparecem")
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 