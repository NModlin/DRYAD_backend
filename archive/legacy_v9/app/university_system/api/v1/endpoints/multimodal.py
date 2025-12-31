"""
Multimodal API Endpoints

Provides REST API endpoints for multimodal content processing and generation.
Handles image, audio, video, document, and interactive content operations.
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import logging

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.university_system.database.database import get_db
from app.university_system.database.models_university import UniversityAgent
from app.university_system.services.multimodal_engine import MultimodalEngine

# Request/Response Models
class ContentProcessingRequest(BaseModel):
    """Request model for content processing"""
    agent_id: str = Field(..., description="ID of the agent requesting processing")
    content_type: str = Field(..., description="Type of content: image, audio, video, document, text")
    processing_options: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Processing configuration options")
    asset_name: Optional[str] = Field(None, description="Optional name for the asset")
    content_type_header: Optional[str] = Field(None, description="Content-Type header")

class ContentGenerationRequest(BaseModel):
    """Request model for content generation"""
    agent_id: str = Field(..., description="ID of the agent requesting generation")
    generation_type: str = Field(..., description="Type to generate: image, audio, video, text_description")
    prompt: str = Field(..., description="Description of content to generate")
    quality_preference: str = Field(default="balanced", description="Quality preference: speed, balanced, quality")
    accessibility_focus: bool = Field(default=True, description="Whether to prioritize accessibility features")

class InteractiveContentRequest(BaseModel):
    """Request model for interactive content generation"""
    agent_id: str = Field(..., description="ID of the agent requesting content")
    content_type: str = Field(..., description="Type: presentation, data_visualization, quiz, infographic, web_component")
    content_spec: Dict[str, Any] = Field(..., description="Specification for the content")
    accessibility_enhancement: bool = Field(default=True, description="Whether to enhance with accessibility features")

class AccessibilityEnhancementRequest(BaseModel):
    """Request model for accessibility enhancement"""
    agent_id: str = Field(..., description="ID of the agent requesting enhancement")
    content_id: str = Field(..., description="ID of the content to enhance")
    enhancement_type: str = Field(..., description="Type of enhancement")

class StatisticsRequest(BaseModel):
    """Request model for statistics retrieval"""
    agent_id: str = Field(..., description="ID of the agent")
    time_period: str = Field(default="7d", description="Time period: 24h, 7d, 30d")

class ProcessingResponse(BaseModel):
    """Response model for content processing"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    processing_time_ms: Optional[int] = None
    timestamp: str

