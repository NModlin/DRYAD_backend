#!/usr/bin/env python3
"""
DRYAD.AI Model Manager

Production-ready model management system with versioning, integrity verification,
fallback selection, and automatic updates for local LLM models.
"""

import os
import json
import hashlib
import logging
import requests
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from tqdm import tqdm
import threading
import time

logger = logging.getLogger(__name__)

@dataclass
class ModelInfo:
    """Information about a model."""
    name: str
    version: str
    size_bytes: int
    sha256_hash: str
    download_url: str
    description: str
    requirements: Dict[str, Any]
    performance_metrics: Dict[str, float]
    created_at: str
    last_used: Optional[str] = None
    usage_count: int = 0
    is_verified: bool = False
    is_active: bool = False

@dataclass
class SystemRequirements:
    """System requirements for model selection."""
    available_memory_gb: float
    cpu_cores: int
    has_gpu: bool = False
    gpu_memory_gb: float = 0.0
    disk_space_gb: float = 0.0

class ModelRegistry:
    """Registry of available models with metadata."""
    
    def __init__(self):
        self.models = {
            # Ultra-fast lightweight model for basic queries
            "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf": ModelInfo(
                name="tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
                version="1.0.0",
                size_bytes=669000000,  # ~669MB
                sha256_hash="",  # Will be updated after download
                download_url="https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
                description="Ultra-fast 1.1B parameter model for basic queries and rapid responses",
                requirements={"min_memory_gb": 1.5, "min_cpu_cores": 2},
                performance_metrics={"tokens_per_second": 20.0, "quality_score": 6.5, "response_time_ms": 800},
                created_at=datetime.now().isoformat()
            ),

            # Balanced model for general use
            "llama-2-7b-chat.Q4_K_M.gguf": ModelInfo(
                name="llama-2-7b-chat.Q4_K_M.gguf",
                version="1.0.0",
                size_bytes=4080000000,  # ~4GB
                sha256_hash="",  # Will be updated after download
                download_url="https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.Q4_K_M.gguf",
                description="Balanced 7B parameter model with good quality and reasonable speed",
                requirements={"min_memory_gb": 6.0, "min_cpu_cores": 4},
                performance_metrics={"tokens_per_second": 8.0, "quality_score": 8.5, "response_time_ms": 3000},
                created_at=datetime.now().isoformat()
            ),

            # High-quality model for complex reasoning
            "llama-2-13b-chat.Q4_K_M.gguf": ModelInfo(
                name="llama-2-13b-chat.Q4_K_M.gguf",
                version="1.0.0",
                size_bytes=7870000000,  # ~7.8GB
                sha256_hash="",  # Will be updated after download
                download_url="https://huggingface.co/TheBloke/Llama-2-13B-Chat-GGUF/resolve/main/llama-2-13b-chat.Q4_K_M.gguf",
                description="High-quality 13B parameter model for complex reasoning and analysis",
                requirements={"min_memory_gb": 12.0, "min_cpu_cores": 6},
                performance_metrics={"tokens_per_second": 4.0, "quality_score": 9.2, "response_time_ms": 6000},
                created_at=datetime.now().isoformat()
            ),
            "llama-2-7b-chat.Q4_K_M.gguf": ModelInfo(
                name="llama-2-7b-chat.Q4_K_M.gguf",
                version="2.0.0",
                size_bytes=4080000000,  # ~4.08GB
                sha256_hash="",
                download_url="https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.Q4_K_M.gguf",
                description="High-quality 7B parameter model with excellent reasoning capabilities",
                requirements={"min_memory_gb": 6.0, "min_cpu_cores": 4},
                performance_metrics={"tokens_per_second": 8.0, "quality_score": 8.5},
                created_at=datetime.now().isoformat()
            ),
            "llama-2-13b-chat.Q4_K_M.gguf": ModelInfo(
                name="llama-2-13b-chat.Q4_K_M.gguf",
                version="2.1.0",
                size_bytes=7370000000,  # ~7.37GB
                sha256_hash="",
                download_url="https://huggingface.co/TheBloke/Llama-2-13B-Chat-GGUF/resolve/main/llama-2-13b-chat.Q4_K_M.gguf",
                description="Large 13B parameter model for complex reasoning tasks",
                requirements={"min_memory_gb": 10.0, "min_cpu_cores": 8},
                performance_metrics={"tokens_per_second": 4.0, "quality_score": 9.2},
                created_at=datetime.now().isoformat()
            )
        }

