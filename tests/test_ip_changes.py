#!/usr/bin/env python3
"""
Teste específico para verificar a detecção de mudanças de IP nas descrições de anomalias
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import json
from datetime import datetime, timedelta
import random

# Configurações
API_BASE = "http://localhost:8000"
TEST_API_ID = "test_ip_changes"

def generate_ip_change_test_logs():
    """Gera logs de teste com mudanças de IP suspeitas"""
    logs = []
    
    # Cliente 1: Mudança de IP privado para público (suspeito)
    client1_base_time = datetime.now() - timedelta(hours=6)
    
    # Logs normais com IP privado
    for i in range(10):
        logs.append({
            "requestId": f"client1_normal_{i}",
            "clientId": "client_001",
            "ip": "192.168.1.100",
            "apiId": TEST_API_ID,
            "method": "GET",
            "path": f"/api/users/{i}",
            "status": 200,
            "timestamp": (client1_base_time + timedelta(minutes=i*30)).isoformat()
        })
    
    # Log anômalo com IP público (mudança suspeita)
    logs.append({
        "requestId": "client1_suspicious_ip",
        "clientId": "client_001",
        "ip": "203.45.67.89",  # IP público
        "apiId": TEST_API_ID,
        "method": "POST",
        "path": "/api/admin/users",
        "status": 200,
        "timestamp": (client1_base_time + timedelta(hours=3)).isoformat()
    })
    
    # Cliente 2: Múltiplos IPs em pouco tempo
    client2_base_time = datetime.now() - timedelta(hours=2)
    
    # Logs com IPs diferentes em sequência rápida
    ips = ["10.0.1.50", "172.16.0.100", "192.168.0.200", "8.8.8.8"]
    for i, ip in enumerate(ips):
        logs.append({
            "requestId": f"client2_multi_ip_{i}",
            "clientId": "client_002",
            "ip": ip,
            "apiId": TEST_API_ID,
            "method": "GET",
            "path": f"/api/data/{i}",
            "status": 200,
            "timestamp": (client2_base_time + timedelta(minutes=i*15)).isoformat()
        })
    
    # Cliente 3: Novo IP nunca visto antes
    client3_base_time = datetime.now() - timedelta(hours=4)
    
    # Logs normais
    for i in range(5):
        logs.append({
            "requestId": f"client3_normal_{i}",
            "clientId": "client_003",
            "ip": "10.10.10.50",
            "apiId": TEST_API_ID,
            "method": "GET",
            "path": f"/api/products/{i}",
            "status": 200,
            "timestamp": (client3_base_time + timedelta(minutes=i*60)).isoformat()
        })
    
    # Log com IP completamente novo
    logs.append({
        "requestId": "client3_new_ip",
        "clientId": "client_003",
        "ip": "45.67.89.123",  # IP completamente novo
        "apiId": TEST_API_ID,
        "method": "DELETE",
        "path": "/api/admin/products/999",
        "status": 200,
        "timestamp": datetime.now().isoformat()
    })
    
    # Cliente 4: Logs normais (controle)
    for i in range(15):
        logs.append({
            "requestId": f"client4_normal_{i}",
            "clientId": "client_004",
            "ip": "192.168.1.200",
            "apiId": TEST_API_ID,
            "method": random.choice(["GET", "POST"]),
            "path": f"/api/orders/{i}",
            "status": 200,
            "timestamp": (datetime.now() - timedelta(minutes=i*30)).isoformat()
        })
    
    return logs

def test_ip_change_detection():
    """Testa a detecção de mudanças de IP nas descrições de anomalias"""
    print("🧪 Testando detecção de mudanças de IP...")
    
    try:
        # 1. Limpar logs existentes
        print("📝 Limpando logs existentes...")
        response = requests.delete(f"{API_BASE}/logs")
        if response.status_code != 200:
            print(f"❌ Erro ao limpar logs: {response.text}")
            return False
        
        # 2. Enviar logs de teste com mudanças de IP
        print("📤 Enviando logs de teste com mudanças de IP...")
        test_logs = generate_ip_change_test_logs()
        
        for log in test_logs:
            response = requests.post(f"{API_BASE}/logs", json=log)
            if response.status_code != 200:
                print(f"❌ Erro ao enviar log: {response.text}")
                return False
        
        print(f"✅ {len(test_logs)} logs enviados")
        
        # 3. Treinar modelos
        print("🎯 Treinando modelos...")
        response = requests.post(f"{API_BASE}/ml/train", json={
            "apiId": TEST_API_ID,
            "hours_back": 24
        })
        
        if response.status_code != 200:
            print(f"❌ Erro ao treinar modelos: {response.text}")
            return False
        
        print("✅ Modelos treinados")
        
        # 4. Detectar anomalias
        print("🔍 Detectando anomalias...")
        response = requests.get(f"{API_BASE}/ml/detect", params={
            "apiId": TEST_API_ID,
            "model_name": "iforest",
            "hours_back": 24
        })
        
        if response.status_code != 200:
            print(f"❌ Erro ao detectar anomalias: {response.text}")
            return False
        
        data = response.json()
        anomalies = data.get("anomalies", [])
        
        print(f"✅ {len(anomalies)} anomalias detectadas")
        
        # 5. Verificar descrições com mudanças de IP
        print("\n📋 Verificando descrições com mudanças de IP:")
        ip_changes_found = 0
        
        for i, anomaly in enumerate(anomalies):
            description = anomaly.get("anomaly_description", "")
            request_id = anomaly.get("requestId", "")
            client_id = anomaly.get("clientId", "")
            ip = anomaly.get("ip", "")
            
            print(f"\n🔍 Anomalia {i+1}:")
            print(f"   Request ID: {request_id}")
            print(f"   Client ID: {client_id}")
            print(f"   IP: {ip}")
            print(f"   Score: {anomaly.get('anomaly_score', 0):.3f}")
            
            # Verificar se a descrição contém informações sobre mudanças de IP
            if "Mudanças de endereços de IP suspeitas:" in description:
                print(f"   ✅ Mudanças de endereços de IP detectadas!")
                print(f"   📝 Descrição: {description}")
                ip_changes_found += 1
            elif "IP" in description.upper():
                print(f"   ⚠️  Possível referência a IP na descrição")
                print(f"   📝 Descrição: {description}")
            else:
                print(f"   📝 Descrição: {description}")
        
        # 6. Estatísticas específicas de IP
        print(f"\n📊 Estatísticas de mudanças de endereços de IP:")
        print(f"   Total de anomalias: {len(anomalies)}")
        print(f"   Anomalias com mudanças de endereços de IP detectadas: {ip_changes_found}")
        print(f"   Taxa de detecção de mudanças de endereços de IP: {(ip_changes_found/len(anomalies)*100):.1f}%" if anomalies else "0%")
        
        if ip_changes_found > 0:
            print("\n✅ Teste concluído com sucesso! Detecção de mudanças de endereços de IP está funcionando.")
            return True
        else:
            print("\n❌ Nenhuma mudança de endereço de IP foi detectada nas descrições.")
            return False
            
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando testes de detecção de mudanças de IP...")
    
    # Verificar se o backend está rodando
    try:
        response = requests.get(f"{API_BASE}/")
        if response.status_code != 200:
            print("❌ Backend não está rodando. Inicie o servidor primeiro.")
            sys.exit(1)
    except:
        print("❌ Não foi possível conectar ao backend. Verifique se está rodando em http://localhost:8000")
        sys.exit(1)
    
    # Executar testes
    success = test_ip_change_detection()
    
    if success:
        print("\n🎉 Teste passou! Detecção de mudanças de IP está funcionando corretamente.")
    else:
        print("\n❌ Teste falhou. Verifique os logs acima.")
        sys.exit(1) 