#!/usr/bin/env python3
"""
Teste para verificar se a correção da função detect_anomalies funcionou
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ml_anomaly_detector import detect_ml_anomalies

def test_detection():
    """Testa a detecção de anomalias"""
    print("🔍 Testando detecção de anomalias...")
    
    try:
        result = detect_ml_anomalies(hours_back=24)
        
        if "error" in result:
            print(f"❌ Erro na detecção: {result['error']}")
            return False
        else:
            print(f"✅ Detecção funcionou!")
            print(f"   - Modelo usado: {result.get('model_used', 'N/A')}")
            print(f"   - Logs analisados: {result.get('logs_analyzed', 0)}")
            print(f"   - Anomalias detectadas: {result.get('anomalies_detected', 0)}")
            print(f"   - Taxa de anomalia: {result.get('anomaly_rate', 0)}%")
            print(f"   - Threshold usado: {result.get('threshold_used', 'N/A')}")
            return True
            
    except Exception as e:
        print(f"❌ Exceção durante teste: {e}")
        return False

if __name__ == "__main__":
    success = test_detection()
    sys.exit(0 if success else 1) 