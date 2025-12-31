# app/core/llm_config.py
"""
Local LLM Configuration Module for DRYAD.AI

This module provides configuration and initialization for various local LLM providers
including Ollama, Hugging Face Transformers, and other local inference servers.
"""

import os
import logging
import time
from typing import Optional, Dict, Any, Union
from enum import Enum

# Import performance and caching utilities
from app.core.caching import cached, cache
from app.core.performance import monitor_performance
from app.core.logging_config import get_logger, LogTimer
from app.core.monitoring_integration import monitor_llm_call, monitoring_integration

logger = get_logger(__name__)

def detect_gpu_config() -> Dict[str, Any]:
    """
    Detect optimal GPU configuration for LLM inference.

    Returns:
        Dict containing GPU configuration with keys:
        - n_gpu_layers: Number of layers to offload to GPU
        - device: Device to use ('cuda' or 'cpu')
        - gpu_memory_gb: Available GPU memory in GB
        - has_gpu: Whether GPU is available
    """
    # Check for CPU-only override
    if os.getenv("FORCE_CPU", "false").lower() == "true":
        logger.info("GPU acceleration disabled by FORCE_CPU environment variable")
        return {
            "n_gpu_layers": 0,
            "device": "cpu",
            "gpu_memory_gb": 0.0,
            "has_gpu": False
        }

    try:
        # Try PyTorch CUDA detection first (most reliable)
        import torch
        if torch.cuda.is_available():
            gpu_count = torch.cuda.device_count()
            gpu_memory_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)

            # Calculate optimal GPU layers based on available memory
            if gpu_memory_gb >= 12:
                n_gpu_layers = 35  # Full GPU acceleration for high-end GPUs
            elif gpu_memory_gb >= 8:
                n_gpu_layers = 28  # Most layers on GPU for mid-range GPUs
            elif gpu_memory_gb >= 6:
                n_gpu_layers = 20  # Partial GPU acceleration
            elif gpu_memory_gb >= 4:
                n_gpu_layers = 15  # Minimal GPU acceleration
            else:
                n_gpu_layers = 8   # Very conservative for low VRAM

            logger.info(f"CUDA GPU detected: {gpu_count} device(s), {gpu_memory_gb:.1f}GB VRAM, using {n_gpu_layers} GPU layers")
            return {
                "n_gpu_layers": n_gpu_layers,
                "device": "cuda",
                "gpu_memory_gb": gpu_memory_gb,
                "has_gpu": True
            }
    except ImportError:
        logger.debug("PyTorch not available for GPU detection")
    except Exception as e:
        logger.warning(f"PyTorch GPU detection failed: {e}")

    try:
        # Fallback to GPUtil for basic GPU detection
        import GPUtil
        gpus = GPUtil.getGPUs()
        if gpus:
            gpu_memory_gb = max(gpu.memoryTotal / 1024 for gpu in gpus)
            # Conservative GPU layer count without PyTorch
            n_gpu_layers = min(20, int(gpu_memory_gb * 2))  # Rough heuristic

            logger.info(f"GPU detected via GPUtil: {len(gpus)} device(s), {gpu_memory_gb:.1f}GB VRAM, using {n_gpu_layers} GPU layers")
            return {
                "n_gpu_layers": n_gpu_layers,
                "device": "cuda",
                "gpu_memory_gb": gpu_memory_gb,
                "has_gpu": True
            }
    except ImportError:
        logger.debug("GPUtil not available for GPU detection")
    except Exception as e:
        logger.warning(f"GPUtil GPU detection failed: {e}")

    # No GPU detected or available
    logger.info("No GPU detected or GPU acceleration unavailable, using CPU-only inference")
    return {
        "n_gpu_layers": 0,
        "device": "cpu",
        "gpu_memory_gb": 0.0,
        "has_gpu": False
    }

class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    OLLAMA = "ollama"
    OLLAMA_CLOUD = "ollama_cloud"  # Cloud Ollama with intelligent routing
    HUGGINGFACE = "huggingface"
    LLAMACPP = "llamacpp"
    MOCK = "mock"

class TaskComplexity(str, Enum):
    """Task complexity levels for intelligent model routing."""
    SIMPLE = "simple"      # Basic queries, simple responses
    MODERATE = "moderate"  # Standard reasoning, analysis
    COMPLEX = "complex"    # Advanced reasoning, coding, agentic tasks
    CRITICAL = "critical"  # Maximum capability requirements

