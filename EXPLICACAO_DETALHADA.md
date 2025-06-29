# 📚 Explicação Detalhada do Sistema

## 🔄 **Como Funciona o Armazenamento de Modelos**

### **1. Estrutura de Armazenamento**

O sistema salva os modelos treinados em uma estrutura organizada:

```
models/
├── iforest_model.pkl              # Modelo Isolation Forest
├── iforest_preprocessors.pkl      # Scaler e LabelEncoders
├── iforest_model_metadata.json    # Metadados do treinamento
├── lof_model.pkl                  # Modelo LOF
├── lof_preprocessors.pkl          # Preprocessadores
├── lof_model_metadata.json        # Metadados
└── ... (outros modelos)
```

### **2. Componentes Salvos**

Para cada modelo, o sistema salva:

- **Modelo PyOD**: O algoritmo treinado (Isolation Forest, LOF, etc.)
- **StandardScaler**: Normalização das características
- **LabelEncoders**: Codificação de valores categóricos (métodos HTTP, clientIds)
- **Metadados**: Informações sobre o treinamento

### **3. Processo de Salvamento**

```python
# Durante o treinamento
metadata = {
    "trained_at": "2024-01-15T10:30:00",
    "features_count": 17,
    "samples_count": 1000,
    "feature_names": ["hour", "day_of_week", ...],
    "feature_stats": {
        "mean": {...},
        "std": {...},
        "min": {...},
        "max": {...}
    }
}

# Salvar tudo
save_trained_models(
    models=self.models,
    scaler=self.scaler,
    label_encoders=self.label_encoders,
    metadata=metadata
)
```

### **4. Externalização do Treinamento**

#### **Opção 1: Treinar e Salvar**
```python
# Treinar modelos
detector = MLAnomalyDetector()
result = detector.train_models(logs, save_models=True)

# Modelos são salvos automaticamente
```

#### **Opção 2: Treinar sem Salvar**
```python
# Treinar sem salvar (para testes)
result = detector.train_models(logs, save_models=False)
```

#### **Opção 3: Carregar Modelo Existente**
```python
# Carregar modelo salvo
detector = MLAnomalyDetector()
success = detector.load_trained_model('iforest')

if success:
    # Usar modelo para detecção
    anomalies = detector.detect_anomalies(new_logs, 'iforest')
```

### **5. Exportação/Importação**

#### **Exportar Modelo**
```python
# Exportar para arquivo externo
export_trained_model('iforest', 'meu_modelo_iforest.pkl')
```

#### **Importar Modelo**
```python
# Importar de arquivo externo
import_trained_model('modelo_externo.pkl')
```

## 🕵️ **Como Funciona a Detecção de IPs Suspeitos**

### **1. Análise de IPs por Cliente**

O sistema analisa padrões de IPs para cada cliente:

```python
# Agrupar IPs por cliente
client_ips = {
    "cliente_001": {"192.168.1.10", "192.168.1.11"},
    "cliente_002": {"10.0.0.5", "10.0.0.6", "10.0.0.7"},
    "cliente_003": {"172.16.0.1"}
}
```

### **2. Detecção de IPs Novos**

```python
# Para cada cliente
for client_id, recent_ips in client_recent_ips.items():
    all_known_ips = client_ips[client_id]
    
    # IPs históricos (vistos antes)
    historical_ips = all_known_ips - recent_ips
    
    # IPs novos (vistos pela primeira vez)
    new_ips = recent_ips - historical_ips
    
    if new_ips:
        # ALERTA: Cliente usando IP novo
        risk_level = "medium" if len(new_ips) == 1 else "high"
```

### **3. Detecção de Múltiplos IPs**

```python
# Verificar se cliente usa muitos IPs diferentes
if len(recent_ips) > 2:
    risk_level = "high" if len(recent_ips) > 4 else "medium"
    
    # Exemplo:
    # Cliente normalmente usa 1-2 IPs
    # Se usar 5+ IPs em 24h = ALERTA ALTO
```

### **4. Análise de Padrões Suspeitos**

#### **Taxa de Erro Alta**
```python
error_rate = len(error_logs) / len(total_logs)
if error_rate > 0.2:  # Mais de 20% de erros
    # ALERTA: Possível ataque ou problema
```

#### **Volume de Requests**
```python
if len(logs) > 20:  # Muitas requisições
    # ALERTA: Possível DDoS ou scraping
```

#### **Acesso a Paths Sensíveis**
```python
sensitive_paths = ["/admin", "/login", "/auth", "/config"]
sensitive_attempts = [log for log in logs 
                     if any(path in log.path.lower() 
                           for path in sensitive_paths)]

if sensitive_attempts:
    # ALERTA: Tentativas de acesso não autorizado
```

### **5. Score de Risco por IP**

```python
def get_ip_risk_score(ip: str) -> Dict:
    ip_obj = ipaddress.ip_address(ip)
    
    risk_factors = {
        "is_private": ip_obj.is_private,      # IP privado = menos risco
        "is_loopback": ip_obj.is_loopback,    # 127.0.0.1 = alto risco
        "is_multicast": ip_obj.is_multicast,  # IP multicast = risco médio
        "is_reserved": ip_obj.is_reserved,    # IP reservado = alto risco
    }
    
    score = 0
    if not risk_factors["is_private"]:
        score += 20  # IP público = mais risco
    
    if risk_factors["is_loopback"]:
        score += 50  # Loopback = muito suspeito
    
    return {
        "risk_score": score,
        "risk_level": "low" if score < 20 else "medium" if score < 40 else "high"
    }
```

