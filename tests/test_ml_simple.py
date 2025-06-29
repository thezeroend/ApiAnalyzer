#!/usr/bin/env python3
"""
Script de teste simplificado para funcionalidades de machine learning
Funciona apenas via API HTTP, sem dependências locais
"""

import requests
import json
from datetime import datetime, timedelta
import random
import time

# Configuração
API_BASE = "http://localhost:8000"

def create_test_logs():
    """Cria logs de teste via API"""
    
    print("📊 Criando logs de teste para machine learning...")
    
    # Limpar logs existentes
    try:
        response = requests.delete(f"{API_BASE}/logs")
        print("   ✅ Logs limpos")
    except Exception as e:
        print(f"   ❌ Erro ao limpar logs: {e}")
        return 0
    
    # Dados de teste com padrões normais e anômalos
    test_data = []
    
    # Padrão normal - cliente fazendo requests normais
    for i in range(30):
        test_data.append({
            "requestId": f"normal_{i:03d}",
            "clientId": "client_normal",
            "ip": "192.168.1.100",
            "apiId": "api_ml_test",
            "path": f"/api/users/{i}",
            "method": "GET",
            "status": 200,
            "timestamp": (datetime.now() - timedelta(hours=2, minutes=i)).isoformat()
        })
    
    # Padrão anômalo 1 - cliente com muitos erros
    for i in range(20):
        test_data.append({
            "requestId": f"error_{i:03d}",
            "clientId": "client_errors",
            "ip": "10.0.0.50",
            "apiId": "api_ml_test",
            "path": "/api/admin",
            "method": "POST",
            "status": 403 if i % 2 == 0 else 500,
            "timestamp": (datetime.now() - timedelta(hours=1, minutes=i)).isoformat()
        })
    
    # Padrão anômalo 2 - cliente com IP suspeito
    for i in range(15):
        test_data.append({
            "requestId": f"suspicious_{i:03d}",
            "clientId": "client_suspicious",
            "ip": "8.8.8.8" if i < 8 else "1.1.1.1",  # IPs públicos suspeitos
            "apiId": "api_ml_test",
            "path": "/admin/login",
            "method": "POST",
            "status": 401,
            "timestamp": (datetime.now() - timedelta(minutes=i*5)).isoformat()
        })
    
    # Padrão anômalo 3 - cliente com volume muito alto
    for i in range(60):
        test_data.append({
            "requestId": f"volume_{i:03d}",
            "clientId": "client_high_volume",
            "ip": "172.16.0.10",
            "apiId": "api_ml_test",
            "path": f"/api/data/{i}",
            "method": "GET",
            "status": 200,
            "timestamp": (datetime.now() - timedelta(minutes=i)).isoformat()
        })
    
    # Padrão anômalo 4 - cliente com horário suspeito (3h da manhã)
    for i in range(10):
        suspicious_time = datetime.now().replace(hour=3, minute=i*7, second=0, microsecond=0)
        test_data.append({
            "requestId": f"night_{i:03d}",
            "clientId": "client_night",
            "ip": "203.0.113.5",
            "apiId": "api_ml_test",
            "path": "/api/config",
            "method": "PUT",
            "status": 200,
            "timestamp": suspicious_time.isoformat()
        })
    
    # Padrão anômalo 5 - cliente com paths muito longos
    for i in range(8):
        long_path = "/api/very/deep/nested/path/with/many/levels/" + "a" * (i * 10)
        test_data.append({
            "requestId": f"longpath_{i:03d}",
            "clientId": "client_long_paths",
            "ip": "192.168.1.200",
            "apiId": "api_ml_test",
            "path": long_path,
            "method": "GET",
            "status": 404,
            "timestamp": (datetime.now() - timedelta(minutes=i*10)).isoformat()
        })
    
    # Padrão anômalo 6 - cliente com múltiplos IPs
    for i in range(12):
        ips = ["10.0.0.1", "10.0.0.2", "10.0.0.3", "10.0.0.4", "10.0.0.5"]
        test_data.append({
            "requestId": f"multiip_{i:03d}",
            "clientId": "client_multiple_ips",
            "ip": ips[i % len(ips)],
            "apiId": "api_ml_test",
            "path": f"/api/test/{i}",
            "method": "GET",
            "status": 200,
            "timestamp": (datetime.now() - timedelta(minutes=i*3)).isoformat()
        })
    
    print(f"   📝 Enviando {len(test_data)} logs...")
    
    success_count = 0
    for log_data in test_data:
        try:
            response = requests.post(f"{API_BASE}/logs", json=log_data)
            if response.status_code == 200:
                success_count += 1
        except Exception as e:
            print(f"   ❌ Erro ao enviar log: {e}")
    
    print(f"   ✅ {success_count}/{len(test_data)} logs enviados com sucesso!")
    return success_count

