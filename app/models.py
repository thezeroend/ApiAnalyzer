from pydantic import BaseModel
from datetime import datetime

class LogEntry(BaseModel):
    requestId: str
    clientId: str
    ip: str
    apiId: str
    path: str
    method: str
    status: int
    timestamp: datetime