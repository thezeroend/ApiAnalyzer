# 🔍 API Log Analyzer

Sistema completo de análise de logs de API com detecção de anomalias usando machine learning e análise tradicional.

## ✨ Funcionalidades

### 🤖 **Machine Learning**
- **Múltiplos algoritmos**: Isolation Forest, LOF, KNN, One-Class SVM, CBLOF
- **Armazenamento de modelos**: Salva, carrega, exporta e importa modelos treinados
- **Características automáticas**: Extrai 17 características dos logs automaticamente
- **Comparação de modelos**: Compara performance de diferentes algoritmos

### 🕵️ **Detecção de Anomalias**
- **Análise tradicional**: Baseada em taxas de erro e padrões
- **Análise de IPs**: Detecta IPs novos, múltiplos IPs e atividade suspeita
- **Análise ML**: Detecção avançada usando algoritmos de machine learning
- **Scores de risco**: Calcula scores de anomalia para cada log

### 📊 **Visualização**
- **Interface web**: Frontend completo com gráficos e estatísticas
- **Estatísticas temporais**: Análise de padrões por hora/dia
- **Alertas visuais**: Diferentes níveis de risco (baixo, médio, alto)
- **Comparação visual**: Gráficos comparativos entre modelos

## 🚀 Instalação

### 1. **Dependências**
```bash
pip install -r requirements.txt
```

### 2. **MongoDB**
Certifique-se de que o MongoDB está rodando:
```bash
# Ubuntu/Debian
sudo systemctl start mongod

# Windows
net start MongoDB

# macOS
brew services start mongodb-community
```

### 3. **Configuração**
O sistema usa as seguintes configurações padrão:
- **MongoDB**: `mongodb://localhost:27017`
- **Database**: `api_logs`
- **Collection**: `logs`

## 🎯 Como Usar

### 1. **Iniciar o Servidor**
```bash
python main.py
```
O servidor estará disponível em `http://localhost:8000`

### 2. **Acessar o Frontend**
Abra `frontend.html` no navegador ou acesse `http://localhost:8000`

### 3. **Inserir Logs**
Via API:
```bash
curl -X POST "http://localhost:8000/logs" \
     -H "Content-Type: application/json" \
     -d '{
       "requestId": "req_001",
       "clientId": "client_001",
       "ip": "192.168.1.100",
       "apiId": "api_001",
       "path": "/api/users",
       "method": "GET",
       "status": 200,
       "timestamp": "2024-01-15T10:30:00"
     }'
```

### 4. **Treinar Modelos ML**
```bash
# Via API
curl -X POST "http://localhost:8000/api/ml/train" \
     -H "Content-Type: application/json" \
     -d '{"apiId": "api_001", "hours_back": 24}'

# Via Python
from app.ml_anomaly_detector import train_ml_models
result = train_ml_models(apiId="api_001", hours_back=24)
```

### 5. **Detectar Anomalias**
```bash
# Via API
curl -X POST "http://localhost:8000/api/ml/detect" \
     -H "Content-Type: application/json" \
     -d '{"model_name": "iforest", "hours_back": 6}'

# Via Python
from app.ml_anomaly_detector import detect_ml_anomalies
anomalies = detect_ml_anomalies(model_name="iforest", hours_back=6)
```

## 🧪 Testes

### **Teste Simples**
```bash
python test_simple.py
```

### **Teste Completo**
```bash
python test_ml.py
```

### **Teste de Anomalias**
```bash
python test_anomalies.py
```

## 📋 Endpoints da API

### **Logs**
- `POST /logs` - Inserir log
- `GET /logs` - Listar logs
- `DELETE /logs` - Limpar logs

### **Estatísticas**
- `GET /stats/{apiId}` - Estatísticas básicas
- `GET /anomalies/{apiId}` - Detecção tradicional de anomalias
- `GET /temporal/{apiId}` - Estatísticas temporais
- `GET /ip-anomalies` - Detecção de IPs suspeitos

### **Machine Learning**
- `POST /api/ml/train` - Treinar modelos
- `POST /api/ml/detect` - Detectar anomalias
- `POST /api/ml/compare` - Comparar modelos
- `GET /api/ml/models` - Listar modelos disponíveis
- `POST /api/ml/models/{model}/export` - Exportar modelo
- `POST /api/ml/models/import` - Importar modelo

