"""
Sampling parameters for text generation
Configures how the model generates tokens
"""

from dataclasses import dataclass
from typing import Optional

@dataclass
class SamplingParams:
    """
    Parameters for controlling text generation sampling
    
    Args:
        temperature: Sampling temperature (0.0 = greedy, >1.0 = more random)
        top_k: Number of top tokens to consider (0 = disabled)
        top_p: Nucleus sampling threshold (1.0 = disabled)
        max_tokens: Maximum number of tokens to generate
        min_tokens: Minimum number of tokens to generate  
        repetition_penalty: Penalty for repeating tokens
        stop_sequences: List of sequences that stop generation
        seed: Random seed for reproducible generation
    """
    
    # Core sampling parameters
    temperature: float = 1.0
    top_k: int = 50
    top_p: float = 1.0
    max_tokens: int = 256
    min_tokens: int = 1
    
    # Advanced parameters
    repetition_penalty: float = 1.0
    stop_sequences: Optional[list] = None
    seed: Optional[int] = None
    
    # Performance parameters
    use_beam_search: bool = False
    num_beams: int = 1
    early_stopping: bool = False
    
    def __post_init__(self):
        """Validate parameters after initialization"""
        if self.temperature < 0:
            raise ValueError("Temperature must be non-negative")
        if self.top_k < 0:
            raise ValueError("top_k must be non-negative")
        if not 0 <= self.top_p <= 1:
            raise ValueError("top_p must be between 0 and 1")
        if self.max_tokens <= 0:
            raise ValueError("max_tokens must be positive")
        if self.min_tokens < 0:
            raise ValueError("min_tokens must be non-negative")
        if self.repetition_penalty < 0:
            raise ValueError("repetition_penalty must be non-negative")
            
        if self.stop_sequences is None:
            self.stop_sequences = []
            
    @classmethod
    def greedy(cls, max_tokens: int = 256):
        """Create greedy sampling parameters"""
        return cls(temperature=0.0, max_tokens=max_tokens)
        
    @classmethod
    def creative(cls, max_tokens: int = 256):
        """Create creative sampling parameters"""
        return cls(
            temperature=0.8,
            top_k=40,
            top_p=0.9,
            max_tokens=max_tokens
        )
        
    @classmethod  
    def balanced(cls, max_tokens: int = 256):
        """Create balanced sampling parameters"""
        return cls(
            temperature=0.6,
            top_k=50,
            top_p=0.95,
            max_tokens=max_tokens
        )
        
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            'temperature': self.temperature,
            'top_k': self.top_k,
            'top_p': self.top_p,
            'max_tokens': self.max_tokens,
            'min_tokens': self.min_tokens,
            'repetition_penalty': self.repetition_penalty,
            'stop_sequences': self.stop_sequences,
            'seed': self.seed,
            'use_beam_search': self.use_beam_search,
            'num_beams': self.num_beams,
            'early_stopping': self.early_stopping
        }
        
    @classmethod
    def from_dict(cls, params: dict):
        """Create from dictionary"""
        return cls(**params)
