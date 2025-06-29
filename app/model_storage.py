"""
Módulo para gerenciar armazenamento e externalização de modelos treinados
"""

import pickle
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import numpy as np
import pandas as pd
from pathlib import Path

# Scikit-learn imports
from sklearn.preprocessing import StandardScaler, LabelEncoder

# PyOD imports
from pyod.models.iforest import IForest
from pyod.models.lof import LOF
from pyod.models.cblof import CBLOF
from pyod.models.knn import KNN
from pyod.models.ocsvm import OCSVM

class ModelStorage:
    """Gerencia o armazenamento e carregamento de modelos treinados"""
    
    def __init__(self, models_dir: str = "models"):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(exist_ok=True)
        
        # Estrutura de armazenamento
        self.model_files = {
            'iforest': 'iforest_model.pkl',
            'lof': 'lof_model.pkl',
            'knn': 'knn_model.pkl',
            'ocsvm': 'ocsvm_model.pkl',
            'cblof': 'cblof_model.pkl'
        }
        
        self.preprocessor_file = 'preprocessors.pkl'
        self.metadata_file = 'model_metadata.json'
    
    def save_model(self, model_name: str, model, scaler: StandardScaler, 
                   label_encoders: Dict, metadata: Dict) -> bool:
        """
        Salva um modelo treinado com seus preprocessadores
        
        Args:
            model_name: Nome do modelo (iforest, lof, etc.)
            model: Modelo PyOD treinado
            scaler: StandardScaler treinado
            label_encoders: Dicionário de LabelEncoders
            metadata: Metadados do treinamento
        """
        try:
            # Salvar modelo
            model_path = self.models_dir / self.model_files[model_name]
            with open(model_path, 'wb') as f:
                pickle.dump(model, f)
            
            # Salvar preprocessadores
            preprocessor_path = self.models_dir / f"{model_name}_{self.preprocessor_file}"
            preprocessors = {
                'scaler': scaler,
                'label_encoders': label_encoders
            }
            with open(preprocessor_path, 'wb') as f:
                pickle.dump(preprocessors, f)
            
            # Salvar metadados
            metadata_path = self.models_dir / f"{model_name}_{self.metadata_file}"
            metadata['saved_at'] = datetime.now().isoformat()
            metadata['model_name'] = model_name
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2, default=str)
            
            print(f"✅ Modelo {model_name} salvo com sucesso!")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao salvar modelo {model_name}: {e}")
            return False
    
    def load_model(self, model_name: str) -> Optional[Dict]:
        """
        Carrega um modelo treinado
        
        Returns:
            Dict com 'model', 'scaler', 'label_encoders', 'metadata' ou None se erro
        """
        try:
            # Carregar modelo
            model_path = self.models_dir / self.model_files[model_name]
            if not model_path.exists():
                print(f"❌ Modelo {model_name} não encontrado")
                return None
            
            with open(model_path, 'rb') as f:
                model = pickle.load(f)
            
            # Carregar preprocessadores
            preprocessor_path = self.models_dir / f"{model_name}_{self.preprocessor_file}"
            with open(preprocessor_path, 'rb') as f:
                preprocessors = pickle.load(f)
            
            # Carregar metadados
            metadata_path = self.models_dir / f"{model_name}_{self.metadata_file}"
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            return {
                'model': model,
                'scaler': preprocessors['scaler'],
                'label_encoders': preprocessors['label_encoders'],
                'metadata': metadata
            }
            
        except Exception as e:
            print(f"❌ Erro ao carregar modelo {model_name}: {e}")
            return None
    
    def list_available_models(self) -> List[Dict]:
        """Lista todos os modelos disponíveis"""
        available_models = []
        
        for model_name, filename in self.model_files.items():
            model_path = self.models_dir / filename
            metadata_path = self.models_dir / f"{model_name}_{self.metadata_file}"
            
            if model_path.exists() and metadata_path.exists():
                try:
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                    
                    available_models.append({
                        'name': model_name,
                        'filename': filename,
                        'metadata': metadata
                    })
                except Exception as e:
                    print(f"Erro ao ler metadados de {model_name}: {e}")
        
        return available_models
    
    def delete_model(self, model_name: str) -> bool:
        """Remove um modelo salvo"""
        try:
            files_to_delete = [
                self.model_files[model_name],
                f"{model_name}_{self.preprocessor_file}",
                f"{model_name}_{self.metadata_file}"
            ]
            
            for filename in files_to_delete:
                file_path = self.models_dir / filename
                if file_path.exists():
                    file_path.unlink()
            
            print(f"✅ Modelo {model_name} removido com sucesso!")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao remover modelo {model_name}: {e}")
            return False
    
    def export_model(self, model_name: str, export_path: str) -> bool:
        """
        Exporta um modelo para um arquivo externo
        
        Args:
            model_name: Nome do modelo
            export_path: Caminho para salvar o arquivo exportado
        """
        try:
            model_data = self.load_model(model_name)
            if not model_data:
                return False
            
            # Criar pacote de exportação
            export_package = {
                'model_name': model_name,
                'exported_at': datetime.now().isoformat(),
                'model': model_data['model'],
                'scaler': model_data['scaler'],
                'label_encoders': model_data['label_encoders'],
                'metadata': model_data['metadata']
            }
            
            # Salvar arquivo exportado
            with open(export_path, 'wb') as f:
                pickle.dump(export_package, f)
            
            print(f"✅ Modelo {model_name} exportado para {export_path}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao exportar modelo {model_name}: {e}")
            return False
    
    def import_model(self, import_path: str) -> bool:
        """
        Importa um modelo de um arquivo externo
        
        Args:
            import_path: Caminho do arquivo a ser importado
        """
        try:
            with open(import_path, 'rb') as f:
                import_package = pickle.load(f)
            
            model_name = import_package['model_name']
            
            # Salvar modelo importado
            success = self.save_model(
                model_name=model_name,
                model=import_package['model'],
                scaler=import_package['scaler'],
                label_encoders=import_package['label_encoders'],
                metadata=import_package['metadata']
            )
            
            if success:
                print(f"✅ Modelo {model_name} importado com sucesso!")
            
            return success
            
        except Exception as e:
            print(f"❌ Erro ao importar modelo: {e}")
            return False