## 🧠 **Características Extraídas para ML**

### **1. Características Temporais**
- **Hora**: 0-23 (padrões de uso por hora)
- **Dia da semana**: 0-6 (padrões semanais)
- **Minuto**: 0-59 (padrões de frequência)

### **2. Características da Requisição**
- **Status Code**: 200, 404, 500, etc.
- **Método HTTP**: GET, POST, PUT, DELETE (codificado)
- **Tamanho do Path**: Número de caracteres
- **Profundidade do Path**: Número de barras

### **3. Características do IP**
- **IP Numérico**: Conversão do IP para número
  ```python
  # Exemplo: 192.168.1.1
  ip_parts = ["192", "168", "1", "1"]
  ip_numeric = 192*256³ + 168*256² + 1*256¹ + 1*256⁰
  ```

### **4. Características do Cliente**
- **Client ID**: Codificado numericamente
- **Padrões de uso**: Histórico de comportamento

### **5. Flags de Segurança**
- **is_api_path**: 1 se contém '/api/'
- **is_admin_path**: 1 se contém '/admin'
- **is_auth_path**: 1 se contém '/login', '/auth', '/token'

### **6. Flags de Status**
- **is_error**: 1 se status >= 400
- **is_server_error**: 1 se status >= 500
- **is_client_error**: 1 se 400 <= status < 500
- **is_success**: 1 se 200 <= status < 300

## 🔧 **Como Usar o Sistema**

### **1. Treinar Modelos**
```bash
# Via API
curl -X POST "http://localhost:8000/api/ml/train" \
     -H "Content-Type: application/json" \
     -d '{"apiId": "api_001", "hours_back": 24}'

# Via Python
from app.ml_anomaly_detector import train_ml_models
result = train_ml_models(apiId="api_001", hours_back=24)
```

### **2. Detectar Anomalias**
```bash
# Via API
curl -X POST "http://localhost:8000/api/ml/detect" \
     -H "Content-Type: application/json" \
     -d '{"model_name": "iforest", "hours_back": 6}'

# Via Python
from app.ml_anomaly_detector import detect_ml_anomalies
anomalies = detect_ml_anomalies(model_name="iforest", hours_back=6)
```

### **3. Gerenciar Modelos**
```bash
# Listar modelos disponíveis
curl "http://localhost:8000/api/ml/models"

# Exportar modelo
curl -X POST "http://localhost:8000/api/ml/models/iforest/export" \
     -H "Content-Type: application/json" \
     -d '{"export_path": "meu_modelo.pkl"}'

# Importar modelo
curl -X POST "http://localhost:8000/api/ml/models/import" \
     -H "Content-Type: application/json" \
     -d '{"import_path": "modelo_externo.pkl"}'
```

## 📊 **Exemplo de Resultado**

### **Detecção de Anomalias ML**
```json
{
  "model_used": "iforest",
  "total_logs": 1000,
  "anomalies_detected": 15,
  "anomaly_rate": 0.015,
  "anomalies": [
    {
      "requestId": "req_123",
      "clientId": "cliente_001",
      "ip": "192.168.1.100",
      "method": "POST",
      "path": "/api/admin/users",
      "status": 403,
      "anomaly_score": 0.85,
      "is_anomaly": true,
      "features": {
        "hour": 23,
        "day_of_week": 6,
        "status_code": 403,
        "is_admin_path": 1,
        "is_error": 1
      }
    }
  ],
  "score_statistics": {
    "mean": 0.12,
    "std": 0.08,
    "min": 0.01,
    "max": 0.95
  }
}
```

### **Detecção de IPs Suspeitos**
```json
{
  "new_ips": {
    "cliente_001": {
      "new_ips": ["203.0.113.45"],
      "known_ips": ["192.168.1.10", "192.168.1.11"],
      "risk_level": "medium"
    }
  },
  "multiple_ips": {
    "cliente_002": {
      "recent_ips": ["10.0.0.5", "10.0.0.6", "10.0.0.7", "10.0.0.8"],
      "count": 4,
      "risk_level": "high"
    }
  },
  "suspicious_activity": {
    "cliente_003": {
      "high_error_rate": {
        "error_rate": 0.35,
        "total_requests": 20,
        "errors": 7
      },
      "sensitive_path_access": {
        "attempts": 3,
        "paths": ["/admin", "/config"]
      }
    }
  }
}
```

## 🎯 **Vantagens do Sistema**

### **1. Flexibilidade**
- Treinamento pode ser feito em qualquer momento
- Modelos podem ser exportados/importados
- Múltiplos algoritmos disponíveis

### **2. Robustez**
- Análise baseada em múltiplas características
- Combinação de ML + regras tradicionais
- Metadados completos para auditoria

### **3. Escalabilidade**
- Modelos salvos podem ser reutilizados
- Processamento em lotes
- API REST para integração

### **4. Interpretabilidade**
- Características bem definidas
- Scores de anomalia explicáveis
- Alertas categorizados por risco 