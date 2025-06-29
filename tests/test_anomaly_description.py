#!/usr/bin/env python3
"""
Teste para verificar se as descrições de anomalias estão sendo geradas corretamente
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
TEST_API_ID = "test_anomaly_description"

def generate_test_logs():
    """Gera logs de teste com padrões normais e anômalos"""
    logs = []
    
    # Logs normais (horário comercial, status 200, métodos GET/POST)
    for i in range(50):
        logs.append({
            "requestId": f"normal_{i}",
            "clientId": f"client_{i % 5}",
            "ip": f"192.168.1.{i % 10}",
            "apiId": TEST_API_ID,
            "method": random.choice(["GET", "POST"]),
            "path": f"/api/users/{i}",
            "status": 200,
            "timestamp": (datetime.now() - timedelta(hours=random.randint(1, 24))).isoformat()
        })
    
    # Logs anômalos - horário atípico
    for i in range(5):
        logs.append({
            "requestId": f"anomaly_hour_{i}",
            "clientId": f"client_{i}",
            "ip": f"192.168.1.{i}",
            "apiId": TEST_API_ID,
            "method": "GET",
            "path": f"/api/users/{i}",
            "status": 200,
            "timestamp": (datetime.now().replace(hour=random.choice([2, 3, 4, 23]))).isoformat()
        })
    
    # Logs anômalos - erros do servidor
    for i in range(5):
        logs.append({
            "requestId": f"anomaly_error_{i}",
            "clientId": f"client_{i}",
            "ip": f"192.168.1.{i}",
            "apiId": TEST_API_ID,
            "method": "POST",
            "path": f"/api/users/{i}",
            "status": random.choice([500, 502, 503]),
            "timestamp": (datetime.now() - timedelta(hours=random.randint(1, 24))).isoformat()
        })
    
    # Logs anômalos - acesso administrativo
    for i in range(3):
        logs.append({
            "requestId": f"anomaly_admin_{i}",
            "clientId": f"client_{i}",
            "ip": f"192.168.1.{i}",
            "apiId": TEST_API_ID,
            "method": "DELETE",
            "path": f"/admin/users/{i}",
            "status": 200,
            "timestamp": (datetime.now() - timedelta(hours=random.randint(1, 24))).isoformat()
        })
    
    # Logs anômalos - path muito longo
    for i in range(3):
        logs.append({
            "requestId": f"anomaly_long_path_{i}",
            "clientId": f"client_{i}",
            "ip": f"192.168.1.{i}",
            "apiId": TEST_API_ID,
            "method": "GET",
            "path": f"/api/very/long/path/with/many/levels/and/parameters/that/makes/it/very/long/indeed/{i}",
            "status": 200,
            "timestamp": (datetime.now() - timedelta(hours=random.randint(1, 24))).isoformat()
        })
    
    return logs

def test_anomaly_descriptions():
    """Testa a funcionalidade de descrições de anomalias"""
    print("🧪 Testando descrições de anomalias...")
    
    try:
        # 1. Limpar logs existentes
        print("📝 Limpando logs existentes...")
        response = requests.delete(f"{API_BASE}/logs")
        if response.status_code != 200:
            print(f"❌ Erro ao limpar logs: {response.text}")
            return False
        
        # 2. Enviar logs de teste
        print("📤 Enviando logs de teste...")
        test_logs = generate_test_logs()
        
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
        
        # 5. Verificar descrições
        print("\n📋 Verificando descrições das anomalias:")
        descriptions_found = 0
        
        for i, anomaly in enumerate(anomalies[:10]):  # Mostrar apenas as primeiras 10
            description = anomaly.get("anomaly_description", "")
            score = anomaly.get("anomaly_score", 0)
            request_id = anomaly.get("requestId", "")
            status = anomaly.get("status", "")
            method = anomaly.get("method", "")
            path = anomaly.get("path", "")
            
            print(f"\n🔍 Anomalia {i+1}:")
            print(f"   Request ID: {request_id}")
            print(f"   Score: {score:.3f}")
            print(f"   Método: {method}")
            print(f"   Status: {status}")
            print(f"   Path: {path[:50]}{'...' if len(path) > 50 else ''}")
            
            if description:
                print(f"   📝 Descrição: {description}")
                descriptions_found += 1
            else:
                print(f"   ❌ Sem descrição")
        
        # 6. Estatísticas
        print(f"\n📊 Estatísticas:")
        print(f"   Total de anomalias: {len(anomalies)}")
        print(f"   Anomalias com descrição: {descriptions_found}")
        print(f"   Taxa de cobertura: {(descriptions_found/len(anomalies)*100):.1f}%" if anomalies else "0%")
        
        if descriptions_found > 0:
            print("\n✅ Teste concluído com sucesso! Descrições de anomalias estão funcionando.")
            return True
        else:
            print("\n❌ Nenhuma descrição de anomalia foi gerada.")
            return False
            
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando testes de descrição de anomalias...")
    
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
    success = test_anomaly_descriptions()
    
    if success:
        print("\n🎉 Teste passou! Descrições de anomalias estão funcionando corretamente.")
    else:
        print("\n❌ Teste falhou. Verifique os logs acima.")
        sys.exit(1) 