class LLMConfig:
    """Configuration class for LLM providers with hybrid cloud/local support."""

    def __init__(self):
        self.provider = self._detect_provider()
        self.model_name = self._get_model_name()
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.1"))
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "2048"))

        # Ollama Configuration - Support both cloud and local
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.cloud_url = os.getenv("OLLAMA_CLOUD_URL", "")
        self.cloud_enabled = bool(self.cloud_url and os.getenv("OLLAMA_CLOUD_ENABLED", "true").lower() == "true")
        self.cloud_first = os.getenv("OLLAMA_CLOUD_FIRST", "true").lower() == "true"

        # Model routing configuration
        self.cloud_models = self._get_cloud_models()
        self.local_models = self._get_local_models()
        self.model_routing = self._get_model_routing()
        
    def _detect_provider(self) -> LLMProvider:
        """Auto-detect the best available LLM provider with cloud/local hybrid support."""
        # Check for explicitly configured provider
        forced_provider = os.getenv("LLM_PROVIDER", "ollama").lower()  # Default to Ollama for hybrid support
        if forced_provider in [p.value for p in LLMProvider]:
            logger.info(f"Using configured LLM provider: {forced_provider}")
            return LLMProvider(forced_provider)

        # Check if cloud Ollama is available and preferred
        if os.getenv("OLLAMA_CLOUD_URL") and os.getenv("OLLAMA_CLOUD_ENABLED", "true").lower() == "true":
            logger.info("Using Ollama with cloud/local hybrid support")
            return LLMProvider.OLLAMA

        # For self-contained AI, default to local LlamaCpp
        logger.info("Using local LlamaCpp for self-contained AI operation")
        return LLMProvider.LLAMACPP
    

    
    def _get_model_name(self) -> str:
        """Get the model name based on provider."""
        provider_models = {
            LLMProvider.OPENAI: os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
            LLMProvider.OLLAMA: os.getenv("OLLAMA_MODEL", "llama3.2:3b"),
            LLMProvider.OLLAMA_CLOUD: os.getenv("OLLAMA_CLOUD_MODEL", "gpt-oss:20b"),
            LLMProvider.HUGGINGFACE: os.getenv("HF_MODEL", "microsoft/DialoGPT-medium"),
            LLMProvider.LLAMACPP: os.getenv("LLAMACPP_MODEL", "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"),
            LLMProvider.MOCK: "mock-model"
        }
        return provider_models.get(self.provider, "default-model")

    def select_optimal_model(self, agent_type: str = "default", task_complexity: TaskComplexity = TaskComplexity.MODERATE, force_local: bool = False) -> tuple[str, str]:
        """
        Intelligently select the optimal model and endpoint based on task requirements.

        Args:
            agent_type: Type of agent making the request
            task_complexity: Complexity level of the task
            force_local: Force local model usage (offline mode)

        Returns:
            Tuple of (model_name, base_url)
        """
        # Force local if requested or cloud is disabled
        if force_local or not self.cloud_enabled or not self.cloud_url:
            return self._select_local_model(agent_type, task_complexity)

        # Get routing configuration for agent type
        routing_config = self.model_routing.get(agent_type, self.model_routing["default"])
        complexity_threshold = TaskComplexity(routing_config["complexity_threshold"])

        # Determine if we should use cloud based on complexity
        use_cloud = self._should_use_cloud(task_complexity, complexity_threshold)

        if use_cloud and self.cloud_first:
            try:
                return self._select_cloud_model(agent_type, task_complexity)
            except Exception as e:
                logger.warning(f"Cloud model selection failed, falling back to local: {e}")
                return self._select_local_model(agent_type, task_complexity)
        else:
            return self._select_local_model(agent_type, task_complexity)

    def _should_use_cloud(self, task_complexity: TaskComplexity, threshold: TaskComplexity) -> bool:
        """Determine if cloud should be used based on complexity."""
        complexity_order = [TaskComplexity.SIMPLE, TaskComplexity.MODERATE, TaskComplexity.COMPLEX, TaskComplexity.CRITICAL]
        task_level = complexity_order.index(task_complexity)
        threshold_level = complexity_order.index(threshold)
        return task_level >= threshold_level

    def _select_cloud_model(self, agent_type: str, task_complexity: TaskComplexity) -> tuple[str, str]:
        """Select appropriate cloud model."""
        routing_config = self.model_routing.get(agent_type, self.model_routing["default"])
        base_model = routing_config["cloud_model"]

        # Adjust model based on complexity
        if task_complexity == TaskComplexity.CRITICAL:
            if agent_type == "coder":
                model = "qwen3-coder:480b"
            elif agent_type == "researcher":
                model = "gpt-oss:120b"
            else:
                model = "deepseek-v3.1"
        elif task_complexity == TaskComplexity.COMPLEX:
            model = base_model
        else:
            # Use smaller cloud models for moderate tasks
            if "480b" in base_model:
                model = base_model.replace("480b", "30b")
            elif "120b" in base_model:
                model = base_model.replace("120b", "20b")
            else:
                model = base_model

        logger.info(f"Selected cloud model: {model} for {agent_type} ({task_complexity.value})")
        return model, self.cloud_url

    def _select_local_model(self, agent_type: str, task_complexity: TaskComplexity) -> tuple[str, str]:
        """Select appropriate local model."""
        routing_config = self.model_routing.get(agent_type, self.model_routing["default"])
        base_model = routing_config["local_model"]

        # Adjust model based on complexity and availability
        if task_complexity == TaskComplexity.SIMPLE:
            model = "llama3.2:1b" if "llama3.2:1b" in self.local_models else base_model
        elif task_complexity == TaskComplexity.CRITICAL and agent_type == "coder":
            model = "codellama:7b" if "codellama:7b" in self.local_models else base_model
        else:
            model = base_model

        logger.info(f"Selected local model: {model} for {agent_type} ({task_complexity.value})")
        return model, self.base_url

    def set_cloud_mode(self, enabled: bool = True):
        """Enable or disable cloud mode."""
        self.cloud_enabled = enabled
        logger.info(f"Cloud mode {'enabled' if enabled else 'disabled'}")

    def set_cloud_first(self, cloud_first: bool = True):
        """Set cloud-first preference."""
        self.cloud_first = cloud_first
        logger.info(f"Cloud-first mode {'enabled' if cloud_first else 'disabled'}")

    def get_status(self) -> Dict[str, Any]:
        """Get current configuration status."""
        return {
            "provider": self.provider.value,
            "cloud_enabled": self.cloud_enabled,
            "cloud_first": self.cloud_first,
            "cloud_url": self.cloud_url,
            "local_url": self.base_url,
            "available_cloud_models": list(self.cloud_models.keys()),
            "available_local_models": list(self.local_models.keys()),
            "model_routing": self.model_routing
        }

    def _get_cloud_models(self) -> Dict[str, str]:
        """Get available cloud models with their use cases."""
        return {
            # Reasoning and agentic tasks
            "gpt-oss:20b": "reasoning",
            "gpt-oss:120b": "complex_reasoning",

            # Thinking and hybrid tasks
            "deepseek-v3.1:671b": "thinking",

            # Coding and development
            "qwen3-coder:480b": "complex_coding",
            "kimi-k2:1t": "coding_agent",
        }

    def _get_local_models(self) -> Dict[str, str]:
        """Get available local models with their use cases."""
        return {
            "llama3.2:3b": "general",
            "llama3.2:1b": "simple",
            "tinyllama": "basic",
            "codellama:7b": "local_coding",
        }

    def _get_model_routing(self) -> Dict[str, Dict[str, str]]:
        """Get model routing configuration based on task complexity and agent type."""
        return {
            # Agent type routing
            "researcher": {
                "cloud_model": "gpt-oss:120b",
                "local_model": "llama3.2:3b",
                "complexity_threshold": "moderate"
            },
            "coder": {
                "cloud_model": "qwen3-coder:480b",
                "local_model": "codellama:7b",
                "complexity_threshold": "simple"
            },
            "analyst": {
                "cloud_model": "deepseek-v3.1:671b",
                "local_model": "llama3.2:3b",
                "complexity_threshold": "moderate"
            },
            "coordinator": {
                "cloud_model": "gpt-oss:20b",
                "local_model": "llama3.2:3b",
                "complexity_threshold": "simple"
            },
            "memory_keeper": {
                "cloud_model": "gpt-oss:20b",
                "local_model": "llama3.2:3b",
                "complexity_threshold": "moderate"
            },
            "default": {
                "cloud_model": "gpt-oss:20b",
                "local_model": "llama3.2:3b",
                "complexity_threshold": "moderate"
            }
        }

