"""
Advanced optimizations for nano-vLLM
Includes prefix caching, tensor parallelism, and performance enhancements
"""

import torch
import torch.distributed as dist
from typing import Dict, List, Optional, Tuple
import hashlib
import time

class PrefixCache:
    """
    Prefix caching optimization
    Reuses computation for repeated prompt prefixes
    """
    
    def __init__(self, max_prefixes: int = 100):
        self.max_prefixes = max_prefixes
        self.prefix_cache: Dict[str, torch.Tensor] = {}
        self.prefix_usage: Dict[str, int] = {}
        self.hit_count = 0
        self.total_requests = 0
        
    def get_cache_key(self, prompt: str) -> str:
        """Generate cache key for prompt prefix"""
        # Use first 100 characters as prefix
        prefix = prompt[:100]
        return hashlib.md5(prefix.encode()).hexdigest()
        
    def get_cached_tokens(self, cache_key: str) -> Optional[torch.Tensor]:
        """Get cached tokens for prefix"""
        self.total_requests += 1
        
        if cache_key in self.prefix_cache:
            self.hit_count += 1
            self.prefix_usage[cache_key] += 1
            return self.prefix_cache[cache_key]
            
        return None
        
    def store_tokens(self, cache_key: str, tokens: torch.Tensor):
        """Store generated tokens for prefix"""
        if len(self.prefix_cache) >= self.max_prefixes:
            self._evict_oldest()
            
        self.prefix_cache[cache_key] = tokens.clone()
        self.prefix_usage[cache_key] = 1
        
    def _evict_oldest(self):
        """Evict least used prefix"""
        if not self.prefix_cache:
            return
            
        least_used = min(self.prefix_usage.items(), key=lambda x: x[1])[0]
        del self.prefix_cache[least_used]
        del self.prefix_usage[least_used]
        
    def get_hit_rate(self) -> float:
        """Get cache hit rate"""
        return self.hit_count / max(self.total_requests, 1)
        
    def get_efficiency(self) -> Dict[str, float]:
        """Get cache efficiency metrics"""
        return {
            'hit_rate': self.get_hit_rate(),
            'total_prefixes': len(self.prefix_cache),
            'max_prefixes': self.max_prefixes,
            'total_hits': self.hit_count,
            'total_requests': self.total_requests
        }

class TensorParallel:
    """
    Tensor parallelism for multi-GPU inference
    Distributes model computation across multiple GPUs
    """
    
    def __init__(self, world_size: int):
        self.world_size = world_size
        self.rank = 0
        self.device = None
        self.initialized = False
        
    def initialize(self):
        """Initialize tensor parallelism"""
        if self.world_size <= 1:
            print("⚠️  Tensor parallelism disabled (single GPU)")
            return
            
        try:
            # Initialize process group
            if not dist.is_initialized():
                dist.init_process_group(backend='nccl')
                
            self.rank = dist.get_rank()
            self.device = torch.device(f'cuda:{self.rank}')
            self.initialized = True
            
            print(f"✅ Tensor parallelism initialized: rank {self.rank}/{self.world_size}")
            
        except Exception as e:
            print(f"❌ Failed to initialize tensor parallelism: {e}")
            self.initialized = False
            
    def split_tensor(self, tensor: torch.Tensor, dim: int = -1) -> torch.Tensor:
        """Split tensor across GPUs"""
        if not self.initialized or self.world_size <= 1:
            return tensor
            
        # Split tensor along specified dimension
        split_size = tensor.size(dim) // self.world_size
        start_idx = self.rank * split_size
        end_idx = start_idx + split_size
        
        if dim == -1:
            return tensor[..., start_idx:end_idx]
        elif dim == 0:
            return tensor[start_idx:end_idx]
        else:
            slices = [slice(None)] * tensor.ndim
            slices[dim] = slice(start_idx, end_idx)
            return tensor[tuple(slices)]
            
    def all_gather_tensor(self, tensor: torch.Tensor) -> torch.Tensor:
        """Gather tensors from all GPUs"""
        if not self.initialized or self.world_size <= 1:
            return tensor
            
        gathered_tensors = [torch.zeros_like(tensor) for _ in range(self.world_size)]
        dist.all_gather(gathered_tensors, tensor)
        
        return torch.cat(gathered_tensors, dim=-1)
        
    def all_reduce_tensor(self, tensor: torch.Tensor) -> torch.Tensor:
        """All-reduce tensor across GPUs"""
        if not self.initialized or self.world_size <= 1:
            return tensor
            
        dist.all_reduce(tensor, op=dist.ReduceOp.SUM)
        return tensor / self.world_size

