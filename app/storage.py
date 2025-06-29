from typing import List, Optional
from .models import LogEntry
from .db import logs_collection
from datetime import datetime
import json
from dateutil.parser import parse

def add_log(log: LogEntry):
    # Converter para dict e garantir que datetime seja serializável
    log_dict = log.dict()
    # Garante que timestamp é datetime
    if isinstance(log_dict["timestamp"], str):
        log_dict["timestamp"] = parse(log_dict["timestamp"])
    logs_collection.insert_one(log_dict)

def insert_log(log: LogEntry):
    """Alias para add_log - mantém compatibilidade com scripts de teste"""
    add_log(log)

def get_all_logs(cutoff_time: Optional[datetime] = None, limit: Optional[int] = None) -> List[LogEntry]:
    """
    Busca todos os logs com filtros opcionais
    
    Args:
        cutoff_time: Filtrar logs a partir desta data/hora
        limit: Limite máximo de logs a retornar
    """
    # Construir query otimizada
    query = {}
    if cutoff_time:
        query["timestamp"] = {"$gte": cutoff_time}
    
    # Usar cursor com limite se especificado
    cursor = logs_collection.find(query)
    if limit:
        cursor = cursor.limit(limit)
    
    # Otimização: Usar list comprehension para melhor performance
    logs = []
    for doc in cursor:
        try:
            # Remover _id do MongoDB se presente
            if '_id' in doc:
                del doc['_id']
            logs.append(LogEntry(**doc))
        except Exception as e:
            print(f"Erro ao processar log: {e}")
            continue
    
    return logs

def get_logs_by_api(apiId: str, cutoff_time: Optional[datetime] = None, limit: Optional[int] = None) -> List[LogEntry]:
    """
    Busca logs de uma API específica com filtros opcionais
    
    Args:
        apiId: ID da API
        cutoff_time: Filtrar logs a partir desta data/hora
        limit: Limite máximo de logs a retornar
    """
    # Construir query otimizada
    query = {"apiId": apiId}
    if cutoff_time:
        query["timestamp"] = {"$gte": cutoff_time}
    
    # Usar cursor com limite se especificado
    cursor = logs_collection.find(query)
    if limit:
        cursor = cursor.limit(limit)
    
    # Otimização: Usar list comprehension para melhor performance
    logs = []
    for doc in cursor:
        try:
            # Remover _id do MongoDB se presente
            if '_id' in doc:
                del doc['_id']
            logs.append(LogEntry(**doc))
        except Exception as e:
            print(f"Erro ao processar log: {e}")
            continue
    
    return logs

def get_logs_count(apiId: Optional[str] = None, cutoff_time: Optional[datetime] = None) -> int:
    """
    Conta logs com filtros opcionais (mais rápido que buscar todos)
    
    Args:
        apiId: ID da API (opcional)
        cutoff_time: Filtrar logs a partir desta data/hora
    """
    query = {}
    if apiId:
        query["apiId"] = apiId
    if cutoff_time:
        query["timestamp"] = {"$gte": cutoff_time}
    
    return logs_collection.count_documents(query)

def clear_logs():
    """Limpa todos os logs (útil para testes)"""
    logs_collection.delete_many({})
    print("Logs limpos com sucesso!") 