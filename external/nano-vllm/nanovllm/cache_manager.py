"""
KV Cache management for nano-vLLM
Optimizes memory usage and speeds up inference
"""

import torch
from typing import Dict, Tuple, Optional
import hashlib

class KVCacheManager:
    """
    Manages Key-Value cache for transformer models
    
    Features:
    - Dynamic cache allocation
    - Memory-efficient storage
    - Cache reuse across requests
    """
    
    def __init__(self, max_cache_size: int = 1000):
        self.max_cache_size = max_cache_size
        self.cache_storage: Dict[str, Tuple[torch.Tensor, torch.Tensor]] = {}
        self.cache_usage_count: Dict[str, int] = {}
        self.total_hits = 0
        self.total_requests = 0
        
    def get_cache_key(self, input_ids: torch.Tensor) -> str:
        """Generate cache key from input token IDs"""
        # Use hash of input_ids as cache key
        ids_str = str(input_ids.cpu().tolist())
        return hashlib.md5(ids_str.encode()).hexdigest()
        
    def get_cached_kv(self, cache_key: str) -> Optional[Tuple[torch.Tensor, torch.Tensor]]:
        """Retrieve cached key-value pairs"""
        self.total_requests += 1
        
        if cache_key in self.cache_storage:
            self.total_hits += 1
            self.cache_usage_count[cache_key] += 1
            return self.cache_storage[cache_key]
            
        return None
        
    def store_kv(self, cache_key: str, key_states: torch.Tensor, value_states: torch.Tensor):
        """Store key-value pairs in cache"""
        # Check cache size limit
        if len(self.cache_storage) >= self.max_cache_size:
            self._evict_least_used()
            
        self.cache_storage[cache_key] = (key_states.clone(), value_states.clone())
        self.cache_usage_count[cache_key] = 1
        
    def _evict_least_used(self):
        """Evict least recently used cache entry"""
        if not self.cache_storage:
            return
            
        # Find least used entry
        least_used_key = min(self.cache_usage_count.items(), key=lambda x: x[1])[0]
        
        # Remove from cache
        del self.cache_storage[least_used_key]
        del self.cache_usage_count[least_used_key]
        
    def clear_cache(self):
        """Clear all cached data"""
        self.cache_storage.clear()
        self.cache_usage_count.clear()
        
        # Free GPU memory
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            
    def get_cache_stats(self) -> Dict[str, float]:
        """Get cache performance statistics"""
        hit_rate = self.total_hits / max(self.total_requests, 1)
        memory_usage = self._calculate_memory_usage()
        
        return {
            'hit_rate': hit_rate,
            'total_entries': len(self.cache_storage),
            'max_entries': self.max_cache_size,
            'memory_usage_mb': memory_usage,
            'total_hits': self.total_hits,
            'total_requests': self.total_requests
        }
        
    def _calculate_memory_usage(self) -> float:
        """Calculate memory usage of cached tensors in MB"""
        total_bytes = 0
        
        for key_tensor, value_tensor in self.cache_storage.values():
            total_bytes += key_tensor.element_size() * key_tensor.numel()
            total_bytes += value_tensor.element_size() * value_tensor.numel()
            
        return total_bytes / (1024 * 1024)  # Convert to MB
        
    def get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        return self._calculate_memory_usage()
        
    def optimize_cache(self):
        """Optimize cache by removing unused entries"""
        # Remove entries with very low usage
        min_usage_threshold = max(1, self.total_requests // 100)
        
        keys_to_remove = [
            key for key, usage in self.cache_usage_count.items()
            if usage < min_usage_threshold
        ]
        
        for key in keys_to_remove:
            if key in self.cache_storage:
                del self.cache_storage[key]
                del self.cache_usage_count[key]
                
        print(f"🧹 Cache optimized: removed {len(keys_to_remove)} entries")
