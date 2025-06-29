#!/usr/bin/env python3
"""
Script para Calibração de Threshold
===================================

Este script testa diferentes valores de threshold para encontrar
o melhor valor que maximize a precisão na detecção de anomalias.
"""

import sys
import os
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
API_ID = "test_threshold_calibration"

def clear_all_data():
    """Limpa todos os dados do MongoDB"""
    print("🧹 Limpando toda a base de dados...")
    
    try:
        clear_logs()
        print("   ✅ Logs limpos")
        
        client = MongoClient('mongodb://localhost:27017/')
        db = client['api_logs']
        db.feedback.delete_many({})
        print("   ✅ Feedback limpo")
        
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
        network_addr = int(network.network_address)
        broadcast_addr = int(network.broadcast_address)
        random_ip = random.randint(network_addr, broadcast_addr)
        ip = ipaddress.IPv4Address(random_ip)
        ips.append(str(ip))
    
    return ips[0] if count == 1 else ips

def create_test_dataset():
    """Cria dataset de teste com logs normais e anômalos"""
    print("📊 Criando dataset de teste...")
    
    normal_logs = []
    anomalous_logs = []
    
    # Logs normais (10.000)
    print("   📝 Criando 10.000 logs normais...")
    now = datetime.now()
    for i in range(10000):
        ip = generate_ip_from_network("10.10.15.0/24")
        timestamp = now - timedelta(minutes=random.randint(0, 1439))
        
        log = LogEntry(
            requestId=f"normal_{i:05d}",
            clientId="client_normal",
            ip=ip,
            apiId=API_ID,
            path=random.choice(["/api/users", "/api/data", "/api/reports"]),
            method=random.choice(["GET", "POST"]),
            status=random.choice([200, 201, 202]),
            responseTime=random.randint(100, 500),
            timestamp=timestamp
        )
        normal_logs.append(log)
    
    # Logs anômalos (50)
    print("   🚨 Criando 50 logs anômalos...")
    for i in range(50):
        ip = generate_ip_from_network("172.16.10.0/24")
        timestamp = now - timedelta(minutes=random.randint(0, 1439))
        
        log = LogEntry(
            requestId=f"anomalous_{i:03d}",
            clientId="client_normal",
            ip=ip,
            apiId=API_ID,
            path=random.choice(["/api/admin/delete", "/api/internal/debug"]),
            method=random.choice(["DELETE", "PUT"]),
            status=random.choice([403, 404, 500]),
            responseTime=random.randint(2000, 8000),
            timestamp=timestamp
        )
        anomalous_logs.append(log)
    
    print(f"   ✅ Dataset criado: {len(normal_logs)} normais + {len(anomalous_logs)} anômalos")
    return normal_logs, anomalous_logs

def insert_logs_batch(logs, batch_size=1000):
    """Insere logs em lotes"""
    print(f"📝 Inserindo {len(logs)} logs...")
    
    success_count = 0
    for i in range(0, len(logs), batch_size):
        batch = logs[i:i + batch_size]
        for log in batch:
            try:
                insert_log(log)
                success_count += 1
            except Exception as e:
                print(f"   ❌ Erro ao inserir log: {e}")
    
    print(f"   ✅ {success_count}/{len(logs)} logs inseridos")
    return success_count

def test_threshold(threshold):
    """Testa um threshold específico"""
    try:
        # Treinar modelo
        train_result = train_ml_models(apiId=API_ID, hours_back=24, save_models=True)
        if "error" in train_result:
            return None
        
        # Detectar anomalias
        result = detect_ml_anomalies(apiId=API_ID, model_name='iforest', hours_back=24, threshold=threshold)
        if "error" in result:
            return None
        
        return result
        
    except Exception as e:
        print(f"   ❌ Erro ao testar threshold {threshold}: {e}")
        return None

def analyze_threshold_result(result, threshold):
    """Analisa resultado de um threshold específico"""
    if not result or 'anomalies' not in result:
        return {
            'threshold': threshold,
            'anomalies_detected': 0,
            'true_positives': 0,
            'false_positives': 0,
            'precision': 0.0,
            'recall': 0.0,
            'f1_score': 0.0
        }
    
    true_positives = 0
    false_positives = 0
    
    for anomaly in result['anomalies']:
        ip = anomaly.get('ip', '')
        if ip.startswith('172.16.10.'):
            true_positives += 1
        elif ip.startswith('10.10.15.'):
            false_positives += 1
    
    total_anomalies = len(result['anomalies'])
    expected_anomalies = 50  # Logs anômalos criados
    
    precision = true_positives / total_anomalies if total_anomalies > 0 else 0.0
    recall = true_positives / expected_anomalies if expected_anomalies > 0 else 0.0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    
    return {
        'threshold': threshold,
        'anomalies_detected': total_anomalies,
        'true_positives': true_positives,
        'false_positives': false_positives,
        'precision': precision,
        'recall': recall,
        'f1_score': f1_score
    }

