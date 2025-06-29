#!/usr/bin/env python3
"""
Script para testar o sistema de configurações
"""

import sys
import os
# Adicionar o diretório pai ao path de forma mais robusta
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

import requests
import json
from datetime import datetime

# Configuração
API_BASE = "http://localhost:8000"

def test_get_config():
    """Testa obter configurações"""
    print("🔧 Testando obtenção de configurações...")
    
    try:
        response = requests.get(f"{API_BASE}/config")
        if response.status_code == 200:
            data = response.json()
            print("✅ Configurações obtidas com sucesso!")
            print(f"   - Status: {data.get('status')}")
            print(f"   - Configurações: {json.dumps(data.get('config', {}), indent=2)}")
            return data.get('config', {})
        else:
            print(f"❌ Erro ao obter configurações: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
        return None

def test_update_threshold():
    """Testa atualizar threshold de detecção"""
    print("\n🎯 Testando atualização de threshold...")
    
    try:
        # Testar diferentes valores de threshold
        test_values = [0.08, 0.15, 0.20]
        
        for threshold in test_values:
            print(f"   📝 Testando threshold: {threshold}")
            
            response = requests.post(f"{API_BASE}/config/update", json={
                "section": "ml_detection",
                "key": "threshold",
                "value": threshold
            })
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Threshold {threshold} atualizado: {data.get('message')}")
            else:
                print(f"   ❌ Erro ao atualizar threshold {threshold}: {response.status_code}")
        
        return True
    except Exception as e:
        print(f"❌ Erro na atualização: {e}")
        return False

def test_update_section():
    """Testa atualizar seção inteira"""
    print("\n📋 Testando atualização de seção...")
    
    try:
        new_ml_config = {
            "threshold": 0.18,
            "contamination": 0.08,
            "model_preference": "lof"
        }
        
        response = requests.post(f"{API_BASE}/config/section", json={
            "section": "ml_detection",
            "config": new_ml_config
        })
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Seção ML atualizada com sucesso!")
            print(f"   - Mensagem: {data.get('message')}")
            print(f"   - Configuração: {json.dumps(data.get('updated_config', {}), indent=2)}")
            return True
        else:
            print(f"❌ Erro ao atualizar seção: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro na atualização de seção: {e}")
        return False

def test_reset_section():
    """Testa resetar seção"""
    print("\n🔄 Testando reset de seção...")
    
    try:
        response = requests.post(f"{API_BASE}/config/reset", json={
            "section": "ml_detection"
        })
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Seção ML resetada com sucesso!")
            print(f"   - Mensagem: {data.get('message')}")
            return True
        else:
            print(f"❌ Erro ao resetar seção: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro no reset de seção: {e}")
        return False

def test_detection_with_config():
    """Testa detecção usando configurações salvas"""
    print("\n🔍 Testando detecção com configurações...")
    
    try:
        # Primeiro, definir um threshold específico
        threshold = 0.14
        requests.post(f"{API_BASE}/config/update", json={
            "section": "ml_detection",
            "key": "threshold",
            "value": threshold
        })
        
        # Agora testar detecção sem passar threshold (deve usar o das configurações)
        response = requests.get(f"{API_BASE}/ml/detect?apiId=test_config")
        
        if response.status_code == 200:
            data = response.json()
            if "error" not in data:
                print("✅ Detecção com configurações funcionando!")
                print(f"   - Threshold usado: {data.get('threshold_used', 'N/A')}")
                print(f"   - Anomalias detectadas: {data.get('anomalies_detected', 0)}")
                return True
            else:
                print(f"⚠️ Detecção retornou erro: {data.get('error')}")
                return False
        else:
            print(f"❌ Erro na detecção: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro no teste de detecção: {e}")
        return False

def main():
    """Função principal"""
    print("🚀 TESTE DO SISTEMA DE CONFIGURAÇÕES")
    print("=" * 50)
    
    try:
        # 1. Testar obtenção de configurações
        config = test_get_config()
        if not config:
            print("❌ Falha ao obter configurações iniciais")
            return
        
        # 2. Testar atualização de threshold
        if not test_update_threshold():
            print("❌ Falha na atualização de threshold")
            return
        
        # 3. Testar atualização de seção
        if not test_update_section():
            print("❌ Falha na atualização de seção")
            return
        
        # 4. Testar reset de seção
        if not test_reset_section():
            print("❌ Falha no reset de seção")
            return
        
        # 5. Testar detecção com configurações
        if not test_detection_with_config():
            print("❌ Falha na detecção com configurações")
            return
        
        print("\n" + "=" * 50)
        print("🏁 TESTE CONCLUÍDO COM SUCESSO!")
        print("=" * 50)
        print("\n📊 RESUMO:")
        print("   - ✅ Obtenção de configurações")
        print("   - ✅ Atualização de threshold")
        print("   - ✅ Atualização de seção")
        print("   - ✅ Reset de seção")
        print("   - ✅ Detecção com configurações")
        print("\n🎉 Sistema de configurações funcionando perfeitamente!")
        
    except Exception as e:
        print(f"\n❌ ERRO GERAL: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 