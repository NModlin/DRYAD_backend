"""
Multi-Modal Processing Core for Phase 7.

This module provides comprehensive multi-modal processing capabilities including:
- Audio processing (speech-to-text, text-to-speech)
- Video processing and analysis
- Image processing and computer vision
- Multi-modal data fusion and unified processing pipeline
"""

import os
import io
import logging
import tempfile
import asyncio
from typing import Dict, Any, List, Optional, Union, BinaryIO
from pathlib import Path
from datetime import datetime

import numpy as np
from PIL import Image

# Optional imports with fallbacks
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

logger = logging.getLogger(__name__)

# Log OpenCV availability after logger is defined
if not CV2_AVAILABLE:
    logger.warning("OpenCV not available - video processing limited")

def get_optimal_device() -> str:
    """
    Detect optimal device for multimodal processing.

    Returns:
        str: Device string ('cuda' or 'cpu')
    """
    # Check for CPU-only override
    if os.getenv("FORCE_CPU", "false").lower() == "true":
        logger.info("Multimodal processing using CPU (FORCE_CPU enabled)")
        return "cpu"

    try:
        import torch
        if torch.cuda.is_available():
            device = "cuda"
            gpu_name = torch.cuda.get_device_name(0)
            logger.info(f"Multimodal processing using GPU: {gpu_name}")
            return device
    except ImportError:
        logger.debug("PyTorch not available for GPU detection")
    except Exception as e:
        logger.warning(f"GPU detection failed: {e}")

    logger.info("Multimodal processing using CPU")
    return "cpu"