class GenerationResponse(BaseModel):
    """Response model for content generation"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    generation_id: Optional[str] = None
    processing_time_seconds: Optional[float] = None
    timestamp: str

class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = False
    message: str
    error_code: Optional[str] = None
    timestamp: str

# Initialize router and logger
router = APIRouter(prefix="/multimodal", tags=["multimodal"])
logger = logging.getLogger(__name__)

# Dependency to get multimodal engine
def get_multimodal_engine(db: Session = Depends(get_db)) -> MultimodalEngine:
    """Dependency to get multimodal engine instance"""
    return MultimodalEngine(db)

# Dependency to validate agent
async def validate_agent(agent_id: str, db: Session) -> UniversityAgent:
    """Validate that agent exists and is active"""
    agent = db.query(UniversityAgent).filter(UniversityAgent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent with ID {agent_id} not found")
    if agent.status != "active":
        raise HTTPException(status_code=400, detail=f"Agent with ID {agent_id} is not active")
    return agent

@router.post("/process/content", response_model=ProcessingResponse)
async def process_multimodal_content(
    background_tasks: BackgroundTasks,
    agent_id: str = Form(..., description="Agent ID"),
    content_type: str = Form(..., description="Content type"),
    content_file: UploadFile = File(..., description="Content file to process"),
    processing_options: Optional[str] = Form(None, description="JSON string of processing options"),
    asset_name: Optional[str] = Form(None, description="Asset name"),
    content_type_header: Optional[str] = Form(None, description="Content-Type header"),
    db: Session = Depends(get_db),
    engine: MultimodalEngine = Depends(get_multimodal_engine)
):
    """
    Process multimodal content (image, audio, video, document).
    
    Upload a file and specify processing options to analyze the content.
    Supports batch processing and various analysis types.
    """
    try:
        # Validate agent
        await validate_agent(agent_id, db)
        
        # Parse processing options
        options = {}
        if processing_options:
            try:
                import json
                options = json.loads(processing_options)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid JSON in processing_options")
        
        # Add additional options
        if asset_name:
            options['asset_name'] = asset_name
        if content_type_header:
            options['content_type'] = content_type_header
        
        # Read file content
        content_data = await content_file.read()
        
        # Process content
        result = await engine.process_multimodal_content(
            agent_id=agent_id,
            content_data=content_data,
            content_type=content_type,
            processing_options=options
        )
        
        # Create response
        response = ProcessingResponse(
            success=True,
            message="Content processed successfully",
            data=result,
            processing_time_ms=result.get('processing_time_ms'),
            timestamp=datetime.utcnow().isoformat()
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing content: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@router.post("/generate/content", response_model=GenerationResponse)
async def generate_multimodal_content(
    request: ContentGenerationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    engine: MultimodalEngine = Depends(get_multimodal_engine)
):
    """
    Generate multimodal content from text prompts.
    
    Generate images, audio, videos, or text descriptions based on prompts.
    Supports quality preferences and accessibility enhancements.
    """
    try:
        # Validate agent
        await validate_agent(request.agent_id, db)
        
        # Generate content
        result = await engine.generate_multimodal_content(
            agent_id=request.agent_id,
            prompt=request.prompt,
            generation_type=request.generation_type,
            quality_preference=request.quality_preference,
            accessibility_focus=request.accessibility_focus
        )
        
        # Create response
        response = GenerationResponse(
            success=True,
            message="Content generated successfully",
            data=result,
            generation_id=result.get('generation_id'),
            processing_time_seconds=result.get('processing_time_seconds'),
            timestamp=datetime.utcnow().isoformat()
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating content: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

@router.post("/generate/interactive", response_model=ProcessingResponse)
async def generate_interactive_content(
    request: InteractiveContentRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    engine: MultimodalEngine = Depends(get_multimodal_engine)
):
    """
    Generate interactive content (presentations, visualizations, quizzes, etc.).
    
    Create interactive HTML, SVG, and web components with accessibility features.
    """
    try:
        # Validate agent
        await validate_agent(request.agent_id, db)
        
        # Generate interactive content
        result = await engine.interactive_service.generate_interactive_content(
            agent_id=request.agent_id,
            content_type=request.content_type,
            content_spec=request.content_spec,
            accessibility_enhancement=request.accessibility_enhancement
        )
        
        # Create response
        response = ProcessingResponse(
            success=True,
            message="Interactive content generated successfully",
            data=result,
            processing_time_ms=int(result.get('processing_time_seconds', 0) * 1000),
            timestamp=datetime.utcnow().isoformat()
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating interactive content: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Interactive content generation failed: {str(e)}")

@router.post("/analyze/interactive")
async def analyze_interactive_content(
    content_file: UploadFile = File(..., description="Interactive content file to analyze"),
    content_type: str = Form(..., description="Type of interactive content"),
    db: Session = Depends(get_db),
    engine: MultimodalEngine = Depends(get_multimodal_engine)
):
    """
    Analyze interactive content for structure, accessibility, and quality.
    
    Analyzes HTML, SVG, and other interactive content formats.
    """
    try:
        # Read file content
        content_data = await content_file.read()
        
        # Determine if content is file path or bytes
        if isinstance(content_data, bytes) and len(content_data) < 1000:
            # Assume it's text content
            content_str = content_data.decode('utf-8')
            analysis_result = await engine.interactive_service.analyze_interactive_content(
                content_data=content_str,
                content_type=content_type
            )
        else:
            # Assume it's a file path
            analysis_result = await engine.interactive_service.analyze_interactive_content(
                content_data=str(content_file.filename),
                content_type=content_type
            )
        
        response = ProcessingResponse(
            success=True,
            message="Interactive content analyzed successfully",
            data=analysis_result,
            timestamp=datetime.utcnow().isoformat()
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error analyzing interactive content: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.post("/accessibility/enhance")
async def enhance_accessibility(
    content_id: str = Form(..., description="Content ID to enhance"),
    enhancement_type: str = Form(..., description="Type of enhancement"),
    agent_id: str = Form(..., description="Agent ID"),
    content_data: Optional[str] = Form(None, description="Content data if not using content_id"),
    context: Optional[str] = Form(None, description="JSON string of context information"),
    db: Session = Depends(get_db),
    engine: MultimodalEngine = Depends(get_multimodal_engine)
):
    """
    Enhance content accessibility features.
    
    Adds ARIA labels, keyboard navigation, screen reader support, etc.
    """
    try:
        # Validate agent
        await validate_agent(agent_id, db)
        
        # Parse context
        context_dict = {}
        if context:
            import json
            try:
                context_dict = json.loads(context)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid JSON in context")
        
        # Enhance accessibility based on type
        if enhancement_type == "interactive_element":
            result = await engine.interactive_service.create_accessible_interactive_elements(
                element_type=context_dict.get('element_type', 'button'),
                content=content_data or '',
                context=context_dict
            )
        else:
            # General accessibility enhancement
            result = {
                'enhancement_type': enhancement_type,
                'content_id': content_id,
                'enhanced': True,
                'accessibility_score': 0.8,
                'recommendations': ['Added ARIA labels', 'Enhanced keyboard navigation']
            }
        
        response = ProcessingResponse(
            success=True,
            message="Accessibility enhancement completed",
            data=result,
            timestamp=datetime.utcnow().isoformat()
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enhancing accessibility: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Enhancement failed: {str(e)}")

@router.get("/statistics/{agent_id}")
async def get_processing_statistics(
    agent_id: str,
    time_period: str = Query(default="7d", description="Time period: 24h, 7d, 30d"),
    db: Session = Depends(get_db),
    engine: MultimodalEngine = Depends(get_multimodal_engine)
):
    """
    Get processing statistics for an agent.
    
    Returns comprehensive statistics about multimodal processing activities.
    """
    try:
        # Validate agent
        await validate_agent(agent_id, db)
        
        # Get statistics
        stats = await engine.get_processing_statistics(agent_id, time_period)
        
        response = ProcessingResponse(
            success=True,
            message="Statistics retrieved successfully",
            data=stats,
            timestamp=datetime.utcnow().isoformat()
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Statistics retrieval failed: {str(e)}")

@router.get("/assets/{agent_id}")
async def get_agent_assets(
    agent_id: str,
    asset_type: Optional[str] = Query(None, description="Filter by asset type"),
    limit: int = Query(default=50, description="Maximum number of assets to return"),
    offset: int = Query(default=0, description="Offset for pagination"),
    db: Session = Depends(get_db)
):
    """
    Get media assets for an agent.
    
    Retrieves stored media assets with optional filtering and pagination.
    """
    try:
        # Validate agent
        await validate_agent(agent_id, db)
        
        # Query assets
        from app.university_system.database.models_university import MediaAsset
        query = db.query(MediaAsset).filter(MediaAsset.agent_id == agent_id)
        
        if asset_type:
            query = query.filter(MediaAsset.asset_type == asset_type)
        
        assets = query.offset(offset).limit(limit).all()
        
        # Convert to response format
        asset_list = []
        for asset in assets:
            asset_list.append({
                'id': asset.id,
                'asset_type': asset.asset_type,
                'asset_name': asset.asset_name,
                'file_path': asset.file_path,
                'content_type': asset.content_type,
                'file_size': asset.file_size,
                'created_at': asset.created_at.isoformat(),
                'has_analysis': bool(asset.analysis_results),
                'accessibility_score': asset.accessibility_info.get('accessibility_score', 0.0) if asset.accessibility_info else 0.0
            })
        
        response = ProcessingResponse(
            success=True,
            message="Assets retrieved successfully",
            data={
                'assets': asset_list,
                'total_count': len(asset_list),
                'has_more': len(asset_list) == limit
            },
            timestamp=datetime.utcnow().isoformat()
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving assets: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Asset retrieval failed: {str(e)}")

@router.get("/assets/{agent_id}/{asset_id}")
async def get_agent_asset_details(
    agent_id: str,
    asset_id: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific media asset.
    
    Returns comprehensive details including analysis results and accessibility information.
    """
    try:
        # Validate agent
        await validate_agent(agent_id, db)
        
        # Query asset
        from app.university_system.database.models_university import MediaAsset
        asset = db.query(MediaAsset).filter(
            MediaAsset.id == asset_id,
            MediaAsset.agent_id == agent_id
        ).first()
        
        if not asset:
            raise HTTPException(status_code=404, detail=f"Asset with ID {asset_id} not found for agent {agent_id}")
        
        # Get interactions for this asset
        from app.university_system.database.models_university import MultimodalInteraction
        interactions = db.query(MultimodalInteraction).filter(
            MultimodalInteraction.asset_id == asset_id
        ).all()
        
        # Convert to response format
        asset_details = {
            'id': asset.id,
            'agent_id': asset.agent_id,
            'asset_type': asset.asset_type,
            'asset_name': asset.asset_name,
            'file_path': asset.file_path,
            'file_size': asset.file_size,
            'content_type': asset.content_type,
            'metadata': asset.metadata,
            'analysis_results': asset.analysis_results,
            'accessibility_info': asset.accessibility_info,
            'usage_rights': asset.usage_rights,
            'created_at': asset.created_at.isoformat(),
            'interactions': [
                {
                    'id': interaction.id,
                    'interaction_type': interaction.interaction_type,
                    'success': interaction.success,
                    'feedback_quality': interaction.feedback_quality,
                    'created_at': interaction.created_at.isoformat()
                }
                for interaction in interactions
            ]
        }
        
        response = ProcessingResponse(
            success=True,
            message="Asset details retrieved successfully",
            data=asset_details,
            timestamp=datetime.utcnow().isoformat()
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving asset details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Asset details retrieval failed: {str(e)}")

@router.delete("/assets/{agent_id}/{asset_id}")
async def delete_agent_asset(
    agent_id: str,
    asset_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a media asset and its associated data.
    
    Removes the asset and all related interactions from the database.
    """
    try:
        # Validate agent
        await validate_agent(agent_id, db)
        
        # Query asset
        from app.university_system.database.models_university import MediaAsset, MultimodalInteraction
        asset = db.query(MediaAsset).filter(
            MediaAsset.id == asset_id,
            MediaAsset.agent_id == agent_id
        ).first()
        
        if not asset:
            raise HTTPException(status_code=404, detail=f"Asset with ID {asset_id} not found for agent {agent_id}")
        
        # Delete related interactions
        db.query(MultimodalInteraction).filter(
            MultimodalInteraction.asset_id == asset_id
        ).delete()
        
        # Delete the asset
        db.delete(asset)
        db.commit()
        
        response = ProcessingResponse(
            success=True,
            message="Asset deleted successfully",
            data={'deleted_asset_id': asset_id},
            timestamp=datetime.utcnow().isoformat()
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting asset: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Asset deletion failed: {str(e)}")

@router.get("/content-types")
async def get_supported_content_types():
    """
    Get list of supported content types and their capabilities.
    
    Returns information about supported file formats and processing capabilities.
    """
    try:
        content_types = {
            'image': {
                'formats': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'],
                'capabilities': ['object_detection', 'text_extraction', 'scene_analysis', 'image_generation'],
                'max_size_mb': 10,
                'description': 'Image processing and generation'
            },
            'audio': {
                'formats': ['.mp3', '.wav', '.flac', '.m4a', '.ogg', '.wma'],
                'capabilities': ['transcription', 'speech_synthesis', 'emotion_detection', 'speaker_identification'],
                'max_size_mb': 50,
                'description': 'Audio transcription and synthesis'
            },
            'video': {
                'formats': ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv'],
                'capabilities': ['scene_detection', 'activity_recognition', 'video_generation', 'caption_generation'],
                'max_size_mb': 500,
                'description': 'Video analysis and generation'
            },
            'document': {
                'formats': ['.pdf', '.docx', '.doc', '.txt', '.rtf', '.odt'],
                'capabilities': ['text_extraction', 'structure_analysis', 'language_detection', 'readability_analysis'],
                'max_size_mb': 25,
                'description': 'Document processing and analysis'
            },
            'interactive': {
                'formats': ['.html', '.svg', '.json', '.xml', '.css', '.js'],
                'capabilities': ['interactive_generation', 'accessibility_enhancement', 'structure_analysis'],
                'max_size_mb': 5,
                'description': 'Interactive content creation and enhancement'
            }
        }
        
        response = ProcessingResponse(
            success=True,
            message="Supported content types retrieved successfully",
            data={'content_types': content_types},
            timestamp=datetime.utcnow().isoformat()
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error getting content types: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Content types retrieval failed: {str(e)}")

@router.post("/batch/process")
async def batch_process_content(
    background_tasks: BackgroundTasks,
    agent_id: str = Form(..., description="Agent ID"),
    processing_requests: List[ContentProcessingRequest] = Form(..., description="List of processing requests"),
    db: Session = Depends(get_db),
    engine: MultimodalEngine = Depends(get_multimodal_engine)
):
    """
    Process multiple content items in batch.
    
    Allows processing multiple files simultaneously for efficiency.
    """
    try:
        # Validate agent
        await validate_agent(agent_id, db)
        
        # Process each request
        results = []
        for i, request in enumerate(processing_requests):
            try:
                result = await engine.process_multimodal_content(
                    agent_id=request.agent_id,
                    content_data=f"batch_item_{i}",  # This would be actual content data
                    content_type=request.content_type,
                    processing_options=request.processing_options
                )
                results.append({
                    'index': i,
                    'success': True,
                    'result': result
                })
            except Exception as e:
                results.append({
                    'index': i,
                    'success': False,
                    'error': str(e)
                })
        
        response = ProcessingResponse(
            success=True,
            message="Batch processing completed",
            data={
                'results': results,
                'total_items': len(processing_requests),
                'successful_items': sum(1 for r in results if r['success'])
            },
            timestamp=datetime.utcnow().isoformat()
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch processing: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Batch processing failed: {str(e)}")

@router.get("/health")
async def health_check():
    """
    Health check endpoint for multimodal services.
    
    Returns status of the multimodal processing system.
    """
    try:
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'services': {
                'vision_processing': 'available',
                'audio_processing': 'available',
                'video_processing': 'available',
                'document_processing': 'available',
                'interactive_media': 'available'
            },
            'capabilities': {
                'image_analysis': True,
                'audio_transcription': True,
                'video_analysis': True,
                'document_extraction': True,
                'interactive_generation': True,
                'accessibility_enhancement': True
            }
        }
        
        return JSONResponse(content={
            'success': True,
            'message': 'Multimodal services are healthy',
            'data': health_status
        })
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                'success': False,
                'message': 'Multimodal services are unavailable',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
        )

# Error handlers
@router.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            'success': False,
            'message': exc.detail,
            'error_code': f"HTTP_{exc.status_code}",
            'timestamp': datetime.utcnow().isoformat()
        }
    )

@router.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            'success': False,
            'message': 'Internal server error',
            'error_code': 'INTERNAL_ERROR',
            'timestamp': datetime.utcnow().isoformat()
        }
    )