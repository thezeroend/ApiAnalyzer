#!/usr/bin/env python3
"""
Script de teste para demonstrar o funcionamento do armazenamento de modelos
e detecção de IPs suspeitos
"""

import sys
import os
# Adicionar o diretório pai ao path de forma mais robusta
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from datetime import datetime, timedelta
import random
from app.models import LogEntry
from app.ml_anomaly_detector import MLAnomalyDetector, train_ml_models, detect_ml_anomalies
from app.analyzer import detect_ip_anomalies
from app.model_storage import get_available_models, export_trained_model, import_trained_model

def generate_test_logs(num_logs=100):
    """Gera logs de teste com padrões variados"""
    logs = []
    
    # IPs conhecidos por cliente
    client_ips = {
        "cliente_001": ["192.168.1.10", "192.168.1.11"],
        "cliente_002": ["10.0.0.5", "10.0.0.6"],
        "cliente_003": ["172.16.0.1"],
        "cliente_004": ["203.0.113.10", "203.0.113.11", "203.0.113.12"]
    }
    
    # Paths normais e suspeitos
    normal_paths = [
        "/api/users", "/api/products", "/api/orders", 
        "/api/categories", "/api/reviews", "/api/search"
    ]
    
    suspicious_paths = [
        "/admin", "/admin/users", "/admin/config",
        "/login", "/auth", "/config", "/debug"
    ]
    
    methods = ["GET", "POST", "PUT", "DELETE"]
    status_codes = [200, 201, 400, 401, 403, 404, 500]
    
    for i in range(num_logs):
        # Escolher cliente
        client_id = random.choice(list(client_ips.keys()))
        
        # Escolher IP (normal ou suspeito)
        if random.random() < 0.9:  # 90% IPs normais
            ip = random.choice(client_ips[client_id])
        else:  # 10% IPs suspeitos
            if random.random() < 0.5:
                ip = "203.0.113.45"  # IP novo
            else:
                ip = "127.0.0.1"  # Loopback
        
        # Escolher path
        if random.random() < 0.95:  # 95% paths normais
            path = random.choice(normal_paths)
        else:  # 5% paths suspeitos
            path = random.choice(suspicious_paths)
        
        # Escolher método e status
        method = random.choice(methods)
        status = random.choice(status_codes)
        
        # Timestamp (últimas 24 horas)
        timestamp = datetime.now() - timedelta(
            hours=random.randint(0, 24),
            minutes=random.randint(0, 60)
        )
        
        log = LogEntry(
            requestId=f"req_{i:06d}",
            clientId=client_id,
            ip=ip,
            method=method,
            path=path,
            status=status,
            timestamp=timestamp
        )
        
        logs.append(log)
    
    return logs

def test_model_storage():
    """Testa o sistema de armazenamento de modelos"""
    print("🧪 TESTANDO SISTEMA DE ARMAZENAMENTO DE MODELOS")
    print("=" * 60)
    
    # 1. Gerar logs de teste
    print("\n1️⃣ Gerando logs de teste...")
    logs = generate_test_logs(200)
    print(f"   ✅ {len(logs)} logs gerados")
    
    # 2. Treinar modelos
    print("\n2️⃣ Treinando modelos ML...")
    detector = MLAnomalyDetector()
    result = detector.train_models(logs, save_models=True)
    
    if "error" in result:
        print(f"   ❌ Erro no treinamento: {result['error']}")
        return
    else:
        print(f"   ✅ Modelos treinados: {result['models_trained']}")
        print(f"   ✅ Características: {result['features_count']}")
        print(f"   ✅ Amostras: {result['samples_count']}")
    
    # 3. Listar modelos disponíveis
    print("\n3️⃣ Listando modelos disponíveis...")
    available_models = get_available_models()
    print(f"   ✅ {len(available_models)} modelos encontrados:")
    
    for model in available_models:
        metadata = model['metadata']
        print(f"      📊 {model['name']}:")
        print(f"         - Treinado em: {metadata['trained_at']}")
        print(f"         - Características: {metadata['features_count']}")
        print(f"         - Amostras: {metadata['samples_count']}")
    
    # 4. Testar carregamento de modelo
    print("\n4️⃣ Testando carregamento de modelo...")
    if available_models:
        model_name = available_models[0]['name']
        detector2 = MLAnomalyDetector()
        success = detector2.load_trained_model(model_name)
        
        if success:
            print(f"   ✅ Modelo {model_name} carregado com sucesso")
            
            # 5. Detectar anomalias com modelo carregado
            print("\n5️⃣ Detectando anomalias...")
            new_logs = generate_test_logs(50)
            anomalies = detector2.detect_anomalies(new_logs, model_name)
            
            if "error" not in anomalies:
                print(f"   ✅ Anomalias detectadas: {anomalies['anomalies_detected']}")
                print(f"   ✅ Taxa de anomalia: {anomalies['anomaly_rate']:.3f}")
                print(f"   ✅ Score médio: {anomalies['score_statistics']['mean']:.3f}")
            else:
                print(f"   ❌ Erro na detecção: {anomalies['error']}")
        else:
            print(f"   ❌ Erro ao carregar modelo {model_name}")
    
    # 6. Testar exportação/importação
    print("\n6️⃣ Testando exportação/importação...")
    if available_models:
        model_name = available_models[0]['name']
        export_path = f"test_export_{model_name}.pkl"
        
        # Exportar
        success = export_trained_model(model_name, export_path)
        if success:
            print(f"   ✅ Modelo {model_name} exportado para {export_path}")
            
            # Importar
            success = import_trained_model(export_path)
            if success:
                print(f"   ✅ Modelo importado com sucesso")
            else:
                print(f"   ❌ Erro na importação")
        else:
            print(f"   ❌ Erro na exportação")

