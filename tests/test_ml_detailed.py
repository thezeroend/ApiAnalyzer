#!/usr/bin/env python3
"""
Script para mostrar detalhes das anomalias detectadas pelo ML
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
from app.ml_anomaly_detector import train_ml_models, detect_ml_anomalies, compare_ml_models
from app.analyzer import detect_ip_anomalies

# Configuração
API_BASE = "http://localhost:8000"

def create_detailed_test_logs():
    """Cria logs de teste mais específicos para demonstrar anomalias"""
    
    print("📊 Criando logs de teste detalhados...")
    
    # Limpar logs existentes
    try:
        clear_logs()
        print("   ✅ Logs limpos do MongoDB")
    except Exception as e:
        print(f"   ❌ Erro ao limpar logs: {e}")
        return 0
    
    test_logs = []
    
    # 1. Logs normais (padrão esperado)
    print("   📝 Criando logs normais...")
    for i in range(20):
        log = LogEntry(
            requestId=f"normal_{i:03d}",
            clientId="client_normal",
            ip="192.168.1.100",
            apiId="api_detailed_test",
            path=f"/api/users/{i}", 
            method="GET",
            status=200,
            responseTime=150,
            timestamp=datetime.now() - timedelta(hours=2, minutes=i)
        )
        test_logs.append(log)
    
    # 2. Logs com erros (anômalos)
    print("   🚨 Criando logs com erros...")
    for i in range(10):
        log = LogEntry(
            requestId=f"error_{i:03d}",
            clientId="client_errors",
            ip="10.0.0.50",
            apiId="api_detailed_test",
            path="/api/admin/delete",
            method="DELETE",
            status=403,
            responseTime=2000,
            timestamp=datetime.now() - timedelta(hours=1, minutes=i)
        )
        test_logs.append(log)
    
    # 3. Logs com IPs suspeitos
    print("   🕵️ Criando logs com IPs suspeitos...")
    for i in range(8):
        log = LogEntry(
            requestId=f"suspicious_{i:03d}",
            clientId="client_suspicious",
            ip="8.8.8.8",
            apiId="api_detailed_test",
            path="/api/admin/login",
            method="POST",
            status=401,
            responseTime=500,
            timestamp=datetime.now() - timedelta(minutes=i*5)
        )
        test_logs.append(log)
    
    # 4. Logs com volume muito alto
    print("   📈 Criando logs com volume alto...")
    for i in range(25):
        log = LogEntry(
            requestId=f"volume_{i:03d}",
            clientId="client_high_volume",
            ip="172.16.0.10",
            apiId="api_detailed_test",
            path=f"/api/data/{i}",
            method="GET",
            status=200,
            responseTime=100,
            timestamp=datetime.now() - timedelta(minutes=i)
        )
        test_logs.append(log)
    
    # 5. Logs com horário suspeito (3h da manhã)
    print("   🌙 Criando logs com horário suspeito...")
    for i in range(5):
        suspicious_time = datetime.now().replace(hour=3, minute=(i*10) % 60, second=0, microsecond=0)
        log = LogEntry(
            requestId=f"night_{i:03d}",
            clientId="client_night",
            ip="203.0.113.5",
            apiId="api_detailed_test",
            path="/api/config/system",
            method="PUT",
            status=200,
            responseTime=3000,
            timestamp=suspicious_time
        )
        test_logs.append(log)
    
    # 6. Logs com paths muito longos
    print("   🛤️ Criando logs com paths longos...")
    for i in range(6):
        long_path = "/api/very/deep/nested/path/with/many/levels/" + "a" * (i * 15)
        log = LogEntry(
            requestId=f"longpath_{i:03d}",
            clientId="client_long_paths",
            ip="192.168.1.200",
            apiId="api_detailed_test",
            path=long_path,
            method="GET",
            status=404,
            responseTime=5000,
            timestamp=datetime.now() - timedelta(minutes=i*15)
        )
        test_logs.append(log)
    
    # 7. Logs com múltiplos IPs
    print("   🌐 Criando logs com múltiplos IPs...")
    ips = ["10.0.0.1", "10.0.0.2", "10.0.0.3", "10.0.0.4", "10.0.0.5"]
    for i in range(10):
        log = LogEntry(
            requestId=f"multiip_{i:03d}",
            clientId="client_multiple_ips",
            ip=ips[i % len(ips)],
            apiId="api_detailed_test",
            path=f"/api/test/{i}",
            method="GET",
            status=200,
            responseTime=200,
            timestamp=datetime.now() - timedelta(minutes=i*2)
        )
        test_logs.append(log)
    
    # 8. Logs com erros de servidor
    print("   💥 Criando logs com erros de servidor...")
    for i in range(8):
        log = LogEntry(
            requestId=f"server_error_{i:03d}",
            clientId="client_server_errors",
            ip="192.168.1.150",
            apiId="api_detailed_test",
            path="/api/internal/system/reboot",
            method="POST",
            status=500,
            responseTime=8000,
            timestamp=datetime.now() - timedelta(minutes=i*8)
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

def show_detailed_anomalies():
    """Mostra detalhes específicos das anomalias detectadas"""
    
    print("\n🔍 ANALISANDO ANOMALIAS DETECTADAS")
    print("=" * 50)
    
    models = ['iforest', 'lof', 'knn', 'ocsvm', 'cblof']
    
    for model in models:
        print(f"\n🧪 MODELO: {model.upper()}")
        print("-" * 30)
        
        try:
            result = detect_ml_anomalies(apiId="api_detailed_test", model_name=model, hours_back=24)
            
            if "error" not in result:
                anomalies = result.get('anomalies', [])
                total_detected = result.get('anomalies_detected', 0)
                anomaly_rate = result.get('anomaly_rate', 0) * 100
                
                print(f"📊 Total de anomalias: {total_detected} ({anomaly_rate:.1f}%)")
                
                if anomalies:
                    print("\n🚨 ANOMALIAS DETECTADAS:")
                    for i, anomaly in enumerate(anomalies[:10]):  # Mostrar apenas as primeiras 10
                        print(f"\n   {i+1}. Log ID: {anomaly['requestId']}")
                        print(f"      Cliente: {anomaly['clientId']}")
                        print(f"      IP: {anomaly['ip']}")
                        print(f"      Path: {anomaly['path']}")
                        print(f"      Método: {anomaly['method']}")
                        print(f"      Status: {anomaly['status']}")
                        print(f"      Score: {anomaly['anomaly_score']:.3f}")
                        print(f"      Timestamp: {anomaly['timestamp']}")
                        
                        # Mostrar features se disponível
                        if 'features' in anomaly:
                            print(f"      Features: {anomaly['features']}")
                else:
                    print("   ✅ Nenhuma anomalia detectada")
            else:
                print(f"   ❌ Erro: {result['error']}")
                
        except Exception as e:
            print(f"   ❌ Erro: {e}")

def show_ip_anomalies():
    """Mostra detalhes das anomalias de IP"""
    
    print("\n🕵️ ANOMALIAS DE IP DETECTADAS")
    print("=" * 40)
    
    try:
        result = detect_ip_anomalies(apiId="api_detailed_test", hours_back=24)
        
        if "error" not in result:
            summary = result.get('summary', {})
            
            print(f"📊 Clientes analisados: {summary.get('total_clients_analyzed', 0)}")
            print(f"🔴 Clientes com IPs novos: {summary.get('clients_with_new_ips', 0)}")
            print(f"🟡 Clientes com múltiplos IPs: {len(result.get('multiple_ips', {}))}")
            print(f"🟠 Clientes com atividade suspeita: {summary.get('clients_with_suspicious_activity', 0)}")
            print(f"📈 Total de anomalias: {summary.get('total_anomalies', 0)}")
            
            # Detalhes das anomalias
            if result.get('new_ips'):
                print("\n🔴 IPs NOVOS DETECTADOS:")
                for client, details in result['new_ips'].items():
                    print(f"   - {client}: {details['new_ips']} (risco: {details['risk_level']})")
            
            if result.get('multiple_ips'):
                print("\n🟡 MÚLTIPLOS IPs DETECTADOS:")
                for client, details in result['multiple_ips'].items():
                    print(f"   - {client}: {details['count']} IPs - {details['ips']} (risco: {details['risk_level']})")
            
            if result.get('suspicious_activity'):
                print("\n🟠 ATIVIDADE SUSPEITA DETECTADA:")
                for client, patterns in result['suspicious_activity'].items():
                    print(f"   - {client}: {list(patterns.keys())}")
        else:
            print(f"❌ Erro: {result['error']}")
            
    except Exception as e:
        print(f"❌ Erro: {e}")

def main():
    """Função principal"""
    print("🚀 TESTE DETALHADO DE DETECÇÃO DE ANOMALIAS")
    print("=" * 50)
    
    try:
        # 1. Criar logs de teste
        logs_created = create_detailed_test_logs()
        if logs_created == 0:
            print("❌ Falha ao criar logs de teste")
            return
        
        # 2. Treinar modelos
        print("\n🎯 Treinando modelos...")
        result = train_ml_models(apiId="api_detailed_test", hours_back=24, save_models=True)
        if "error" in result:
            print(f"❌ Erro no treinamento: {result['error']}")
            return
        print("✅ Modelos treinados com sucesso!")
        
        # 3. Mostrar anomalias detalhadas
        show_detailed_anomalies()
        
        # 4. Mostrar anomalias de IP
        show_ip_anomalies()
        
        print("\n\n✅ ANÁLISE CONCLUÍDA!")
        print("\n📋 RESUMO:")
        print("   • Logs de teste criados com padrões específicos")
        print("   • Modelos ML treinados")
        print("   • Anomalias detalhadas analisadas")
        print("   • Anomalias de IP verificadas")
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 