class ModelManager:
    """Production-ready model management system."""
    
    def __init__(self, models_dir: str = "./models"):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(exist_ok=True)
        
        self.registry = ModelRegistry()
        self.metadata_file = self.models_dir / "model_metadata.json"
        self.lock = threading.RLock()
        
        # Load existing metadata
        self._load_metadata()
        
        # System requirements
        self.system_requirements = self._detect_system_requirements()
        
        logger.info(f"ModelManager initialized with {len(self.registry.models)} available models")
        logger.info(f"System requirements: {self.system_requirements}")
    
    def _detect_system_requirements(self) -> SystemRequirements:
        """Detect system capabilities for model selection."""
        import psutil
        
        # Get memory info
        memory = psutil.virtual_memory()
        available_memory_gb = memory.available / (1024**3)
        
        # Get CPU info
        cpu_cores = psutil.cpu_count(logical=False) or 4
        
        # Get disk space
        disk_usage = psutil.disk_usage(str(self.models_dir))
        disk_space_gb = disk_usage.free / (1024**3)
        
        # Check for GPU (basic check)
        has_gpu = False
        gpu_memory_gb = 0.0
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                has_gpu = True
                gpu_memory_gb = max(gpu.memoryTotal / 1024 for gpu in gpus)
        except ImportError:
            pass
        
        return SystemRequirements(
            available_memory_gb=available_memory_gb,
            cpu_cores=cpu_cores,
            has_gpu=has_gpu,
            gpu_memory_gb=gpu_memory_gb,
            disk_space_gb=disk_space_gb
        )
    
    def _load_metadata(self):
        """Load model metadata from disk."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    metadata = json.load(f)
                
                # Update registry with saved metadata
                for model_name, model_data in metadata.items():
                    if model_name in self.registry.models:
                        # Update with saved data
                        saved_model = ModelInfo(**model_data)
                        self.registry.models[model_name] = saved_model
                
                logger.info(f"Loaded metadata for {len(metadata)} models")
            except Exception as e:
                logger.error(f"Failed to load model metadata: {e}")
    
    def _save_metadata(self):
        """Save model metadata to disk."""
        try:
            metadata = {}
            for model_name, model_info in self.registry.models.items():
                metadata[model_name] = asdict(model_info)
            
            with open(self.metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.debug("Model metadata saved successfully")
        except Exception as e:
            logger.error(f"Failed to save model metadata: {e}")
    
    def get_recommended_model(self, preference: str = "balanced") -> Optional[str]:
        """
        Get the best model for the current system and use case.

        Args:
            preference: "fast", "balanced", or "quality"
        """
        suitable_models = []

        for model_name, model_info in self.registry.models.items():
            # Check if model meets system requirements
            req_memory = model_info.requirements.get("min_memory_gb", 0)
            req_cores = model_info.requirements.get("min_cpu_cores", 0)

            if (self.system_requirements.available_memory_gb >= req_memory and
                self.system_requirements.cpu_cores >= req_cores):

                # Calculate suitability score based on preference
                memory_ratio = self.system_requirements.available_memory_gb / req_memory
                quality_score = model_info.performance_metrics.get("quality_score", 0)
                speed_score = model_info.performance_metrics.get("tokens_per_second", 0)

                if preference == "fast":
                    # Prioritize speed over quality
                    suitability_score = (speed_score * 0.7 + quality_score * 0.3) * min(memory_ratio, 2.0)
                elif preference == "quality":
                    # Prioritize quality over speed
                    suitability_score = (quality_score * 0.8 + speed_score * 0.2) * min(memory_ratio, 2.0)
                else:  # balanced
                    # Balance speed and quality
                    suitability_score = (quality_score * 0.6 + speed_score * 0.4) * min(memory_ratio, 2.0)

                suitable_models.append((model_name, suitability_score))
        
        if suitable_models:
            # Sort by suitability score and return the best
            suitable_models.sort(key=lambda x: x[1], reverse=True)
            recommended_model = suitable_models[0][0]
            
            logger.info(f"Recommended model: {recommended_model} (score: {suitable_models[0][1]:.2f})")
            return recommended_model
        
        # Fallback to smallest model
        smallest_model = min(self.registry.models.items(), key=lambda x: x[1].size_bytes)
        logger.warning(f"No suitable model found, falling back to smallest: {smallest_model[0]}")
        return smallest_model[0]
    
    def is_model_available(self, model_name: str) -> bool:
        """Check if a model is downloaded and verified."""
        if model_name not in self.registry.models:
            return False
        
        model_path = self.models_dir / model_name
        if not model_path.exists():
            return False
        
        model_info = self.registry.models[model_name]
        return model_info.is_verified
    
    def get_model_path(self, model_name: Optional[str] = None) -> Path:
        """Get the path to a model, downloading if necessary."""
        if model_name is None:
            model_name = self.get_recommended_model()
        
        if not model_name:
            raise RuntimeError("No suitable model available")
        
        model_path = self.models_dir / model_name
        
        # Download if not available
        if not self.is_model_available(model_name):
            logger.info(f"Model {model_name} not available, downloading...")
            self.download_model(model_name)
        
        # Update usage statistics
        self._update_model_usage(model_name)
        
        return model_path

    def get_model_for_query(self, query: str, max_response_time_ms: Optional[int] = None) -> str:
        """
        Select the best model based on query complexity and performance requirements.

        Args:
            query: The input query to analyze
            max_response_time_ms: Maximum acceptable response time in milliseconds

        Returns:
            Model name best suited for the query
        """
        # Analyze query complexity
        complexity = self._analyze_query_complexity(query)

        # Get suitable models based on system resources
        suitable_models = []
        for model_name, model_info in self.registry.models.items():
            req_memory = model_info.requirements.get("min_memory_gb", 0)
            req_cores = model_info.requirements.get("min_cpu_cores", 0)

            if (self.system_requirements.available_memory_gb >= req_memory and
                self.system_requirements.cpu_cores >= req_cores):

                # Check response time requirement
                model_response_time = model_info.performance_metrics.get("response_time_ms", 5000)
                if max_response_time_ms and model_response_time > max_response_time_ms:
                    continue

                suitable_models.append((model_name, model_info))

        if not suitable_models:
            # Fallback to smallest available model
            return self.get_recommended_model("fast")

        # Select model based on complexity
        if complexity == "simple":
            # Use fastest model for simple queries
            best_model = min(suitable_models,
                           key=lambda x: x[1].performance_metrics.get("response_time_ms", 5000))
        elif complexity == "complex":
            # Use highest quality model for complex queries
            best_model = max(suitable_models,
                           key=lambda x: x[1].performance_metrics.get("quality_score", 0))
        else:  # medium complexity
            # Balance speed and quality
            best_model = max(suitable_models,
                           key=lambda x: (x[1].performance_metrics.get("quality_score", 0) * 0.6 +
                                        (20 - x[1].performance_metrics.get("response_time_ms", 5000) / 1000) * 0.4))

        return best_model[0]

    def _analyze_query_complexity(self, query: str) -> str:
        """
        Analyze query complexity to determine appropriate model.

        Returns:
            "simple", "medium", or "complex"
        """
        query_lower = query.lower()
        word_count = len(query.split())

        # Simple queries (use fast model)
        simple_patterns = [
            "what is", "who is", "when is", "where is", "how much", "how many",
            "define", "explain briefly", "yes or no", "true or false"
        ]

        # Complex queries (use quality model)
        complex_patterns = [
            "analyze", "compare", "evaluate", "research", "write", "create",
            "develop", "design", "plan", "strategy", "comprehensive", "detailed"
        ]

        if word_count <= 5 or any(pattern in query_lower for pattern in simple_patterns):
            return "simple"
        elif word_count >= 20 or any(pattern in query_lower for pattern in complex_patterns):
            return "complex"
        else:
            return "medium"

    def download_model(self, model_name: str, force: bool = False) -> bool:
        """Download a model with integrity verification."""
        if model_name not in self.registry.models:
            raise ValueError(f"Unknown model: {model_name}")

        model_info = self.registry.models[model_name]
        model_path = self.models_dir / model_name

        # Check if already downloaded and verified
        if not force and self.is_model_available(model_name):
            logger.info(f"Model {model_name} already available")
            return True

        with self.lock:
            try:
                logger.info(f"Downloading model: {model_name}")
                logger.info(f"Size: {model_info.size_bytes / (1024**3):.2f} GB")
                logger.info(f"URL: {model_info.download_url}")

                # Check disk space
                required_space = model_info.size_bytes * 1.2  # 20% buffer
                if self.system_requirements.disk_space_gb * (1024**3) < required_space:
                    raise RuntimeError(f"Insufficient disk space. Required: {required_space / (1024**3):.2f} GB")

                # Download with progress bar
                response = requests.get(model_info.download_url, stream=True)
                response.raise_for_status()

                total_size = int(response.headers.get('content-length', model_info.size_bytes))

                # Create temporary file
                temp_path = model_path.with_suffix('.tmp')

                with open(temp_path, 'wb') as f, tqdm(
                    desc=f"Downloading {model_name}",
                    total=total_size,
                    unit='B',
                    unit_scale=True,
                    unit_divisor=1024,
                ) as pbar:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            pbar.update(len(chunk))

                # Verify integrity
                logger.info("Verifying model integrity...")
                if self._verify_model_integrity(temp_path, model_info):
                    # Move to final location
                    shutil.move(str(temp_path), str(model_path))

                    # Update model info
                    model_info.is_verified = True
                    model_info.last_used = datetime.now().isoformat()
                    self._save_metadata()

                    logger.info(f"✅ Model {model_name} downloaded and verified successfully")
                    return True
                else:
                    # Clean up failed download
                    if temp_path.exists():
                        temp_path.unlink()
                    raise RuntimeError("Model integrity verification failed")

            except Exception as e:
                logger.error(f"❌ Failed to download model {model_name}: {e}")
                # Clean up partial download
                temp_path = model_path.with_suffix('.tmp')
                if temp_path.exists():
                    temp_path.unlink()
                return False

    def _verify_model_integrity(self, model_path: Path, model_info: ModelInfo) -> bool:
        """Verify model file integrity using SHA256 hash."""
        try:
            # Calculate SHA256 hash
            sha256_hash = hashlib.sha256()
            with open(model_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)

            calculated_hash = sha256_hash.hexdigest()

            # If we don't have a stored hash, store the calculated one
            if not model_info.sha256_hash:
                model_info.sha256_hash = calculated_hash
                logger.info(f"Stored SHA256 hash for {model_info.name}: {calculated_hash[:16]}...")
                return True

            # Verify against stored hash
            if calculated_hash == model_info.sha256_hash:
                logger.info("✅ Model integrity verification passed")
                return True
            else:
                logger.error(f"❌ Model integrity verification failed")
                logger.error(f"Expected: {model_info.sha256_hash}")
                logger.error(f"Calculated: {calculated_hash}")
                return False

        except Exception as e:
            logger.error(f"Failed to verify model integrity: {e}")
            return False

    def _update_model_usage(self, model_name: str):
        """Update model usage statistics."""
        if model_name in self.registry.models:
            model_info = self.registry.models[model_name]
            model_info.usage_count += 1
            model_info.last_used = datetime.now().isoformat()
            model_info.is_active = True
            self._save_metadata()

    def cleanup_old_models(self, keep_count: int = 2, max_age_days: int = 30) -> List[str]:
        """Clean up old or unused models to free disk space."""
        removed_models = []

        with self.lock:
            try:
                # Get models sorted by last used (oldest first)
                models_by_usage = []
                for model_name, model_info in self.registry.models.items():
                    model_path = self.models_dir / model_name
                    if model_path.exists():
                        last_used = datetime.fromisoformat(model_info.last_used) if model_info.last_used else datetime.min
                        models_by_usage.append((model_name, last_used, model_path))

                models_by_usage.sort(key=lambda x: x[1])

                # Keep the most recently used models
                models_to_remove = models_by_usage[:-keep_count] if len(models_by_usage) > keep_count else []

                # Also remove models older than max_age_days
                cutoff_date = datetime.now() - timedelta(days=max_age_days)
                for model_name, last_used, model_path in models_by_usage:
                    if last_used < cutoff_date and (model_name, last_used, model_path) not in models_to_remove:
                        models_to_remove.append((model_name, last_used, model_path))

                # Remove old models
                for model_name, last_used, model_path in models_to_remove:
                    try:
                        model_path.unlink()
                        self.registry.models[model_name].is_verified = False
                        self.registry.models[model_name].is_active = False
                        removed_models.append(model_name)
                        logger.info(f"Removed old model: {model_name}")
                    except Exception as e:
                        logger.error(f"Failed to remove model {model_name}: {e}")

                if removed_models:
                    self._save_metadata()
                    logger.info(f"Cleaned up {len(removed_models)} old models")

            except Exception as e:
                logger.error(f"Failed to cleanup old models: {e}")

        return removed_models

    def get_model_info(self, model_name: str) -> Optional[ModelInfo]:
        """Get detailed information about a model."""
        return self.registry.models.get(model_name)

    def list_available_models(self) -> List[Dict[str, Any]]:
        """List all available models with their status."""
        models = []
        for model_name, model_info in self.registry.models.items():
            model_path = self.models_dir / model_name
            is_downloaded = model_path.exists()

            models.append({
                "name": model_name,
                "version": model_info.version,
                "size_gb": model_info.size_bytes / (1024**3),
                "description": model_info.description,
                "is_downloaded": is_downloaded,
                "is_verified": model_info.is_verified,
                "is_active": model_info.is_active,
                "usage_count": model_info.usage_count,
                "last_used": model_info.last_used,
                "performance_metrics": model_info.performance_metrics,
                "requirements": model_info.requirements
            })

        return models

    def benchmark_model(self, model_name: str, test_prompts: List[str] = None) -> Dict[str, float]:
        """Benchmark a model's performance."""
        if not self.is_model_available(model_name):
            raise ValueError(f"Model {model_name} is not available")

        if test_prompts is None:
            test_prompts = [
                "What is artificial intelligence?",
                "Explain quantum computing in simple terms.",
                "Write a short story about a robot."
            ]

        try:
            # Import here to avoid circular dependencies
            from app.core.llm_config import LLMConfig, _create_llamacpp_llm

            # Create temporary config for this model
            config = LLMConfig()
            config.model_name = model_name

            # Override model path
            original_model_path = os.environ.get("LLAMACPP_MODEL_PATH", "./models/")
            os.environ["LLAMACPP_MODEL_PATH"] = str(self.models_dir)

            try:
                # Create LLM instance
                llm = _create_llamacpp_llm(config)

                # Run benchmarks
                total_tokens = 0
                total_time = 0
                response_lengths = []

                for prompt in test_prompts:
                    start_time = time.time()
                    response = llm.invoke(prompt)
                    end_time = time.time()

                    response_text = response.content if hasattr(response, 'content') else str(response)
                    response_length = len(response_text.split())

                    total_tokens += response_length
                    total_time += (end_time - start_time)
                    response_lengths.append(response_length)

                # Calculate metrics
                avg_tokens_per_second = total_tokens / total_time if total_time > 0 else 0
                avg_response_length = sum(response_lengths) / len(response_lengths)
                avg_response_time = total_time / len(test_prompts)

                metrics = {
                    "tokens_per_second": avg_tokens_per_second,
                    "avg_response_time": avg_response_time,
                    "avg_response_length": avg_response_length,
                    "total_test_time": total_time
                }

                # Update model performance metrics
                model_info = self.registry.models[model_name]
                model_info.performance_metrics.update(metrics)
                self._save_metadata()

                logger.info(f"Benchmarked {model_name}: {avg_tokens_per_second:.2f} tokens/sec")
                return metrics

            finally:
                # Restore original model path
                if original_model_path:
                    os.environ["LLAMACPP_MODEL_PATH"] = original_model_path
                else:
                    os.environ.pop("LLAMACPP_MODEL_PATH", None)

        except Exception as e:
            logger.error(f"Failed to benchmark model {model_name}: {e}")
            return {}

    def get_system_status(self) -> Dict[str, Any]:
        """Get system status and model management information."""
        downloaded_models = sum(1 for name in self.registry.models if self.is_model_available(name))
        total_size = sum(
            self.registry.models[name].size_bytes
            for name in self.registry.models
            if self.is_model_available(name)
        )

        return {
            "models_directory": str(self.models_dir),
            "total_models": len(self.registry.models),
            "downloaded_models": downloaded_models,
            "total_size_gb": total_size / (1024**3),
            "system_requirements": asdict(self.system_requirements),
            "recommended_model": self.get_recommended_model(),
            "disk_usage": {
                "free_space_gb": self.system_requirements.disk_space_gb,
                "models_size_gb": total_size / (1024**3)
            }
        }

# Global model manager instance
model_manager = ModelManager()