def create_llm(config: Optional[LLMConfig] = None, agent_type: str = "default", task_complexity: TaskComplexity = TaskComplexity.MODERATE, force_local: bool = False):
    """
    Create an LLM instance with intelligent cloud/local routing.

    Args:
        config: LLM configuration. If None, auto-detects the best provider.
        agent_type: Type of agent for model selection
        task_complexity: Complexity level for model routing
        force_local: Force local model usage (offline mode)

    Returns:
        LLM instance compatible with LangChain
    """
    if config is None:
        config = LLMConfig()

    # For Ollama provider, use intelligent model selection
    if config.provider == LLMProvider.OLLAMA and config.cloud_enabled:
        model_name, base_url = config.select_optimal_model(agent_type, task_complexity, force_local)
        # Create a temporary config with selected model and endpoint
        temp_config = LLMConfig()
        temp_config.provider = config.provider
        temp_config.model_name = model_name
        temp_config.base_url = base_url
        temp_config.temperature = config.temperature
        temp_config.max_tokens = config.max_tokens
        config = temp_config

    logger.info(f"Initializing LLM with provider: {config.provider}, model: {config.model_name}, endpoint: {config.base_url}")

    try:
        if config.provider == LLMProvider.OPENAI:
            return _create_openai_llm(config)
        elif config.provider == LLMProvider.OLLAMA or config.provider == LLMProvider.OLLAMA_CLOUD:
            return _create_ollama_llm(config)
        elif config.provider == LLMProvider.HUGGINGFACE:
            return _create_huggingface_llm(config)
        elif config.provider == LLMProvider.LLAMACPP:
            return _create_llamacpp_llm(config)
        elif config.provider == LLMProvider.MOCK:
            logger.warning("Using mock LLM - only for testing purposes")
            return _create_mock_llm(config)
        else:
            raise RuntimeError(f"Unsupported LLM provider: {config.provider}. Supported providers: {[p.value for p in LLMProvider]}")

    except Exception as e:
        logger.error(f"Failed to initialize {config.provider} LLM: {e}")

        # For Ollama cloud failures, try local fallback
        if config.provider == LLMProvider.OLLAMA and config.cloud_enabled and not force_local:
            logger.info("Attempting fallback to local Ollama...")
            try:
                return create_llm(config, agent_type, task_complexity, force_local=True)
            except Exception as local_error:
                logger.error(f"Local Ollama fallback failed: {local_error}")

        # Provide specific guidance based on the provider
        if config.provider == LLMProvider.LLAMACPP:
            error_msg = (
                f"Local LLM initialization failed: {e}. "
                "This is a critical error for self-contained AI operation. "
                "Please ensure:\n"
                "1. llama-cpp-python is installed: pip install llama-cpp-python\n"
                "2. Model files are available in the models directory\n"
                "3. Sufficient system resources (RAM/CPU) are available\n"
                "4. Model files are not corrupted (check SHA256 hashes)"
            )
        elif config.provider == LLMProvider.OPENAI:
            error_msg = f"OpenAI LLM initialization failed: {e}. Please check your API key and network connection."
        elif config.provider == LLMProvider.OLLAMA or config.provider == LLMProvider.OLLAMA_CLOUD:
            if config.cloud_enabled:
                error_msg = f"Ollama (cloud/local) initialization failed: {e}. Please check cloud connectivity and local Ollama server."
            else:
                error_msg = f"Ollama LLM initialization failed: {e}. Please ensure Ollama server is running and accessible."
        elif config.provider == LLMProvider.HUGGINGFACE:
            error_msg = f"Hugging Face LLM initialization failed: {e}. Please check model availability and dependencies."
        else:
            error_msg = f"LLM initialization failed: {e}"

        raise RuntimeError(error_msg)

def _create_openai_llm(config: LLMConfig):
    """Create OpenAI LLM instance with enhanced configuration."""
    try:
        from langchain_openai import ChatOpenAI
        import openai

        # Validate API key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")

        # Test API connectivity
        client = openai.OpenAI(api_key=api_key)
        try:
            # Simple test call to verify API key works
            client.models.list()
            logger.info("✅ OpenAI API key validated successfully")
        except Exception as e:
            logger.error(f"❌ OpenAI API key validation failed: {e}")
            raise

        # Create LangChain OpenAI instance
        llm = ChatOpenAI(
            model=config.model_name,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            api_key=api_key,
            timeout=30,  # 30 second timeout
            max_retries=3,  # Retry failed requests
        )

        logger.info(f"✅ OpenAI LLM initialized: {config.model_name}")
        return llm

    except ImportError as e:
        logger.error(f"❌ OpenAI dependencies not installed: {e}")
        logger.info("Install with: pip install langchain-openai openai")
        raise
    except Exception as e:
        logger.error(f"❌ Failed to create OpenAI LLM: {e}")
        raise

def _create_ollama_llm(config: LLMConfig):
    """
    Create Ollama LLM instance.

    Uses mistral:latest model to differentiate from llamacpp provider (which uses llama3.2:3b).
    This allows both providers to load their models simultaneously without conflicts.
    """
    try:
        from langchain_ollama import ChatOllama
        import os

        # Use mistral:latest for ollama provider (different from llamacpp's llama3.2:3b)
        # This allows parallel multi-provider queries without Ollama conflicts
        ollama_model = os.getenv("OLLAMA_MODEL", "mistral:latest")
        ollama_base_url = config.base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        ollama_keep_alive = os.getenv("OLLAMA_KEEP_ALIVE")  # Optional: e.g., "10m", "1h"

        logger.info(f"Using Ollama API for ollama provider (model: {ollama_model})")
        logger.info(f"Ollama base URL: {ollama_base_url}")
        if ollama_keep_alive:
            logger.info(f"Ollama keep_alive: {ollama_keep_alive}")

        # Build kwargs for ChatOllama
        ollama_kwargs = {
            "model": ollama_model,
            "base_url": ollama_base_url,
            "temperature": config.temperature,
            "num_predict": config.max_tokens,
            # Add timeout to prevent hanging (120s for model loading + inference)
            "timeout": 120.0,
        }

        # Only add keep_alive if specified
        if ollama_keep_alive:
            ollama_kwargs["keep_alive"] = ollama_keep_alive

        llm = ChatOllama(**ollama_kwargs)
        logger.info(f"✅ Ollama LLM created successfully for ollama provider")
        return llm

    except ImportError:
        logger.error("langchain-ollama not installed. Install with: pip install langchain-ollama")
        raise
    except Exception as e:
        logger.error(f"Failed to create Ollama LLM: {e}")
        raise

def _create_huggingface_llm(config: LLMConfig):
    """Create Hugging Face LLM instance."""
    try:
        from langchain_huggingface import HuggingFacePipeline
        from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
        
        # Load model and tokenizer
        tokenizer = AutoTokenizer.from_pretrained(config.model_name)
        model = AutoModelForCausalLM.from_pretrained(
            config.model_name,
            device_map="auto",
            torch_dtype="auto"
        )
        
        # Create pipeline
        pipe = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            max_new_tokens=config.max_tokens,
            temperature=config.temperature,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id
        )
        
        return HuggingFacePipeline(pipeline=pipe)
        
    except ImportError:
        logger.error("Hugging Face dependencies not installed. Install with: pip install transformers accelerate")
        raise

