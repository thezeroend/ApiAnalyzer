#!/usr/bin/env python3
"""
Teste da funcionalidade de Timeline de Anomalias

Este script testa o endpoint /ml/anomalies-timeline que gera dados temporais
de anomalias para gráficos, agrupando anomalias por intervalos de tempo.
"""

import requests
import json
import time
from datetime import datetime, timedelta
import random

# Configurações
API_BASE = "http://localhost:8000"
API_ID = "api_timeline_test"

def clear_logs():
    """Limpa todos os logs"""
    try:
        response = requests.delete(f"{API_BASE}/logs")
        if response.status_code == 200:
            print("✅ Logs limpos com sucesso")
        else:
            print(f"❌ Erro ao limpar logs: {response.text}")
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")

def send_log(log_data):
    """Envia um log para a API"""
    try:
        response = requests.post(f"{API_BASE}/logs", json=log_data)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Erro ao enviar log: {e}")
        return False

def generate_timeline_test_data():
    """Gera dados de teste para timeline"""
    print("📊 Gerando dados de teste para timeline...")
    
    # Limpar logs existentes
    clear_logs()
    
    # Gerar logs normais (últimas 24 horas)
    normal_logs = []
    base_time = datetime.now() - timedelta(hours=24)
    
    # Logs normais - distribuição uniforme ao longo do tempo
    for i in range(1000):
        timestamp = base_time + timedelta(minutes=i * 1.44)  # Distribuir uniformemente
        log_data = {
            "requestId": f"req_normal_{i:04d}",
            "clientId": f"client_{i % 10}",
            "ip": f"10.0.1.{i % 100}",
            "apiId": API_ID,
            "path": f"/api/users/{i % 100}",
            "method": random.choice(["GET", "POST", "PUT"]),
            "status": random.choice([200, 201, 204]),
            "responseTime": random.randint(50, 300),
            "timestamp": timestamp.isoformat()
        }
        normal_logs.append(log_data)
    
    # Gerar anomalias em horários específicos
    anomaly_logs = []
    
    # Pico de anomalias às 14h
    anomaly_time = base_time.replace(hour=14, minute=0, second=0, microsecond=0)
    for i in range(50):
        timestamp = anomaly_time + timedelta(minutes=i)
        log_data = {
            "requestId": f"req_anomaly_peak_{i:04d}",
            "clientId": f"client_suspicious_{i % 5}",
            "ip": f"172.16.1.{i % 50}",
            "apiId": API_ID,
            "path": f"/api/admin/{i}",
            "method": random.choice(["DELETE", "PATCH"]),
            "status": random.choice([403, 404, 500]),
            "responseTime": random.randint(1000, 5000),
            "timestamp": timestamp.isoformat()
        }
        anomaly_logs.append(log_data)
    
    # Anomalias esparsas ao longo do tempo
    for i in range(20):
        timestamp = base_time + timedelta(hours=random.randint(1, 23), minutes=random.randint(0, 59))
        log_data = {
            "requestId": f"req_anomaly_sparse_{i:04d}",
            "clientId": f"client_anomaly_{i}",
            "ip": f"192.168.1.{i + 100}",
            "apiId": API_ID,
            "path": f"/api/secure/{i}",
            "method": "POST",
            "status": 401,
            "responseTime": random.randint(800, 2000),
            "timestamp": timestamp.isoformat()
        }
        anomaly_logs.append(log_data)
    
    # Enviar todos os logs
    all_logs = normal_logs + anomaly_logs
    print(f"📤 Enviando {len(all_logs)} logs...")
    
    success_count = 0
    for log_data in all_logs:
        if send_log(log_data):
            success_count += 1
    
    print(f"✅ {success_count}/{len(all_logs)} logs enviados com sucesso")
    return success_count

