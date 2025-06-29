#!/usr/bin/env python3
"""
Teste de Consistência entre Endpoints ML
========================================

Este script testa se os endpoints /ml/detect e /ml/compare estão funcionando
de forma consistente, usando os mesmos parâmetros e filtros.
"""

import requests
import json
import time
from datetime import datetime, timedelta

# Configurações
BASE_URL = "http://localhost:8000"
API_ID = "test_api_001"

def test_endpoints_consistency():
    """Testa consistência entre endpoints de detecção ML"""
    
    print("🔍 Testando Consistência entre Endpoints ML")
    print("=" * 50)
    
    # 1. Verificar se o backend está rodando
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code != 200:
            print("❌ Backend não está rodando")
            return False
        print("✅ Backend está rodando")
    except Exception as e:
        print(f"❌ Erro ao conectar com backend: {e}")
        return False
    
    # 2. Configurar threshold baixo para detectar mais anomalias
    print("\n🔧 Configurando threshold baixo para teste...")
    config_data = {
        "threshold": 0.05  # Threshold baixo para detectar mais anomalias
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/config/ml_detection",
            json=config_data
        )
        if response.status_code == 200:
            print("✅ Threshold configurado para 0.05")
        else:
            print(f"⚠️ Erro ao configurar threshold: {response.status_code}")
    except Exception as e:
        print(f"⚠️ Erro ao configurar threshold: {e}")
    
    # 3. Gerar logs de teste se necessário
    print("\n📊 Verificando logs disponíveis...")
    try:
        response = requests.get(f"{BASE_URL}/logs/{API_ID}")
        logs = response.json()
        
        if "logs" not in logs or len(logs["logs"]) < 10:
            print("⚠️ Poucos logs encontrados. Gerando logs de teste...")
            generate_test_logs()
        else:
            print(f"✅ {len(logs['logs'])} logs encontrados")
    except Exception as e:
        print(f"❌ Erro ao verificar logs: {e}")
        return False
    
    # 4. Testar endpoint /ml/detect
    print("\n🎯 Testando endpoint /ml/detect...")
    detect_result = test_detect_endpoint()
    
    # 5. Testar endpoint /ml/compare
    print("\n🔄 Testando endpoint /ml/compare...")
    compare_result = test_compare_endpoint()
    
    # 6. Comparar resultados
    print("\n📈 Comparando Resultados:")
    print("-" * 30)
    
    if detect_result and compare_result:
        print("✅ Ambos endpoints funcionaram")
        
        # Verificar se detectaram anomalias
        detect_anomalies = detect_result.get("anomalies_detected", 0)
        compare_anomalies = 0
        
        # Contar anomalias do modelo iforest no compare
        if "models_comparison" in compare_result:
            iforest_result = compare_result["models_comparison"].get("iforest", {})
            compare_anomalies = iforest_result.get("anomalies_detected", 0)
        
        print(f"📊 /ml/detect detectou: {detect_anomalies} anomalias")
        print(f"📊 /ml/compare (iforest) detectou: {compare_anomalies} anomalias")
        
        if detect_anomalies == compare_anomalies:
            print("✅ Resultados consistentes!")
        else:
            print("⚠️ Resultados inconsistentes - investigar diferenças")
            
        # Mostrar detalhes dos resultados
        print("\n📋 Detalhes /ml/detect:")
        print(f"   - Logs analisados: {detect_result.get('logs_analyzed', 'N/A')}")
        print(f"   - Threshold usado: {detect_result.get('threshold_used', 'N/A')}")
        print(f"   - Falsos positivos filtrados: {detect_result.get('processed_false_positives', 'N/A')}")
        
        print("\n📋 Detalhes /ml/compare:")
        print(f"   - Logs analisados: {compare_result.get('logs_analyzed', 'N/A')}")
        print(f"   - Threshold usado: {compare_result.get('threshold_used', 'N/A')}")
        print(f"   - Falsos positivos filtrados: {compare_result.get('processed_false_positives', 'N/A')}")
        
        # Mostrar comparação de todos os modelos
        if "models_comparison" in compare_result:
            print("\n🔍 Comparação de Todos os Modelos:")
            for model_name, model_result in compare_result["models_comparison"].items():
                if "error" not in model_result:
                    anomalies = model_result.get("anomalies_detected", 0)
                    rate = model_result.get("anomaly_rate", 0)
                    print(f"   - {model_name}: {anomalies} anomalias ({rate:.2%})")
                else:
                    print(f"   - {model_name}: Erro - {model_result['error']}")
        
    else:
        print("❌ Um ou ambos endpoints falharam")
        return False
    
    return True

def test_detect_endpoint():
    """Testa o endpoint /ml/detect"""
    try:
        response = requests.get(f"{BASE_URL}/ml/detect", params={
            "apiId": API_ID,
            "model_name": "iforest",
            "hours_back": 24
        })
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ /ml/detect funcionou - {result.get('anomalies_detected', 0)} anomalias")
            return result
        else:
            print(f"❌ /ml/detect falhou: {response.status_code}")
            print(f"   Resposta: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Erro em /ml/detect: {e}")
        return None

def test_compare_endpoint():
    """Testa o endpoint /ml/compare"""
    try:
        response = requests.get(f"{BASE_URL}/ml/compare", params={
            "apiId": API_ID,
            "hours_back": 24
        })
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ /ml/compare funcionou")
            return result
        else:
            print(f"❌ /ml/compare falhou: {response.status_code}")
            print(f"   Resposta: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Erro em /ml/compare: {e}")
        return None

def generate_test_logs():
    """Gera logs de teste se necessário"""
    print("📝 Gerando logs de teste...")
    
    # Logs normais
    normal_logs = []
    for i in range(50):
        log = {
            "requestId": f"normal_{i:03d}",
            "apiId": API_ID,
            "clientId": "client_001",
            "ip": "10.10.15.10",
            "method": "GET",
            "path": "/api/users",
            "status": 200,
            "responseTime": 150 + (i % 50),
            "timestamp": (datetime.now() - timedelta(minutes=i)).isoformat(),
            "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        normal_logs.append(log)
    
    # Logs anômalos
    anomalous_logs = []
    for i in range(10):
        log = {
            "requestId": f"anomaly_{i:03d}",
            "apiId": API_ID,
            "clientId": "client_001",
            "ip": "172.16.10.100",  # IP diferente
            "method": "POST",
            "path": "/api/admin/delete",
            "status": 403,  # Status de erro
            "responseTime": 5000 + (i * 100),  # Tempo muito alto
            "timestamp": (datetime.now() - timedelta(minutes=i*5)).isoformat(),
            "userAgent": "curl/7.68.0"  # User agent suspeito
        }
        anomalous_logs.append(log)
    
    # Enviar logs
    all_logs = normal_logs + anomalous_logs
    
    try:
        response = requests.post(
            f"{BASE_URL}/logs/bulk",
            json={"logs": all_logs}
        )
        
        if response.status_code == 200:
            print(f"✅ {len(all_logs)} logs de teste enviados")
        else:
            print(f"⚠️ Erro ao enviar logs: {response.status_code}")
            
    except Exception as e:
        print(f"⚠️ Erro ao enviar logs: {e}")

if __name__ == "__main__":
    print("🚀 Iniciando Teste de Consistência entre Endpoints ML")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    success = test_endpoints_consistency()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ Teste de Consistência Concluído com Sucesso!")
    else:
        print("❌ Teste de Consistência Falhou!")
    print("=" * 50) 