def _create_llamacpp_llm(config: LLMConfig):
    """
    Create LlamaCpp LLM instance using Ollama HTTP API for better stability.

    This uses Ollama's HTTP API instead of llama-cpp-python to avoid C++ crashes
    and provide better process isolation. The Ollama service must be running.
    """
    try:
        from langchain_ollama import ChatOllama
        import os

        # Use Ollama API for better stability and process isolation
        # Map GGUF model names to Ollama model names
        model_mapping = {
            "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf": "llama3.2:3b",  # Use llama3.2 as TinyLlama alternative
            "mistral-7b-instruct-v0.2.Q4_K_M.gguf": "mistral:latest",
            "llama-2-7b-chat.Q4_K_M.gguf": "llama2:latest",
        }

        # Get model name from environment or use default
        gguf_model = os.getenv("LLAMACPP_MODEL", "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf")
        ollama_model = model_mapping.get(gguf_model, "llama3.2:3b")

        # Get Ollama base URL and keep_alive from environment
        ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        ollama_keep_alive = os.getenv("OLLAMA_KEEP_ALIVE")  # Optional: e.g., "10m", "1h"

        logger.info(f"Using Ollama API for llamacpp provider (model: {ollama_model})")
        logger.info(f"Ollama base URL: {ollama_base_url}")
        if ollama_keep_alive:
            logger.info(f"Ollama keep_alive: {ollama_keep_alive}")

        # Create Ollama LLM instance with error handling
        try:
            # Build kwargs for ChatOllama
            ollama_kwargs = {
                "model": ollama_model,
                "base_url": ollama_base_url,
                "temperature": config.temperature,
                "num_predict": config.max_tokens,
                # Add timeout to prevent hanging (120s for model loading + inference)
                "timeout": 120.0,
            }

            # Only add keep_alive if specified
            if ollama_keep_alive:
                ollama_kwargs["keep_alive"] = ollama_keep_alive

            llm = ChatOllama(**ollama_kwargs)

            logger.info(f"✅ Ollama LLM created successfully for llamacpp provider")
            return llm

        except Exception as e:
            logger.error(f"Failed to create Ollama LLM: {e}")
            logger.error(f"Make sure Ollama is running at {ollama_base_url}")
            logger.error(f"Check available models with: curl {ollama_base_url}/api/tags")
            raise

    except ImportError as e:
        logger.error("langchain-ollama not installed. Install with: pip install langchain-ollama")
        raise
    except Exception as e:
        logger.error(f"Failed to create LlamaCpp LLM (Ollama backend): {e}")
        raise

# Model downloading is now handled by the ModelManager class

class OptimizedLLM:
    """Wrapper for LLM with performance optimization."""

    def __init__(self, llm, model_name: str = ""):
        self.llm = llm
        self.model_name = model_name

        # Initialize performance optimizer
        try:
            from app.core.performance_optimizer import performance_optimizer
            self.performance_optimizer = performance_optimizer
            if not performance_optimizer.is_initialized:
                performance_optimizer.initialize()
        except Exception as e:
            logger.warning(f"Performance optimizer not available: {e}")
            self.performance_optimizer = None

    def invoke(self, prompt: str, **kwargs) -> Any:
        """Invoke LLM with performance optimization."""

        # Format prompt for TinyLlama if needed
        formatted_prompt = self._format_prompt_for_model(prompt)

        if not self.performance_optimizer:
            # Direct invocation without optimization
            return self.llm.invoke(formatted_prompt, **kwargs)

        # Check cache first
        temperature = kwargs.get('temperature', 0.7)
        cached_response = self.performance_optimizer.response_cache.get(
            prompt, self.model_name, temperature  # Use original prompt for cache key
        )
        if cached_response:
            # Return cached response wrapped in appropriate format
            class CachedResponse:
                def __init__(self, content):
                    self.content = content
                def __str__(self):
                    return self.content
            return CachedResponse(cached_response)

        # Execute with optimization
        def execute_llm():
            response = self.llm.invoke(formatted_prompt, **kwargs)  # Use formatted prompt

            # Cache the response
            response_text = response.content if hasattr(response, 'content') else str(response)
            self.performance_optimizer.response_cache.put(
                prompt, response_text, self.model_name, temperature  # Cache with original prompt
            )

            return response

        # Submit to optimized request queue
        future = self.performance_optimizer.optimize_request(execute_llm)
        return future.result()  # Wait for completion

    def _format_prompt_for_model(self, prompt: str) -> str:
        """Format prompt appropriately for the specific model."""
        # Check if this is a TinyLlama model
        if "tinyllama" in self.model_name.lower():
            # TinyLlama needs "Question: ... Answer:" format
            if not prompt.strip().startswith("Question:") and not prompt.strip().endswith("Answer:"):
                return f"Question: {prompt.strip()} Answer:"

        # For other models, return prompt as-is
        return prompt

    def __getattr__(self, name):
        """Delegate other attributes to the underlying LLM."""
        return getattr(self.llm, name)

def _create_mock_llm(config: LLMConfig):
    """Create an intelligent mock LLM for development/testing."""
    from langchain_core.language_models.llms import LLM
    from langchain_core.callbacks.manager import CallbackManagerForLLMRun
    from typing import Optional, List, Any
    import random
    import re

    class IntelligentMockLLM(LLM):
        """A fallback LLM that attempts real LLM invocation with proper fallback chain."""

        def __init__(self):
            super().__init__()
            self._fallback_attempts = []

        @property
        def _llm_type(self) -> str:
            return "intelligent-fallback"

        def _call(
            self,
            prompt: str,
            stop: Optional[List[str]] = None,
            run_manager: Optional[CallbackManagerForLLMRun] = None,
            **kwargs: Any,
        ) -> str:
            """
            SELF-CONTAINED AI: Explicit failure instead of external API fallback.

            This mock LLM should NEVER be used in production. It exists only for testing
            and will fail explicitly to prevent accidental use instead of real local LLM.
            """

            # Log that mock LLM was called (this should not happen in production)
            logger.error("🚨 MOCK LLM CALLED - This indicates a configuration problem!")
            logger.error("   The system should be using a real local LLM (Ollama, LlamaCpp, etc.)")
            logger.error("   Mock LLM usage suggests LLM_PROVIDER is not properly configured.")

            # Try Local LLM first (only attempt, no external API fallback)
            try:
                logger.debug("Attempting local LLM as last resort...")
                local_response = self._try_local_llm(prompt, stop, **kwargs)
                logger.debug(f"Local LLM response: '{local_response}'")
                if local_response and str(local_response).strip():
                    logger.warning("✅ Local LLM fallback successful, but mock LLM should not be used")
                    return str(local_response).strip()
                else:
                    self._fallback_attempts.append(f"Local LLM returned empty/invalid response: '{local_response}'")
            except Exception as e:
                self._fallback_attempts.append(f"Local LLM failed: {str(e)}")
                logger.debug(f"Local LLM attempt failed: {e}")

            # NO EXTERNAL API FALLBACK - Fail explicitly for self-contained AI
            logger.error("🚨 EXPLICIT FAILURE: No external API fallback for self-contained AI")
            return self._generate_explicit_failure_error(prompt)

        def _try_local_llm(self, prompt: str, stop: Optional[List[str]] = None, **kwargs) -> Optional[str]:
            """Attempt to use local LLM (LlamaCpp)."""
            try:
                from langchain_community.llms import LlamaCpp
                import os

                # Check if model file exists
                model_path = "models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
                if not os.path.exists(model_path):
                    raise FileNotFoundError(f"Model file not found: {model_path}")

                # Detect GPU configuration for fallback LLM
                gpu_config = detect_gpu_config()

                # Create temporary LlamaCpp instance with GPU acceleration
                llm = LlamaCpp(
                    model_path=model_path,
                    temperature=0.1,
                    max_tokens=512,
                    n_ctx=2048,
                    n_threads=2,
                    verbose=False,
                    n_gpu_layers=gpu_config['n_gpu_layers'],  # Auto-detected GPU layers
                    use_mlock=False,
                    use_mmap=True,
                )

                # Format prompt for better response from TinyLlama
                formatted_prompt = f"Question: {prompt}\nAnswer:"
                response = llm.invoke(formatted_prompt)
                logger.info("✅ Local LLM fallback successful")

                # Handle different response types
                if hasattr(response, 'content'):
                    return response.content.strip()
                elif isinstance(response, str):
                    return response.strip()
                else:
                    return str(response).strip()

            except ImportError:
                raise Exception("llama-cpp-python not installed")
            except Exception as e:
                raise Exception(f"Local LLM initialization failed: {e}")

        def _generate_explicit_failure_error(self, prompt: str) -> str:
            """Generate informative error message after all fallbacks failed."""
            import os
            attempts_summary = "\n".join([f"  - {attempt}" for attempt in self._fallback_attempts])

            return f"""🚨 SELF-CONTAINED AI SYSTEM FAILURE

Query: "{prompt[:100]}{'...' if len(prompt) > 100 else ''}"

❌ MOCK LLM SHOULD NOT BE USED - This indicates a configuration problem!

The DRYAD.AI system is designed to be self-contained and should use local LLM providers.
Mock LLM usage suggests the LLM_PROVIDER environment variable is not properly configured.

🔧 TO FIX THIS ISSUE:

1. Set LLM_PROVIDER in your .env file:
   - LLM_PROVIDER=ollama (recommended - for Ollama Docker container)
   - LLM_PROVIDER=llamacpp (for local GGUF models)

2. For Ollama setup:
   - Ensure Ollama container is running: docker ps | grep ollama
   - Download a model: docker exec ollama ollama pull llama3.2:3b
   - Set OLLAMA_BASE_URL=http://localhost:11434

3. For LlamaCpp setup:
   - Ensure model file exists in ./models/ directory
   - Install dependencies: pip install llama-cpp-python

📊 CURRENT STATUS:
- Fallback attempts: {len(self._fallback_attempts)}
- LLM_PROVIDER: {os.getenv('LLM_PROVIDER', 'NOT SET')}
- OLLAMA_BASE_URL: {os.getenv('OLLAMA_BASE_URL', 'NOT SET')}

🚫 NO EXTERNAL API FALLBACK: This system is designed to be self-contained.
   External APIs (OpenAI, etc.) are not used to maintain local AI operation.

Please configure a local LLM provider instead of relying on mock implementations."""

        @property
        def _identifying_params(self) -> dict:
            return {"type": "intelligent-fallback", "model": "fallback-chain", "attempts": len(self._fallback_attempts)}

    return IntelligentMockLLM()

