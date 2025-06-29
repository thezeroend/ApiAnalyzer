#!/usr/bin/env python3
"""
Teste de Threshold e Timeline

Este script testa se:
1. A timeline respeita o threshold configurado
2. Erros de servidor (5xx) não são considerados anomalias
3. A consistência entre detector e timeline
"""

import requests
import json
import time
from datetime import datetime, timedelta
import random

# Configurações
API_BASE = "http://localhost:8000"
API_ID = "api_threshold_test"

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

def set_threshold(threshold):
    """Define o threshold nas configurações"""
    try:
        response = requests.post(f"{API_BASE}/config/update", json={
            "section": "ml_detection",
            "key": "threshold",
            "value": threshold
        })
        
        if response.status_code == 200:
            print(f"✅ Threshold definido para {threshold}")
            return True
        else:
            print(f"❌ Erro ao definir threshold: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
        return False

def get_current_threshold():
    """Obtém o threshold atual das configurações"""
    try:
        response = requests.get(f"{API_BASE}/config?section=ml_detection")
        
        if response.status_code == 200:
            data = response.json()
            threshold = data.get('config', {}).get('threshold', 0.12)
            print(f"📊 Threshold atual: {threshold}")
            return threshold
        else:
            print(f"❌ Erro ao obter threshold: {response.text}")
            return 0.12
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
        return 0.12

def generate_test_data():
    """Gera dados de teste com diferentes tipos de logs"""
    print("📊 Gerando dados de teste...")
    
    # Limpar logs existentes
    clear_logs()
    
    base_time = datetime.now() - timedelta(hours=24)
    success_count = 0
    
    # Cenário 1: Logs normais (200)
    print("🔍 Cenário 1: Logs normais (200)")
    for i in range(100):
        timestamp = base_time + timedelta(minutes=i * 2)
        log_data = {
            "requestId": f"req_normal_{i:04d}",
            "clientId": f"client_{i % 10}",
            "ip": f"10.0.1.{i % 100}",
            "apiId": API_ID,
            "path": f"/api/users/{i}",
            "method": "GET",
            "status": 200,
            "responseTime": random.randint(50, 200),
            "timestamp": timestamp.isoformat()
        }
        if send_log(log_data):
            success_count += 1
    
    # Cenário 2: Erros de cliente (4xx) - podem ser anomalias
    print("🔍 Cenário 2: Erros de cliente (4xx)")
    for i in range(20):
        timestamp = base_time + timedelta(minutes=i * 3)
        log_data = {
            "requestId": f"req_client_error_{i:04d}",
            "clientId": f"client_error_{i % 5}",
            "ip": f"192.168.1.{i % 50}",
            "apiId": API_ID,
            "path": f"/api/admin/{i}",
            "method": "POST",
            "status": random.choice([400, 401, 403, 404]),
            "responseTime": random.randint(100, 500),
            "timestamp": timestamp.isoformat()
        }
        if send_log(log_data):
            success_count += 1
    
    # Cenário 3: Erros de servidor (5xx) - NÃO devem ser anomalias
    print("🔍 Cenário 3: Erros de servidor (5xx)")
    for i in range(30):
        timestamp = base_time + timedelta(minutes=i * 2.5)
        log_data = {
            "requestId": f"req_server_error_{i:04d}",
            "clientId": f"client_server_{i % 8}",
            "ip": f"203.0.113.{i % 100}",
            "apiId": API_ID,
            "path": f"/api/data/{i}",
            "method": "GET",
            "status": random.choice([500, 502, 503, 504]),
            "responseTime": random.randint(1000, 3000),
            "timestamp": timestamp.isoformat()
        }
        if send_log(log_data):
            success_count += 1
    
    # Cenário 4: Comportamento anômalo real (horário atípico + path admin)
    print("🔍 Cenário 4: Comportamento anômalo real")
    for i in range(15):
        timestamp = base_time.replace(hour=3, minute=i * 4)  # 3h da manhã
        log_data = {
            "requestId": f"req_anomaly_{i:04d}",
            "clientId": f"client_anomaly_{i}",
            "ip": f"172.16.{i % 50}.{i % 100}",
            "apiId": API_ID,
            "path": f"/api/admin/delete/{i}",
            "method": "DELETE",
            "status": 200,
            "responseTime": random.randint(50, 150),
            "timestamp": timestamp.isoformat()
        }
        if send_log(log_data):
            success_count += 1
    
    print(f"✅ {success_count} logs enviados com sucesso")
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

def test_detector_vs_timeline():
    """Testa a consistência entre detector e timeline"""
    print("🔍 Testando consistência entre detector e timeline...")
    
    # Obter threshold atual
    current_threshold = get_current_threshold()
    
    # Testar detector
    print("\n📊 Testando detector...")
    try:
        params = {
            "apiId": API_ID,
            "model_name": "iforest",
            "hours_back": 24
        }
        
        response = requests.get(f"{API_BASE}/ml/detect", params=params)
        
        if response.status_code == 200:
            detector_data = response.json()
            
            if "error" in detector_data:
                print(f"❌ Erro na detecção: {detector_data['error']}")
                return
            
            detector_anomalies = detector_data.get('anomalies', [])
            detector_threshold = detector_data.get('threshold_used', current_threshold)
            
            print(f"✅ Detector: {len(detector_anomalies)} anomalias detectadas")
            print(f"   📊 Threshold usado: {detector_threshold}")
            
            # Verificar se erros de servidor foram detectados como anomalias
            server_error_anomalies = [a for a in detector_anomalies if a.get('status', 200) >= 500]
            print(f"   ⚠️ Anomalias com erro de servidor: {len(server_error_anomalies)}")
            
            if server_error_anomalies:
                print("   ❌ PROBLEMA: Erros de servidor foram detectados como anomalias!")
                for anomaly in server_error_anomalies[:3]:
                    print(f"      - {anomaly.get('requestId')}: {anomaly.get('status')} (Score: {anomaly.get('anomaly_score', 0):.3f})")
            else:
                print("   ✅ OK: Nenhum erro de servidor detectado como anomalia")
            
        else:
            print(f"❌ Erro HTTP {response.status_code}: {response.text}")
            return
            
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
        return
    
    # Testar timeline
    print("\n📊 Testando timeline...")
    try:
        params = {
            "apiId": API_ID,
            "model_name": "iforest",
            "hours_back": 24,
            "interval_minutes": 30
        }
        
        response = requests.get(f"{API_BASE}/ml/anomalies-timeline", params=params)
        
        if response.status_code == 200:
            timeline_data = response.json()
            
            if "error" in timeline_data:
                print(f"❌ Erro na timeline: {timeline_data['error']}")
                return
            
            timeline_anomalies = timeline_data.get('total_anomalies', 0)
            timeline_threshold = timeline_data.get('threshold_used', current_threshold)
            
            print(f"✅ Timeline: {timeline_anomalies} anomalias detectadas")
            print(f"   📊 Threshold usado: {timeline_threshold}")
            
            # Verificar consistência
            if abs(len(detector_anomalies) - timeline_anomalies) <= 2:  # Permitir pequena diferença
                print("   ✅ OK: Timeline e detector são consistentes")
            else:
                print(f"   ❌ PROBLEMA: Inconsistência entre detector ({len(detector_anomalies)}) e timeline ({timeline_anomalies})")
            
            # Verificar se os thresholds são iguais
            if abs(detector_threshold - timeline_threshold) < 0.001:
                print("   ✅ OK: Thresholds são consistentes")
            else:
                print(f"   ❌ PROBLEMA: Thresholds diferentes - Detector: {detector_threshold}, Timeline: {timeline_threshold}")
            
        else:
            print(f"❌ Erro HTTP {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")

def test_different_thresholds():
    """Testa diferentes thresholds"""
    print("\n🧪 Testando diferentes thresholds...")
    
    thresholds_to_test = [0.05, 0.12, 0.20, 0.30]
    
    for threshold in thresholds_to_test:
        print(f"\n📊 Testando threshold: {threshold}")
        
        # Definir threshold
        if not set_threshold(threshold):
            continue
        
        # Aguardar um pouco
        time.sleep(1)
        
        # Testar detector
        try:
            params = {
                "apiId": API_ID,
                "model_name": "iforest",
                "hours_back": 24
            }
            
            response = requests.get(f"{API_BASE}/ml/detect", params=params)
            
            if response.status_code == 200:
                detector_data = response.json()
                detector_anomalies = len(detector_data.get('anomalies', []))
                print(f"   🔍 Detector: {detector_anomalies} anomalias")
                
                # Verificar se erros de servidor foram detectados
                server_errors = [a for a in detector_data.get('anomalies', []) if a.get('status', 200) >= 500]
                print(f"   ⚠️ Erros de servidor como anomalias: {len(server_errors)}")
                
            else:
                print(f"   ❌ Erro no detector: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Erro: {e}")
        
        # Testar timeline
        try:
            params = {
                "apiId": API_ID,
                "model_name": "iforest",
                "hours_back": 24,
                "interval_minutes": 30
            }
            
            response = requests.get(f"{API_BASE}/ml/anomalies-timeline", params=params)
            
            if response.status_code == 200:
                timeline_data = response.json()
                timeline_anomalies = timeline_data.get('total_anomalies', 0)
                print(f"   📊 Timeline: {timeline_anomalies} anomalias")
                
                # Verificar consistência
                if abs(detector_anomalies - timeline_anomalies) <= 2:
                    print(f"   ✅ Consistente")
                else:
                    print(f"   ❌ Inconsistente")
                
            else:
                print(f"   ❌ Erro na timeline: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Erro: {e}")

def main():
    """Função principal"""
    print("🚀 Iniciando teste de Threshold e Timeline")
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
    success_count = generate_test_data()
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
    
    # Testar consistência
    test_detector_vs_timeline()
    
    # Testar diferentes thresholds
    test_different_thresholds()
    
    print("\n" + "=" * 60)
    print("✅ Teste de Threshold e Timeline concluído!")
    print("\n📋 Resumo:")
    print("   • Dados de teste gerados com diferentes tipos de logs")
    print("   • Consistência entre detector e timeline verificada")
    print("   • Diferentes thresholds testados")
    print("   • Erros de servidor não devem ser anomalias")
    print("\n🎯 Resultados esperados:")
    print("   • Timeline e detector devem mostrar números similares")
    print("   • Thresholds devem ser consistentes")
    print("   • Erros 5xx não devem aparecer como anomalias")
    print("   • Threshold mais baixo = mais anomalias")
    print("   • Threshold mais alto = menos anomalias")

if __name__ == "__main__":
    main() 