class MultiModalProcessor:
    """
    Comprehensive multi-modal processing system for audio, video, and image content.
    
    Provides unified interface for processing different media types with fallback
    mechanisms when optional dependencies are not available.
    """
    
    def __init__(self):
        self.audio_processor = AudioProcessor()
        self.video_processor = VideoProcessor()
        self.image_processor = ImageProcessor()
        self.fusion_processor = MultiModalFusionProcessor()
        
        # Check available capabilities
        self.capabilities = self._check_capabilities()
        logger.info(f"MultiModal processor initialized with capabilities: {list(self.capabilities.keys())}")
    
    def _check_capabilities(self) -> Dict[str, bool]:
        """Check which multi-modal capabilities are available."""
        capabilities = {}
        
        # Check audio capabilities
        try:
            import whisper
            import pydub
            capabilities['audio_transcription'] = True
        except ImportError:
            capabilities['audio_transcription'] = False
            logger.warning("Audio transcription not available - install whisper and pydub")
        
        try:
            import pyttsx3
            capabilities['text_to_speech'] = True
        except ImportError:
            capabilities['text_to_speech'] = False
            logger.warning("Text-to-speech not available - install pyttsx3")
        
        # Check video capabilities
        try:
            import ffmpeg
            capabilities['video_processing'] = CV2_AVAILABLE  # Requires both ffmpeg and opencv
        except ImportError:
            capabilities['video_processing'] = False
            logger.warning("Video processing not available - install ffmpeg-python and opencv-python")
        
        # Check image capabilities
        try:
            import torch
            import torchvision
            capabilities['advanced_image_processing'] = True
        except ImportError:
            capabilities['advanced_image_processing'] = False
            logger.warning("Advanced image processing not available - install torch and torchvision")
        
        # Basic image processing is always available (PIL/OpenCV)
        capabilities['basic_image_processing'] = True
        
        return capabilities
    
    async def process_media(self, media_data: bytes, media_type: str, 
                          processing_options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Unified media processing interface.
        
        Args:
            media_data: Raw media data as bytes
            media_type: Type of media ('audio', 'video', 'image')
            processing_options: Optional processing parameters
            
        Returns:
            Dictionary containing processing results and metadata
        """
        try:
            start_time = datetime.now()
            
            if media_type == 'audio':
                result = await self.audio_processor.process_audio(media_data, processing_options)
            elif media_type == 'video':
                result = await self.video_processor.process_video(media_data, processing_options)
            elif media_type == 'image':
                result = await self.image_processor.process_image(media_data, processing_options)
            else:
                raise ValueError(f"Unsupported media type: {media_type}")
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "success": True,
                "media_type": media_type,
                "processing_time": processing_time,
                "capabilities_used": [cap for cap, available in self.capabilities.items() if available],
                "result": result,
                "timestamp": start_time.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Media processing failed for {media_type}: {e}")
            return {
                "success": False,
                "media_type": media_type,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def fuse_multimodal_data(self, media_results: List[Dict[str, Any]], 
                                 fusion_strategy: str = "concatenate") -> Dict[str, Any]:
        """
        Fuse results from multiple media types into unified output.
        
        Args:
            media_results: List of processing results from different media types
            fusion_strategy: Strategy for fusion ('concatenate', 'weighted', 'semantic')
            
        Returns:
            Fused multi-modal result
        """
        return await self.fusion_processor.fuse_results(media_results, fusion_strategy)


class AudioProcessor:
    """Audio processing capabilities including speech-to-text and text-to-speech."""
    
    def __init__(self):
        self.whisper_model = None
        self.tts_engine = None
        self.device = get_optimal_device()
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize audio processing models with fallback handling."""
        try:
            import whisper
            # Load Whisper model with GPU support when available
            self.whisper_model = whisper.load_model("base", device=self.device)
            logger.info(f"Whisper model loaded successfully on {self.device}")
        except ImportError:
            logger.warning("Whisper not available - speech-to-text disabled")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            # Fallback to CPU if GPU loading fails
            if self.device == "cuda":
                try:
                    import whisper
                    self.whisper_model = whisper.load_model("base", device="cpu")
                    logger.info("Whisper model loaded successfully on CPU (GPU fallback)")
                except Exception as fallback_e:
                    logger.error(f"CPU fallback also failed: {fallback_e}")
        
        try:
            import pyttsx3
            self.tts_engine = pyttsx3.init()
            logger.info("TTS engine initialized successfully")
        except ImportError:
            logger.warning("pyttsx3 not available - text-to-speech disabled")
        except Exception as e:
            logger.error(f"Failed to initialize TTS engine: {e}")
    
    async def process_audio(self, audio_data: bytes, 
                          options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process audio data with various operations.
        
        Args:
            audio_data: Raw audio data
            options: Processing options (transcribe, analyze, etc.)
            
        Returns:
            Audio processing results
        """
        options = options or {}
        results = {}
        
        # Save audio data to temporary file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_file.write(audio_data)
            temp_path = temp_file.name
        
        try:
            # Speech-to-text transcription
            if options.get('transcribe', True) and self.whisper_model:
                transcription = await self._transcribe_audio(temp_path)
                results['transcription'] = transcription
            
            # Audio analysis
            if options.get('analyze', False):
                analysis = await self._analyze_audio(temp_path)
                results['analysis'] = analysis
            
            # Audio metadata
            metadata = await self._extract_audio_metadata(temp_path)
            results['metadata'] = metadata
            
        finally:
            # Cleanup temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        
        return results
    
    async def _transcribe_audio(self, audio_path: str) -> Dict[str, Any]:
        """Transcribe audio using Whisper."""
        if not self.whisper_model:
            return {"error": "Whisper model not available"}
        
        try:
            result = self.whisper_model.transcribe(audio_path)
            return {
                "text": result["text"],
                "language": result.get("language", "unknown"),
                "segments": result.get("segments", [])
            }
        except Exception as e:
            logger.error(f"Audio transcription failed: {e}")
            return {"error": str(e)}
    
    async def _analyze_audio(self, audio_path: str) -> Dict[str, Any]:
        """Analyze audio characteristics."""
        try:
            # Basic audio analysis using librosa if available
            try:
                import librosa
                y, sr = librosa.load(audio_path)
                
                return {
                    "duration": len(y) / sr,
                    "sample_rate": sr,
                    "channels": 1 if y.ndim == 1 else y.shape[0],
                    "rms_energy": float(np.sqrt(np.mean(y**2))),
                    "zero_crossing_rate": float(np.mean(librosa.feature.zero_crossing_rate(y)))
                }
            except ImportError:
                # Fallback to basic analysis
                return {"message": "Advanced audio analysis not available - install librosa"}
                
        except Exception as e:
            logger.error(f"Audio analysis failed: {e}")
            return {"error": str(e)}
    
    async def _extract_audio_metadata(self, audio_path: str) -> Dict[str, Any]:
        """Extract basic audio metadata."""
        try:
            file_size = os.path.getsize(audio_path)
            return {
                "file_size": file_size,
                "format": Path(audio_path).suffix.lower(),
                "processed_at": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": str(e)}

    async def enhanced_transcribe_audio(self, audio_path: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced audio transcription with multiple providers and options."""
        transcription_results = {}

        # Try Whisper first (local)
        if self.whisper_model:
            try:
                result = self.whisper_model.transcribe(
                    audio_path,
                    language=options.get("language"),
                    task=options.get("task", "transcribe"),
                    temperature=options.get("temperature", 0.0)
                )

                transcription_results["whisper"] = {
                    "text": result["text"],
                    "language": result.get("language", "unknown"),
                    "segments": result.get("segments", []),
                    "confidence": self._calculate_confidence(result.get("segments", [])),
                    "provider": "whisper_local"
                }
            except Exception as e:
                logger.error(f"Whisper transcription failed: {e}")
                transcription_results["whisper"] = {"error": str(e)}

        # Try OpenAI Whisper API if available
        if options.get("use_openai_whisper", False):
            try:
                from app.core.llm_config import get_openai_client
                client = get_openai_client()

                if client:
                    with open(audio_path, "rb") as audio_file:
                        transcript = client.audio.transcriptions.create(
                            model="whisper-1",
                            file=audio_file,
                            language=options.get("language"),
                            response_format="verbose_json"
                        )

                    transcription_results["openai_whisper"] = {
                        "text": transcript.text,
                        "language": transcript.language,
                        "duration": transcript.duration,
                        "segments": getattr(transcript, 'segments', []),
                        "provider": "openai_whisper"
                    }
            except Exception as e:
                logger.error(f"OpenAI Whisper transcription failed: {e}")
                transcription_results["openai_whisper"] = {"error": str(e)}

        # Return best result or combined results
        if options.get("combine_results", False):
            return transcription_results
        else:
            # Return the best available result
            for provider in ["openai_whisper", "whisper"]:
                if provider in transcription_results and not transcription_results[provider].get("error"):
                    return transcription_results[provider]

            # Return error if all failed
            return {"error": "All transcription providers failed", "details": transcription_results}

    def _calculate_confidence(self, segments: List[Dict]) -> float:
        """Calculate average confidence from segments."""
        if not segments:
            return 0.0

        confidences = []
        for segment in segments:
            if "avg_logprob" in segment:
                # Convert log probability to confidence score
                confidence = min(1.0, max(0.0, (segment["avg_logprob"] + 1.0)))
                confidences.append(confidence)

        return sum(confidences) / len(confidences) if confidences else 0.5
    
    async def text_to_speech(self, text: str, output_path: Optional[str] = None) -> Dict[str, Any]:
        """Convert text to speech."""
        if not self.tts_engine:
            return {"error": "TTS engine not available"}
        
        try:
            if output_path:
                self.tts_engine.save_to_file(text, output_path)
                return {"success": True, "output_path": output_path}
            else:
                # For in-memory TTS, we'd need a different approach
                return {"error": "In-memory TTS not implemented"}
                
        except Exception as e:
            logger.error(f"Text-to-speech failed: {e}")
            return {"error": str(e)}


class VideoProcessor:
    """Video processing and analysis capabilities."""
    
    def __init__(self):
        self.ffmpeg_available = self._check_ffmpeg()
    
    def _check_ffmpeg(self) -> bool:
        """Check if ffmpeg is available."""
        try:
            import ffmpeg
            return True
        except ImportError:
            logger.warning("ffmpeg-python not available - video processing limited")
            return False
    
    async def process_video(self, video_data: bytes, 
                          options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process video data with various operations.
        
        Args:
            video_data: Raw video data
            options: Processing options
            
        Returns:
            Video processing results
        """
        options = options or {}
        results = {}
        
        # Save video data to temporary file
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
            temp_file.write(video_data)
            temp_path = temp_file.name
        
        try:
            # Extract frames
            if options.get('extract_frames', False):
                frames = await self._extract_frames(temp_path, options.get('frame_count', 10))
                results['frames'] = frames
            
            # Extract audio and transcribe
            if options.get('transcribe_audio', True):
                audio_transcription = await self._extract_and_transcribe_audio(temp_path)
                results['audio_transcription'] = audio_transcription
            
            # Video analysis
            if options.get('analyze', False):
                analysis = await self._analyze_video(temp_path)
                results['analysis'] = analysis
            
            # Video metadata
            metadata = await self._extract_video_metadata(temp_path)
            results['metadata'] = metadata
            
        finally:
            # Cleanup temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        
        return results
    
    async def _extract_frames(self, video_path: str, frame_count: int = 10) -> List[Dict[str, Any]]:
        """Extract frames from video."""
        if not CV2_AVAILABLE:
            return [{"error": "OpenCV not available for frame extraction"}]

        try:
            cap = cv2.VideoCapture(video_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            if total_frames == 0:
                return []

            frame_indices = np.linspace(0, total_frames - 1, frame_count, dtype=int)
            frames = []

            for i, frame_idx in enumerate(frame_indices):
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()

                if ret:
                    # Convert frame to base64 for storage/transmission
                    _, buffer = cv2.imencode('.jpg', frame)
                    frame_data = buffer.tobytes()

                    frames.append({
                        "frame_index": int(frame_idx),
                        "timestamp": frame_idx / cap.get(cv2.CAP_PROP_FPS),
                        "size": len(frame_data),
                        "dimensions": (frame.shape[1], frame.shape[0])
                    })

            cap.release()
            return frames

        except Exception as e:
            logger.error(f"Frame extraction failed: {e}")
            return []
    
    async def _extract_and_transcribe_audio(self, video_path: str) -> Dict[str, Any]:
        """Extract audio from video and transcribe it."""
        if not self.ffmpeg_available:
            return {"error": "ffmpeg not available for audio extraction"}
        
        try:
            import ffmpeg
            
            # Extract audio to temporary file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
                audio_path = temp_audio.name
            
            try:
                # Extract audio using ffmpeg
                (
                    ffmpeg
                    .input(video_path)
                    .output(audio_path, acodec='pcm_s16le', ac=1, ar='16000')
                    .overwrite_output()
                    .run(quiet=True)
                )
                
                # Transcribe using audio processor
                audio_processor = AudioProcessor()
                with open(audio_path, 'rb') as f:
                    audio_data = f.read()
                
                transcription_result = await audio_processor.process_audio(
                    audio_data, {'transcribe': True}
                )
                
                return transcription_result.get('transcription', {})
                
            finally:
                if os.path.exists(audio_path):
                    os.unlink(audio_path)
                    
        except Exception as e:
            logger.error(f"Video audio transcription failed: {e}")
            return {"error": str(e)}
    
    async def _analyze_video(self, video_path: str) -> Dict[str, Any]:
        """Analyze video characteristics."""
        if not CV2_AVAILABLE:
            return {"error": "OpenCV not available for video analysis"}

        try:
            cap = cv2.VideoCapture(video_path)

            analysis = {
                "frame_count": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
                "fps": cap.get(cv2.CAP_PROP_FPS),
                "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                "duration": cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS)
            }

            cap.release()
            return analysis

        except Exception as e:
            logger.error(f"Video analysis failed: {e}")
            return {"error": str(e)}
    
    async def _extract_video_metadata(self, video_path: str) -> Dict[str, Any]:
        """Extract video metadata."""
        try:
            file_size = os.path.getsize(video_path)
            return {
                "file_size": file_size,
                "format": Path(video_path).suffix.lower(),
                "processed_at": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": str(e)}


class ImageProcessor:
    """Image processing and computer vision capabilities."""
    
    def __init__(self):
        self.torch_available = self._check_torch()
    
    def _check_torch(self) -> bool:
        """Check if PyTorch is available for advanced image processing."""
        try:
            import torch
            import torchvision
            return True
        except ImportError:
            logger.warning("PyTorch not available - advanced image processing disabled")
            return False
    
    async def process_image(self, image_data: bytes, 
                          options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process image data with various operations.
        
        Args:
            image_data: Raw image data
            options: Processing options
            
        Returns:
            Image processing results
        """
        options = options or {}
        results = {}
        
        try:
            # Load image
            image = Image.open(io.BytesIO(image_data))
            
            # Basic image analysis
            analysis = await self._analyze_image(image)
            results['analysis'] = analysis
            
            # Object detection (if available)
            if options.get('detect_objects', False) and self.torch_available:
                objects = await self._detect_objects(image)
                results['objects'] = objects
            
            # Image enhancement
            if options.get('enhance', False):
                enhanced = await self._enhance_image(image)
                results['enhanced'] = enhanced
            
            # Extract text (OCR)
            if options.get('extract_text', False):
                text = await self._extract_text(image)
                results['text'] = text
            
        except Exception as e:
            logger.error(f"Image processing failed: {e}")
            results['error'] = str(e)
        
        return results
    
    async def _analyze_image(self, image: Image.Image) -> Dict[str, Any]:
        """Analyze basic image characteristics."""
        try:
            return {
                "dimensions": image.size,
                "mode": image.mode,
                "format": image.format,
                "has_transparency": image.mode in ('RGBA', 'LA') or 'transparency' in image.info,
                "color_channels": len(image.getbands()),
                "processed_at": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def _detect_objects(self, image: Image.Image) -> Dict[str, Any]:
        """Detect objects in image using computer vision."""
        if not self.torch_available:
            return {"error": "PyTorch not available for object detection"}
        
        try:
            # This would use a pre-trained model like YOLO or COCO
            # For now, return a placeholder
            return {
                "message": "Object detection would be implemented here",
                "detected_objects": [],
                "confidence_threshold": 0.5
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def _enhance_image(self, image: Image.Image) -> Dict[str, Any]:
        """Enhance image quality."""
        try:
            # Basic image enhancement using PIL
            from PIL import ImageEnhance
            
            # Apply basic enhancements
            enhancer = ImageEnhance.Contrast(image)
            enhanced = enhancer.enhance(1.2)
            
            enhancer = ImageEnhance.Sharpness(enhanced)
            enhanced = enhancer.enhance(1.1)
            
            return {
                "enhanced": True,
                "operations": ["contrast_enhancement", "sharpness_enhancement"],
                "original_size": image.size
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def _extract_text(self, image: Image.Image) -> Dict[str, Any]:
        """Extract text from image using OCR."""
        try:
            # This would use pytesseract or similar OCR library
            # For now, return a placeholder
            return {
                "message": "OCR would be implemented here",
                "extracted_text": "",
                "confidence": 0.0
            }
        except Exception as e:
            return {"error": str(e)}


class MultiModalFusionProcessor:
    """Fuse results from multiple media types into unified output."""
    
    async def fuse_results(self, media_results: List[Dict[str, Any]], 
                         strategy: str = "concatenate") -> Dict[str, Any]:
        """
        Fuse multi-modal processing results.
        
        Args:
            media_results: List of processing results from different media types
            strategy: Fusion strategy
            
        Returns:
            Fused result
        """
        try:
            if strategy == "concatenate":
                return await self._concatenate_fusion(media_results)
            elif strategy == "weighted":
                return await self._weighted_fusion(media_results)
            elif strategy == "semantic":
                return await self._semantic_fusion(media_results)
            else:
                raise ValueError(f"Unknown fusion strategy: {strategy}")
                
        except Exception as e:
            logger.error(f"Multi-modal fusion failed: {e}")
            return {"error": str(e)}
    
    async def _concatenate_fusion(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Simple concatenation fusion."""
        fused = {
            "fusion_strategy": "concatenate",
            "media_types": [],
            "combined_text": "",
            "combined_metadata": {},
            "processing_summary": {}
        }
        
        for result in results:
            if result.get("success"):
                media_type = result.get("media_type")
                fused["media_types"].append(media_type)
                
                # Extract text content
                result_data = result.get("result", {})
                if "transcription" in result_data:
                    fused["combined_text"] += f"[{media_type.upper()}] {result_data['transcription'].get('text', '')}\n"
                elif "text" in result_data:
                    fused["combined_text"] += f"[{media_type.upper()}] {result_data['text']}\n"
                
                # Combine metadata
                if "metadata" in result_data:
                    fused["combined_metadata"][media_type] = result_data["metadata"]
                
                # Processing summary
                fused["processing_summary"][media_type] = {
                    "processing_time": result.get("processing_time"),
                    "success": True
                }
        
        return fused
    
    async def _weighted_fusion(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Weighted fusion based on confidence scores."""
        # Placeholder for weighted fusion
        return await self._concatenate_fusion(results)
    
    async def _semantic_fusion(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Semantic fusion using embeddings."""
        # Placeholder for semantic fusion
        return await self._concatenate_fusion(results)


# Global multi-modal processor instance
multimodal_processor = MultiModalProcessor()