# Global LLM configuration instance
llm_config = LLMConfig()

# Global LLM instance cache with thread safety
import threading
_llm_instance_cache = None
_llm_config_hash = None
_llm_cache_lock = threading.RLock()

def _get_config_hash(config: LLMConfig) -> str:
    """Generate a hash of the current LLM configuration for cache invalidation."""
    config_tuple = (
        config.provider.value,
        config.model_name,
        config.temperature,
        config.max_tokens,
        config.base_url
    )
    return str(hash(config_tuple))

def get_llm():
    """
    Get the configured LLM instance with caching.

    This function implements thread-safe caching to avoid creating multiple
    LLM instances unnecessarily, which improves performance and reduces memory usage.

    Returns:
        LLM instance compatible with LangChain
    """
    global _llm_instance_cache, _llm_config_hash, _llm_metrics

    with _llm_cache_lock:
        # Check if config changed
        current_hash = _get_config_hash(llm_config)

        if _llm_instance_cache is None or _llm_config_hash != current_hash:
            logger.info(f"Creating new LLM instance (provider: {llm_config.provider}, model: {llm_config.model_name})")
            _llm_instance_cache = create_llm(llm_config)
            _llm_config_hash = current_hash
            _llm_metrics.record_cache_miss()
            logger.info("LLM instance cached successfully")
        else:
            _llm_metrics.record_cache_hit()
            logger.debug("Using cached LLM instance")

        return _llm_instance_cache

def invalidate_llm_cache():
    """
    Invalidate the LLM cache to force creation of a new instance.
    Useful for testing or when configuration changes externally.
    """
    global _llm_instance_cache, _llm_config_hash

    with _llm_cache_lock:
        logger.info("Invalidating LLM cache")
        _llm_instance_cache = None
        _llm_config_hash = None

def get_llm_cache_info() -> Dict[str, Any]:
    """Get information about the LLM cache status."""
    with _llm_cache_lock:
        return {
            "cache_active": _llm_instance_cache is not None,
            "config_hash": _llm_config_hash,
            "cache_instance_type": type(_llm_instance_cache).__name__ if _llm_instance_cache else None
        }

