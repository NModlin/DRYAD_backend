from logging.config import fileConfig
import os
import sys

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our models and database configuration
from app.database.database import Base, DATABASE_URL
from app.database.models import Conversation, Message, Document, DocumentChunk, SearchQuery

# Import Dryad models for migration support
from app.dryad.models import (
    Grove, Branch, Vessel, Dialogue, DialogueMessage,
    ObservationPoint, Possibility
)

# Import Tool Registry models (Level 0 Component 1)
from app.services.tool_registry.models import Tool, ToolPermission

# Import Memory Guild models (Level 0 Component 2)
from app.services.memory_guild.models import (
    MemoryRecord,
    MemoryEmbedding,
    MemoryRelationship,
    DataSource,
    MemoryAccessPolicy,
)

# Import Structured Logging models (Level 0 Component 3)
from app.services.logging.models import SystemLog

# Import Agent Enhancement models (Phase 1 & Phase 2)
from app.models.agent_enhancements import VisualProfile, BehavioralProfile
from app.models.specialization import SpecializationProfile
from app.models.skill_tree import SkillTree, SkillNode
from app.models.skill_progress import AgentSkillProgress
from app.models.progression_path import ProgressionPath

# Import Enhanced University models (Level 6 - Enhanced)
from app.database.models_university import (
    University, UniversityAgent, CurriculumPath, CurriculumLevel, AgentProgress, TrainingDataCollection,
    ImprovementProposal, Achievement, AgentAchievement, Competition, CompetitionParticipant,
    CompetitionMatch
)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Set the database URL from environment variable
config.set_main_option("sqlalchemy.url", DATABASE_URL)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
