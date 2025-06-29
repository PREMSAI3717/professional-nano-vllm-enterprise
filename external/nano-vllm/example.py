#!/usr/bin/env python3
"""
Example usage of nano-vLLM
Based on the official nano-vLLM example from GeeeekExplorer
"""

from nanovllm import LLM, SamplingParams

def main():
    # Initialize the LLM
    # Replace with your model path
    model_path = "/YOUR/MODEL/PATH"  # e.g., "Qwen/Qwen3-0.6B"
    
    # Create LLM instance
    llm = LLM(
        model_path, 
        enforce_eager=True, 
        tensor_parallel_size=1
    )
    
    # Set sampling parameters
    sampling_params = SamplingParams(
        temperature=0.6, 
        max_tokens=256
    )
    
    # Example prompts
    prompts = [
        "Hello, Nano-vLLM.",
        "Explain quantum computing in simple terms.",
        "Write a short poem about artificial intelligence."
    ]
    
    # Generate responses
    print("🚀 Running nano-vLLM inference...")
    outputs = llm.generate(prompts, sampling_params)
    
    # Display results
    for i, output in enumerate(outputs):
        print(f"\n--- Prompt {i+1} ---")
        print(f"Input: {prompts[i]}")
        print(f"Output: {output['text']}")

if __name__ == "__main__":
    main()
