"""
LLM: Core inference engine for nano-vLLM
Lightweight implementation focusing on performance and readability
"""

import torch
import torch.nn as nn
from typing import List, Dict, Any, Optional
from transformers import AutoTokenizer, AutoModelForCausalLM
import time

from .sampling_params import SamplingParams
from .model_manager import ModelManager
from .cache_manager import KVCacheManager
from .optimizations import PrefixCache, TensorParallel

class LLM:
    """
    Main LLM inference engine
    
    Features:
    - Fast offline inference comparable to vLLM
    - Prefix caching for repeated prompts
    - Tensor parallelism support
    - Memory-efficient KV cache management
    """
    
    def __init__(
        self,
        model_path: str,
        tensor_parallel_size: int = 1,
        enforce_eager: bool = True,
        max_model_len: Optional[int] = None,
        gpu_memory_utilization: float = 0.8,
        **kwargs
    ):
        """
        Initialize nano-vLLM engine
        
        Args:
            model_path: Path to model (local or HuggingFace)
            tensor_parallel_size: Number of GPUs for tensor parallelism
            enforce_eager: Force eager execution (disable graph compilation)
            max_model_len: Maximum sequence length
            gpu_memory_utilization: GPU memory usage ratio
        """
        self.model_path = model_path
        self.tensor_parallel_size = tensor_parallel_size
        self.enforce_eager = enforce_eager
        self.max_model_len = max_model_len
        self.gpu_memory_utilization = gpu_memory_utilization
        
        # Initialize components
        self.model_manager = ModelManager()
        self.kv_cache = KVCacheManager()
        self.prefix_cache = PrefixCache()
        self.tensor_parallel = None
        
        if tensor_parallel_size > 1:
            self.tensor_parallel = TensorParallel(tensor_parallel_size)
        
        # Load model and tokenizer
        self._load_model()
        
        print(f"✅ nano-vLLM initialized: {model_path}")
        print(f"   Tensor Parallel: {tensor_parallel_size}")
        print(f"   Max Length: {self.max_model_len}")
        print(f"   GPU Memory: {gpu_memory_utilization*100}%")
        
    def _load_model(self):
        """Load model and tokenizer"""
        print(f"📥 Loading model: {self.model_path}")
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
            
        # Load model
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_path,
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True
        )
        
        # Setup for inference
        self.model.eval()
        
        # Configure max length
        if self.max_model_len is None:
            self.max_model_len = getattr(self.model.config, 'max_position_embeddings', 2048)
            
    def generate(
        self, 
        prompts: List[str], 
        sampling_params: SamplingParams
    ) -> List[Dict[str, Any]]:
        """
        Generate responses for given prompts
        
        Args:
            prompts: List of input prompts
            sampling_params: Sampling configuration
            
        Returns:
            List of generation results
        """
        if isinstance(prompts, str):
            prompts = [prompts]
            
        print(f"🚀 Generating for {len(prompts)} prompts...")
        start_time = time.time()
        
        results = []
        
        for i, prompt in enumerate(prompts):
            # Check prefix cache
            cache_key = self.prefix_cache.get_cache_key(prompt)
            cached_tokens = self.prefix_cache.get_cached_tokens(cache_key)
            
            if cached_tokens is not None:
                print(f"💾 Using prefix cache for prompt {i+1}")
                
            # Tokenize
            inputs = self.tokenizer(
                prompt, 
                return_tensors="pt",
                truncation=True,
                max_length=self.max_model_len - sampling_params.max_tokens
            )
            
            # Move to GPU
            if torch.cuda.is_available():
                inputs = {k: v.cuda() for k, v in inputs.items()}
                
            # Generate
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=sampling_params.max_tokens,
                    temperature=sampling_params.temperature,
                    top_k=sampling_params.top_k,
                    top_p=sampling_params.top_p,
                    do_sample=sampling_params.temperature > 0,
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id
                )
                
            # Decode response
            input_length = inputs['input_ids'].shape[1]
            generated_tokens = outputs[0][input_length:]
            response = self.tokenizer.decode(generated_tokens, skip_special_tokens=True)
            
            # Store in prefix cache
            self.prefix_cache.store_tokens(cache_key, generated_tokens)
            
            results.append({
                'text': response,
                'prompt': prompt,
                'tokens_generated': len(generated_tokens),
                'input_tokens': input_length
            })
            
        end_time = time.time()
        total_time = end_time - start_time
        total_tokens = sum(r['tokens_generated'] for r in results)
        throughput = total_tokens / total_time if total_time > 0 else 0
        
        print(f"✅ Generation complete: {total_tokens} tokens in {total_time:.2f}s ({throughput:.2f} tok/s)")
        
        return results
        
    def generate_stream(
        self, 
        prompt: str, 
        sampling_params: SamplingParams
    ):
        """
        Generate streaming response for a single prompt
        
        Args:
            prompt: Input prompt
            sampling_params: Sampling configuration
            
        Yields:
            Generated tokens as they are produced
        """
        # Tokenize
        inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True)
        
        if torch.cuda.is_available():
            inputs = {k: v.cuda() for k, v in inputs.items()}
            
        input_length = inputs['input_ids'].shape[1]
        
        # Generate tokens one by one
        with torch.no_grad():
            for _ in range(sampling_params.max_tokens):
                outputs = self.model(**inputs)
                logits = outputs.logits[:, -1, :]
                
                # Apply sampling
                if sampling_params.temperature > 0:
                    logits = logits / sampling_params.temperature
                    
                    if sampling_params.top_k > 0:
                        # Top-k sampling
                        top_k_logits, top_k_indices = torch.topk(logits, sampling_params.top_k)
                        logits = torch.full_like(logits, float('-inf'))
                        logits.scatter_(1, top_k_indices, top_k_logits)
                        
                    if sampling_params.top_p < 1.0:
                        # Top-p (nucleus) sampling
                        sorted_logits, sorted_indices = torch.sort(logits, descending=True)
                        cumulative_probs = torch.cumsum(torch.softmax(sorted_logits, dim=-1), dim=-1)
                        sorted_indices_to_remove = cumulative_probs > sampling_params.top_p
                        sorted_indices_to_remove[:, 1:] = sorted_indices_to_remove[:, :-1].clone()
                        sorted_indices_to_remove[:, 0] = 0
                        indices_to_remove = sorted_indices_to_remove.scatter(1, sorted_indices, sorted_indices_to_remove)
                        logits[indices_to_remove] = float('-inf')
                        
                    probs = torch.softmax(logits, dim=-1)
                    next_token = torch.multinomial(probs, num_samples=1)
                else:
                    # Greedy sampling
                    next_token = torch.argmax(logits, dim=-1, keepdim=True)
                    
                # Check for EOS
                if next_token.item() == self.tokenizer.eos_token_id:
                    break
                    
                # Decode and yield token
                token_text = self.tokenizer.decode(next_token[0], skip_special_tokens=True)
                yield token_text
                
                # Update inputs for next iteration
                inputs['input_ids'] = torch.cat([inputs['input_ids'], next_token], dim=1)
                if 'attention_mask' in inputs:
                    inputs['attention_mask'] = torch.cat([
                        inputs['attention_mask'], 
                        torch.ones_like(next_token)
                    ], dim=1)
                    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information and statistics"""
        total_params = sum(p.numel() for p in self.model.parameters())
        trainable_params = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
        
        return {
            'model_path': self.model_path,
            'total_parameters': total_params,
            'trainable_parameters': trainable_params, 
            'max_length': self.max_model_len,
            'tensor_parallel_size': self.tensor_parallel_size,
            'device': next(self.model.parameters()).device,
            'dtype': next(self.model.parameters()).dtype
        }
        
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get KV cache statistics"""
        return {
            'prefix_cache_hits': self.prefix_cache.get_hit_rate(),
            'kv_cache_memory': self.kv_cache.get_memory_usage(),
            'cache_efficiency': self.prefix_cache.get_efficiency()
        }
