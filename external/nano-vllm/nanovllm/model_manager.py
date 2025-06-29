"""
Model management utilities for nano-vLLM
Handles model loading, unloading, and metadata
"""

import os
import json
import torch
from typing import Dict, List, Any, Optional
from transformers import AutoConfig

class ModelInfo:
    """Information about a loaded model"""
    
    def __init__(self, model_path: str, config: dict):
        self.model_path = model_path
        self.config = config
        self.load_time = None
        self.memory_usage = 0
        
class ModelManager:
    """
    Manages multiple models and their lifecycle
    
    Features:
    - Model loading/unloading
    - Memory management  
    - Model metadata tracking
    - Hot-swapping support
    """
    
    def __init__(self):
        self.loaded_models: Dict[str, ModelInfo] = {}
        self.model_configs: Dict[str, dict] = {}
        
    def load_model(self, model_path: str, **kwargs) -> ModelInfo:
        """Load a model and return model info"""
        if model_path in self.loaded_models:
            return self.loaded_models[model_path]
            
        print(f"📥 Loading model: {model_path}")
        
        # Load config
        try:
            config = AutoConfig.from_pretrained(model_path)
            config_dict = config.to_dict()
        except Exception as e:
            print(f"⚠️  Could not load config: {e}")
            config_dict = {}
            
        # Create model info
        model_info = ModelInfo(model_path, config_dict)
        
        # Store in registry
        self.loaded_models[model_path] = model_info
        
        return model_info
        
    def unload_model(self, model_path: str) -> bool:
        """Unload a model to free memory"""
        if model_path not in self.loaded_models:
            return False
            
        print(f"🗑️  Unloading model: {model_path}")
        del self.loaded_models[model_path]
        
        # Force garbage collection
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            
        return True
        
    def list_models(self) -> List[ModelInfo]:
        """List all loaded models"""
        return list(self.loaded_models.values())
        
    def get_model_info(self, model_path: str) -> Optional[ModelInfo]:
        """Get information about a specific model"""
        return self.loaded_models.get(model_path)
        
    def get_memory_usage(self) -> Dict[str, float]:
        """Get memory usage statistics"""
        if not torch.cuda.is_available():
            return {'cpu_memory': 0, 'gpu_memory': 0}
            
        gpu_memory = torch.cuda.memory_allocated() / 1024**3  # GB
        gpu_cached = torch.cuda.memory_reserved() / 1024**3   # GB
        
        return {
            'gpu_allocated': gpu_memory,
            'gpu_cached': gpu_cached,
            'gpu_total': torch.cuda.get_device_properties(0).total_memory / 1024**3
        }
        
    def validate_model_path(self, model_path: str) -> bool:
        """Validate if a model path exists and is accessible"""
        if os.path.isdir(model_path):
            # Local model directory
            required_files = ['config.json']
            return all(
                os.path.exists(os.path.join(model_path, f)) 
                for f in required_files
            )
        else:
            # Assume HuggingFace model ID
            try:
                AutoConfig.from_pretrained(model_path)
                return True
            except:
                return False
                
    def get_model_statistics(self) -> Dict[str, Any]:
        """Get comprehensive model statistics"""
        stats = {
            'total_models': len(self.loaded_models),
            'models': [],
            'memory': self.get_memory_usage()
        }
        
        for model_path, model_info in self.loaded_models.items():
            model_stats = {
                'path': model_path,
                'config': model_info.config,
                'parameters': model_info.config.get('total_params', 'unknown'),
                'vocab_size': model_info.config.get('vocab_size', 'unknown'),
                'hidden_size': model_info.config.get('hidden_size', 'unknown'),
                'num_layers': model_info.config.get('num_hidden_layers', 'unknown')
            }
            stats['models'].append(model_stats)
            
        return stats