def get_specialized_llm(agent_type: str):
    """
    Get LLM instance with agent-specific parameters.

    This function provides role-specific LLM configurations optimized for different
    agent types while maintaining the benefits of instance caching.

    Args:
        agent_type: Type of agent ('researcher', 'writer', 'analyst', 'coordinator', or 'default')

    Returns:
        LLM instance with specialized parameters for the agent type
    """
    global _llm_metrics
    _llm_metrics.record_specialized_request(agent_type)

    base_llm = get_llm()  # Get cached base instance

    # Agent-specific parameter configurations with task complexity mapping
    agent_configs = {
        'researcher': {
            'temperature': 0.1,  # More focused and factual
            'max_tokens': 2048,
            'description': 'Optimized for factual research and information gathering',
            'task_complexity': TaskComplexity.COMPLEX,  # Research often needs advanced reasoning
            'preferred_models': {'cloud': 'gpt-oss:120b', 'local': 'llama3.2:3b'}
        },
        'writer': {
            'temperature': 0.3,  # More creative and varied
            'max_tokens': 2048,
            'description': 'Optimized for creative and engaging content creation',
            'task_complexity': TaskComplexity.MODERATE,
            'preferred_models': {'cloud': 'gpt-oss:20b', 'local': 'llama3.2:3b'}
        },
        'analyst': {
            'temperature': 0.05,  # Very precise and analytical
            'max_tokens': 2048,
            'description': 'Optimized for precise analysis and data interpretation',
            'task_complexity': TaskComplexity.COMPLEX,
            'preferred_models': {'cloud': 'deepseek-v3.1', 'local': 'llama3.2:3b'}
        },
        'coordinator': {
            'temperature': 0.2,  # Balanced for task management
            'max_tokens': 1024,  # Shorter responses for coordination
            'description': 'Optimized for task coordination and workflow management',
            'task_complexity': TaskComplexity.MODERATE,
            'preferred_models': {'cloud': 'gpt-oss:20b', 'local': 'llama3.2:3b'}
        },
        'coder': {
            'temperature': 0.1,  # Precise for code generation
            'max_tokens': 4096,  # Longer context for code
            'description': 'Optimized for code generation and programming tasks',
            'task_complexity': TaskComplexity.COMPLEX,
            'preferred_models': {'cloud': 'qwen3-coder:480b', 'local': 'codellama:7b'}
        },
        'memory_keeper': {
            'temperature': 0.1,  # Precise for memory operations
            'max_tokens': 2048,
            'description': 'Optimized for memory management and retrieval',
            'task_complexity': TaskComplexity.MODERATE,
            'preferred_models': {'cloud': 'gpt-oss:20b', 'local': 'llama3.2:3b'}
        },
        'default': {
            'temperature': llm_config.temperature,
            'max_tokens': llm_config.max_tokens,
            'description': 'Default configuration',
            'task_complexity': TaskComplexity.MODERATE,
            'preferred_models': {'cloud': 'gpt-oss:20b', 'local': 'llama3.2:3b'}
        }
    }

    config = agent_configs.get(agent_type.lower(), agent_configs['default'])

    # For Ollama, create specialized instance with intelligent routing
    if llm_config.provider == LLMProvider.OLLAMA:
        try:
            # Use intelligent model selection for this agent
            task_complexity = config.get('task_complexity', TaskComplexity.MODERATE)
            model_name, base_url = llm_config.select_optimal_model(agent_type, task_complexity)

            # Create a new instance with specialized parameters
            from langchain_ollama import ChatOllama

            specialized_llm = ChatOllama(
                model=model_name,
                base_url=base_url,
                temperature=config['temperature'],
                num_predict=config['max_tokens']
            )

            # Add metadata for monitoring
            specialized_llm._agent_type = agent_type
            specialized_llm._config_description = config['description']
            specialized_llm._selected_model = model_name
            specialized_llm._selected_endpoint = base_url

            logger.info(f"Created specialized LLM for {agent_type}: {model_name} at {base_url}")
            return specialized_llm

        except Exception as e:
            logger.warning(f"Failed to create specialized LLM for {agent_type}, using base LLM: {e}")
            return base_llm

    # For other providers, try to bind parameters if supported
    try:
        if hasattr(base_llm, 'bind'):
            specialized_llm = base_llm.bind(
                temperature=config['temperature'],
                max_tokens=config['max_tokens']
            )
            specialized_llm._agent_type = agent_type
            specialized_llm._config_description = config['description']
            return specialized_llm
    except Exception as e:
        logger.debug(f"Parameter binding not supported for {llm_config.provider}, using base LLM: {e}")

    # Fallback to base LLM
    return base_llm

def get_agent_config_info(agent_type: str) -> Dict[str, Any]:
    """Get information about agent-specific configuration."""
    agent_configs = {
        'researcher': {'temperature': 0.1, 'max_tokens': 2048, 'focus': 'factual_research'},
        'writer': {'temperature': 0.3, 'max_tokens': 2048, 'focus': 'creative_content'},
        'analyst': {'temperature': 0.05, 'max_tokens': 2048, 'focus': 'precise_analysis'},
        'coordinator': {'temperature': 0.2, 'max_tokens': 1024, 'focus': 'task_management'},
        'default': {'temperature': llm_config.temperature, 'max_tokens': llm_config.max_tokens, 'focus': 'general'}
    }

    config = agent_configs.get(agent_type.lower(), agent_configs['default'])

    return {
        "agent_type": agent_type,
        "temperature": config['temperature'],
        "max_tokens": config['max_tokens'],
        "focus": config['focus'],
        "provider": llm_config.provider.value,
        "base_model": llm_config.model_name
    }

