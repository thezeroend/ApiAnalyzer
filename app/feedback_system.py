"""
Sistema de Feedback para Anomalias
Permite ao usuário marcar falsos positivos e treinar o modelo com feedback
"""

import json
import pickle
from datetime import datetime
from typing import Dict, List, Optional
from pymongo import MongoClient
from app.db import client, db
from app.ml_anomaly_detector import train_ml_models, detect_ml_anomalies, train_ml_models_with_collection
from app.models import LogEntry

class FeedbackSystem:
    def __init__(self):
        self.client = client
        self.db = db
        self.feedback_collection = self.db.feedback
        
    def mark_as_false_positive(self, log_id: str, api_id: str, user_comment: str = "", anomaly_score: float = None, features: dict = None) -> Dict:
        """
        Marca uma anomalia detectada como falso positivo
        
        Args:
            log_id: ID do log que foi marcado como falso positivo
            api_id: ID da API
            user_comment: Comentário opcional do usuário
            anomaly_score: Score da anomalia detectada
            features: Features da anomalia
            
        Returns:
            Dict com status da operação
        """
        try:
            # Buscar o log original
            log = self.db.logs.find_one({"requestId": log_id})
            if not log:
                return {"error": "Log não encontrado"}
            
            # Criar registro de feedback
            feedback = {
                "log_id": log_id,
                "api_id": api_id,
                "feedback_type": "false_positive",
                "user_comment": user_comment,
                "anomaly_score": anomaly_score,
                "features": features,
                "original_log": log,
                "timestamp": datetime.now(),
                "processed": False  # Indica se já foi usado para retreinamento
            }
            
            # Salvar feedback
            result = self.feedback_collection.insert_one(feedback)
            
            return {
                "success": True,
                "message": "Falso positivo registrado com sucesso",
                "feedback_id": str(result.inserted_id)
            }
            
        except Exception as e:
            return {"error": f"Erro ao registrar feedback: {str(e)}"}
    
    def mark_as_true_positive(self, log_id: str, api_id: str, user_comment: str = "", anomaly_score: float = None, features: dict = None) -> Dict:
        """
        Marca uma anomalia detectada como verdadeiro positivo
        
        Args:
            log_id: ID do log que foi confirmado como anomalia real
            api_id: ID da API
            user_comment: Comentário opcional do usuário
            anomaly_score: Score da anomalia detectada
            features: Features da anomalia
            
        Returns:
            Dict com status da operação
        """
        try:
            # Buscar o log original
            log = self.db.logs.find_one({"requestId": log_id})
            if not log:
                return {"error": "Log não encontrado"}
            
            # Criar registro de feedback
            feedback = {
                "log_id": log_id,
                "api_id": api_id,
                "feedback_type": "true_positive",
                "user_comment": user_comment,
                "anomaly_score": anomaly_score,
                "features": features,
                "original_log": log,
                "timestamp": datetime.now(),
                "processed": False
            }
            
            # Salvar feedback
            result = self.feedback_collection.insert_one(feedback)
            
            return {
                "success": True,
                "message": "Verdadeiro positivo registrado com sucesso",
                "feedback_id": str(result.inserted_id)
            }
            
        except Exception as e:
            return {"error": f"Erro ao registrar feedback: {str(e)}"}
    
    def get_feedback_history(self, api_id: str = None, limit: int = 50) -> Dict:
        """
        Obtém histórico de feedback
        
        Args:
            api_id: ID da API (opcional)
            limit: Limite de registros
            
        Returns:
            Dict com histórico de feedback
        """
        try:
            query = {}
            if api_id:
                query["api_id"] = api_id
            
            feedbacks = list(self.feedback_collection.find(query).sort("timestamp", -1).limit(limit))
            
            # Converter ObjectId para string e tratar serialização
            for feedback in feedbacks:
                feedback["_id"] = str(feedback["_id"])
                feedback["timestamp"] = feedback["timestamp"].isoformat()
                
                # Remover _id do log original para evitar problemas de serialização
                if "original_log" in feedback and "_id" in feedback["original_log"]:
                    del feedback["original_log"]["_id"]
            
            return {
                "success": True,
                "feedbacks": feedbacks,
                "total": len(feedbacks)
            }
            
        except Exception as e:
            return {"error": f"Erro ao buscar feedback: {str(e)}"}
    
    def retrain_with_feedback(self, api_id: str) -> Dict:
        """
        Retreina o modelo usando feedback do usuário
        
        Args:
            api_id: ID da API para retreinar
            
        Returns:
            Dict com status do retreinamento
        """
        try:
            # Buscar feedbacks não processados
            unprocessed_feedbacks = list(self.feedback_collection.find({
                "api_id": api_id,
                "processed": False
            }))
            
            if not unprocessed_feedbacks:
                return {"message": "Nenhum feedback não processado encontrado"}
            
            # Separar falsos positivos
            false_positives = [f for f in unprocessed_feedbacks if f["feedback_type"] == "false_positive"]
            
            # Obter todos os logs da API
            all_logs = list(self.db.logs.find({"apiId": api_id}))
            
            if not all_logs:
                return {"error": "Nenhum log encontrado para a API"}
            
            # Criar conjunto de logs de treinamento
            training_logs = []
            
            # Adicionar todos os logs normais
            for log in all_logs:
                # Remover _id para evitar duplicidade
                if '_id' in log:
                    del log['_id']
                training_logs.append(log)
            
            # Para cada falso positivo, adicionar o log múltiplas vezes para "diluir" sua anomalia
            # Isso faz com que o modelo aprenda que esse padrão é normal
            for feedback in false_positives:
                log = feedback["original_log"]
                # Remover _id se presente
                if '_id' in log:
                    del log['_id']
                
                # Adicionar o log 5 vezes para dar mais peso como "normal"
                for _ in range(5):
                    training_logs.append(log.copy())
                
                # Marcar como processado
                self.feedback_collection.update_one(
                    {"_id": feedback["_id"]},
                    {"$set": {"processed": True}}
                )
            
            # Salvar logs de treinamento em uma coleção permanente
            training_collection = self.db.training_logs
            training_collection.drop()  # Limpar dados anteriores
            if training_logs:
                training_collection.insert_many(training_logs)
            
            # Retreinar modelo usando a coleção de treinamento
            retrain_result = train_ml_models_with_collection(apiId=api_id, hours_back=168, save_models=True)
            
            return {
                "success": True,
                "message": f"Modelo retreinado com {len(false_positives)} falsos positivos",
                "false_positives_processed": len(false_positives),
                "total_logs_used": len(training_logs),
                "retrain_result": retrain_result
            }
            
        except Exception as e:
            return {"error": f"Erro no retreinamento: {str(e)}"}
    
    def get_feedback_stats(self, api_id: str = None) -> Dict:
        """
        Obtém estatísticas de feedback
        
        Args:
            api_id: ID da API (opcional)
            
        Returns:
            Dict com estatísticas
        """
        try:
            query = {}
            if api_id:
                query["api_id"] = api_id
            
            # Contar por tipo
            false_positives = self.feedback_collection.count_documents({
                **query,
                "feedback_type": "false_positive"
            })
            
            true_positives = self.feedback_collection.count_documents({
                **query,
                "feedback_type": "true_positive"
            })
            
            unprocessed = self.feedback_collection.count_documents({
                **query,
                "processed": False
            })
            
            return {
                "success": True,
                "stats": {
                    "false_positives": false_positives,
                    "true_positives": true_positives,
                    "unprocessed": unprocessed,
                    "total": false_positives + true_positives
                }
            }
            
        except Exception as e:
            return {"error": f"Erro ao buscar estatísticas: {str(e)}"}
    
    def get_logs_with_feedback(self, api_id: str = None) -> List[str]:
        """
        Obtém lista de log_ids que já foram marcados com feedback
        
        Args:
            api_id: ID da API (opcional)
            
        Returns:
            Lista de log_ids que já têm feedback
        """
        try:
            query = {}
            if api_id:
                query["api_id"] = api_id
            
            feedbacks = list(self.feedback_collection.find(query, {"log_id": 1}))
            return [feedback["log_id"] for feedback in feedbacks]
            
        except Exception as e:
            print(f"Erro ao buscar logs com feedback: {str(e)}")
            return []

    def get_processed_false_positives(self, api_id: str = None) -> List[str]:
        """
        Obtém lista de log_ids que foram marcados como falsos positivos E processados
        (estes não devem mais aparecer como anomalias)
        
        Args:
            api_id: ID da API (opcional)
            
        Returns:
            Lista de log_ids de falsos positivos processados
        """
        try:
            query = {
                "feedback_type": "false_positive",
                "processed": True
            }
            if api_id:
                query["api_id"] = api_id
            
            feedbacks = list(self.feedback_collection.find(query, {"log_id": 1}))
            return [feedback["log_id"] for feedback in feedbacks]
            
        except Exception as e:
            print(f"Erro ao buscar falsos positivos processados: {str(e)}")
            return []

    def get_true_positives(self, api_id: str = None) -> List[str]:
        """
        Obtém lista de log_ids que foram marcados como verdadeiros positivos
        (estes devem continuar sendo detectados como anomalias)
        
        Args:
            api_id: ID da API (opcional)
            
        Returns:
            Lista de log_ids de verdadeiros positivos
        """
        try:
            query = {
                "feedback_type": "true_positive"
            }
            if api_id:
                query["api_id"] = api_id
            
            feedbacks = list(self.feedback_collection.find(query, {"log_id": 1}))
            return [feedback["log_id"] for feedback in feedbacks]
            
        except Exception as e:
            print(f"Erro ao buscar verdadeiros positivos: {str(e)}")
            return []

# Instância global
feedback_system = FeedbackSystem() 