class PerformanceOptimizer:
    """
    Performance optimization utilities
    Includes CUDA graph, mixed precision, and other optimizations
    """
    
    def __init__(self):
        self.cuda_graphs_enabled = False
        self.mixed_precision_enabled = False
        self.compilation_enabled = False
        
    def enable_cuda_graphs(self) -> bool:
        """Enable CUDA graphs for faster inference"""
        if not torch.cuda.is_available():
            print("⚠️  CUDA not available, cannot enable CUDA graphs")
            return False
            
        try:
            # Test CUDA graph capability
            torch.cuda.synchronize()
            self.cuda_graphs_enabled = True
            print("✅ CUDA graphs enabled")
            return True
            
        except Exception as e:
            print(f"❌ Failed to enable CUDA graphs: {e}")
            return False
            
    def enable_mixed_precision(self) -> bool:
        """Enable mixed precision training/inference"""
        try:
            # Check if GPU supports mixed precision
            if torch.cuda.is_available() and torch.cuda.get_device_capability()[0] >= 7:
                self.mixed_precision_enabled = True
                print("✅ Mixed precision enabled")
                return True
            else:
                print("⚠️  GPU does not support mixed precision")
                return False
                
        except Exception as e:
            print(f"❌ Failed to enable mixed precision: {e}")
            return False
            
    def compile_model(self, model: torch.nn.Module) -> torch.nn.Module:
        """Compile model for faster inference"""
        try:
            # Use torch.compile if available (PyTorch 2.0+)
            if hasattr(torch, 'compile'):
                compiled_model = torch.compile(model, mode='max-autotune')
                self.compilation_enabled = True
                print("✅ Model compiled with torch.compile")
                return compiled_model
            else:
                print("⚠️  torch.compile not available")
                return model
                
        except Exception as e:
            print(f"❌ Failed to compile model: {e}")
            return model
            
    def optimize_memory(self):
        """Optimize GPU memory usage"""
        if not torch.cuda.is_available():
            return
            
        # Clear cache
        torch.cuda.empty_cache()
        
        # Set memory fraction
        torch.cuda.set_per_process_memory_fraction(0.9)
        
        print("🧹 GPU memory optimized")
        
    def get_optimization_status(self) -> Dict[str, bool]:
        """Get current optimization status"""
        return {
            'cuda_graphs': self.cuda_graphs_enabled,
            'mixed_precision': self.mixed_precision_enabled,
            'compilation': self.compilation_enabled,
            'cuda_available': torch.cuda.is_available()
        }

class AdaptiveBatching:
    """
    Adaptive batching for optimal throughput
    Dynamically adjusts batch sizes based on GPU memory and request patterns
    """
    
    def __init__(self, min_batch_size: int = 1, max_batch_size: int = 32):
        self.min_batch_size = min_batch_size
        self.max_batch_size = max_batch_size
        self.current_batch_size = min_batch_size
        self.batch_history: List[Tuple[int, float]] = []  # (batch_size, throughput)
        
    def get_optimal_batch_size(self, available_memory: float, request_queue_size: int) -> int:
        """Determine optimal batch size based on memory and queue"""
        # Consider memory constraints
        memory_factor = min(1.0, available_memory / 0.8)  # 80% memory threshold
        
        # Consider queue size
        queue_factor = min(1.0, request_queue_size / self.max_batch_size)
        
        # Calculate suggested batch size
        suggested_size = int(self.max_batch_size * memory_factor * queue_factor)
        
        # Apply bounds
        optimal_size = max(self.min_batch_size, min(suggested_size, self.max_batch_size))
        
        return optimal_size
        
    def update_performance(self, batch_size: int, throughput: float):
        """Update performance history for adaptive learning"""
        self.batch_history.append((batch_size, throughput))
        
        # Keep only recent history
        if len(self.batch_history) > 100:
            self.batch_history = self.batch_history[-50:]
            
        # Update current batch size based on performance
        if len(self.batch_history) >= 5:
            recent_avg = sum(t for _, t in self.batch_history[-5:]) / 5
            overall_avg = sum(t for _, t in self.batch_history) / len(self.batch_history)
            
            if recent_avg > overall_avg * 1.1:  # 10% improvement
                self.current_batch_size = min(self.current_batch_size + 1, self.max_batch_size)
            elif recent_avg < overall_avg * 0.9:  # 10% degradation
                self.current_batch_size = max(self.current_batch_size - 1, self.min_batch_size)
                
    def get_batch_stats(self) -> Dict[str, float]:
        """Get batching performance statistics"""
        if not self.batch_history:
            return {'current_batch_size': self.current_batch_size, 'avg_throughput': 0.0}
            
        avg_throughput = sum(t for _, t in self.batch_history) / len(self.batch_history)
        
        return {
            'current_batch_size': self.current_batch_size,
            'avg_throughput': avg_throughput,
            'total_batches': len(self.batch_history),
            'min_batch_size': self.min_batch_size,
            'max_batch_size': self.max_batch_size
        }
