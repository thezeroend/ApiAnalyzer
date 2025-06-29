from collections import defaultdict, Counter
from datetime import datetime, timedelta
from typing import Dict, List, Set
from .models import LogEntry
from .storage import get_logs_by_api, get_all_logs
import ipaddress

def basic_stats(apiId: str):
    logs: List[LogEntry] = get_logs_by_api(apiId)
    total = len(logs)

    stats = {
        "total_logs": total,
        "status_counts": Counter([l.status for l in logs]),
        "requests_by_client": Counter([l.clientId for l in logs]),
        "requests_by_path": Counter([l.path for l in logs]),
        "requests_by_ip": Counter([l.ip for l in logs]),
    }

    return stats

def detect_anomalies(apiId: str, threshold=0.5):
    logs: List[LogEntry] = get_logs_by_api(apiId)
    errors_by_client = defaultdict(int)
    total_by_client = defaultdict(int)

    for log in logs:
        total_by_client[log.clientId] += 1
        if log.status >= 400:
            errors_by_client[log.clientId] += 1

    anomalous_clients = {}
    for client, total in total_by_client.items():
        error_rate = errors_by_client[client] / total
        if error_rate > threshold:
            anomalous_clients[client] = {
                "error_rate": error_rate,
                "total_requests": total,
                "errors": errors_by_client[client]
            }

    return anomalous_clients

def error_rate_by_minute(apiId: str) -> Dict[str, Dict[str, int]]:
    logs = get_logs_by_api(apiId)
    stats = defaultdict(lambda: {"total": 0, "errors": 0})

    for log in logs:
        minute_key = log.timestamp.strftime("%Y-%m-%d %H:%M")
        stats[minute_key]["total"] += 1
        if log.status >= 400:
            stats[minute_key]["errors"] += 1

    return dict(stats)

def detect_ip_anomalies(apiId: str = None, hours_back: int = 24) -> Dict:
    """
    Detecta anomalias baseadas em IPs suspeitos de forma simplificada
    """
    try:
        # Obter logs (todos ou por API específica)
        if apiId:
            logs = get_logs_by_api(apiId)
        else:
            logs = get_all_logs()
        
        if not logs:
            return {
                "new_ips": {},
                "suspicious_activity": {},
                "multiple_ips": {},
                "summary": {
                    "total_clients_analyzed": 0,
                    "clients_with_new_ips": 0,
                    "clients_with_suspicious_activity": 0,
                    "total_anomalies": 0
                }
            }
        
        # Filtrar logs das últimas N horas
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        recent_logs = [log for log in logs if log.timestamp >= cutoff_time]
        
        # Agrupar por cliente
        client_ips = defaultdict(set)
        client_recent_ips = defaultdict(set)
        client_recent_activity = defaultdict(list)
        
        # Processar todos os logs
        for log in logs:
            client_ips[log.clientId].add(log.ip)
            if log.timestamp >= cutoff_time:
                client_recent_ips[log.clientId].add(log.ip)
                client_recent_activity[log.clientId].append(log)
        
        anomalies = {
            "new_ips": {},
            "suspicious_activity": {},
            "multiple_ips": {},
            "summary": {
                "total_clients_analyzed": len(client_ips),
                "clients_with_new_ips": 0,
                "clients_with_suspicious_activity": 0,
                "total_anomalies": 0
            }
        }
        
        for client_id, recent_ips in client_recent_ips.items():
            all_known_ips = client_ips[client_id]
            recent_activity = client_recent_activity[client_id]
            
            # Detectar IPs novos (se o cliente tem histórico)
            if len(all_known_ips) > len(recent_ips):
                historical_ips = all_known_ips - recent_ips
                new_ips = recent_ips - historical_ips
                if new_ips:
                    anomalies["new_ips"][client_id] = {
                        "new_ips": list(new_ips),
                        "known_ips": list(historical_ips),
                        "risk_level": "medium" if len(new_ips) == 1 else "high"
                    }
                    anomalies["summary"]["clients_with_new_ips"] += 1
            
            # Detectar múltiplos IPs em pouco tempo
            if len(recent_ips) > 2:  # Mais de 2 IPs diferentes
                anomalies["multiple_ips"][client_id] = {
                    "recent_ips": list(recent_ips),
                    "count": len(recent_ips),
                    "risk_level": "high" if len(recent_ips) > 4 else "medium"
                }
            
            # Detectar atividade suspeita
            if len(recent_activity) >= 3:  # Pelo menos 3 requests para análise
                suspicious_patterns = detect_suspicious_patterns_simple(client_id, recent_activity)
                if suspicious_patterns:
                    anomalies["suspicious_activity"][client_id] = suspicious_patterns
                    anomalies["summary"]["clients_with_suspicious_activity"] += 1
        
        # Calcular totais
        anomalies["summary"]["total_anomalies"] = (
            len(anomalies["new_ips"]) + 
            len(anomalies["multiple_ips"]) + 
            len(anomalies["suspicious_activity"])
        )
        
        return anomalies
        
    except Exception as e:
        print(f"Erro na detecção de anomalias: {e}")
        return {
            "new_ips": {},
            "suspicious_activity": {},
            "multiple_ips": {},
            "summary": {
                "total_clients_analyzed": 0,
                "clients_with_new_ips": 0,
                "clients_with_suspicious_activity": 0,
                "total_anomalies": 0,
                "error": str(e)
            }
        }

