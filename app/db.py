from pymongo import MongoClient
from pymongo.collection import Collection

client = MongoClient("mongodb://localhost:27017")
db = client["api_logs_db"]
logs_collection: Collection = db["logs"]

# Índices recomendados
logs_collection.create_index("timestamp")
logs_collection.create_index("apiId")
logs_collection.create_index("clientId")
logs_collection.create_index("status")
