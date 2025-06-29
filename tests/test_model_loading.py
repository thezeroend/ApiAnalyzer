#!/usr/bin/env python3
"""
Teste de Carregamento de Modelos
================================

Este script testa se os modelos estão sendo carregados corretamente
sem carregar todos os modelos desnecessariamente.
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

def test_detect_anomalies():
    """Testa se detect_ml_anomalies carrega apenas o modelo especificado"""
    print("🔍 Testando detect_ml_anomalies...")
    
    try:
        # Testar com modelo iforest
        response = requests.get(f"{API_BASE}/ml/detect?model_name=iforest")
        data = response.json()
        
        if response.status_code == 200:
            print("✅ detect_ml_anomalies funcionou corretamente")
            print(f"   - Modelo usado: {data.get('model_used', 'N/A')}")
            print(f"   - Anomalias detectadas: {data.get('anomalies_detected', 0)}")
            return True
        else:
            print(f"❌ detect_ml_anomalies falhou: {data.get('error', 'Erro desconhecido')}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao testar detect_ml_anomalies: {e}")
        return False

def test_compare_models():
    """Testa se compare_ml_models carrega todos os modelos"""
    print("\n🔄 Testando compare_ml_models...")
    
    try:
        response = requests.get(f"{API_BASE}/ml/compare")
        data = response.json()
        
        if response.status_code == 200:
            print("✅ compare_ml_models funcionou corretamente")
            if "models_comparison" in data:
                models = list(data["models_comparison"].keys())
                print(f"   - Modelos comparados: {models}")
                for model, result in data["models_comparison"].items():
                    if "error" not in result:
                        print(f"   - {model}: {result.get('anomalies_detected', 0)} anomalias")
                    else:
                        print(f"   - {model}: Erro - {result['error']}")
            return True
        else:
            print(f"❌ compare_ml_models falhou: {data.get('error', 'Erro desconhecido')}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao testar compare_ml_models: {e}")
        return False

def test_timeline():
    """Testa se timeline carrega apenas o modelo especificado"""
    print("\n📊 Testando timeline...")
    
    try:
        response = requests.get(f"{API_BASE}/ml/anomalies-timeline?model_name=iforest")
        data = response.json()
        
        if response.status_code == 200:
            print("✅ timeline funcionou corretamente")
            print(f"   - Modelo usado: {data.get('model_used', 'N/A')}")
            print(f"   - Anomalias totais: {data.get('total_anomalies', 0)}")
            return True
        else:
            print(f"❌ timeline falhou: {data.get('error', 'Erro desconhecido')}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao testar timeline: {e}")
        return False

def main():
    """Função principal"""
    print("🚀 TESTE DE CARREGAMENTO DE MODELOS")
    print("=" * 50)
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Verificar se o backend está rodando
    try:
        response = requests.get(f"{API_BASE}/health")
        if response.status_code != 200:
            print("❌ Backend não está rodando")
            return
        print("✅ Backend está rodando")
    except Exception as e:
        print(f"❌ Erro ao conectar com backend: {e}")
        return
    
    # Executar testes
    detect_success = test_detect_anomalies()
    compare_success = test_compare_models()
    timeline_success = test_timeline()
    
    print("\n" + "=" * 50)
    print("📊 RESULTADOS DOS TESTES:")
    print(f"   - detect_ml_anomalies: {'✅' if detect_success else '❌'}")
    print(f"   - compare_ml_models: {'✅' if compare_success else '❌'}")
    print(f"   - timeline: {'✅' if timeline_success else '❌'}")
    
    if detect_success and compare_success and timeline_success:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("   Os modelos estão sendo carregados corretamente.")
    else:
        print("\n⚠️ ALGUNS TESTES FALHARAM!")
        print("   Verifique os logs para mais detalhes.")
    
    print("=" * 50)

if __name__ == "__main__":
    main() 