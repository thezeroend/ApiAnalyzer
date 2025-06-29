from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from typing import Optional, Any
from app.models import LogEntry
from app.storage import add_log, clear_logs
from app.analyzer import basic_stats, detect_anomalies, error_rate_by_minute, detect_ip_anomalies
from app.ml_anomaly_detector import train_ml_models, detect_ml_anomalies, compare_ml_models, get_anomalies_timeline_data
from app.model_storage import get_available_models, export_trained_model, import_trained_model
from app.feedback_system import feedback_system
from app.config_manager import config_manager

app = FastAPI()

# Configurar CORS para permitir acesso de qualquer origem
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite todas as origens
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos os métodos HTTP
    allow_headers=["*"],  # Permite todos os headers
)

# Modelos Pydantic para as requisições
class ExportModelRequest(BaseModel):
    export_path: Optional[str] = None

class ImportModelRequest(BaseModel):
    import_path: str

# Modelos Pydantic para feedback
class FeedbackRequest(BaseModel):
    log_id: str
    api_id: str
    user_comment: Optional[str] = ""
    anomaly_score: Optional[float] = None
    features: Optional[dict] = None
    
    @validator('features', pre=True)
    def parse_features(cls, v):
        """Converte features de string JSON para dict se necessário"""
        if isinstance(v, str):
            try:
                import json
                return json.loads(v)
            except json.JSONDecodeError:
                raise ValueError('Features deve ser um JSON válido')
        return v

class RetrainRequest(BaseModel):
    api_id: str

# Modelos Pydantic para configurações
class ConfigUpdateRequest(BaseModel):
    section: str
    key: str
    value: Any

class ConfigSectionUpdateRequest(BaseModel):
    section: str
    config: dict

class ConfigResetRequest(BaseModel):
    section: Optional[str] = None

@app.post("/logs")
def receive_log(log: LogEntry):
    try:
        add_log(log)
        return {"message": "Log received", "status": "success"}
    except Exception as e:
        return {"message": f"Error: {str(e)}", "status": "error"}

@app.get("/stats/{apiId}")
def get_stats(apiId: str):
    try:
        return basic_stats(apiId)
    except Exception as e:
        return {"error": str(e)}

@app.get("/anomalies/{apiId}")
def get_anomalies(apiId: str, threshold: float = 0.5):
    try:
        return detect_anomalies(apiId, threshold=threshold)
    except Exception as e:
        return {"error": str(e)}

@app.get("/temporal/{apiId}")
def get_temporal_stats(apiId: str):
    try:
        return error_rate_by_minute(apiId)
    except Exception as e:
        return {"error": str(e)}

@app.get("/ip-anomalies")
def get_ip_anomalies(apiId: str = None, hours_back: int = 24):
    """
    Detecta anomalias baseadas em IPs suspeitos:
    - IPs novos para clientes existentes
    - Múltiplos IPs para o mesmo cliente
    - Atividade suspeita
    """
    try:
        return detect_ip_anomalies(apiId=apiId, hours_back=hours_back)
    except Exception as e:
        return {"error": str(e)}

@app.post("/ml/train")
def train_ml_anomaly_models(apiId: str = None, hours_back: int = 24):
    """
    Treina modelos de machine learning para detecção de anomalias
    """
    try:
        return train_ml_models(apiId=apiId, hours_back=hours_back)
    except Exception as e:
        return {"error": str(e)}

@app.get("/ml/detect")
def detect_ml_anomalies_endpoint(apiId: str = None, model_name: str = 'iforest', hours_back: int = 24):
    """
    Detecta anomalias usando machine learning
    Modelos disponíveis: iforest, lof, knn, ocsvm, cblof
    """
    try:
        return detect_ml_anomalies(apiId=apiId, model_name=model_name, hours_back=hours_back)
    except Exception as e:
        return {"error": str(e)}

@app.get("/ml/compare")
def compare_ml_models_endpoint(apiId: str = None, hours_back: int = 24):
    """
    Compara diferentes modelos de machine learning
    """
    try:
        return compare_ml_models(apiId=apiId, hours_back=hours_back)
    except Exception as e:
        return {"error": str(e)}