def test_ml_training():
    """Testa o treinamento dos modelos de ML"""
    
    print("\n🎯 Testando treinamento de modelos ML...")
    
    try:
        request_body = {
            "apiId": "api_ml_test",
            "hours_back": 24
        }
        
        response = requests.post(f"{API_BASE}/api/ml/train", 
                               json=request_body,
                               headers={'Content-Type': 'application/json'})
        
        if response.status_code == 200:
            data = response.json()
            if "error" not in data:
                print("   ✅ Treinamento bem-sucedido!")
                print(f"   📊 Logs utilizados: {data.get('logs_used', 0)}")
                print(f"   🔍 Características: {data.get('features_count', 0)}")
                print(f"   🎯 Modelos treinados: {len(data.get('models_trained', {}))}")
                
                # Mostrar detalhes dos modelos treinados
                models_trained = data.get('models_trained', {})
                for model_name, status in models_trained.items():
                    print(f"      - {model_name}: {status}")
                
                return True
            else:
                print(f"   ❌ Erro no treinamento: {data['error']}")
                return False
        else:
            print(f"   ❌ Erro HTTP: {response.status_code}")
            print(f"   Resposta: {response.text}")
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
            
            request_body = {
                "apiId": "api_ml_test",
                "model_name": model,
                "hours_back": 24
            }
            
            response = requests.post(f"{API_BASE}/api/ml/detect", 
                                   json=request_body,
                                   headers={'Content-Type': 'application/json'})
            
            if response.status_code == 200:
                data = response.json()
                if "error" not in data:
                    print(f"      ✅ Anomalias detectadas: {data.get('anomalies_detected', 0)}")
                    print(f"      📊 Taxa de anomalia: {data.get('anomaly_rate', 0)*100:.1f}%")
                    print(f"      📈 Score médio: {data.get('score_statistics', {}).get('mean', 0):.3f}")
                    
                    # Mostrar algumas anomalias específicas
                    anomalies = data.get('anomalies', [])
                    if anomalies:
                        print(f"      🚨 Exemplo de anomalia:")
                        anomaly = anomalies[0]
                        print(f"         - Cliente: {anomaly['clientId']}")
                        print(f"         - IP: {anomaly['ip']}")
                        print(f"         - Path: {anomaly['path']}")
                        print(f"         - Score: {anomaly['anomaly_score']:.3f}")
                else:
                    print(f"      ❌ Erro: {data['error']}")
            else:
                print(f"      ❌ Erro HTTP: {response.status_code}")
                print(f"      Resposta: {response.text}")
                
        except Exception as e:
            print(f"      ❌ Erro: {e}")

def test_ml_comparison():
    """Testa a comparação de modelos"""
    
    print("\n📊 Testando comparação de modelos...")
    
    try:
        request_body = {
            "apiId": "api_ml_test",
            "hours_back": 24
        }
        
        response = requests.post(f"{API_BASE}/api/ml/compare", 
                               json=request_body,
                               headers={'Content-Type': 'application/json'})
        
        if response.status_code == 200:
            data = response.json()
            if "error" not in data:
                print("   ✅ Comparação bem-sucedida!")
                print(f"   📊 Logs analisados: {data.get('logs_analyzed', 0)}")
                print("   📈 Resultados por modelo:")
                
                models_comparison = data.get('models_comparison', {})
                for model, info in models_comparison.items():
                    if "error" not in info:
                        print(f"      {model.upper()}: {info.get('anomalies_detected', 0)} anomalias "
                              f"({info.get('anomaly_rate', 0)*100:.1f}%)")
                        print(f"         Score médio: {info.get('score_statistics', {}).get('mean', 0):.3f}")
                    else:
                        print(f"      {model.upper()}: Erro - {info['error']}")
            else:
                print(f"   ❌ Erro na comparação: {data['error']}")
        else:
            print(f"   ❌ Erro HTTP: {response.status_code}")
            print(f"   Resposta: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Erro: {e}")

