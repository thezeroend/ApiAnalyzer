#!/usr/bin/env python3
"""
Teste específico para verificar se o campo apiId está sendo retornado corretamente
"""

import sys
import os

# Adicionar o diretório pai ao path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from datetime import datetime, timedelta
from app.models import LogEntry
from app.storage import insert_log, clear_logs
from app.ml_anomaly_detector import train_ml_models, detect_ml_anomalies

def test_api_id_in_anomalies():
    """Testa se o campo apiId está sendo retornado nas anomalias"""
    print("🧪 TESTE: Campo apiId nas Anomalias")
    print("=" * 50)
    
    try:
        # Limpar logs existentes
        clear_logs()
        print("✅ Logs limpos")
        
        # Criar logs de teste com apiId específico
        logs = []
        
        # Logs normais
        for i in range(8):
            log = LogEntry(
                requestId=f"normal_{i}",
                clientId="client_001",
                ip="192.168.1.10",
                apiId="test_api_123",  # apiId específico
                path=f"/api/users/{i}",
                method="GET",
                status=200,
                timestamp=datetime.now() - timedelta(hours=1, minutes=i)
            )
            logs.append(log)
        
        # Logs anômalos (diferentes IPs, métodos, status)
        for i in range(3):
            log = LogEntry(
                requestId=f"anomaly_{i}",
                clientId="client_001",
                ip=f"203.0.113.{i+1}",  # IPs diferentes
                apiId="test_api_123",  # apiId específico
                path="/admin/login",  # Path suspeito
                method="POST",  # Método diferente
                status=403,  # Status de erro
                timestamp=datetime.now() - timedelta(minutes=i*5)
            )
            logs.append(log)
        
        # Inserir logs
        for log in logs:
            insert_log(log)
        print(f"✅ {len(logs)} logs inseridos com apiId: test_api_123")
        
        # Treinar modelos
        print("🎯 Treinando modelos...")
        train_result = train_ml_models(apiId="test_api_123", hours_back=24)
        
        if "error" in train_result:
            print(f"❌ Erro no treinamento: {train_result['error']}")
            return False
        
        print("✅ Modelos treinados")
        
        # Detectar anomalias
        print("🔍 Detectando anomalias...")
        anomalies_result = detect_ml_anomalies(apiId="test_api_123", model_name="lof", hours_back=24)
        
        if "error" in anomalies_result:
            print(f"❌ Erro na detecção: {anomalies_result['error']}")
            return False
        
        anomalies = anomalies_result.get("anomalies", [])
        print(f"✅ {len(anomalies)} anomalias detectadas")
        
        # Verificar se o campo apiId está presente
        if anomalies:
            print("\n📋 Verificando campo apiId nas anomalias:")
            for i, anomaly in enumerate(anomalies[:3]):  # Mostrar apenas as primeiras 3
                print(f"   Anomalia {i+1}:")
                print(f"      - requestId: {anomaly.get('requestId', 'N/A')}")
                print(f"      - apiId: {anomaly.get('apiId', 'N/A')}")
                print(f"      - clientId: {anomaly.get('clientId', 'N/A')}")
                print(f"      - score: {anomaly.get('anomaly_score', 'N/A')}")
                
                # Verificar se apiId está presente e correto
                if 'apiId' in anomaly:
                    if anomaly['apiId'] == 'test_api_123':
                        print(f"      ✅ apiId correto: {anomaly['apiId']}")
                    else:
                        print(f"      ❌ apiId incorreto: {anomaly['apiId']} (esperado: test_api_123)")
                else:
                    print(f"      ❌ apiId não encontrado!")
        
        # Verificar se todas as anomalias têm apiId
        anomalies_without_api_id = [a for a in anomalies if 'apiId' not in a]
        if anomalies_without_api_id:
            print(f"\n❌ {len(anomalies_without_api_id)} anomalias sem campo apiId")
            return False
        else:
            print(f"\n✅ Todas as {len(anomalies)} anomalias têm o campo apiId")
        
        print("\n🎉 TESTE CONCLUÍDO COM SUCESSO!")
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_api_id_in_anomalies()
    sys.exit(0 if success else 1) 