#!/usr/bin/env python3
"""
Script simples para testar o sistema ML com MongoDB
"""

import sys
import os

# Adicionar o diretório pai ao path de forma mais robusta
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from datetime import datetime, timedelta
import random
from app.models import LogEntry
from app.storage import insert_log, clear_logs, get_all_logs
from app.ml_anomaly_detector import train_ml_models, detect_ml_anomalies
from app.analyzer import detect_ip_anomalies

def create_simple_test_data():
    """Cria dados de teste simples"""
    print("📊 Criando dados de teste simples...")
    
    # Limpar logs existentes
    clear_logs()
    print("   ✅ Logs limpos")
    
    # Criar logs de teste
    logs = []
    
    # Logs normais
    for i in range(20):
        log = LogEntry(
            requestId=f"normal_{i}",
            clientId="client_001",
            ip="192.168.1.10",
            apiId="test_api",
            path=f"/api/users/{i}",
            method="GET",
            status=200,
            timestamp=datetime.now() - timedelta(hours=1, minutes=i)
        )
        logs.append(log)
    
    # Logs suspeitos
    for i in range(5):
        log = LogEntry(
            requestId=f"suspicious_{i}",
            clientId="client_001",
            ip="203.0.113.45",  # IP novo
            apiId="test_api",
            path="/admin/login",
            method="POST",
            status=403,
            timestamp=datetime.now() - timedelta(minutes=i*10)
        )
        logs.append(log)
    
    # Inserir logs
    for log in logs:
        insert_log(log)
    
    print(f"   ✅ {len(logs)} logs inseridos")
    return len(logs)

def test_ml():
    """Testa o sistema ML"""
    print("\n🤖 Testando sistema ML...")
    
    # Treinar modelos
    print("   🎯 Treinando modelos...")
    result = train_ml_models(apiId="test_api", hours_back=24)
    
    if "error" in result:
        print(f"   ❌ Erro no treinamento: {result['error']}")
        return False
    
    print(f"   ✅ Modelos treinados: {result['models_trained']}")
    
    # Detectar anomalias
    print("   🔍 Detectando anomalias...")
    anomalies = detect_ml_anomalies(apiId="test_api", model_name="iforest", hours_back=24)
    
    if "error" in anomalies:
        print(f"   ❌ Erro na detecção: {anomalies['error']}")
        return False
    
    print(f"   ✅ Anomalias detectadas: {anomalies['anomalies_detected']}")
    print(f"   📊 Taxa de anomalia: {anomalies['anomaly_rate']*100:.1f}%")
    
    return True

def test_ip_anomalies():
    """Testa detecção de IPs suspeitos"""
    print("\n🕵️ Testando detecção de IPs suspeitos...")
    
    result = detect_ip_anomalies(apiId="test_api", hours_back=24)
    
    if "error" in result:
        print(f"   ❌ Erro: {result['error']}")
        return False
    
    summary = result['summary']
    print(f"   ✅ Clientes analisados: {summary['total_clients_analyzed']}")
    print(f"   🔴 IPs novos: {summary['clients_with_new_ips']}")
    print(f"   🟡 Múltiplos IPs: {len(result['multiple_ips'])}")
    print(f"   🟠 Atividade suspeita: {summary['clients_with_suspicious_activity']}")
    
    return True

def main():
    """Função principal"""
    print("🚀 TESTE SIMPLES DO SISTEMA")
    print("=" * 40)
    
    try:
        # Criar dados de teste
        logs_created = create_simple_test_data()
        if logs_created == 0:
            print("❌ Falha ao criar dados de teste")
            return
        
        # Testar ML
        ml_success = test_ml()
        
        # Testar IPs suspeitos
        ip_success = test_ip_anomalies()
        
        if ml_success and ip_success:
            print("\n✅ TODOS OS TESTES PASSARAM!")
        else:
            print("\n❌ ALGUNS TESTES FALHARAM")
            
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 