class LLMPool:
    """
    Enhanced connection pool for LLM instances optimized for llama-cpp-python.

    This class manages a pool of LLM instances to improve concurrent request handling
    while maintaining memory efficiency. Features:
    - Dynamic pool sizing based on system resources
    - Load balancing with health checking
    - Memory-aware instance management
    - Performance monitoring and optimization
    """

    def __init__(self, pool_size: int = 2, agent_type: str = "default"):
        """
        Initialize enhanced LLM pool with dynamic sizing.

        Args:
            pool_size: Number of LLM instances in the pool
            agent_type: Type of agent for specialized configuration
        """
        # Dynamic pool sizing based on system resources
        import psutil
        available_memory_gb = psutil.virtual_memory().available / (1024**3)
        cpu_cores = psutil.cpu_count()

        # Adjust pool size based on available resources
        if available_memory_gb < 4:
            # Low memory: single instance
            optimal_pool_size = 1
        elif available_memory_gb < 8:
            # Medium memory: small pool
            optimal_pool_size = min(pool_size, 2)
        else:
            # High memory: allow larger pools
            optimal_pool_size = min(pool_size, min(cpu_cores // 2, 4))

        self.pool_size = max(1, optimal_pool_size)
        self.agent_type = agent_type
        self.instances = []
        self.instance_health = []  # Track health of each instance
        self.current_index = 0
        self.creation_count = 0
        self.request_count = 0
        self.failed_requests = 0
        self._pool_lock = threading.RLock()
        self._last_health_check = 0

        logger.info(f"Initializing optimized LLM pool: size={self.pool_size}, agent={agent_type}, memory={available_memory_gb:.1f}GB")

    def get_llm(self):
        """
        Get an LLM instance from the pool with health checking and load balancing.

        Returns:
            LLM instance from the pool
        """
        with self._pool_lock:
            self.request_count += 1

            # Create pool instances if not already created
            if not self.instances:
                self._create_pool()

            # Periodic health check
            current_time = time.time()
            if current_time - self._last_health_check > 60:  # Check every minute
                self._health_check()
                self._last_health_check = current_time

            # Find healthy instance using round-robin
            attempts = 0
            while attempts < len(self.instances):
                instance_idx = self.current_index
                self.current_index = (self.current_index + 1) % len(self.instances)

                # Check if instance is healthy
                if (instance_idx < len(self.instance_health) and
                    self.instance_health[instance_idx]):
                    llm = self.instances[instance_idx]
                    logger.debug(f"Serving healthy LLM instance {instance_idx} from pool (request #{self.request_count})")
                    return llm

                attempts += 1

            # If no healthy instances, return first available (fallback)
            if self.instances:
                logger.warning("No healthy instances found, using fallback")
                return self.instances[0]

            # This should not happen, but create emergency instance
            logger.error("No instances available, creating emergency instance")
            return create_llm()

    def _create_pool(self):
        """Create the pool of LLM instances."""
        logger.info(f"Creating LLM pool with {self.pool_size} instances for {self.agent_type}")

        for i in range(self.pool_size):
            try:
                # Always create new instances for the pool to enable true pooling
                if self.agent_type == "default":
                    # Create new instance directly instead of using cache
                    llm = create_llm(llm_config)
                else:
                    llm = get_specialized_llm(self.agent_type)

                self.instances.append(llm)
                self.instance_health.append(True)  # Mark as healthy initially
                self.creation_count += 1
                logger.debug(f"Created pool instance {i+1}/{self.pool_size}")

            except Exception as e:
                logger.error(f"Failed to create pool instance {i+1}: {e}")
                # If we can't create the full pool, work with what we have
                if not self.instances:
                    raise Exception(f"Failed to create any LLM instances for pool: {e}")
                break

        logger.info(f"LLM pool created with {len(self.instances)} instances")

    def _health_check(self):
        """Perform health check on all pool instances."""
        logger.debug(f"Performing health check on {len(self.instances)} instances")

        for i, instance in enumerate(self.instances):
            try:
                # Simple health check - try a minimal inference
                test_response = instance.invoke("Hi", max_tokens=1, temperature=0.1)
                self.instance_health[i] = True
                logger.debug(f"Instance {i} health check: OK")
            except Exception as e:
                self.instance_health[i] = False
                self.failed_requests += 1
                logger.warning(f"Instance {i} health check failed: {e}")

        healthy_count = sum(self.instance_health)
        logger.debug(f"Health check complete: {healthy_count}/{len(self.instances)} instances healthy")

    def get_pool_stats(self) -> Dict[str, Any]:
        """Get statistics about the pool usage."""
        with self._pool_lock:
            return {
                "pool_size": len(self.instances),
                "target_pool_size": self.pool_size,
                "agent_type": self.agent_type,
                "creation_count": self.creation_count,
                "request_count": self.request_count,
                "current_index": self.current_index,
                "instances_created": len(self.instances) > 0,
                "avg_requests_per_instance": self.request_count / max(len(self.instances), 1)
            }

    def optimize_pool_size(self, target_utilization: float = 0.8):
        """Optimize pool size based on usage patterns."""
        with self._pool_lock:
            if self.request_count < 100:  # Need sufficient data
                return

            current_utilization = self.request_count / (len(self.instances) * 100)  # Simplified calculation

            if current_utilization > target_utilization and self.pool_size < 8:
                # Increase pool size
                new_size = min(self.pool_size + 1, 8)
                logger.info(f"Optimizing {self.agent_type} pool size from {self.pool_size} to {new_size}")
                self._expand_pool(new_size - self.pool_size)
                self.pool_size = new_size
            elif current_utilization < target_utilization * 0.5 and self.pool_size > 1:
                # Decrease pool size
                new_size = max(self.pool_size - 1, 1)
                logger.info(f"Optimizing {self.agent_type} pool size from {self.pool_size} to {new_size}")
                self._shrink_pool(self.pool_size - new_size)
                self.pool_size = new_size

    def _expand_pool(self, additional_instances: int):
        """Add more instances to the pool."""
        for i in range(additional_instances):
            try:
                if self.agent_type == "default":
                    llm = create_llm(llm_config)
                else:
                    llm = get_specialized_llm(self.agent_type)

                self.instances.append(llm)
                logger.debug(f"Added instance {len(self.instances)} to {self.agent_type} pool")
            except Exception as e:
                logger.error(f"Failed to expand pool: {e}")
                break

    def _shrink_pool(self, instances_to_remove: int):
        """Remove instances from the pool."""
        for _ in range(min(instances_to_remove, len(self.instances) - 1)):
            if len(self.instances) > 1:  # Keep at least one instance
                removed_instance = self.instances.pop()
                logger.debug(f"Removed instance from {self.agent_type} pool, {len(self.instances)} remaining")

        # Adjust current index if needed
        if self.current_index >= len(self.instances):
            self.current_index = 0

    def invalidate_pool(self):
        """Invalidate the pool, forcing recreation on next request."""
        with self._pool_lock:
            logger.info(f"Invalidating LLM pool for {self.agent_type}")
            self.instances.clear()
            self.current_index = 0
            self.creation_count = 0

# Global pool instances for different agent types
_llm_pools: Dict[str, LLMPool] = {}
_pool_lock = threading.RLock()

def get_pooled_llm(agent_type: str = "default", pool_size: int = 2):
    """
    Get an LLM instance from a connection pool.

    This function provides connection pooling for better concurrent request handling.
    Each agent type gets its own pool with specialized configurations.

    Args:
        agent_type: Type of agent ('researcher', 'writer', 'analyst', 'coordinator', 'default')
        pool_size: Size of the connection pool (default: 2)

    Returns:
        LLM instance from the appropriate pool
    """
    global _llm_pools, _llm_metrics
    _llm_metrics.record_pooled_request()

    with _pool_lock:
        # Create pool if it doesn't exist
        if agent_type not in _llm_pools:
            _llm_pools[agent_type] = LLMPool(pool_size=pool_size, agent_type=agent_type)

        return _llm_pools[agent_type].get_llm()

def get_pool_stats(agent_type: str = None) -> Dict[str, Any]:
    """
    Get statistics for LLM pools.

    Args:
        agent_type: Specific agent type to get stats for, or None for all pools

    Returns:
        Dictionary with pool statistics
    """
    with _pool_lock:
        if agent_type:
            if agent_type in _llm_pools:
                return _llm_pools[agent_type].get_pool_stats()
            else:
                return {"error": f"No pool found for agent type: {agent_type}"}
        else:
            # Return stats for all pools
            return {
                pool_type: pool.get_pool_stats()
                for pool_type, pool in _llm_pools.items()
            }

def invalidate_all_pools():
    """Invalidate all LLM pools."""
    with _pool_lock:
        logger.info("Invalidating all LLM pools")
        for pool in _llm_pools.values():
            pool.invalidate_pool()
        _llm_pools.clear()

# Global metrics tracking
class LLMMetrics:
    """Class to track LLM usage metrics and performance."""

    def __init__(self):
        self.reset_metrics()
        self._metrics_lock = threading.RLock()

    def reset_metrics(self):
        """Reset all metrics to initial state."""
        with getattr(self, '_metrics_lock', threading.RLock()):
            self.cache_hits = 0
            self.cache_misses = 0
            self.specialized_llm_requests = 0
            self.pooled_llm_requests = 0
            self.total_llm_creations = 0
            self.agent_type_requests = {}
            self.start_time = time.time()
            self.last_reset_time = time.time()

    def record_cache_hit(self):
        """Record a cache hit."""
        with self._metrics_lock:
            self.cache_hits += 1

    def record_cache_miss(self):
        """Record a cache miss (new LLM creation)."""
        with self._metrics_lock:
            self.cache_misses += 1
            self.total_llm_creations += 1

    def record_specialized_request(self, agent_type: str):
        """Record a specialized LLM request."""
        with self._metrics_lock:
            self.specialized_llm_requests += 1
            self.agent_type_requests[agent_type] = self.agent_type_requests.get(agent_type, 0) + 1

    def record_pooled_request(self):
        """Record a pooled LLM request."""
        with self._metrics_lock:
            self.pooled_llm_requests += 1

    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        with self._metrics_lock:
            current_time = time.time()
            uptime = current_time - self.start_time
            time_since_reset = current_time - self.last_reset_time

            total_requests = self.cache_hits + self.cache_misses
            cache_hit_rate = (self.cache_hits / total_requests * 100) if total_requests > 0 else 0

            return {
                "uptime_seconds": uptime,
                "time_since_reset_seconds": time_since_reset,
                "cache_hits": self.cache_hits,
                "cache_misses": self.cache_misses,
                "total_requests": total_requests,
                "cache_hit_rate_percent": cache_hit_rate,
                "specialized_llm_requests": self.specialized_llm_requests,
                "pooled_llm_requests": self.pooled_llm_requests,
                "total_llm_creations": self.total_llm_creations,
                "agent_type_requests": self.agent_type_requests.copy(),
                "requests_per_second": total_requests / time_since_reset if time_since_reset > 0 else 0
            }

# Global metrics instance
_llm_metrics = LLMMetrics()

def get_llm_metrics() -> Dict[str, Any]:
    """Get current LLM usage metrics."""
    return _llm_metrics.get_metrics()

def reset_llm_metrics():
    """Reset LLM metrics."""
    _llm_metrics.reset_metrics()
    logger.info("LLM metrics reset")

@cached(ttl=60, key_prefix="llm_health")  # Cache for 1 minute
@monitor_performance("llm_health_check")
def get_llm_health_status() -> Dict[str, Any]:
    """
    Get comprehensive health status of the LLM system.

    Returns:
        Dictionary with health status information
    """
    try:
        # Test basic LLM functionality
        start_time = time.time()
        test_llm = get_llm()
        llm_creation_time = time.time() - start_time

        # Get system information
        cache_info = get_llm_cache_info()
        metrics = get_llm_metrics()
        pool_stats = get_pool_stats()

        # Check if LLM is actually available and test connectivity
        llm_available = test_llm is not None and llm_config.provider != LLMProvider.MOCK
        api_connectivity = False

        # Test API connectivity for OpenAI
        if llm_config.provider == LLMProvider.OPENAI:
            try:
                import openai
                client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                client.models.list()
                api_connectivity = True
            except Exception as e:
                logger.warning(f"OpenAI API connectivity test failed: {e}")
        elif llm_config.provider == LLMProvider.OLLAMA:
            try:
                import requests
                response = requests.get(f"{llm_config.base_url}/api/tags", timeout=5)
                api_connectivity = response.status_code == 200
            except Exception as e:
                logger.warning(f"Ollama connectivity test failed: {e}")
        else:
            api_connectivity = llm_available

        # Calculate health score
        health_score = 100
        issues = []

        if not llm_available:
            health_score -= 50
            issues.append("LLM not available or using mock provider")
        elif not api_connectivity:
            health_score -= 30
            issues.append(f"{llm_config.provider.value} API not accessible")

        if not cache_info["cache_active"]:
            health_score -= 20
            issues.append("LLM cache not active")

        if llm_creation_time > 2.0:  # If LLM creation takes more than 2 seconds
            health_score -= 15
            issues.append(f"Slow LLM creation time: {llm_creation_time:.2f}s")

        if metrics["cache_hit_rate_percent"] < 50 and metrics["total_requests"] > 10:
            health_score -= 10
            issues.append(f"Low cache hit rate: {metrics['cache_hit_rate_percent']:.1f}%")

        # Determine overall status
        if health_score >= 90:
            status = "healthy"
        elif health_score >= 70:
            status = "degraded"
        else:
            status = "unhealthy"

        return {
            "status": status,
            "health_score": max(0, health_score),
            "llm_available": llm_available,
            "llm_creation_time": llm_creation_time,
            "provider": llm_config.provider.value,
            "model": llm_config.model_name,
            "cache_active": cache_info["cache_active"],
            "active_pools": len(pool_stats) if isinstance(pool_stats, dict) else 0,
            "metrics": metrics,
            "issues": issues,
            "timestamp": time.time()
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "error",
            "health_score": 0,
            "error": str(e),
            "timestamp": time.time()
        }

def get_llm_info() -> Dict[str, Any]:
    """Get information about the current LLM configuration."""
    cache_info = get_llm_cache_info()
    pool_info = get_pool_stats()
    metrics = get_llm_metrics()

    return {
        "provider": llm_config.provider.value,
        "model_name": llm_config.model_name,
        "temperature": llm_config.temperature,
        "max_tokens": llm_config.max_tokens,
        "base_url": llm_config.base_url if llm_config.provider == LLMProvider.OLLAMA else None,
        "available": llm_config.provider != LLMProvider.MOCK,
        "cache_active": cache_info["cache_active"],
        "cache_instance_type": cache_info["cache_instance_type"],
        "specialized_agents_supported": True,
        "connection_pooling_supported": True,
        "active_pools": len(pool_info) if isinstance(pool_info, dict) else 0,
        "metrics": metrics
    }

# Hybrid Cloud/Local Management Functions

def set_cloud_mode(enabled: bool = True):
    """Enable or disable cloud mode globally."""
    global llm_config
    llm_config.set_cloud_mode(enabled)

def set_cloud_first(cloud_first: bool = True):
    """Set cloud-first preference globally."""
    global llm_config
    llm_config.set_cloud_first(cloud_first)

def force_local_mode():
    """Force local-only mode (disable cloud)."""
    set_cloud_mode(False)
    logger.info("Forced local-only mode - cloud disabled")

def enable_hybrid_mode(cloud_url: str = None):
    """Enable hybrid cloud/local mode."""
    global llm_config
    if cloud_url:
        llm_config.cloud_url = cloud_url
        llm_config.cloud_enabled = True
    set_cloud_mode(True)
    set_cloud_first(True)
    logger.info("Enabled hybrid cloud/local mode")

def get_hybrid_status() -> Dict[str, Any]:
    """Get current hybrid configuration status."""
    global llm_config
    return llm_config.get_status()

def create_agent_llm(agent_type: str, task_complexity: str = "moderate", force_local: bool = False):
    """
    Create an LLM instance optimized for a specific agent type with intelligent routing.

    Args:
        agent_type: Type of agent ('researcher', 'coder', 'analyst', etc.)
        task_complexity: Complexity level ('simple', 'moderate', 'complex', 'critical')
        force_local: Force local model usage

    Returns:
        Optimized LLM instance for the agent
    """
    complexity_map = {
        'simple': TaskComplexity.SIMPLE,
        'moderate': TaskComplexity.MODERATE,
        'complex': TaskComplexity.COMPLEX,
        'critical': TaskComplexity.CRITICAL
    }

    complexity = complexity_map.get(task_complexity.lower(), TaskComplexity.MODERATE)
    return create_llm(agent_type=agent_type, task_complexity=complexity, force_local=force_local)

def test_cloud_connectivity() -> bool:
    """Test if cloud Ollama endpoint is accessible."""
    global llm_config
    if not llm_config.cloud_url:
        return False

    try:
        import httpx
        response = httpx.get(f"{llm_config.cloud_url}/api/tags", timeout=10)
        return response.status_code == 200
    except Exception as e:
        logger.warning(f"Cloud connectivity test failed: {e}")
        return False

def list_available_models() -> Dict[str, Dict[str, Any]]:
    """List all available models (cloud and local)."""
    global llm_config

    cloud_available = test_cloud_connectivity() if llm_config.cloud_enabled else False

    return {
        "cloud": {
            "available": cloud_available,
            "endpoint": llm_config.cloud_url,
            "models": llm_config.cloud_models
        },
        "local": {
            "available": True,  # Assume local is always available
            "endpoint": llm_config.base_url,
            "models": llm_config.local_models
        }
    }
