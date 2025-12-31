"""
Celery application configuration for DRYAD.AI Phase 5.
Handles asynchronous task execution and orchestration.
"""

import os
import logging
from celery import Celery
from kombu import Queue

logger = logging.getLogger(__name__)

# Create Celery app instance
def create_celery_app() -> Celery:
    """Create and configure Celery application."""

    # Redis URL for broker and backend
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Check if we're in testing mode
    is_testing = os.getenv("TESTING", "false").lower() == "true"

    if is_testing:
        # Use memory transport for testing
        logger.info("Using memory transport for Celery in testing mode")
        celery_app = Celery(
            'DRYAD.AI',
            broker='memory://',
            backend='cache+memory://',
            include=[
                'app.tasks.agent_tasks',
                'app.tasks.document_tasks',
                'app.tasks.orchestration_tasks'
            ]
        )
    else:
        # Create Celery instance with Redis
        celery_app = Celery(
            'DRYAD.AI',
            broker=redis_url,
            backend=redis_url,
            include=[
                'app.tasks.agent_tasks',
                'app.tasks.document_tasks',
                'app.tasks.orchestration_tasks'
            ]
        )
    
    # Configure Celery
    celery_app.conf.update(
        # Task settings
        task_track_started=True,
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        
        # Result backend settings
        result_expires=3600,  # 1 hour
        result_backend_transport_options={
            'master_name': 'mymaster',
            'visibility_timeout': 3600,
        },
        
        # Worker settings
        worker_prefetch_multiplier=1,
        worker_max_tasks_per_child=1000,
        
        # Task routing
        task_routes={
            'app.tasks.agent_tasks.*': {'queue': 'agent_queue'},
            'app.tasks.document_tasks.*': {'queue': 'document_queue'},
            'app.tasks.orchestration_tasks.*': {'queue': 'orchestration_queue'},
        },
        
        # Queue configuration
        task_default_queue='default',
        task_queues=(
            Queue('default'),
            Queue('agent_queue'),
            Queue('document_queue'),
            Queue('orchestration_queue'),
        ),
        
        # Monitoring
        worker_send_task_events=True,
        task_send_sent_event=True,
    )
    
    return celery_app

# Create the global Celery app instance
celery_app = create_celery_app()

# Task decorator for convenience
task = celery_app.task