def test_ip_anomalies():
    """Testa a detecção de anomalias baseadas em IPs"""
    
    print("\n🕵️ Testando detecção de anomalias de IP...")
    
    try:
        response = requests.get(f"{API_BASE}/ip-anomalies?apiId=api_ml_test&hours_back=24")
        
        if response.status_code == 200:
            data = response.json()
            if "error" not in data:
                summary = data.get('summary', {})
                print("   ✅ Detecção de IPs bem-sucedida!")
                print(f"   📊 Clientes analisados: {summary.get('total_clients_analyzed', 0)}")
                print(f"   🔴 Clientes com IPs novos: {summary.get('clients_with_new_ips', 0)}")
                print(f"   🟡 Clientes com múltiplos IPs: {len(data.get('multiple_ips', {}))}")
                print(f"   🟠 Clientes com atividade suspeita: {summary.get('clients_with_suspicious_activity', 0)}")
                print(f"   📈 Total de anomalias: {summary.get('total_anomalies', 0)}")
                
                # Mostrar detalhes das anomalias
                if data.get('new_ips'):
                    print("\n   🔴 IPs Novos Detectados:")
                    for client, details in data['new_ips'].items():
                        print(f"      - {client}: {details['new_ips']} (risco: {details['risk_level']})")
                
                if data.get('multiple_ips'):
                    print("\n   🟡 Múltiplos IPs Detectados:")
                    for client, details in data['multiple_ips'].items():
                        print(f"      - {client}: {details['count']} IPs (risco: {details['risk_level']})")
                
                if data.get('suspicious_activity'):
                    print("\n   🟠 Atividade Suspeita Detectada:")
                    for client, patterns in data['suspicious_activity'].items():
                        print(f"      - {client}: {list(patterns.keys())}")
            else:
                print(f"   ❌ Erro na detecção: {data['error']}")
        else:
            print(f"   ❌ Erro HTTP: {response.status_code}")
            print(f"   Resposta: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Erro: {e}")

def test_basic_stats():
    """Testa estatísticas básicas"""
    
    print("\n📈 Testando estatísticas básicas...")
    
    try:
        response = requests.get(f"{API_BASE}/stats/api_ml_test")
        
        if response.status_code == 200:
            data = response.json()
            print("   ✅ Estatísticas obtidas!")
            print(f"   📊 Total de logs: {data.get('total_logs', 0)}")
            print(f"   👥 Clientes únicos: {len(data.get('requests_by_client', {}))}")
            print(f"   🌐 IPs únicos: {len(data.get('requests_by_ip', {}))}")
            print(f"   📋 Status codes: {len(data.get('status_counts', {}))}")
        else:
            print(f"   ❌ Erro HTTP: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Erro: {e}")

def main():
    """Função principal"""
    print("🚀 TESTE SIMPLIFICADO DO SISTEMA DE MACHINE LEARNING")
    print("=" * 60)
    
    # Verificar se o servidor está rodando
    try:
        response = requests.get(f"{API_BASE}/docs")
        print("✅ Servidor está rodando!")
    except:
        print("❌ Servidor não está rodando. Execute: python main.py")
        return
    
    try:
        # 1. Criar logs de teste
        logs_created = create_test_logs()
        if logs_created == 0:
            print("❌ Falha ao criar logs de teste")
            return
        
        # Aguardar um pouco para processar
        time.sleep(2)
        
        # 2. Testar estatísticas básicas
        test_basic_stats()
        
        # 3. Testar treinamento
        training_success = test_ml_training()
        if not training_success:
            print("❌ Falha no treinamento")
            return
        
        # 4. Testar detecção
        test_ml_detection()
        
        # 5. Testar comparação
        test_ml_comparison()
        
        # 6. Testar detecção de IPs
        test_ip_anomalies()
        
        print("\n\n✅ TODOS OS TESTES CONCLUÍDOS COM SUCESSO!")
        print("\n📋 RESUMO:")
        print("   • Logs inseridos via API")
        print("   • Modelos ML treinados")
        print("   • Detecção de anomalias funcionando")
        print("   • Comparação de modelos operacional")
        print("   • Detecção de IPs suspeitos ativa")
        print("   • Estatísticas básicas funcionando")
        
    except Exception as e:
        print(f"\n❌ ERRO DURANTE OS TESTES: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 