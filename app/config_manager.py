"""
Gerenciador de Configurações do Sistema
Permite ajustar parâmetros como threshold de detecção de anomalias
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from pymongo import MongoClient

class ConfigManager:
    def __init__(self):
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client['api_logs']
        self.config_collection = self.db.config
        
        # Configurações padrão
        self.default_config = {
            "ml_detection": {
                "threshold": 0.12,
                "contamination": 0.1,
                "model_preference": "iforest"
            },
            "feedback": {
                "auto_retrain": True,
                "retrain_interval_hours": 24,
                "false_positive_weight": 5
            },
            "monitoring": {
                "alert_threshold": 10,
                "notification_enabled": False,
                "log_retention_days": 30
            },
            "ui": {
                "theme": "light",
                "language": "pt-BR",
                "refresh_interval_seconds": 30
            }
        }
        
        # Inicializar configurações se não existirem
        self._initialize_config()
    
    def _initialize_config(self):
        """Inicializa configurações padrão se não existirem"""
        try:
            existing_config = self.config_collection.find_one({"config_type": "system"})
            if not existing_config:
                config_doc = {
                    "config_type": "system",
                    "config": self.default_config,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now(),
                    "version": "1.0"
                }
                self.config_collection.insert_one(config_doc)
                print("✅ Configurações padrão inicializadas")
        except Exception as e:
            print(f"❌ Erro ao inicializar configurações: {e}")
    
    def get_config(self, section: str = None) -> Dict[str, Any]:
        """
        Obtém configurações do sistema
        
        Args:
            section: Seção específica (ex: 'ml_detection', 'feedback')
        
        Returns:
            Dict com configurações
        """
        try:
            config_doc = self.config_collection.find_one({"config_type": "system"})
            if not config_doc:
                return self.default_config
            
            config = config_doc.get("config", self.default_config)
            
            if section:
                return config.get(section, {})
            
            return config
            
        except Exception as e:
            print(f"❌ Erro ao obter configurações: {e}")
            return self.default_config if not section else {}
    
    def update_config(self, section: str, key: str, value: Any) -> Dict[str, Any]:
        """
        Atualiza uma configuração específica
        
        Args:
            section: Seção da configuração (ex: 'ml_detection')
            key: Chave da configuração (ex: 'threshold')
            value: Novo valor
        
        Returns:
            Dict com status da operação
        """
        try:
            # Obter configuração atual
            config_doc = self.config_collection.find_one({"config_type": "system"})
            if not config_doc:
                return {"error": "Configuração não encontrada"}
            
            config = config_doc.get("config", self.default_config)
            
            # Atualizar valor
            if section not in config:
                config[section] = {}
            
            config[section][key] = value
            
            # Salvar no banco
            self.config_collection.update_one(
                {"config_type": "system"},
                {
                    "$set": {
                        "config": config,
                        "updated_at": datetime.now()
                    }
                }
            )
            
            return {
                "success": True,
                "message": f"Configuração {section}.{key} atualizada para {value}",
                "updated_config": config[section]
            }
            
        except Exception as e:
            return {"error": f"Erro ao atualizar configuração: {str(e)}"}
    
    def update_section(self, section: str, section_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Atualiza uma seção inteira de configurações
        
        Args:
            section: Seção da configuração
            section_config: Nova configuração da seção
        
        Returns:
            Dict com status da operação
        """
        try:
            # Obter configuração atual
            config_doc = self.config_collection.find_one({"config_type": "system"})
            if not config_doc:
                return {"error": "Configuração não encontrada"}
            
            config = config_doc.get("config", self.default_config)
            
            # Atualizar seção
            config[section] = section_config
            
            # Salvar no banco
            self.config_collection.update_one(
                {"config_type": "system"},
                {
                    "$set": {
                        "config": config,
                        "updated_at": datetime.now()
                    }
                }
            )
            
            return {
                "success": True,
                "message": f"Seção {section} atualizada com sucesso",
                "updated_config": config[section]
            }
            
        except Exception as e:
            return {"error": f"Erro ao atualizar seção: {str(e)}"}
    
    def reset_to_default(self, section: str = None) -> Dict[str, Any]:
        """
        Reseta configurações para valores padrão
        
        Args:
            section: Seção específica para resetar (None para todas)
        
        Returns:
            Dict com status da operação
        """
        try:
            if section:
                # Resetar seção específica
                config_doc = self.config_collection.find_one({"config_type": "system"})
                if not config_doc:
                    return {"error": "Configuração não encontrada"}
                
                config = config_doc.get("config", self.default_config)
                if section in self.default_config:
                    config[section] = self.default_config[section]
                
                self.config_collection.update_one(
                    {"config_type": "system"},
                    {
                        "$set": {
                            "config": config,
                            "updated_at": datetime.now()
                        }
                    }
                )
                
                return {
                    "success": True,
                    "message": f"Seção {section} resetada para valores padrão",
                    "reset_config": config[section]
                }
            else:
                # Resetar todas as configurações
                config_doc = {
                    "config_type": "system",
                    "config": self.default_config,
                    "updated_at": datetime.now(),
                    "version": "1.0"
                }
                
                self.config_collection.replace_one(
                    {"config_type": "system"},
                    config_doc
                )
                
                return {
                    "success": True,
                    "message": "Todas as configurações resetadas para valores padrão",
                    "reset_config": self.default_config
                }
                
        except Exception as e:
            return {"error": f"Erro ao resetar configurações: {str(e)}"}
    
    def get_config_history(self, limit: int = 10) -> Dict[str, Any]:
        """
        Obtém histórico de alterações de configuração
        
        Args:
            limit: Limite de registros
        
        Returns:
            Dict com histórico
        """
        try:
            # Por enquanto, retorna apenas a configuração atual
            # Em uma implementação mais avançada, você poderia manter um histórico
            config_doc = self.config_collection.find_one({"config_type": "system"})
            
            if not config_doc:
                return {"history": []}
            
            return {
                "history": [{
                    "timestamp": config_doc.get("updated_at", datetime.now()).isoformat(),
                    "version": config_doc.get("version", "1.0"),
                    "config": config_doc.get("config", {})
                }]
            }
            
        except Exception as e:
            return {"error": f"Erro ao obter histórico: {str(e)}"}

# Instância global
config_manager = ConfigManager() 