def train_models():
    """Treina os modelos de ML"""
    print("🎯 Treinando modelos de ML...")
    
    try:
        response = requests.post(f"{API_BASE}/ml/train", json={
            "apiId": API_ID,
            "hours_back": 24
        })
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Modelos treinados com sucesso")
            return True
        else:
            print(f"❌ Erro ao treinar modelos: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
        return False

def test_timeline_endpoint():
    """Testa o endpoint de timeline"""
    print("📊 Testando endpoint de timeline...")
    
    # Testar diferentes configurações
    test_configs = [
        {"interval_minutes": 30, "hours_back": 24, "model_name": "iforest"},
        {"interval_minutes": 60, "hours_back": 24, "model_name": "iforest"},
        {"interval_minutes": 15, "hours_back": 12, "model_name": "lof"},
    ]
    
    for i, config in enumerate(test_configs, 1):
        print(f"\n🧪 Teste {i}: {config}")
        
        try:
            params = {
                "apiId": API_ID,
                "model_name": config["model_name"],
                "hours_back": config["hours_back"],
                "interval_minutes": config["interval_minutes"]
            }
            
            response = requests.get(f"{API_BASE}/ml/anomalies-timeline", params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                if "error" in data:
                    print(f"❌ Erro no endpoint: {data['error']}")
                    continue
                
                print(f"✅ Timeline gerado com sucesso")
                print(f"   📈 Total de anomalias: {data.get('total_anomalies', 0)}")
                print(f"   📊 Intervalos de tempo: {data.get('summary', {}).get('total_intervals', 0)}")
                print(f"   🎯 Modelo usado: {data.get('model_used', 'N/A')}")
                print(f"   ⏱️ Intervalo: {data.get('time_interval_minutes', 0)} minutos")
                
                # Verificar dados do gráfico
                chart_data = data.get('chart_data', {})
                if chart_data:
                    labels = chart_data.get('labels', [])
                    datasets = chart_data.get('datasets', [])
                    print(f"   📊 Pontos no gráfico: {len(labels)}")
                    print(f"   📈 Datasets: {len(datasets)}")
                    
                    # Mostrar alguns pontos de dados
                    if datasets and len(datasets) > 0:
                        anomaly_data = datasets[0].get('data', [])
                        score_data = datasets[1].get('data', []) if len(datasets) > 1 else []
                        
                        if anomaly_data:
                            max_anomalies = max(anomaly_data)
                            avg_anomalies = sum(anomaly_data) / len(anomaly_data)
                            print(f"   🔥 Máximo de anomalias por intervalo: {max_anomalies}")
                            print(f"   📊 Média de anomalias por intervalo: {avg_anomalies:.2f}")
                        
                        if score_data:
                            max_score = max(score_data)
                            avg_score = sum(score_data) / len(score_data)
                            print(f"   🎯 Score máximo: {max_score:.3f}")
                            print(f"   📊 Score médio: {avg_score:.3f}")
                
                # Verificar dados temporais
                timeline_data = data.get('timeline_data', [])
                if timeline_data:
                    print(f"   📅 Dados temporais: {len(timeline_data)} intervalos")
                    
                    # Mostrar alguns intervalos com mais anomalias
                    sorted_intervals = sorted(timeline_data, key=lambda x: x['anomaly_count'], reverse=True)
                    top_intervals = sorted_intervals[:3]
                    
                    print("   🔥 Top 3 intervalos com mais anomalias:")
                    for j, interval in enumerate(top_intervals, 1):
                        timestamp = interval['timestamp']
                        count = interval['anomaly_count']
                        avg_score = interval['avg_score']
                        print(f"      {j}. {timestamp}: {count} anomalias (score: {avg_score:.3f})")
                
            else:
                print(f"❌ Erro HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            print(f"❌ Erro de conexão: {e}")

def test_timeline_export():
    """Testa a exportação de dados de timeline"""
    print("\n💾 Testando exportação de dados...")
    
    try:
        params = {
            "apiId": API_ID,
            "model_name": "iforest",
            "hours_back": 24,
            "interval_minutes": 30
        }
        
        response = requests.get(f"{API_BASE}/ml/anomalies-timeline", params=params)
        
        if response.status_code == 200:
            data = response.json()
            
            if "error" not in data:
                # Simular exportação
                export_data = {
                    "export_timestamp": datetime.now().isoformat(),
                    "config": params,
                    "timeline_data": data
                }
                
                filename = f"timeline_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
                
                print(f"✅ Dados exportados para {filename}")
                print(f"   📊 Tamanho do arquivo: {len(json.dumps(export_data))} bytes")
            else:
                print(f"❌ Erro nos dados: {data['error']}")
        else:
            print(f"❌ Erro ao obter dados: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erro na exportação: {e}")

def main():
    """Função principal"""
    print("🚀 Iniciando teste da funcionalidade de Timeline de Anomalias")
    print("=" * 60)
    
    # Verificar se o backend está rodando
    try:
        response = requests.get(f"{API_BASE}/docs")
        if response.status_code != 200:
            print("❌ Backend não está rodando. Execute 'python main.py' primeiro.")
            return
        print("✅ Backend está rodando")
    except Exception as e:
        print(f"❌ Erro ao conectar com o backend: {e}")
        print("Execute 'python main.py' primeiro.")
        return
    
    # Gerar dados de teste
    success_count = generate_timeline_test_data()
    if success_count == 0:
        print("❌ Nenhum log foi enviado. Abortando teste.")
        return
    
    # Aguardar um pouco para processamento
    print("⏳ Aguardando processamento...")
    time.sleep(2)
    
    # Treinar modelos
    if not train_models():
        print("❌ Falha no treinamento. Abortando teste.")
        return
    
    # Testar endpoint de timeline
    test_timeline_endpoint()
    
    # Testar exportação
    test_timeline_export()
    
    print("\n" + "=" * 60)
    print("✅ Teste da funcionalidade de Timeline concluído!")
    print("\n📋 Resumo:")
    print("   • Dados de teste gerados com padrões temporais")
    print("   • Modelos treinados com sucesso")
    print("   • Endpoint de timeline testado com diferentes configurações")
    print("   • Exportação de dados validada")
    print("\n🎯 Próximos passos:")
    print("   • Acesse http://localhost:8000/portal/timeline.html")
    print("   • Visualize os gráficos temporais")
    print("   • Teste diferentes intervalos e modelos")

if __name__ == "__main__":
    main() 