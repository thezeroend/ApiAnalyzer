from typing import List
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

def get_all_logs() -> List[LogEntry]:
    docs = logs_collection.find()
    logs = []
    for doc in docs:
        try:
            # Remover _id do MongoDB se presente
            if '_id' in doc:
                del doc['_id']
            logs.append(LogEntry(**doc))
        except Exception as e:
            print(f"Erro ao processar log: {e}")
            continue
    return logs

def get_logs_by_api(apiId: str) -> List[LogEntry]:
    docs = logs_collection.find({"apiId": apiId})
    logs = []
    for doc in docs:
        try:
            # Remover _id do MongoDB se presente
            if '_id' in doc:
                del doc['_id']
            logs.append(LogEntry(**doc))
        except Exception as e:
            print(f"Erro ao processar log: {e}")
            continue
    return logs

def clear_logs():
    """Limpa todos os logs (útil para testes)"""
    logs_collection.delete_many({})
    print("Logs limpos com sucesso!")