def calibrate_threshold():
    """Calibra o threshold testando diferentes valores"""
    print("🎯 Iniciando Calibração de Threshold")
    print("=" * 50)
    
    # Limpar dados
    if not clear_all_data():
        return None
    
    # Criar dataset
    normal_logs, anomalous_logs = create_test_dataset()
    all_logs = normal_logs + anomalous_logs
    
    # Inserir logs
    logs_inserted = insert_logs_batch(all_logs)
    if logs_inserted == 0:
        print("❌ Falha ao inserir logs")
        return None
    
    print(f"\n🔍 Testando diferentes thresholds...")
    
    # Testar diferentes thresholds
    thresholds_to_test = [
        0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10,
        0.11, 0.12, 0.13, 0.14, 0.15, 0.16, 0.17, 0.18, 0.19, 0.20,
        0.25, 0.30, 0.35, 0.40, 0.45, 0.50
    ]
    
    results = []
    
    for threshold in thresholds_to_test:
        print(f"   🔧 Testando threshold: {threshold:.2f}")
        
        # Limpar modelos para garantir treinamento limpo
        import os
        models_dir = "models"
        if os.path.exists(models_dir):
            for file in os.listdir(models_dir):
                if file.endswith('.pkl'):
                    os.remove(os.path.join(models_dir, file))
        
        result = test_threshold(threshold)
        if result:
            analysis = analyze_threshold_result(result, threshold)
            results.append(analysis)
            
            print(f"      📊 Anomalias: {analysis['anomalies_detected']}, "
                  f"TP: {analysis['true_positives']}, "
                  f"FP: {analysis['false_positives']}, "
                  f"Precisão: {analysis['precision']:.3f}, "
                  f"Recall: {analysis['recall']:.3f}, "
                  f"F1: {analysis['f1_score']:.3f}")
        else:
            print(f"      ❌ Falha no teste")
    
    return results

def find_best_threshold(results):
    """Encontra o melhor threshold baseado em diferentes métricas"""
    if not results:
        return None
    
    print("\n🏆 ANÁLISE DOS MELHORES THRESHOLDS:")
    print("=" * 50)
    
    # Melhor por F1-Score
    best_f1 = max(results, key=lambda x: x['f1_score'])
    print(f"🥇 Melhor F1-Score: {best_f1['f1_score']:.3f} (threshold: {best_f1['threshold']:.2f})")
    print(f"   - Precisão: {best_f1['precision']:.3f}")
    print(f"   - Recall: {best_f1['recall']:.3f}")
    print(f"   - Verdadeiros Positivos: {best_f1['true_positives']}/50")
    print(f"   - Falsos Positivos: {best_f1['false_positives']}")
    
    # Melhor por Precisão (com recall mínimo)
    high_precision = [r for r in results if r['recall'] >= 0.5]  # Pelo menos 50% de recall
    if high_precision:
        best_precision = max(high_precision, key=lambda x: x['precision'])
        print(f"\n🎯 Melhor Precisão (recall >= 50%): {best_precision['precision']:.3f} (threshold: {best_precision['threshold']:.2f})")
        print(f"   - Recall: {best_precision['recall']:.3f}")
        print(f"   - F1-Score: {best_precision['f1_score']:.3f}")
    
    # Melhor por Recall (com precisão mínima)
    high_recall = [r for r in results if r['precision'] >= 0.5]  # Pelo menos 50% de precisão
    if high_recall:
        best_recall = max(high_recall, key=lambda x: x['recall'])
        print(f"\n🎯 Melhor Recall (precisão >= 50%): {best_recall['recall']:.3f} (threshold: {best_recall['threshold']:.2f})")
        print(f"   - Recall: {best_recall['recall']:.3f}")
        print(f"   - Precisão: {best_recall['precision']:.3f}")
        print(f"   - F1-Score: {best_recall['f1_score']:.3f}")
    
    # Recomendação
    print(f"\n💡 RECOMENDAÇÃO:")
    print(f"   Para máxima precisão: threshold = {best_f1['threshold']:.2f}")
    print(f"   Este valor maximiza o F1-Score, balanceando precisão e recall")
    
    return best_f1

def update_threshold_config(best_threshold):
    """Atualiza a configuração com o melhor threshold"""
    try:
        config_data = {"threshold": best_threshold}
        response = requests.post(f"{API_BASE}/config/ml_detection", json=config_data)
        
        if response.status_code == 200:
            print(f"\n✅ Threshold atualizado para {best_threshold:.2f} na configuração!")
            return True
        else:
            print(f"\n⚠️ Erro ao atualizar threshold: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"\n⚠️ Erro ao atualizar threshold: {e}")
        return False

def main():
    """Função principal"""
    print("🚀 CALIBRAÇÃO DE THRESHOLD PARA DETECÇÃO DE ANOMALIAS")
    print("=" * 60)
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Calibrar threshold
        results = calibrate_threshold()
        if not results:
            print("❌ Falha na calibração")
            return
        
        # Encontrar melhor threshold
        best_result = find_best_threshold(results)
        if not best_result:
            print("❌ Nenhum resultado válido encontrado")
            return
        
        # Atualizar configuração
        update_threshold_config(best_result['threshold'])
        
        print("\n" + "=" * 60)
        print("🏁 CALIBRAÇÃO CONCLUÍDA!")
        print("=" * 60)
        
        # Salvar resultados em arquivo
        with open('threshold_calibration_results.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n📄 Resultados salvos em: threshold_calibration_results.json")
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 