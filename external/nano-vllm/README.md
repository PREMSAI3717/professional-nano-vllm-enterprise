# nano-vLLM

A lightweight vLLM implementation built from scratch in ~1,200 lines of Python code.

## 🚀 Features

- **Fast offline inference** - Comparable inference speeds to vLLM
- **Readable codebase** - Clean implementation under 1,200 lines of Python code  
- **Optimization Suite** - Prefix caching, Tensor parallelism, Torch compilation, CUDA graph, etc.

## 📊 Performance

Test Configuration:
- Hardware: RTX 4070
- Model: Qwen3-0.6B
- Total Requests: 256 sequences
- Input Length: Randomly sampled between 100–1024 tokens
- Output Length: Randomly sampled between 100–1024 tokens

Performance Results:

| Inference Engine | Output Tokens | Time (s) | Throughput (tokens/s) |
|------------------|---------------|----------|----------------------|
| vLLM             | 133,966       | 98.95    | 1353.86             |
| Nano-vLLM        | 133,966       | 101.90   | 1314.65             |

## 🛠️ Installation

```bash
pip install git+https://github.com/GeeeekExplorer/nano-vllm.git
```

## 🔧 Usage

### Basic Usage

```python
from nanovllm import LLM, SamplingParams

# Initialize the LLM
llm = LLM("/YOUR/MODEL/PATH", enforce_eager=True, tensor_parallel_size=1)

# Set sampling parameters
sampling_params = SamplingParams(temperature=0.6, max_tokens=256)

# Generate responses
prompts = ["Hello, Nano-vLLM."]
outputs = llm.generate(prompts, sampling_params)
print(outputs[0]["text"])
```

### Streaming Generation

```python
# Stream generation
for token in llm.generate_stream("Tell me a story", sampling_params):
    print(token, end="", flush=True)
```

### Advanced Usage

```python
# Multiple prompts with different sampling
creative_params = SamplingParams.creative(max_tokens=512)
balanced_params = SamplingParams.balanced(max_tokens=256)
greedy_params = SamplingParams.greedy(max_tokens=128)

prompts = [
    "Write a creative story about space exploration",
    "Explain quantum computing simply", 
    "What is 2+2?"
]

params = [creative_params, balanced_params, greedy_params]

for prompt, param in zip(prompts, params):
    output = llm.generate([prompt], param)
    print(f"Prompt: {prompt}")
    print(f"Response: {output[0]['text']}\n")
```

## 🔧 Configuration

### Model Loading Options

```python
llm = LLM(
    model_path="Qwen/Qwen3-0.6B",           # Model path or HuggingFace ID
    tensor_parallel_size=1,                  # Number of GPUs for tensor parallelism
    enforce_eager=True,                      # Disable graph compilation
    max_model_len=2048,                     # Maximum sequence length
    gpu_memory_utilization=0.8,             # GPU memory usage ratio
)
```

### Sampling Parameters

```python
sampling_params = SamplingParams(
    temperature=0.6,        # Randomness (0.0 = greedy, >1.0 = creative)
    top_k=50,              # Top-k sampling
    top_p=0.9,             # Nucleus sampling  
    max_tokens=256,        # Maximum tokens to generate
    repetition_penalty=1.0, # Penalty for repetition
    stop_sequences=["END"]  # Stop generation at these sequences
)
```

## 🧪 Benchmarking

Run the benchmark script to test performance:

```bash
python bench.py --model Qwen/Qwen3-0.6B --requests 256
```

Example output:
```
🔥 nano-vLLM Performance Benchmark
==================================================
🚀 Benchmarking nano-vLLM with 256 requests...
✅ Generation complete: 133966 tokens in 101.90s (1314.65 tok/s)

📈 BENCHMARK RESULTS
==================================================
Engine: Nano-vLLM
Total Requests: 256
Total Tokens: 133,966
Total Time: 101.90s
Throughput: 1314.65 tokens/s
Baseline Comparison: +0.00%
```

## 🏗️ Architecture

### Core Components

1. **LLM Engine** (`llm.py`) - Main inference engine
2. **Model Manager** (`model_manager.py`) - Model lifecycle management
3. **Cache Manager** (`cache_manager.py`) - KV cache optimization
4. **Sampling Params** (`sampling_params.py`) - Generation configuration
5. **Optimizations** (`optimizations.py`) - Performance enhancements

### Key Features

- **Prefix Caching**: Reuses computation for repeated prompt prefixes
- **Tensor Parallelism**: Distributes computation across multiple GPUs
- **Adaptive Batching**: Dynamically adjusts batch sizes for optimal throughput
- **Memory Management**: Efficient KV cache and GPU memory usage
- **CUDA Optimizations**: CUDA graphs and mixed precision support

## 📈 Optimizations

### Enable Advanced Optimizations

```python
from nanovllm.optimizations import PerformanceOptimizer

optimizer = PerformanceOptimizer()

# Enable CUDA graphs
optimizer.enable_cuda_graphs()

# Enable mixed precision
optimizer.enable_mixed_precision()

# Compile model
model = optimizer.compile_model(model)

# Optimize memory
optimizer.optimize_memory()
```

### Tensor Parallelism

```python
# Multi-GPU inference
llm = LLM(
    "large-model-path",
    tensor_parallel_size=4,  # Use 4 GPUs
    enforce_eager=False
)
```

## 🤝 Contributing

Contributions are welcome! Areas of interest:

- Performance optimizations
- New model support
- Memory efficiency improvements
- Documentation and examples

## 📝 License

MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

- Original vLLM project for inspiration
- HuggingFace Transformers for model support
- PyTorch team for the underlying framework

## 📞 Support

- Issues: [GitHub Issues](https://github.com/GeeeekExplorer/nano-vllm/issues)
- Discussions: [GitHub Discussions](https://github.com/GeeeekExplorer/nano-vllm/discussions)

---

**nano-vLLM**: Simplicity meets performance in LLM inference.
