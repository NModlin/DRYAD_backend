"""
Multi-Modal API endpoints for Phase 7.

Provides REST API endpoints for processing audio, video, and image content
with comprehensive multi-modal analysis and fusion capabilities.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Depends
from dryad.core.security import get_current_user, User
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from dryad.core.multimodal import multimodal_processor
from dryad.infrastructure.models import MultiModalContent
from dryad.services.multimodal_service import MultiModalService
from dryad.api.v1.schemas.multimodal import (
    MultiModalProcessRequest,
    MultiModalProcessResponse,
    MediaAnalysisResponse,
    MultiModalFusionRequest,
    MultiModalFusionResponse
)
from dryad.core.exceptions import (
    MultiModalProcessingException,
    ValidationException,
    ValidationErrorDetail,
    ExternalServiceException
)
from dryad.core.error_handlers import (
    create_multimodal_processing_error,
    create_service_degradation_response
)
from dryad.api.v1.schemas.errors import ERROR_RESPONSES

logger = logging.getLogger(__name__)

router = APIRouter()

# Dependency to get multimodal service
def get_multimodal_service() -> MultiModalService:
    return MultiModalService()


# Simplified routes for backward compatibility
@router.post(
    "/audio",
    response_model=MediaAnalysisResponse,
    responses=ERROR_RESPONSES
)
async def process_audio_simple(
    file: UploadFile = File(...),
    transcribe: bool = Form(True),
    analyze: bool = Form(False),
    conversation_id: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    multimodal_service: MultiModalService = Depends(get_multimodal_service)
):
    """
    Process audio file with speech-to-text and analysis capabilities (simplified endpoint).
    """
    return await process_audio(file, transcribe, analyze, conversation_id, multimodal_service)


@router.post(
    "/image",
    response_model=MediaAnalysisResponse,
    responses=ERROR_RESPONSES
)
async def process_image_simple(
    file: Optional[UploadFile] = File(None),
    image: Optional[UploadFile] = File(None),
    detect_objects: bool = Form(False),
    extract_text: bool = Form(False),
    enhance: bool = Form(False),
    analyze: bool = Form(True),
    conversation_id: Optional[str] = Form(None),
    options: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    multimodal_service: MultiModalService = Depends(get_multimodal_service)
):
    """
    Process image file with computer vision and analysis capabilities (simplified endpoint).
    """
    # Determine which file parameter was provided
    upload_file = file if file else image
    if not upload_file:
        raise HTTPException(status_code=422, detail="Either 'file' or 'image' parameter is required")

    # Parse options if provided
    if options:
        try:
            import json
            opts = json.loads(options)
            detect_objects = opts.get("detect_objects", detect_objects)
            extract_text = opts.get("extract_text", extract_text)
            enhance = opts.get("enhance", enhance)
            analyze = opts.get("analyze", analyze)
        except (json.JSONDecodeError, AttributeError):
            pass  # Use default values if parsing fails

    return await process_image(upload_file, detect_objects, extract_text, enhance, analyze, conversation_id, multimodal_service)


@router.post(
    "/video",
    response_model=MediaAnalysisResponse,
    responses=ERROR_RESPONSES
)
async def process_video_simple(
    file: Optional[UploadFile] = File(None),
    video: Optional[UploadFile] = File(None),
    extract_frames: bool = Form(False),
    transcribe_audio: bool = Form(True),
    analyze: bool = Form(False),
    frame_count: int = Form(10),
    conversation_id: Optional[str] = Form(None),
    options: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    multimodal_service: MultiModalService = Depends(get_multimodal_service)
):
    """
    Process video file with frame extraction, audio transcription, and analysis (simplified endpoint).
    """
    # Determine which file parameter was provided
    upload_file = file if file else video
    if not upload_file:
        raise HTTPException(status_code=422, detail="Either 'file' or 'video' parameter is required")

    # Parse options if provided
    if options:
        try:
            import json
            opts = json.loads(options)
            extract_frames = opts.get("extract_frames", extract_frames)
            transcribe_audio = opts.get("transcribe_audio", transcribe_audio)
            analyze = opts.get("analyze", analyze)
            frame_count = opts.get("frame_count", frame_count)
        except (json.JSONDecodeError, AttributeError):
            pass  # Use default values if parsing fails

    return await process_video(upload_file, extract_frames, transcribe_audio, analyze, frame_count, conversation_id, multimodal_service)


@router.post(
    "/process/audio",
    response_model=MediaAnalysisResponse,
    responses=ERROR_RESPONSES
)
async def process_audio(
    file: UploadFile = File(...),
    transcribe: bool = Form(True),
    analyze: bool = Form(False),
    conversation_id: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    multimodal_service: MultiModalService = Depends(get_multimodal_service)
):
    """
    Process audio file with speech-to-text and analysis capabilities.
    
    - **file**: Audio file to process (WAV, MP3, M4A, etc.)
    - **transcribe**: Whether to transcribe speech to text
    - **analyze**: Whether to perform audio analysis
    - **conversation_id**: Optional conversation ID to associate with
    """
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('audio/'):
            raise ValidationException(
                error_message="Invalid file type for audio processing",
                validation_errors=[ValidationErrorDetail(
                    field="file",
                    message="File must be an audio file",
                    invalid_value=file.content_type,
                    expected_type="audio/*"
                )]
            )

        # Read file data
        audio_data = await file.read()

        if len(audio_data) == 0:
            raise ValidationException(
                error_message="Empty audio file provided",
                validation_errors=[ValidationErrorDetail(
                    field="file",
                    message="Audio file cannot be empty",
                    invalid_value="0 bytes",
                    expected_type="non-empty audio file"
                )]
            )
        
        # Process audio
        processing_options = {
            'transcribe': transcribe,
            'analyze': analyze
        }

        try:
            result = await multimodal_processor.process_media(
                media_data=audio_data,
                media_type='audio',
                processing_options=processing_options
            )

            # Check if processing failed
            if not result.get('success', False):
                error_details = result.get('error', 'Unknown audio processing error')
                raise MultiModalProcessingException(
                    error_message="Audio processing failed",
                    media_type="audio",
                    error_details=error_details,
                    processing_step="audio_processing",
                    fallback_available=True
                )

        except MultiModalProcessingException:
            raise
        except Exception as e:
            raise MultiModalProcessingException(
                error_message="Unexpected error during audio processing",
                media_type="audio",
                error_details=str(e),
                processing_step="audio_processing",
                fallback_available=False
            )
        
        # Save to database if conversation_id provided
        if conversation_id and result.get('success'):
            await multimodal_service.save_multimodal_content(
                conversation_id=conversation_id,
                media_type='audio',
                filename=file.filename,
                content_data=audio_data,
                processing_result=result
            )
        
        # Extract nested result data for backward compatibility
        result_data = result.get('result', {})

        # Create response with expected structure
        response_data = {
            "success": result.get('success', False),
            "media_type": 'audio',
            "filename": file.filename,
            "processing_time": result.get('processing_time', 0),
            "result": result_data,
            "error": result.get('error'),
            "timestamp": result.get('timestamp', datetime.now().isoformat())
        }

        # Add transcription and analysis at top level for test compatibility
        if 'transcription' in result_data:
            response_data['transcription'] = result_data['transcription']
        if 'analysis' in result_data:
            response_data['analysis'] = result_data['analysis']

        return MediaAnalysisResponse(**response_data)
        
    except (ValidationException, MultiModalProcessingException):
        raise
    except Exception as e:
        logger.error(f"Unexpected error in audio processing endpoint: {e}")
        raise MultiModalProcessingException(
            error_message="Unexpected error in audio processing endpoint",
            media_type="audio",
            error_details=str(e),
            processing_step="endpoint_handling",
            fallback_available=False
        )


@router.post("/process/video", response_model=MediaAnalysisResponse)
async def process_video(
    file: UploadFile = File(...),
    extract_frames: bool = Form(False),
    transcribe_audio: bool = Form(True),
    analyze: bool = Form(False),
    frame_count: int = Form(10),
    conversation_id: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    multimodal_service: MultiModalService = Depends(get_multimodal_service)
):
    """
    Process video file with frame extraction, audio transcription, and analysis.
    
    - **file**: Video file to process (MP4, AVI, MOV, etc.)
    - **extract_frames**: Whether to extract key frames
    - **transcribe_audio**: Whether to transcribe audio track
    - **analyze**: Whether to perform video analysis
    - **frame_count**: Number of frames to extract (if extract_frames=True)
    - **conversation_id**: Optional conversation ID to associate with
    """
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('video/'):
            raise HTTPException(status_code=400, detail="File must be a video file")
        
        # Read file data
        video_data = await file.read()
        
        if len(video_data) == 0:
            raise HTTPException(status_code=400, detail="Empty video file")
        
        # Process video
        processing_options = {
            'extract_frames': extract_frames,
            'transcribe_audio': transcribe_audio,
            'analyze': analyze,
            'frame_count': frame_count
        }
        
        result = await multimodal_processor.process_media(
            media_data=video_data,
            media_type='video',
            processing_options=processing_options
        )
        
        # Save to database if conversation_id provided
        if conversation_id and result.get('success'):
            await multimodal_service.save_multimodal_content(
                conversation_id=conversation_id,
                media_type='video',
                filename=file.filename,
                content_data=video_data,
                processing_result=result
            )
        
        # Extract nested result data for backward compatibility
        result_data = result.get('result', {})

        # Create response with expected structure
        response_data = {
            "success": result.get('success', False),
            "media_type": 'video',
            "filename": file.filename,
            "processing_time": result.get('processing_time', 0),
            "result": result_data,
            "error": result.get('error'),
            "timestamp": result.get('timestamp', datetime.now().isoformat())
        }

        # Add video-specific fields at top level for test compatibility
        if 'frames' in result_data:
            response_data['frames'] = result_data['frames']
        if 'audio_transcription' in result_data:
            response_data['audio_transcription'] = result_data['audio_transcription']
        if 'analysis' in result_data:
            response_data['analysis'] = result_data['analysis']

        return MediaAnalysisResponse(**response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Video processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Video processing failed: {str(e)}")


@router.post("/process/image", response_model=MediaAnalysisResponse)
async def process_image(
    file: UploadFile = File(...),
    detect_objects: bool = Form(False),
    extract_text: bool = Form(False),
    enhance: bool = Form(False),
    analyze: bool = Form(True),
    conversation_id: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    multimodal_service: MultiModalService = Depends(get_multimodal_service)
):
    """
    Process image file with computer vision and analysis capabilities.
    
    - **file**: Image file to process (JPG, PNG, GIF, etc.)
    - **detect_objects**: Whether to detect objects in the image
    - **extract_text**: Whether to extract text using OCR
    - **enhance**: Whether to enhance image quality
    - **analyze**: Whether to perform image analysis
    - **conversation_id**: Optional conversation ID to associate with
    """
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="Unsupported image format")
        
        # Read file data
        image_data = await file.read()
        
        if len(image_data) == 0:
            raise HTTPException(status_code=400, detail="Empty image file")
        
        # Process image
        processing_options = {
            'detect_objects': detect_objects,
            'extract_text': extract_text,
            'enhance': enhance,
            'analyze': analyze
        }
        
        result = await multimodal_processor.process_media(
            media_data=image_data,
            media_type='image',
            processing_options=processing_options
        )
        
        # Save to database if conversation_id provided
        if conversation_id and result.get('success'):
            await multimodal_service.save_multimodal_content(
                conversation_id=conversation_id,
                media_type='image',
                filename=file.filename,
                content_data=image_data,
                processing_result=result
            )
        
        # Extract nested result data for backward compatibility
        result_data = result.get('result', {})

        # Create response with expected structure
        response_data = {
            "success": result.get('success', False),
            "media_type": 'image',
            "filename": file.filename,
            "processing_time": result.get('processing_time', 0),
            "result": result_data,
            "error": result.get('error'),
            "timestamp": result.get('timestamp', datetime.now().isoformat())
        }

        # Add analysis and other fields at top level for test compatibility
        if 'analysis' in result_data:
            response_data['analysis'] = result_data['analysis']
        if 'objects' in result_data:
            response_data['objects'] = result_data['objects']
        if 'text' in result_data:
            response_data['text'] = result_data['text']

        return MediaAnalysisResponse(**response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Image processing failed: {str(e)}")


@router.post("/process/multimodal", response_model=MultiModalProcessResponse)
async def process_multimodal(
    files: List[UploadFile] = File(...),
    fusion_strategy: str = Form("concatenate"),
    conversation_id: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    multimodal_service: MultiModalService = Depends(get_multimodal_service)
):
    """
    Process multiple media files and fuse results into unified output.
    
    - **files**: List of media files (audio, video, image)
    - **fusion_strategy**: Strategy for fusing results ('concatenate', 'weighted', 'semantic')
    - **conversation_id**: Optional conversation ID to associate with
    """
    try:
        if len(files) == 0:
            raise HTTPException(status_code=400, detail="At least one file must be provided")
        
        media_results = []
        
        # Process each file
        for file in files:
            # Determine media type from content type
            if file.content_type.startswith('audio/'):
                media_type = 'audio'
                processing_options = {'transcribe': True, 'analyze': False}
            elif file.content_type.startswith('video/'):
                media_type = 'video'
                processing_options = {'transcribe_audio': True, 'extract_frames': False, 'analyze': False}
            elif file.content_type.startswith('image/'):
                media_type = 'image'
                processing_options = {'analyze': True, 'detect_objects': False, 'extract_text': False}
            else:
                logger.warning(f"Unsupported file type: {file.content_type}")
                continue
            
            # Read and process file
            file_data = await file.read()
            
            result = await multimodal_processor.process_media(
                media_data=file_data,
                media_type=media_type,
                processing_options=processing_options
            )
            
            result['filename'] = file.filename
            media_results.append(result)
            
            # Save individual results if conversation_id provided
            if conversation_id and result.get('success'):
                await multimodal_service.save_multimodal_content(
                    conversation_id=conversation_id,
                    media_type=media_type,
                    filename=file.filename,
                    content_data=file_data,
                    processing_result=result
                )
        
        # Fuse results
        fused_result = await multimodal_processor.fuse_multimodal_data(
            media_results=media_results,
            fusion_strategy=fusion_strategy
        )
        
        return MultiModalProcessResponse(
            success=True,
            processed_files=len(media_results),
            fusion_strategy=fusion_strategy,
            individual_results=media_results,
            fused_result=fused_result,
            timestamp=datetime.now().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Multi-modal processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Multi-modal processing failed: {str(e)}")


@router.get("/capabilities")
async def get_multimodal_capabilities():
    """
    Get available multi-modal processing capabilities.
    
    Returns information about which processing features are available
    based on installed dependencies.
    """
    try:
        capabilities = multimodal_processor.capabilities
        
        return {
            "success": True,
            "capabilities": capabilities,
            "supported_media_types": ["audio", "video", "image"],
            "supported_audio_formats": ["wav", "mp3", "m4a", "flac"],
            "supported_video_formats": ["mp4", "avi", "mov", "mkv"],
            "supported_image_formats": ["jpg", "jpeg", "png", "gif", "bmp"],
            "fusion_strategies": ["concatenate", "weighted", "semantic"],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get capabilities: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get capabilities: {str(e)}")


@router.get("/conversation/{conversation_id}/multimodal")
async def get_conversation_multimodal_content(
    conversation_id: str,
    media_type: Optional[str] = None,
    multimodal_service: MultiModalService = Depends(get_multimodal_service)
):
    """
    Get multi-modal content associated with a conversation.
    
    - **conversation_id**: ID of the conversation
    - **media_type**: Optional filter by media type ('audio', 'video', 'image')
    """
    try:
        content = await multimodal_service.get_conversation_multimodal_content(
            conversation_id=conversation_id,
            media_type=media_type
        )
        
        return {
            "success": True,
            "conversation_id": conversation_id,
            "content_count": len(content),
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get conversation multimodal content: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get content: {str(e)}")


@router.delete("/content/{content_id}")
async def delete_multimodal_content(
    content_id: str,
    multimodal_service: MultiModalService = Depends(get_multimodal_service)
):
    """
    Delete multi-modal content by ID.
    
    - **content_id**: ID of the content to delete
    """
    try:
        success = await multimodal_service.delete_multimodal_content(content_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Content not found")
        
        return {
            "success": True,
            "message": "Content deleted successfully",
            "content_id": content_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete multimodal content: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete content: {str(e)}")


@router.post("/text-to-speech")
async def text_to_speech(
    text: str = Form(...),
    output_format: str = Form("wav"),
    multimodal_service: MultiModalService = Depends(get_multimodal_service)
):
    """
    Convert text to speech.
    
    - **text**: Text to convert to speech
    - **output_format**: Output audio format (wav, mp3)
    """
    try:
        if not text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        result = await multimodal_processor.audio_processor.text_to_speech(text)
        
        return {
            "success": result.get("success", False),
            "text": text,
            "output_format": output_format,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Text-to-speech failed: {e}")
        raise HTTPException(status_code=500, detail=f"Text-to-speech failed: {str(e)}")


@router.get("/health")
async def multimodal_health_check():
    """
    Health check endpoint for multi-modal services.
    """
    try:
        capabilities = multimodal_processor.capabilities
        
        # Count available capabilities
        available_count = sum(1 for available in capabilities.values() if available)
        total_count = len(capabilities)
        
        health_status = "healthy" if available_count > 0 else "degraded"
        
        return {
            "status": health_status,
            "available_capabilities": available_count,
            "total_capabilities": total_count,
            "capabilities": capabilities,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
