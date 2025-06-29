#!/usr/bin/env python3
"""
Benchmark script for nano-vLLM
Compares performance against original vLLM
"""

import time
import random
import argparse
from typing import List
import torch
from nanovllm import LLM, SamplingParams

class PerformanceBenchmark:
    def __init__(self, model_path: str, num_requests: int = 256):
        self.model_path = model_path
        self.num_requests = num_requests
        self.nano_llm = None
        
    def setup_models(self):
        """Initialize models for benchmarking"""
        print("🔧 Setting up nano-vLLM...")
        self.nano_llm = LLM(
            self.model_path,
            enforce_eager=True,
            tensor_parallel_size=1
        )
        
    def generate_test_data(self) -> List[str]:
        """Generate test prompts with varying lengths"""
        prompts = []
        base_prompts = [
            "Explain the concept of",
            "Write a story about", 
            "Describe the process of",
            "What are the benefits of",
            "How does technology impact"
        ]
        
        topics = [
            "artificial intelligence", "quantum computing", "climate change",
            "renewable energy", "space exploration", "genetic engineering",
            "blockchain technology", "virtual reality", "machine learning"
        ]
        
        for i in range(self.num_requests):
            # Random input length between 100-1024 tokens (approx)
            base = random.choice(base_prompts)
            topic = random.choice(topics)
            
            # Add random context to vary input length
            context_words = random.randint(20, 200)
            context = " ".join(["context"] * context_words)
            
            prompt = f"{base} {topic}. {context}"
            prompts.append(prompt)
            
        return prompts
        
    def benchmark_nano_vllm(self, prompts: List[str]) -> dict:
        """Benchmark nano-vLLM performance"""
        print(f"🚀 Benchmarking nano-vLLM with {len(prompts)} requests...")
        
        # Random output length between 100-1024 tokens
        sampling_params = SamplingParams(
            temperature=0.6,
            max_tokens=random.randint(100, 1024),
            top_k=50,
            top_p=0.9
        )
        
        # Start timing
        start_time = time.time()
        
        # Generate responses
        outputs = self.nano_llm.generate(prompts, sampling_params)
        
        # End timing
        end_time = time.time()
        
        # Calculate metrics
        total_time = end_time - start_time
        total_tokens = sum(len(output.get('text', '').split()) for output in outputs)
        throughput = total_tokens / total_time
        
        return {
            'engine': 'Nano-vLLM',
            'total_tokens': total_tokens,
            'total_time': total_time,
            'throughput': throughput,
            'num_requests': len(prompts)
        }
        
    def run_benchmark(self):
        """Run complete benchmark suite"""
        print("=" * 60)
        print("🔥 nano-vLLM Performance Benchmark")
        print("=" * 60)
        
        # Setup
        self.setup_models()
        
        # Generate test data
        print(f"📊 Generating {self.num_requests} test prompts...")
        prompts = self.generate_test_data()
        
        # Run benchmark
        results = self.benchmark_nano_vllm(prompts)
        
        # Display results
        self.display_results(results)
        
    def display_results(self, results: dict):
        """Display benchmark results"""
        print("\n" + "=" * 60)
        print("📈 BENCHMARK RESULTS")
        print("=" * 60)
        
        print(f"Engine: {results['engine']}")
        print(f"Total Requests: {results['num_requests']}")
        print(f"Total Tokens: {results['total_tokens']:,}")
        print(f"Total Time: {results['total_time']:.2f}s")
        print(f"Throughput: {results['throughput']:.2f} tokens/s")
        
        # Expected baseline (from original benchmark)
        baseline_throughput = 1314.65  # tokens/s
        improvement = ((results['throughput'] - baseline_throughput) / baseline_throughput) * 100
        
        print(f"Baseline Comparison: {improvement:+.2f}%")
        
        if improvement > 0:
            print("🎉 Performance improved vs baseline!")
        else:
            print("📉 Performance below baseline")

def main():
    parser = argparse.ArgumentParser(description='nano-vLLM Benchmark')
    parser.add_argument(
        '--model', 
        type=str, 
        default='Qwen/Qwen3-0.6B',
        help='Model path for benchmarking'
    )
    parser.add_argument(
        '--requests', 
        type=int, 
        default=256,
        help='Number of requests to benchmark'
    )
    
    args = parser.parse_args()
    
    # Check GPU availability
    if not torch.cuda.is_available():
        print("⚠️  Warning: CUDA not available, running on CPU")
    else:
        gpu_name = torch.cuda.get_device_name(0)
        print(f"🎮 GPU: {gpu_name}")
    
    # Run benchmark
    benchmark = PerformanceBenchmark(args.model, args.requests)
    benchmark.run_benchmark()

if __name__ == "__main__":
    main()