def detect_suspicious_patterns_simple(client_id: str, logs: List[LogEntry]) -> Dict:
    """Versão simplificada para detectar padrões suspeitos"""
    if len(logs) < 3:
        return None
    
    patterns = {}
    
    # Verificar taxa de erro
    error_logs = [log for log in logs if log.status >= 400]
    error_rate = len(error_logs) / len(logs)
    
    if error_rate > 0.2:  # Mais de 20% de erros
        patterns["high_error_rate"] = {
            "error_rate": error_rate,
            "total_requests": len(logs),
            "errors": len(error_logs)
        }
    
    # Verificar volume de requests
    if len(logs) > 20:  # Muitas requisições
        patterns["high_request_volume"] = {
            "requests_count": len(logs),
            "time_span_hours": 24
        }
    
    # Verificar paths sensíveis
    sensitive_paths = ["/admin", "/login", "/auth", "/config", "/debug", "/test"]
    sensitive_attempts = [log for log in logs if any(path in log.path.lower() for path in sensitive_paths)]
    
    if sensitive_attempts:
        patterns["sensitive_path_access"] = {
            "attempts": len(sensitive_attempts),
            "paths": list(set([log.path for log in sensitive_attempts]))
        }
    
    return patterns if patterns else None

def get_ip_risk_score(ip: str) -> Dict:
    """Calcula um score de risco para um IP"""
    try:
        ip_obj = ipaddress.ip_address(ip)
        
        risk_factors = {
            "is_private": ip_obj.is_private,
            "is_loopback": ip_obj.is_loopback,
            "is_multicast": ip_obj.is_multicast,
            "is_reserved": ip_obj.is_reserved,
            "is_unspecified": ip_obj.is_unspecified
        }
        
        score = 0
        if not risk_factors["is_private"]:
            score += 20
        
        if risk_factors["is_loopback"]:
            score += 50
        
        if risk_factors["is_multicast"]:
            score += 30
        
        if risk_factors["is_reserved"]:
            score += 40
        
        return {
            "ip": ip,
            "risk_score": score,
            "risk_level": "low" if score < 20 else "medium" if score < 40 else "high",
            "factors": risk_factors
        }
    except ValueError:
        return {
            "ip": ip,
            "risk_score": 100,
            "risk_level": "high",
            "factors": {"invalid_ip": True}
        }