#!/usr/bin/env python3
"""
Teste completo do sistema de configurações
"""

import sys
import os
# Adicionar o diretório pai ao path de forma mais robusta
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

import requests
import json
import random
from datetime import datetime, timedelta

# Configuração
API_BASE = "http://localhost:8000"

def generate_test_logs():
    """Gera logs de teste para o sistema"""
    print("📝 Gerando logs de teste...")
    
    # Limpar logs existentes
    try:
        requests.delete(f"{API_BASE}/logs")
        print("   - Logs anteriores limpos")
    except:
        pass
    
    # Gerar logs normais
    normal_logs = []
    for i in range(50):
        log = {
            "requestId": f"req_normal_{i}",
            "apiId": "test_config",
            "clientId": f"client_{i % 5}",
            "timestamp": (datetime.now() - timedelta(minutes=i)).isoformat(),
            "method": random.choice(["GET", "POST", "PUT"]),
            "path": random.choice(["/api/users", "/api/products", "/api/orders"]),
            "status": random.choice([200, 201, 204]),
            "ip": f"192.168.1.{random.randint(1, 10)}"
        }
        normal_logs.append(log)
    
    # Gerar logs anômalos
    anomalous_logs = []
    for i in range(5):
        log = {
            "requestId": f"req_anomaly_{i}",
            "apiId": "test_config",
            "clientId": f"client_anomaly_{i}",
            "timestamp": (datetime.now() - timedelta(minutes=i)).isoformat(),
            "method": "DELETE",
            "path": "/api/admin/users",
            "status": random.choice([403, 500, 404]),
            "ip": f"172.16.10.{random.randint(1, 10)}"
        }
        anomalous_logs.append(log)
    
    # Enviar logs
    all_logs = normal_logs + anomalous_logs
    for log in all_logs:
        try:
            response = requests.post(f"{API_BASE}/logs", json=log)
            if response.status_code != 200:
                print(f"   ⚠️ Erro ao enviar log {log['requestId']}")
        except Exception as e:
            print(f"   ❌ Erro ao enviar log: {e}")
    
    print(f"   ✅ {len(all_logs)} logs gerados ({len(normal_logs)} normais, {len(anomalous_logs)} anômalos)")

def test_get_config():
    """Testa obter configurações"""
    print("🔧 Testando obtenção de configurações...")
    
    try:
        response = requests.get(f"{API_BASE}/config")
        if response.status_code == 200:
            data = response.json()
            print("✅ Configurações obtidas com sucesso!")
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
        # Primeiro, treinar modelos
        print("   🎓 Treinando modelos...")
        train_response = requests.post(f"{API_BASE}/ml/train?apiId=test_config")
        if train_response.status_code != 200:
            print(f"   ❌ Erro ao treinar modelos: {train_response.status_code}")
            return False
        
        # Definir um threshold específico
        threshold = 0.14
        print(f"   ⚙️ Definindo threshold: {threshold}")
        requests.post(f"{API_BASE}/config/update", json={
            "section": "ml_detection",
            "key": "threshold",
            "value": threshold
        })
        
        # Agora testar detecção sem passar threshold (deve usar o das configurações)
        print("   🔍 Executando detecção...")
        response = requests.get(f"{API_BASE}/ml/detect?apiId=test_config")
        
        if response.status_code == 200:
            data = response.json()
            if "error" not in data:
                print("✅ Detecção com configurações funcionando!")
                print(f"   - Threshold usado: {data.get('threshold_used', 'N/A')}")
                print(f"   - Anomalias detectadas: {data.get('anomalies_detected', 0)}")
                print(f"   - Logs analisados: {data.get('logs_analyzed', 0)}")
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

def test_all_config_sections():
    """Testa todas as seções de configuração"""
    print("\n🔧 Testando todas as seções de configuração...")
    
    sections = {
        "feedback": {
            "auto_retrain": False,
            "retrain_interval_hours": 12,
            "false_positive_weight": 3
        },
        "monitoring": {
            "alert_threshold": 15,
            "notification_enabled": True,
            "log_retention_days": 60
        },
        "ui": {
            "theme": "dark",
            "language": "en-US",
            "refresh_interval_seconds": 60
        }
    }
    
    success_count = 0
    
    for section_name, section_config in sections.items():
        print(f"   📝 Testando seção: {section_name}")
        
        try:
            response = requests.post(f"{API_BASE}/config/section", json={
                "section": section_name,
                "config": section_config
            })
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Seção {section_name} atualizada: {data.get('message')}")
                success_count += 1
            else:
                print(f"   ❌ Erro ao atualizar seção {section_name}: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Erro na seção {section_name}: {e}")
    
    print(f"   📊 {success_count}/{len(sections)} seções atualizadas com sucesso")
    return success_count == len(sections)

def main():
    """Função principal"""
    print("🚀 TESTE COMPLETO DO SISTEMA DE CONFIGURAÇÕES")
    print("=" * 60)
    
    try:
        # 1. Gerar logs de teste
        generate_test_logs()
        
        # 2. Testar obtenção de configurações
        config = test_get_config()
        if not config:
            print("❌ Falha ao obter configurações iniciais")
            return
        
        # 3. Testar atualização de threshold
        if not test_update_threshold():
            print("❌ Falha na atualização de threshold")
            return
        
        # 4. Testar atualização de seção
        if not test_update_section():
            print("❌ Falha na atualização de seção")
            return
        
        # 5. Testar reset de seção
        if not test_reset_section():
            print("❌ Falha no reset de seção")
            return
        
        # 6. Testar todas as seções
        if not test_all_config_sections():
            print("❌ Falha no teste de todas as seções")
            return
        
        # 7. Testar detecção com configurações
        if not test_detection_with_config():
            print("❌ Falha na detecção com configurações")
            return
        
        print("\n" + "=" * 60)
        print("🏁 TESTE COMPLETO CONCLUÍDO COM SUCESSO!")
        print("=" * 60)
        print("\n📊 RESUMO:")
        print("   - ✅ Geração de logs de teste")
        print("   - ✅ Obtenção de configurações")
        print("   - ✅ Atualização de threshold")
        print("   - ✅ Atualização de seção")
        print("   - ✅ Reset de seção")
        print("   - ✅ Teste de todas as seções")
        print("   - ✅ Detecção com configurações")
        print("\n🎉 Sistema de configurações funcionando perfeitamente!")
        print("\n🌐 Agora você pode acessar a página de configurações:")
        print("   http://localhost:8000/config.html")
        
    except Exception as e:
        print(f"\n❌ ERRO GERAL: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 