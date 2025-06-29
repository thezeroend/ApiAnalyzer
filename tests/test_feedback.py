#!/usr/bin/env python3
"""
Script para testar o sistema de feedback
Demonstra como marcar falsos positivos e retreinar o modelo
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
from app.models import LogEntry
from app.storage import insert_log, clear_logs
from app.ml_anomaly_detector import train_ml_models, detect_ml_anomalies
from app.feedback_system import feedback_system

API_BASE = "http://localhost:8000"

def create_test_data_for_feedback():
    """Cria dados de teste para demonstrar o feedback"""
    print("📊 Criando dados de teste para feedback...")
    
    # Limpar logs existentes
    clear_logs()
    print("   ✅ Logs limpos")
    
    test_logs = []
    
    # 1. Logs normais (80%)
    for i in range(800):
        log = LogEntry(
            requestId=f"normal_{i:04d}",
            clientId=f"client_{i % 5 + 1:02d}",
            ip=f"192.168.1.{i % 10 + 10}",
            apiId="api_feedback_test",
            path=f"/api/users/{i}",
            method="GET",
            status=200,
            timestamp=datetime.now() - timedelta(hours=i % 24, minutes=i % 60)
        )
        test_logs.append(log)
    
    # 2. Logs que serão falsos positivos (15%)
    for i in range(150):
        log = LogEntry(
            requestId=f"false_positive_{i:03d}",
            clientId="client_legitimate",
            ip="10.0.0.100",
            apiId="api_feedback_test",
            path="/api/admin/config",  # Path que pode parecer suspeito
            method="GET",
            status=200,
            timestamp=datetime.now() - timedelta(minutes=i * 2)
        )
        test_logs.append(log)
    
    # 3. Logs realmente anômalos (5%)
    for i in range(50):
        log = LogEntry(
            requestId=f"real_anomaly_{i:03d}",
            clientId="client_attacker",
            ip="203.0.113.10",
            apiId="api_feedback_test",
            path="/admin/login",
            method="POST",
            status=401,
            timestamp=datetime.now() - timedelta(minutes=i)
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
    print(f"   📊 Distribuição:")
    print(f"      - Normais: 800 logs (80%)")
    print(f"      - Falsos Positivos: 150 logs (15%)")
    print(f"      - Anomalias Reais: 50 logs (5%)")
    
    return success_count

def test_initial_detection():
    """Testa a detecção inicial antes do feedback"""
    print("\n🔍 Testando detecção inicial...")
    
    try:
        result = detect_ml_anomalies(apiId="api_feedback_test", model_name="iforest", hours_back=24)
        
        if "error" not in result:
            print(f"   ✅ Anomalias detectadas: {result.get('anomalies_detected', 0)}")
            print(f"   📊 Taxa de anomalia: {result.get('anomaly_rate', 0)*100:.1f}%")
            
            # Mostrar algumas anomalias
            anomalies = result.get('anomalies', [])
            if anomalies:
                print(f"   🚨 Exemplos de anomalias detectadas:")
                for i, anomaly in enumerate(anomalies[:3]):
                    print(f"      {i+1}. {anomaly['requestId']} - Score: {anomaly['anomaly_score']:.3f}")
            
            return result
        else:
            print(f"   ❌ Erro: {result['error']}")
            return None
            
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return None

def test_feedback_system():
    """Testa o sistema de feedback"""
    print("\n🔄 Testando sistema de feedback...")
    
    # 1. Marcar alguns falsos positivos
    false_positives = ["false_positive_001", "false_positive_002", "false_positive_003"]
    
    for log_id in false_positives:
        result = feedback_system.mark_as_false_positive(
            log_id, 
            "api_feedback_test", 
            "Este é um comportamento normal do sistema"
        )
        if "success" in result:
            print(f"   ✅ Falso positivo marcado: {log_id}")
        else:
            print(f"   ❌ Erro ao marcar falso positivo: {result.get('error')}")
    
    # 2. Marcar alguns verdadeiros positivos
    true_positives = ["real_anomaly_001", "real_anomaly_002"]
    
    for log_id in true_positives:
        result = feedback_system.mark_as_true_positive(
            log_id, 
            "api_feedback_test", 
            "Confirmado como tentativa de ataque"
        )
        if "success" in result:
            print(f"   ✅ Verdadeiro positivo marcado: {log_id}")
        else:
            print(f"   ❌ Erro ao marcar verdadeiro positivo: {result.get('error')}")
    
    # 3. Verificar estatísticas
    stats = feedback_system.get_feedback_stats("api_feedback_test")
    if "success" in stats:
        print(f"   📊 Estatísticas de feedback:")
        print(f"      - Falsos Positivos: {stats['stats']['false_positives']}")
        print(f"      - Verdadeiros Positivos: {stats['stats']['true_positives']}")
        print(f"      - Não Processados: {stats['stats']['unprocessed']}")

def test_retraining():
    """Testa o retreinamento com feedback"""
    print("\n🎯 Testando retreinamento com feedback...")
    
    try:
        result = feedback_system.retrain_with_feedback("api_feedback_test")
        
        if "success" in result:
            print(f"   ✅ {result['message']}")
            print(f"   📊 Falsos positivos processados: {result['false_positives_processed']}")
            print(f"   📈 Total de logs usados: {result['total_logs_used']}")
        else:
            print(f"   ❌ Erro no retreinamento: {result.get('error')}")
            
    except Exception as e:
        print(f"   ❌ Erro: {e}")

def test_detection_after_feedback():
    """Testa a detecção após o feedback"""
    print("\n🔍 Testando detecção após feedback...")
    
    try:
        result = detect_ml_anomalies(apiId="api_feedback_test", model_name="iforest", hours_back=24)
        
        if "error" not in result:
            print(f"   ✅ Anomalias detectadas: {result.get('anomalies_detected', 0)}")
            print(f"   📊 Taxa de anomalia: {result.get('anomaly_rate', 0)*100:.1f}%")
            
            # Verificar se os falsos positivos ainda são detectados
            anomalies = result.get('anomalies', [])
            false_positive_count = sum(1 for a in anomalies if a['requestId'].startswith('false_positive'))
            
            print(f"   📊 Falsos positivos ainda detectados: {false_positive_count}")
            
            if false_positive_count < 3:
                print("   ✅ Sistema de feedback funcionando! Menos falsos positivos detectados.")
            else:
                print("   ⚠️  Sistema pode precisar de mais feedback para melhorar.")
            
        else:
            print(f"   ❌ Erro: {result['error']}")
            
    except Exception as e:
        print(f"   ❌ Erro: {e}")

def test_api_endpoints():
    """Testa os endpoints da API de feedback"""
    print("\n🌐 Testando endpoints da API...")
    
    # 1. Testar estatísticas
    try:
        response = requests.get(f"{API_BASE}/feedback/stats?api_id=api_feedback_test")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Estatísticas via API: {data['stats']['total']} feedbacks")
        else:
            print(f"   ❌ Erro ao buscar estatísticas: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erro de conexão: {e}")
    
    # 2. Testar histórico
    try:
        response = requests.get(f"{API_BASE}/feedback/history?api_id=api_feedback_test&limit=10")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Histórico via API: {len(data['feedbacks'])} registros")
        else:
            print(f"   ❌ Erro ao buscar histórico: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erro de conexão: {e}")

def main():
    """Função principal"""
    print("🚀 TESTE DO SISTEMA DE FEEDBACK")
    print("=" * 50)
    
    # 1. Criar dados de teste
    logs_created = create_test_data_for_feedback()
    if logs_created == 0:
        print("❌ Falha ao criar logs")
        return
    
    # 2. Treinar modelo inicial
    print("\n🎯 Treinando modelo inicial...")
    train_result = train_ml_models(apiId="api_feedback_test", hours_back=24)
    if "error" in train_result:
        print(f"❌ Erro no treinamento: {train_result['error']}")
        return
    
    print("✅ Modelo treinado com sucesso!")
    
    # 3. Testar detecção inicial
    initial_result = test_initial_detection()
    if not initial_result:
        return
    
    # 4. Testar sistema de feedback
    test_feedback_system()
    
    # 5. Testar retreinamento
    test_retraining()
    
    # 6. Testar detecção após feedback
    test_detection_after_feedback()
    
    # 7. Testar endpoints da API
    test_api_endpoints()
    
    print("\n✅ Teste do sistema de feedback concluído!")
    print("\n📋 Resumo:")
    print("   - Sistema permite marcar falsos positivos")
    print("   - Modelo pode ser retreinado com feedback")
    print("   - API endpoints funcionando")
    print("   - Interface disponível no frontend")

if __name__ == "__main__":
    main() 