# Instância global
model_storage = ModelStorage()

def save_trained_models(models: Dict, scaler: StandardScaler, 
                       label_encoders: Dict, metadata: Dict) -> Dict:
    """
    Salva todos os modelos treinados
    
    Args:
        models: Dicionário com modelos treinados
        scaler: StandardScaler treinado
        label_encoders: Dicionário de LabelEncoders
        metadata: Metadados do treinamento
    
    Returns:
        Dict com status de salvamento de cada modelo
    """
    results = {}
    
    for model_name, model in models.items():
        if hasattr(model, 'fit'):  # Verificar se é um modelo treinado
            success = model_storage.save_model(
                model_name=model_name,
                model=model,
                scaler=scaler,
                label_encoders=label_encoders,
                metadata=metadata
            )
            results[model_name] = "salvo" if success else "erro"
        else:
            results[model_name] = "não treinado"
    
    return results

def load_trained_model(model_name: str) -> Optional[Dict]:
    """
    Carrega um modelo treinado específico
    
    Args:
        model_name: Nome do modelo a ser carregado
    
    Returns:
        Dict com modelo e preprocessadores ou None
    """
    return model_storage.load_model(model_name)

def get_available_models() -> List[Dict]:
    """Retorna lista de modelos disponíveis"""
    return model_storage.list_available_models()

def export_trained_model(model_name: str, export_path: str) -> bool:
    """Exporta um modelo treinado"""
    return model_storage.export_model(model_name, export_path)

def import_trained_model(import_path: str) -> bool:
    """Importa um modelo treinado"""
    return model_storage.import_model(import_path) 