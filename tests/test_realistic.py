#!/usr/bin/env python3
"""
Script para gerar dados mais realistas para teste do sistema ML
Com proporção menor de anomalias (~2-3%)
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
from app.storage import insert_log, clear_logs
from app.ml_anomaly_detector import train_ml_models, detect_ml_anomalies

def create_realistic_test_data():
    """Cria dados de teste mais realistas com poucas anomalias"""
    print("📊 Criando dados de teste realistas...")
    
    # Limpar logs existentes
    clear_logs()
    print("   ✅ Logs limpos")
    
    test_logs = []
    
    # 1. Dados normais (95% dos logs)
    normal_clients = ["client_001", "client_002", "client_003", "client_004", "client_005"]
    normal_ips = ["192.168.1.10", "192.168.1.11", "192.168.1.12", "10.0.0.5", "10.0.0.6"]
    normal_paths = ["/api/users", "/api/products", "/api/orders", "/api/categories", "/api/search"]
    
    for i in range(950):  # 95% normais
        log = LogEntry(
            requestId=f"normal_{i:04d}",
            clientId=random.choice(normal_clients),
            ip=random.choice(normal_ips),
            apiId="api_realistic",
            path=random.choice(normal_paths),
            method=random.choice(["GET", "POST", "PUT", "DELETE"]),
            status=random.choice([200, 201, 400, 404]),  # Alguns erros normais
            timestamp=datetime.now() - timedelta(hours=random.randint(1, 24), minutes=random.randint(0, 59))
        )
        test_logs.append(log)
    
    # 2. Anomalias sutis (5% dos logs)
    # Cliente com muitos erros (mas poucos)
    for i in range(15):
        log = LogEntry(
            requestId=f"error_{i:03d}",
            clientId="client_suspicious",
            ip="203.0.113.10",
            apiId="api_realistic",
            path="/admin/login",
            method="POST",
            status=403,
            timestamp=datetime.now() - timedelta(minutes=i*5)
        )
        test_logs.append(log)
    
    # IP público suspeito
    for i in range(10):
        log = LogEntry(
            requestId=f"public_ip_{i:03d}",
            clientId="client_public",
            ip="8.8.8.8",
            apiId="api_realistic",
            path="/api/config",
            method="GET",
            status=200,
            timestamp=datetime.now() - timedelta(minutes=i*10)
        )
        test_logs.append(log)
    
    # Atividade noturna
    for i in range(10):
        night_time = datetime.now().replace(hour=2, minute=(i*7) % 60, second=0, microsecond=0)
        log = LogEntry(
            requestId=f"night_{i:03d}",
            clientId="client_night",
            ip="192.168.1.100",
            apiId="api_realistic",
            path="/api/admin",
            method="PUT",
            status=200,
            timestamp=night_time
        )
        test_logs.append(log)
    
    # Path muito longo
    for i in range(5):
        long_path = "/very/deep/nested/path/with/many/levels/" + "a" * (i * 20)
        log = LogEntry(
            requestId=f"longpath_{i:03d}",
            clientId="client_long",
            ip="192.168.1.200",
            apiId="api_realistic",
            path=long_path,
            method="GET",
            status=404,
            timestamp=datetime.now() - timedelta(minutes=i*15)
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
    print(f"      - Normais: 950 logs (95%)")
    print(f"      - Anomalias: 40 logs (4%)")
    print(f"      - Total: {success_count} logs")
    
    return success_count

def test_realistic_detection():
    """Testa a detecção com dados realistas"""
    print("\n🔍 Testando detecção com dados realistas...")
    
    try:
        result = detect_ml_anomalies(apiId="api_realistic", model_name="iforest", hours_back=24)
        
        if "error" not in result:
            print(f"   ✅ Anomalias detectadas: {result.get('anomalies_detected', 0)}")
            print(f"   📊 Taxa de anomalia: {result.get('anomaly_rate', 0)*100:.1f}%")
            print(f"   📈 Score médio: {result.get('score_statistics', {}).get('mean', 0):.3f}")
            
            # Mostrar algumas anomalias específicas
            anomalies = result.get('anomalies', [])
            if anomalies:
                print(f"   🚨 Exemplos de anomalias detectadas:")
                for i, anomaly in enumerate(anomalies[:3]):
                    print(f"      {i+1}. Cliente: {anomaly['clientId']}")
                    print(f"         IP: {anomaly['ip']}")
                    print(f"         Path: {anomaly['path']}")
                    print(f"         Score: {anomaly['anomaly_score']:.3f}")
        else:
            print(f"   ❌ Erro: {result['error']}")
            
    except Exception as e:
        print(f"   ❌ Erro: {e}")

def main():
    """Função principal"""
    print("🚀 TESTE COM DADOS REALISTAS")
    print("=" * 50)
    
    # 1. Criar dados realistas
    logs_created = create_realistic_test_data()
    if logs_created == 0:
        print("❌ Falha ao criar logs")
        return
    
    # 2. Treinar modelos
    print("\n🎯 Treinando modelos...")
    train_result = train_ml_models(apiId="api_realistic", hours_back=24)
    if "error" in train_result:
        print(f"❌ Erro no treinamento: {train_result['error']}")
        return
    
    print("✅ Modelos treinados com sucesso!")
    
    # 3. Testar detecção
    test_realistic_detection()
    
    print("\n✅ Teste concluído!")

if __name__ == "__main__":
    main() 