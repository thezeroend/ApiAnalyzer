#!/usr/bin/env python3
"""
Script para Verificar e Treinar Modelos
=======================================

Este script verifica se os modelos ML estão treinados e os treina
se necessário, evitando retreinamento desnecessário durante detecção.
"""

import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

import requests
import json
from datetime import datetime

# Configuração
API_BASE = "http://localhost:8000"

def check_backend_status():
    """Verifica se o backend está rodando"""
    try:
        response = requests.get(f"{API_BASE}/health")
        if response.status_code == 200:
            print("✅ Backend está rodando")
            return True
        else:
            print("❌ Backend não está respondendo corretamente")
            return False
    except Exception as e:
        print(f"❌ Erro ao conectar com backend: {e}")
        return False

def check_models_status():
    """Verifica se os modelos estão treinados"""
    print("\n🔍 Verificando status dos modelos...")
    
    try:
        # Tentar detectar anomalias para ver se os modelos estão carregados
        response = requests.get(f"{API_BASE}/ml/detect")
        data = response.json()
        
        if "error" in data:
            error_msg = data["error"]
            if "não encontrado" in error_msg or "Treine o modelo primeiro" in error_msg:
                print("❌ Modelos não estão treinados")
                return False
            else:
                print(f"⚠️ Erro ao verificar modelos: {error_msg}")
                return None
        else:
            print("✅ Modelos estão treinados e funcionando")
            return True
            
    except Exception as e:
        print(f"❌ Erro ao verificar modelos: {e}")
        return None

def check_logs_availability():
    """Verifica se há logs disponíveis para treinamento"""
    print("\n📊 Verificando disponibilidade de logs...")
    
    try:
        response = requests.get(f"{API_BASE}/logs")
        data = response.json()
        
        if "logs" in data and len(data["logs"]) > 0:
            print(f"✅ {len(data['logs'])} logs disponíveis")
            return len(data["logs"])
        else:
            print("❌ Nenhum log encontrado")
            return 0
            
    except Exception as e:
        print(f"❌ Erro ao verificar logs: {e}")
        return 0

def train_models():
    """Treina os modelos ML"""
    print("\n🎯 Treinando modelos ML...")
    
    try:
        response = requests.post(f"{API_BASE}/ml/train", json={
            "apiId": None,  # Todas as APIs
            "hours_back": 24
        })
        
        data = response.json()
        
        if response.status_code == 200:
            print("✅ Modelos treinados com sucesso!")
            
            if "models_trained" in data:
                print("   Modelos treinados:")
                for model, status in data["models_trained"].items():
                    print(f"   - {model}: {status}")
            
            if "logs_used" in data:
                print(f"   Logs utilizados: {data['logs_used']}")
            
            return True
        else:
            print(f"❌ Erro ao treinar modelos: {data.get('error', 'Erro desconhecido')}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao treinar modelos: {e}")
        return False

def test_detection():
    """Testa se a detecção está funcionando"""
    print("\n🧪 Testando detecção de anomalias...")
    
    try:
        response = requests.get(f"{API_BASE}/ml/detect")
        data = response.json()
        
        if "error" in data:
            print(f"❌ Erro na detecção: {data['error']}")
            return False
        else:
            anomalies = data.get("anomalies_detected", 0)
            print(f"✅ Detecção funcionando - {anomalies} anomalias detectadas")
            return True
            
    except Exception as e:
        print(f"❌ Erro ao testar detecção: {e}")
        return False

def main():
    """Função principal"""
    print("🚀 VERIFICAÇÃO E PREPARAÇÃO DOS MODELOS ML")
    print("=" * 50)
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 1. Verificar backend
    if not check_backend_status():
        print("\n❌ Backend não está disponível. Inicie o servidor primeiro.")
        return
    
    # 2. Verificar logs
    logs_count = check_logs_availability()
    if logs_count == 0:
        print("\n❌ Nenhum log disponível para treinamento.")
        print("   Adicione alguns logs antes de treinar os modelos.")
        return
    
    # 3. Verificar modelos
    models_status = check_models_status()
    
    if models_status is False:
        # Modelos não estão treinados, treinar
        print(f"\n🔄 Modelos não encontrados. Treinando com {logs_count} logs...")
        
        if train_models():
            # Testar após treinamento
            if test_detection():
                print("\n✅ SISTEMA PRONTO!")
                print("   Os modelos foram treinados e estão funcionando.")
                print("   Agora você pode usar a detecção sem retreinamento.")
            else:
                print("\n⚠️ Modelos treinados mas detecção com problemas.")
        else:
            print("\n❌ Falha no treinamento dos modelos.")
    
    elif models_status is True:
        # Modelos estão treinados, testar
        print("\n✅ Modelos já estão treinados!")
        
        if test_detection():
            print("\n✅ SISTEMA PRONTO!")
            print("   Os modelos estão treinados e funcionando.")
            print("   Você pode usar a detecção sem retreinamento.")
        else:
            print("\n⚠️ Modelos existem mas detecção com problemas.")
    
    else:
        print("\n❌ Não foi possível determinar o status dos modelos.")
    
    print("\n" + "=" * 50)
    print("🏁 VERIFICAÇÃO CONCLUÍDA!")
    print("=" * 50)

if __name__ == "__main__":
    main() 