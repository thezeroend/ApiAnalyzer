#!/usr/bin/env python3
"""
Script para testar detecção de anomalias baseada em redes IP
Cenário: 10.000 requisições normais da rede 10.10.15.0/24
         Algumas requisições anômalas da rede 172.16.10.0/24
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
import ipaddress
from app.models import LogEntry
from app.storage import insert_log, clear_logs, get_all_logs
from app.ml_anomaly_detector import train_ml_models, detect_ml_anomalies
from app.feedback_system import feedback_system
from pymongo import MongoClient

# Configuração
API_BASE = "http://localhost:8000"
API_ID = "test_network_anomaly"

def clear_all_data():
    """Limpa todos os dados do MongoDB"""
    print("🧹 Limpando toda a base de dados...")
    
    try:
        # Limpar logs
        clear_logs()
        print("   ✅ Logs limpos")
        
        # Limpar feedback
        client = MongoClient('mongodb://localhost:27017/')
        db = client['api_logs']
        db.feedback.delete_many({})
        print("   ✅ Feedback limpo")
        
        # Limpar modelos
        import os
        models_dir = "models"
        if os.path.exists(models_dir):
            for file in os.listdir(models_dir):
                if file.endswith('.pkl'):
                    os.remove(os.path.join(models_dir, file))
            print("   ✅ Modelos limpos")
        
        print("   ✅ Base de dados completamente limpa!")
        return True
        
    except Exception as e:
        print(f"   ❌ Erro ao limpar dados: {e}")
        return False

def generate_ip_from_network(network_str, count=1):
    """Gera IPs aleatórios de uma rede específica"""
    network = ipaddress.IPv4Network(network_str, strict=False)
    ips = []
    
    for _ in range(count):
        # Gerar IP aleatório na rede
        network_addr = int(network.network_address)
        broadcast_addr = int(network.broadcast_address)
        random_ip = random.randint(network_addr, broadcast_addr)
        ip = ipaddress.IPv4Address(random_ip)
        ips.append(str(ip))
    
    return ips[0] if count == 1 else ips

def get_configured_threshold():
    """Busca o threshold configurado via API"""
    try:
        resp = requests.get(f"{API_BASE}/config/ml_detection")
        if resp.status_code == 200:
            data = resp.json()
            return float(data.get("threshold", 0.12))
        else:
            print(f"⚠️  Não foi possível obter threshold da API, usando padrão 0.12")
            return 0.12
    except Exception as e:
        print(f"⚠️  Erro ao buscar threshold: {e}")
        return 0.12

def create_normal_logs():
    """Cria 10.000 logs normais da rede 10.10.15.0/24 (timestamps garantidos nas últimas 24h)"""
    print("📊 Criando 10.000 logs normais da rede 10.10.15.0/24...")
    normal_logs = []
    client_id = "client_normal"
    success_statuses = [200, 201, 202, 204]
    methods = ["GET", "POST", "PUT", "DELETE"]
    paths = [
        "/api/users",
        "/api/users/profile",
        "/api/users/settings",
        "/api/data",
        "/api/data/export",
        "/api/reports",
        "/api/reports/daily",
        "/api/reports/weekly",
        "/api/config",
        "/api/config/app"
    ]
    now = datetime.now()
    for i in range(10000):
        ip = generate_ip_from_network("10.10.15.0/24")
        # Timestamp garantido nas últimas 24h
        timestamp = now - timedelta(minutes=random.randint(0, 1439))
        log = LogEntry(
            requestId=f"normal_{i:05d}",
            clientId=client_id,
            ip=ip,
            apiId=API_ID,
            path=random.choice(paths),
            method=random.choice(methods),
            status=random.choice(success_statuses),
            responseTime=random.randint(100, 500),
            timestamp=timestamp
        )
        normal_logs.append(log)
        if (i + 1) % 1000 == 0:
            print(f"   📝 {i + 1}/10000 logs normais criados...")
    print(f"   ✅ {len(normal_logs)} logs normais criados!")
    return normal_logs

def create_anomalous_logs():
    """Cria logs anômalos da rede 172.16.10.0/24 (timestamps garantidos nas últimas 24h)"""
    print("🚨 Criando logs anômalos da rede 172.16.10.0/24...")
    anomalous_logs = []
    client_id = "client_normal"
    error_statuses = [400, 401, 403, 404, 500, 502, 503]
    suspicious_methods = ["DELETE", "PUT", "PATCH"]
    suspicious_paths = [
        "/api/users",
        "/api/users/profile",
        "/api/users/settings",
        "/api/data",
        "/api/data/export",
        "/api/reports",
        "/api/reports/daily",
        "/api/reports/weekly",
        "/api/config",
        "/api/config/app"
    ]
    now = datetime.now()
    for i in range(50):
        ip = generate_ip_from_network("172.16.10.0/24")
        # Timestamp garantido nas últimas 24h
        timestamp = now - timedelta(minutes=random.randint(0, 1439))
        log = LogEntry(
            requestId=f"anomalous_{i:03d}",
            clientId=client_id,
            ip=ip,
            apiId=API_ID,
            path=random.choice(suspicious_paths),
            method=random.choice(suspicious_methods),
            status=random.choice(error_statuses),
            responseTime=random.randint(1000, 5000),
            timestamp=timestamp
        )
        anomalous_logs.append(log)
    print(f"   ✅ {len(anomalous_logs)} logs anômalos criados!")
    return anomalous_logs

def insert_logs_batch(logs, batch_size=1000):
    """Insere logs em lotes para melhor performance"""
    print(f"📝 Inserindo {len(logs)} logs no MongoDB...")
    
    success_count = 0
    total_batches = (len(logs) + batch_size - 1) // batch_size
    
    for i in range(0, len(logs), batch_size):
        batch = logs[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        
        print(f"   📦 Inserindo lote {batch_num}/{total_batches} ({len(batch)} logs)...")
        
        for log in batch:
            try:
                insert_log(log)
                success_count += 1
            except Exception as e:
                print(f"   ❌ Erro ao inserir log: {e}")
        
        print(f"   ✅ Lote {batch_num} inserido com sucesso!")
    
    print(f"   ✅ {success_count}/{len(logs)} logs inseridos com sucesso!")
    return success_count

def train_and_detect(threshold=0.12):
    """Treina modelo e detecta anomalias"""
    print(f"\n🎯 Treinando modelo com dados de rede (threshold={threshold})...")
    
    result = train_ml_models(apiId=API_ID, hours_back=24, save_models=True)
    if "error" in result:
        print(f"❌ Erro no treinamento: {result['error']}")
        return None
    
    print("✅ Modelo treinado com sucesso!")
    
    print(f"\n🔍 Detectando anomalias (threshold={threshold})...")
    result = detect_ml_anomalies(apiId=API_ID, model_name='iforest', hours_back=24, threshold=threshold)
    
    if "error" in result:
        print(f"❌ Erro na detecção: {result['error']}")
        return None
    
    print(f"📊 Anomalias detectadas: {result.get('anomalies_detected', 0)}")
    return result

def analyze_results(result):
    """Analisa os resultados da detecção"""
    if not result or 'anomalies' not in result:
        print("❌ Nenhuma anomalia detectada para análise")
        return
    
    print("\n📋 Análise detalhada das anomalias detectadas:")
    
    normal_network_anomalies = []
    anomalous_network_anomalies = []
    other_anomalies = []
    
    for anomaly in result['anomalies']:
        log_id = anomaly['requestId']
        ip = anomaly.get('ip', '')
        score = anomaly.get('anomaly_score', 0)
        
        if ip.startswith('10.10.15.'):
            normal_network_anomalies.append((log_id, ip, score))
        elif ip.startswith('172.16.10.'):
            anomalous_network_anomalies.append((log_id, ip, score))
        else:
            other_anomalies.append((log_id, ip, score))
    
    print(f"\n🔍 Anomalias da rede normal (10.10.15.0/24): {len(normal_network_anomalies)}")
    if normal_network_anomalies:
        print("   (Falsos positivos - não deveriam ser detectados)")
        for log_id, ip, score in normal_network_anomalies[:5]:  # Mostrar apenas os primeiros 5
            print(f"   - {log_id}: {ip} (score: {score:.3f})")
        if len(normal_network_anomalies) > 5:
            print(f"   ... e mais {len(normal_network_anomalies) - 5}")
    
    print(f"\n🚨 Anomalias da rede suspeita (172.16.10.0/24): {len(anomalous_network_anomalies)}")
    if anomalous_network_anomalies:
        print("   (Verdadeiros positivos - deveriam ser detectados)")
        for log_id, ip, score in anomalous_network_anomalies:
            print(f"   - {log_id}: {ip} (score: {score:.3f})")
    
    print(f"\n❓ Outras anomalias: {len(other_anomalies)}")
    if other_anomalies:
        for log_id, ip, score in other_anomalies[:3]:
            print(f"   - {log_id}: {ip} (score: {score:.3f})")
    
    # Calcular métricas
    total_normal_logs = 10000
    total_anomalous_logs = 50
    
    false_positives = len(normal_network_anomalies)
    true_positives = len(anomalous_network_anomalies)
    
    false_positive_rate = (false_positives / total_normal_logs) * 100
    true_positive_rate = (true_positives / total_anomalous_logs) * 100
    
    print(f"\n📊 MÉTRICAS DE DETECÇÃO:")
    print(f"   - Taxa de falsos positivos: {false_positive_rate:.2f}% ({false_positives}/{total_normal_logs})")
    print(f"   - Taxa de verdadeiros positivos: {true_positive_rate:.2f}% ({true_positives}/{total_anomalous_logs})")
    print(f"   - Precisão: {true_positives}/{true_positives + false_positives} = {(true_positives/(true_positives + false_positives)*100):.2f}%" if (true_positives + false_positives) > 0 else "   - Precisão: N/A")

def main():
    """Função principal"""
    print("🚀 TESTE DE DETECÇÃO DE ANOMALIAS POR REDE IP")
    print("=" * 60)
    print("Cenário: 10.000 logs normais (10.10.15.0/24) + 50 logs anômalos (172.16.10.0/24)")
    print("=" * 60)
    
    try:
        # 1. Limpar toda a base
        if not clear_all_data():
            print("❌ Falha ao limpar dados")
            return
        
        # 2. Criar logs normais
        normal_logs = create_normal_logs()
        
        # 3. Criar logs anômalos
        anomalous_logs = create_anomalous_logs()
        
        # 4. Inserir todos os logs
        all_logs = normal_logs + anomalous_logs
        logs_inserted = insert_logs_batch(all_logs)
        
        if logs_inserted == 0:
            print("❌ Falha ao inserir logs")
            return
        
        # 5. Buscar threshold configurado
        threshold = get_configured_threshold()
        print(f"\n🔧 Threshold configurado na aplicação: {threshold}")
        
        # 6. Treinar e detectar (com threshold ajustado)
        result = train_and_detect(threshold=threshold)
        if not result:
            print("❌ Falha na detecção")
            return
        
        # 7. Analisar resultados
        analyze_results(result)
        
        print("\n" + "=" * 60)
        print("🏁 TESTE CONCLUÍDO!")
        print("=" * 60)
        
        # Resumo final
        print(f"\n📊 RESUMO FINAL:")
        print(f"   - Logs normais criados: {len(normal_logs)}")
        print(f"   - Logs anômalos criados: {len(anomalous_logs)}")
        print(f"   - Total inserido: {logs_inserted}")
        print(f"   - Anomalias detectadas: {result.get('anomalies_detected', 0)}")
        
        # Verificar se o ML detectou as anomalias de rede
        if 'anomalies' in result:
            anomalous_ips = [a.get('ip', '') for a in result['anomalies'] if a.get('ip', '').startswith('172.16.10.')]
            if anomalous_ips:
                print(f"   - ✅ SUCCESS: ML detectou anomalias da rede 172.16.10.0/24!")
                print(f"   - IPs anômalos detectados: {len(anomalous_ips)}")
            else:
                print(f"   - ⚠️  WARNING: ML não detectou anomalias da rede 172.16.10.0/24")
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 