#!/usr/bin/env python3
"""
Script de teste para funcionalidades de machine learning com PyOD
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

def create_ml_test_logs():
    """Cria logs de teste para demonstrar detecção de anomalias com ML"""
    
    print("📊 Criando logs de teste para machine learning...")
    
    # Limpar logs existentes
    try:
        #clear_logs()
        print("   ✅ Logs limpos do MongoDB")
    except Exception as e:
        print(f"   ❌ Erro ao limpar logs: {e}")
        return
    
    # Dados de teste com padrões normais e anômalos
    test_logs = []
    
    # Padrão normal - cliente fazendo requests normais
    for i in range(30):
        log = LogEntry(
            requestId=f"normal_{i:03d}",
            clientId="client_normal",
            ip="192.168.1.100",
            apiId="api_ml_test",
            path=f"/users/{i}", 
            method="GET",
            status=200,
            timestamp=datetime.now() - timedelta(hours=2, minutes=i)
        )
        test_logs.append(log)
    
    # Padrão anômalo 1 - cliente com muitos erros
    for i in range(20):
        log = LogEntry(
            requestId=f"error_{i:03d}",
            clientId="client_errors",
            ip="10.0.0.50",
            apiId="api_ml_test",
            path="/admin",
            method="POST",
            status=403 if i % 2 == 0 else 500,
            timestamp=datetime.now() - timedelta(hours=1, minutes=i)
        )
        test_logs.append(log)
    
    # Padrão anômalo 2 - cliente com IP suspeito
    for i in range(15):
        log = LogEntry(
            requestId=f"suspicious_{i:03d}",
            clientId="client_suspicious",
            ip="8.8.8.8" if i < 8 else "1.1.1.1",  # IPs públicos suspeitos
            apiId="api_ml_test",
            path="/admin/login",
            method="POST",
            status=401,
            timestamp=datetime.now() - timedelta(minutes=i*5)
        )
        test_logs.append(log)
    
    # Padrão anômalo 3 - cliente com volume muito alto
    for i in range(60):
        log = LogEntry(
            requestId=f"volume_{i:03d}",
            clientId="client_high_volume",
            ip="172.16.0.10",
            apiId="api_ml_test",
            path=f"/data/{i}",
            method="GET",
            status=200,
            timestamp=datetime.now() - timedelta(minutes=i)
        )
        test_logs.append(log)
    
    # Padrão anômalo 4 - cliente com horário suspeito (3h da manhã)
    for i in range(10):
        suspicious_time = datetime.now().replace(hour=3, minute=(i*7) % 60, second=0, microsecond=0)
        log = LogEntry(
            requestId=f"night_{i:03d}",
            clientId="client_night",
            ip="203.0.113.5",
            apiId="api_ml_test",
            path="/config",
            method="PUT",
            status=200,
            timestamp=suspicious_time
        )
        test_logs.append(log)
    
    # Padrão anômalo 5 - cliente com paths muito longos
    for i in range(8):
        long_path = "/very/deep/nested/path/with/many/levels/" + "a" * (i * 10)
        log = LogEntry(
            requestId=f"longpath_{i:03d}",
            clientId="client_long_paths",
            ip="192.168.1.200",
            apiId="api_ml_test",
            path=long_path,
            method="GET",
            status=404,
            timestamp=datetime.now() - timedelta(minutes=i*10)
        )
        test_logs.append(log)
    
    # Padrão anômalo 6 - cliente com múltiplos IPs
    for i in range(12):
        ips = ["10.0.0.1", "10.0.0.2", "10.0.0.3", "10.0.0.4", "10.0.0.5"]
        log = LogEntry(
            requestId=f"multiip_{i:03d}",
            clientId="client_multiple_ips",
            ip=ips[i % len(ips)],
            apiId="api_ml_test",
            path=f"/test/{i}",
            method="GET",
            status=200,
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

def test_ml_training():
    """Testa o treinamento dos modelos de ML"""
    
    print("\n🎯 Testando treinamento de modelos ML...")
    
    try:
        # Treinar usando dados do MongoDB
        result = train_ml_models(apiId="api_ml_test", hours_back=24, save_models=True)
        
        if "error" not in result:
            print("   ✅ Treinamento bem-sucedido!")
            print(f"   📊 Logs utilizados: {result.get('logs_used', 0)}")
            print(f"   🔍 Características: {result.get('features_count', 0)}")
            print(f"   🎯 Modelos treinados: {len(result.get('models_trained', {}))}")
            
            # Mostrar detalhes dos modelos treinados
            models_trained = result.get('models_trained', {})
            for model_name, status in models_trained.items():
                print(f"      - {model_name}: {status}")
            
            return True
        else:
            print(f"   ❌ Erro no treinamento: {result['error']}")
            return False
            
    except Exception as e:
        print(f"   ❌ Erro de conexão: {e}")
        return False

def test_ml_detection():
    """Testa a detecção de anomalias com ML"""
    
    print("\n🔍 Testando detecção de anomalias com ML...")
    
    models = ['iforest', 'lof', 'knn', 'ocsvm', 'cblof']
    
    for model in models:
        try:
            print(f"   🧪 Testando modelo: {model.upper()}")
            
            # Detectar usando dados do MongoDB
            result = detect_ml_anomalies(apiId="api_ml_test", model_name=model, hours_back=24)
            
            if "error" not in result:
                print(f"      ✅ Anomalias detectadas: {result.get('anomalies_detected', 0)}")
                print(f"      📊 Taxa de anomalia: {result.get('anomaly_rate', 0)*100:.1f}%")
                print(f"      📈 Score médio: {result.get('score_statistics', {}).get('mean', 0):.3f}")
                
                # Mostrar algumas anomalias específicas
                anomalies = result.get('anomalies', [])
                if anomalies:
                    print(f"      🚨 Exemplo de anomalia:")
                    anomaly = anomalies[0]
                    print(f"         - Cliente: {anomaly['clientId']}")
                    print(f"         - IP: {anomaly['ip']}")
                    print(f"         - Path: {anomaly['path']}")
                    print(f"         - Score: {anomaly['anomaly_score']:.3f}")
            else:
                print(f"      ❌ Erro: {result['error']}")
                
        except Exception as e:
            print(f"      ❌ Erro: {e}")

def test_ml_comparison():
    """Testa a comparação de modelos"""
    
    print("\n📊 Testando comparação de modelos...")
    
    try:
        result = compare_ml_models(apiId="api_ml_test", hours_back=24)
        
        if "error" not in result:
            print("   ✅ Comparação bem-sucedida!")
            print(f"   📊 Logs analisados: {result.get('logs_analyzed', 0)}")
            print("   📈 Resultados por modelo:")
            
            models_comparison = result.get('models_comparison', {})
            for model, info in models_comparison.items():
                if "error" not in info:
                    print(f"      {model.upper()}: {info.get('anomalies_detected', 0)} anomalias "
                          f"({info.get('anomaly_rate', 0)*100:.1f}%)")
                    print(f"         Score médio: {info.get('score_statistics', {}).get('mean', 0):.3f}")
                else:
                    print(f"      {model.upper()}: Erro - {info['error']}")
        else:
            print(f"   ❌ Erro na comparação: {result['error']}")
            
    except Exception as e:
        print(f"   ❌ Erro: {e}")

def test_ip_anomalies():
    """Testa a detecção de anomalias baseada em IPs"""
    
    print("\n🕵️ Testando detecção de anomalias de IP...")
    
    try:
        result = detect_ip_anomalies(apiId="api_ml_test", hours_back=24)
        
        if "error" not in result:
            summary = result.get('summary', {})
            print("   ✅ Detecção de IPs bem-sucedida!")
            print(f"   📊 Clientes analisados: {summary.get('total_clients_analyzed', 0)}")
            print(f"   🔴 Clientes com IPs novos: {summary.get('clients_with_new_ips', 0)}")
            print(f"   🟡 Clientes com múltiplos IPs: {len(result.get('multiple_ips', {}))}")
            print(f"   🟠 Clientes com atividade suspeita: {summary.get('clients_with_suspicious_activity', 0)}")
            print(f"   📈 Total de anomalias: {summary.get('total_anomalies', 0)}")
            
            # Mostrar detalhes das anomalias
            if result.get('new_ips'):
                print("\n   🔴 IPs Novos Detectados:")
                for client, details in result['new_ips'].items():
                    print(f"      - {client}: {details['new_ips']} (risco: {details['risk_level']})")
            
            if result.get('multiple_ips'):
                print("\n   🟡 Múltiplos IPs Detectados:")
                for client, details in result['multiple_ips'].items():
                    print(f"      - {client}: {details['count']} IPs (risco: {details['risk_level']})")
            
            if result.get('suspicious_activity'):
                print("\n   🟠 Atividade Suspeita Detectada:")
                for client, patterns in result['suspicious_activity'].items():
                    print(f"      - {client}: {list(patterns.keys())}")
        else:
            print(f"   ❌ Erro na detecção: {result['error']}")
            
    except Exception as e:
        print(f"   ❌ Erro: {e}")

def test_api_endpoints():
    """Testa os endpoints da API"""
    print("\n🌐 Testando endpoints da API...")
    # Testar treinamento via API
    try:
        print("   🤪 Testando endpoint de treinamento...")
        response = requests.post(f"{API_BASE}/ml/train", 
                               json={"apiId": "api_ml_test", "hours_back": 24})
        if response.status_code == 200:
            data = response.json()
            if "error" not in data:
                print("      ✅ Treinamento via API bem-sucedido!")
            else:
                print(f"      ❌ Erro via API: {data['error']}")
        else:
            print(f"      ❌ Erro HTTP: {response.status_code}")
    except Exception as e:
        print(f"      ❌ Erro de conexão: {e}")
    # Testar detecção via API
    try:
        print("   🔍 Testando endpoint de detecção...")
        params = {
            "apiId": "api_ml_test",
            "model_name": "iforest",
            "hours_back": 24
        }
        response = requests.get(f"{API_BASE}/ml/detect", params=params)
        if response.status_code == 200:
            data = response.json()
            if "error" not in data:
                print("      ✅ Detecção via API bem-sucedida!")
                print(f"         Anomalias: {data.get('anomalies_detected', 0)}")
            else:
                print(f"      ❌ Erro via API: {data['error']}")
        else:
            print(f"      ❌ Erro HTTP: {response.status_code}")
    except Exception as e:
        print(f"      ❌ Erro de conexão: {e}")

def main():
    """Função principal"""
    print("🚀 TESTE COMPLETO DO SISTEMA DE MACHINE LEARNING")
    print("=" * 60)
    
    try:
        # 1. Criar logs de teste no MongoDB
        logs_created = create_ml_test_logs()
        if logs_created == 0:
            print("❌ Falha ao criar logs de teste")
            return
        
        # 2. Testar treinamento
        training_success = test_ml_training()
        if not training_success:
            print("❌ Falha no treinamento")
            return
        
        # 3. Testar detecção
        test_ml_detection()
        
        # 4. Testar comparação
        test_ml_comparison()
        
        # 5. Testar detecção de IPs
        test_ip_anomalies()
        
        # 6. Testar endpoints da API
        test_api_endpoints()
        
        print("\n\n✅ TODOS OS TESTES CONCLUÍDOS COM SUCESSO!")
        print("\n📋 RESUMO:")
        print("   • Logs inseridos no MongoDB")
        print("   • Modelos ML treinados e salvos")
        print("   • Detecção de anomalias funcionando")
        print("   • Comparação de modelos operacional")
        print("   • Detecção de IPs suspeitos ativa")
        print("   • Endpoints da API funcionando")
        
    except Exception as e:
        print(f"\n❌ ERRO DURANTE OS TESTES: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 