## 🔧 Configuração Avançada

### **Armazenamento de Modelos**
Os modelos são salvos automaticamente em `models/`:
```
models/
├── iforest_model.pkl
├── iforest_preprocessors.pkl
├── iforest_model_metadata.json
└── ...
```

### **Características Extraídas**
O sistema extrai automaticamente 17 características:
- **Temporais**: hora, dia da semana, minuto
- **Requisição**: status code, método HTTP, tamanho do path
- **IP**: conversão numérica do IP
- **Cliente**: ID codificado
- **Segurança**: flags para APIs, admin, auth
- **Status**: flags para erros, sucessos, redirecionamentos

### **Algoritmos Disponíveis**
- **Isolation Forest**: Detecção baseada em isolamento
- **LOF (Local Outlier Factor)**: Detecção baseada em densidade local
- **KNN**: Detecção baseada em vizinhos próximos
- **One-Class SVM**: Detecção baseada em separação linear
- **CBLOF**: Detecção baseada em clustering

## 🕵️ Detecção de IPs Suspeitos

### **Tipos de Anomalias**
1. **IPs Novos**: Cliente usando IP nunca visto antes
2. **Múltiplos IPs**: Cliente usando muitos IPs diferentes
3. **Atividade Suspeita**: Alta taxa de erro, volume alto, paths sensíveis

### **Score de Risco**
- **Baixo**: 0-19 pontos
- **Médio**: 20-39 pontos  
- **Alto**: 40+ pontos

### **Fatores de Risco**
- IP público: +20 pontos
- IP loopback: +50 pontos
- IP multicast: +30 pontos
- IP reservado: +40 pontos

## 📊 Exemplo de Uso

### **1. Inserir Logs de Teste**
```python
from app.models import LogEntry
from app.storage import insert_log
from datetime import datetime

log = LogEntry(
    requestId="req_001",
    clientId="client_001", 
    ip="192.168.1.100",
    apiId="api_001",
    path="/api/users",
    method="GET",
    status=200,
    timestamp=datetime.now()
)

insert_log(log)
```

### **2. Treinar Modelos**
```python
from app.ml_anomaly_detector import train_ml_models

result = train_ml_models(apiId="api_001", hours_back=24)
print(f"Modelos treinados: {result['models_trained']}")
```

### **3. Detectar Anomalias**
```python
from app.ml_anomaly_detector import detect_ml_anomalies

anomalies = detect_ml_anomalies(model_name="iforest", hours_back=6)
print(f"Anomalias detectadas: {anomalies['anomalies_detected']}")
```

### **4. Analisar IPs Suspeitos**
```python
from app.analyzer import detect_ip_anomalies

ip_anomalies = detect_ip_anomalies(hours_back=24)
print(f"IPs novos: {ip_anomalies['summary']['clients_with_new_ips']}")
```

## 🔍 Solução de Problemas

### **Erro de Conexão com MongoDB**
```bash
# Verificar se o MongoDB está rodando
sudo systemctl status mongod

# Reiniciar MongoDB
sudo systemctl restart mongod
```

### **Erro de Dependências**
```bash
# Atualizar pip
pip install --upgrade pip

# Reinstalar dependências
pip install -r requirements.txt --force-reinstall
```

### **Modelos Não Treinados**
```bash
# Verificar se há logs suficientes
curl "http://localhost:8000/logs"

# Treinar modelos novamente
curl -X POST "http://localhost:8000/api/ml/train"
```

### **Frontend Não Funciona**
- Verificar se o servidor está rodando
- Verificar console do navegador para erros
- Verificar CORS no backend

## 📈 Performance

### **Recomendações**
- **Mínimo de logs**: 10 logs para treinamento
- **Período de análise**: 24 horas para melhor precisão
- **Frequência de treinamento**: Diária ou semanal
- **Armazenamento**: Modelos salvos automaticamente

### **Limitações**
- Requer dados suficientes para treinamento
- Performance depende da qualidade dos dados
- Análise em tempo real pode ser lenta com muitos logs

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.

## 🆘 Suporte

Para suporte, abra uma issue no GitHub ou entre em contato através do email.

---

**Desenvolvido com ❤️ para análise de logs de API**