@app.get("/ml/anomalies-timeline")
def get_anomalies_timeline(apiId: str = None, model_name: str = 'iforest', hours_back: int = 24, interval_minutes: int = 30):
    """
    Obtém dados temporais de anomalias para gráficos
    Agrupa anomalias por intervalos de tempo
    """
    try:
        return get_anomalies_timeline_data(apiId=apiId, model_name=model_name, hours_back=hours_back, interval_minutes=interval_minutes)
    except Exception as e:
        return {"error": str(e)}

@app.delete("/logs")
def clear_all_logs():
    """Limpa todos os logs (útil para testes)"""
    try:
        clear_logs()
        return {"message": "All logs cleared", "status": "success"}
    except Exception as e:
        return {"message": f"Error: {str(e)}", "status": "error"}

@app.get("/ml/models")
def list_ml_models():
    """Lista modelos ML disponíveis"""
    try:
        models = get_available_models()
        return {
            "status": "success",
            "models": models,
            "count": len(models)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ml/models/{model_name}/export")
def export_ml_model(model_name: str, request: ExportModelRequest):
    """Exporta um modelo ML"""
    try:
        export_path = request.export_path or f'exported_{model_name}_model.pkl'
        
        success = export_trained_model(model_name, export_path)
        
        if success:
            return {
                "status": "success",
                "message": f"Modelo {model_name} exportado com sucesso",
                "export_path": export_path
            }
        else:
            raise HTTPException(status_code=400, detail=f"Erro ao exportar modelo {model_name}")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ml/models/import")
def import_ml_model(request: ImportModelRequest):
    """Importa um modelo ML"""
    try:
        import_path = request.import_path
        
        success = import_trained_model(import_path)
        
        if success:
            return {
                "status": "success",
                "message": "Modelo importado com sucesso",
                "import_path": import_path
            }
        else:
            raise HTTPException(status_code=400, detail="Erro ao importar modelo")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoints de Feedback
@app.post("/feedback/false-positive")
async def mark_false_positive(feedback: FeedbackRequest):
    """Marca uma anomalia como falso positivo"""
    result = feedback_system.mark_as_false_positive(
        feedback.log_id, 
        feedback.api_id, 
        feedback.user_comment,
        feedback.anomaly_score,
        feedback.features
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.post("/feedback/true-positive")
async def mark_true_positive(feedback: FeedbackRequest):
    """Marca uma anomalia como verdadeiro positivo"""
    result = feedback_system.mark_as_true_positive(
        feedback.log_id, 
        feedback.api_id, 
        feedback.user_comment,
        feedback.anomaly_score,
        feedback.features
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.get("/feedback/history")
async def get_feedback_history(api_id: Optional[str] = None, limit: int = 50):
    """Obtém histórico de feedback"""
    result = feedback_system.get_feedback_history(api_id, limit)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.post("/feedback/retrain")
async def retrain_with_feedback(request: RetrainRequest):
    """Retreina o modelo usando feedback do usuário"""
    result = feedback_system.retrain_with_feedback(request.api_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.get("/feedback/stats")
async def get_feedback_stats(api_id: Optional[str] = None):
    """Obtém estatísticas de feedback"""
    result = feedback_system.get_feedback_stats(api_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.get("/feedback/logs-with-feedback")
async def get_logs_with_feedback(api_id: Optional[str] = None):
    """Obtém logs que já foram marcados com feedback"""
    try:
        logs = feedback_system.get_logs_with_feedback(api_id)
        return {
            "status": "success",
            "logs_with_feedback": logs,
            "count": len(logs)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoints de Configuração
@app.get("/config")
async def get_config(section: Optional[str] = None):
    """Obtém configurações do sistema"""
    try:
        config = config_manager.get_config(section)
        return {
            "status": "success",
            "config": config
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/config/update")
async def update_config(request: ConfigUpdateRequest):
    """Atualiza uma configuração específica"""
    try:
        result = config_manager.update_config(request.section, request.key, request.value)
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/config/section")
async def update_config_section(request: ConfigSectionUpdateRequest):
    """Atualiza uma seção inteira de configurações"""
    try:
        result = config_manager.update_section(request.section, request.config)
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/config/reset")
async def reset_config(request: ConfigResetRequest):
    """Reseta configurações para valores padrão"""
    try:
        result = config_manager.reset_to_default(request.section)
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/config/history")
async def get_config_history(limit: int = 10):
    """Obtém histórico de alterações de configuração"""
    try:
        result = config_manager.get_config_history(limit)
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoints para ML de descrições de anomalias
@app.post("/ml/descriptions/train")
async def train_description_model():
    """Treina o modelo de ML para geração de descrições"""
    try:
        from app.anomaly_description_ml import description_ml
        from app.storage import get_all_logs
        
        # Obtém logs para treinamento
        logs = get_all_logs()
        if not logs:
            return {"error": "Nenhum log encontrado para treinamento"}
        
        # Converte para formato compatível
        training_data = []
        for log in logs:
            training_data.append({
                'requestId': log.requestId,
                'clientId': log.clientId,
                'ip': log.ip,
                'apiId': log.apiId,
                'method': log.method,
                'path': log.path,
                'status': log.status,
                'timestamp': log.timestamp.isoformat()
            })
        
        # Treina modelo
        success = description_ml.train_description_model(training_data)
        
        if success:
            return {
                "message": "Modelo de descrições treinado com sucesso",
                "logs_used": len(training_data),
                "models_saved": ["scaler", "pca", "cluster"]
            }
        else:
            return {"error": "Erro ao treinar modelo de descrições"}
            
    except Exception as e:
        return {"error": f"Erro no treinamento: {str(e)}"}

@app.get("/ml/descriptions/analyze")
async def analyze_anomaly_patterns():
    """Analisa padrões entre anomalias detectadas"""
    try:
        from app.anomaly_description_ml import description_ml
        from app.ml_anomaly_detector import detect_ml_anomalies
        
        # Detecta anomalias
        detection_result = detect_ml_anomalies(hours_back=24)
        
        if "error" in detection_result:
            return {"error": f"Erro na detecção: {detection_result['error']}"}
        
        anomalies = detection_result.get("anomalies", [])
        if not anomalies:
            return {"message": "Nenhuma anomalia encontrada para análise"}
        
        # Converte anomalias para formato compatível
        anomalies_data = []
        for anomaly in anomalies:
            anomalies_data.append({
                'requestId': anomaly.get('requestId', ''),
                'clientId': anomaly.get('clientId', ''),
                'ip': anomaly.get('ip', ''),
                'apiId': anomaly.get('apiId', ''),
                'method': anomaly.get('method', ''),
                'path': anomaly.get('path', ''),
                'status': anomaly.get('status', 0),
                'timestamp': anomaly.get('timestamp', datetime.now().isoformat()),
                'anomaly_score': anomaly.get('anomaly_score', 0)
            })
        
        # Analisa padrões
        pattern_analysis = description_ml.analyze_patterns(anomalies_data)
        
        return {
            "total_anomalies": len(anomalies),
            "pattern_analysis": pattern_analysis,
            "summary": {
                "types_detected": list(pattern_analysis.keys()),
                "most_common_type": max(pattern_analysis.items(), key=lambda x: x[1]['count'])[0] if pattern_analysis else None
            }
        }
        
    except Exception as e:
        return {"error": f"Erro na análise: {str(e)}"}

@app.post("/ml/descriptions/generate")
async def generate_custom_description(request: dict):
    """Gera descrição personalizada para um log específico"""
    try:
        from app.anomaly_description_ml import description_ml
        from app.storage import get_all_logs
        
        # Valida dados de entrada
        required_fields = ['requestId', 'clientId', 'ip', 'apiId', 'method', 'path', 'status', 'timestamp', 'score']
        for field in required_fields:
            if field not in request:
                return {"error": f"Campo obrigatório ausente: {field}"}
        
        # Obtém contexto de logs
        all_logs = get_all_logs()
        all_logs_dict = []
        for log in all_logs:
            all_logs_dict.append({
                'requestId': log.requestId,
                'clientId': log.clientId,
                'ip': log.ip,
                'apiId': log.apiId,
                'method': log.method,
                'path': log.path,
                'status': log.status,
                'timestamp': log.timestamp.isoformat()
            })
        
        # Gera descrição
        description = description_ml.generate_ml_description(request, request['score'], all_logs_dict)
        
        # Extrai features para análise adicional
        features = description_ml.extract_contextual_features(request, all_logs_dict)
        anomaly_type = description_ml.classify_anomaly_type(features, request['score'])
        severity = description_ml.determine_severity(request['score'], features)
        
        return {
            "description": description,
            "analysis": {
                "anomaly_type": anomaly_type,
                "severity": severity,
                "features": features
            }
        }
        
    except Exception as e:
        return {"error": f"Erro na geração: {str(e)}"}