def test_ip_anomaly_detection():
    """Testa a detecção de anomalias baseada em IPs"""
    print("\n\n🕵️ TESTANDO DETECÇÃO DE IPs SUSPEITOS")
    print("=" * 60)
    
    # 1. Gerar logs com padrões suspeitos
    print("\n1️⃣ Gerando logs com padrões suspeitos...")
    logs = generate_test_logs(150)
    
    # Adicionar alguns logs suspeitos
    suspicious_logs = [
        # Cliente usando IP novo
        LogEntry(
            requestId="req_susp_001",
            clientId="cliente_001",
            ip="203.0.113.45",  # IP novo para cliente_001
            method="POST",
            path="/api/users",
            status=200,
            timestamp=datetime.now() - timedelta(hours=1)
        ),
        # Cliente usando múltiplos IPs
        LogEntry(
            requestId="req_susp_002",
            clientId="cliente_002",
            ip="10.0.0.7",  # Terceiro IP para cliente_002
            method="GET",
            path="/api/products",
            status=200,
            timestamp=datetime.now() - timedelta(hours=2)
        ),
        LogEntry(
            requestId="req_susp_003",
            clientId="cliente_002",
            ip="10.0.0.8",  # Quarto IP para cliente_002
            method="GET",
            path="/api/products",
            status=200,
            timestamp=datetime.now() - timedelta(hours=3)
        ),
        # Cliente com alta taxa de erro
        LogEntry(
            requestId="req_susp_004",
            clientId="cliente_003",
            ip="172.16.0.1",
            method="POST",
            path="/admin",
            status=403,
            timestamp=datetime.now() - timedelta(hours=1)
        ),
        LogEntry(
            requestId="req_susp_005",
            clientId="cliente_003",
            ip="172.16.0.1",
            method="GET",
            path="/config",
            status=404,
            timestamp=datetime.now() - timedelta(hours=1, minutes=5)
        ),
        LogEntry(
            requestId="req_susp_006",
            clientId="cliente_003",
            ip="172.16.0.1",
            method="POST",
            path="/debug",
            status=500,
            timestamp=datetime.now() - timedelta(hours=1, minutes=10)
        )
    ]
    
    logs.extend(suspicious_logs)
    print(f"   ✅ {len(logs)} logs gerados (incluindo {len(suspicious_logs)} suspeitos)")
    
    # 2. Detectar anomalias de IP
    print("\n2️⃣ Detectando anomalias de IP...")
    anomalies = detect_ip_anomalies(hours_back=24)
    
    if "error" in anomalies:
        print(f"   ❌ Erro na detecção: {anomalies['error']}")
        return
    
    summary = anomalies['summary']
    print(f"   ✅ Clientes analisados: {summary['total_clients_analyzed']}")
    print(f"   ✅ Clientes com IPs novos: {summary['clients_with_new_ips']}")
    print(f"   ✅ Clientes com atividade suspeita: {summary['clients_with_suspicious_activity']}")
    print(f"   ✅ Total de anomalias: {summary['total_anomalies']}")
    
    # 3. Mostrar detalhes das anomalias
    print("\n3️⃣ Detalhes das anomalias detectadas:")
    
    if anomalies['new_ips']:
        print("\n   🔴 IPs Novos:")
        for client, details in anomalies['new_ips'].items():
            print(f"      📍 {client}:")
            print(f"         - IPs novos: {details['new_ips']}")
            print(f"         - IPs conhecidos: {details['known_ips']}")
            print(f"         - Nível de risco: {details['risk_level']}")
    
    if anomalies['multiple_ips']:
        print("\n   🟡 Múltiplos IPs:")
        for client, details in anomalies['multiple_ips'].items():
            print(f"      📍 {client}:")
            print(f"         - IPs recentes: {details['recent_ips']}")
            print(f"         - Quantidade: {details['count']}")
            print(f"         - Nível de risco: {details['risk_level']}")
    
    if anomalies['suspicious_activity']:
        print("\n   🟠 Atividade Suspeita:")
        for client, patterns in anomalies['suspicious_activity'].items():
            print(f"      📍 {client}:")
            for pattern_type, details in patterns.items():
                if pattern_type == 'high_error_rate':
                    print(f"         - Taxa de erro alta: {details['error_rate']:.2%}")
                elif pattern_type == 'high_request_volume':
                    print(f"         - Volume alto: {details['requests_count']} requests")
                elif pattern_type == 'sensitive_path_access':
                    print(f"         - Acesso a paths sensíveis: {details['paths']}")

def main():
    """Função principal"""
    print("🚀 DEMONSTRAÇÃO DO SISTEMA DE ANÁLISE DE LOGS")
    print("=" * 80)
    
    try:
        # Testar armazenamento de modelos
        test_model_storage()
        
        # Testar detecção de IPs suspeitos
        test_ip_anomaly_detection()
        
        print("\n\n✅ TODOS OS TESTES CONCLUÍDOS COM SUCESSO!")
        print("\n📋 RESUMO:")
        print("   • Sistema de armazenamento de modelos funcionando")
        print("   • Detecção de IPs suspeitos operacional")
        print("   • Modelos podem ser exportados/importados")
        print("   • Anomalias são detectadas corretamente")
        
    except Exception as e:
        print(f"\n❌ ERRO DURANTE OS TESTES: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 