#!/usr/bin/env python3
"""
Direct proposal generation script that bypasses frontend.
Creates a test user and generates proposals directly.
"""

import asyncio
import sys
from pathlib import Path
from typing import List

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import Config
from app.database.models import User, Document
from app.services.proposal_service import proposal_service

config = Config()

# Create async engine
engine = create_async_engine(
    config.DATABASE_URL.replace('sqlite:///', 'sqlite+aiosqlite:///'),
    echo=False
)

AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def get_or_create_test_user(session: AsyncSession) -> User:
    """Get or create a test user."""
    from sqlalchemy import select
    import uuid

    result = await session.execute(
        select(User).where(User.email == "test@DRYAD.AI.local")
    )
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            id=str(uuid.uuid4()),
            email="test@DRYAD.AI.local",
            name="Test User",
            provider="test",
            provider_id="test_provider_id",
            picture=None,
            email_verified=True,
            roles=["user"],
            permissions=["read", "write"],
            is_active=True,
            is_verified=True
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        print("✅ Created test user")
    else:
        print("✅ Using existing test user")

    return user

async def upload_document(session: AsyncSession, user: User, file_path: str) -> Document:
    """Upload a single document."""
    from app.services.document_service import DocumentService
    import mimetypes

    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    print(f"📤 Uploading: {file_path.name}")

    # Determine content type
    content_type, _ = mimetypes.guess_type(str(file_path))
    if not content_type:
        if file_path.suffix.lower() == '.md':
            content_type = 'text/markdown'
        else:
            content_type = 'application/octet-stream'

    # Read file content
    if file_path.suffix.lower() in ['.txt', '.md', '.py', '.js', '.json', '.xml', '.html', '.css']:
        # Text files - read as text
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    else:
        # Binary files - read as bytes then decode if possible
        with open(file_path, 'rb') as f:
            file_bytes = f.read()
        try:
            content = file_bytes.decode('utf-8', errors='ignore')
        except:
            content = str(file_bytes)

    # Create document using DocumentService static method
    document = await DocumentService.create_document_record(
        db=session,
        user_id=user.id,
        title=file_path.stem,
        content=content,
        content_type=content_type,
        file_path=str(file_path),
        file_size=len(content),
        doc_metadata={'original_filename': file_path.name}
    )

    if document:
        # Process content (chunk and index) - but catch vector store errors
        try:
            await DocumentService.process_document_content(
                db=session,
                document_id=document.id,
                content=content,
                title=document.title,
                content_type=content_type
            )
        except Exception as e:
            # Vector indexing failed, but document is still saved
            if "Vector store not connected" in str(e):
                print(f"⚠️ Vector indexing skipped (Weaviate not connected)")
            else:
                print(f"⚠️ Vector indexing failed: {e}")

        print(f"✅ Uploaded: {document.title} (ID: {document.id})")
        return document
    else:
        raise Exception("Failed to create document")

async def upload_directory(session: AsyncSession, user: User, dir_path: str, recursive: bool = True) -> List[Document]:
    """Upload all documents from a directory."""
    dir_path = Path(dir_path)
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {dir_path}")

    if not dir_path.is_dir():
        raise ValueError(f"Not a directory: {dir_path}")

    print(f"\n📁 Uploading documents from: {dir_path}")

    # Supported file extensions
    supported_extensions = {
        '.txt', '.md', '.pdf', '.doc', '.docx',
        '.py', '.js', '.json', '.xml', '.html', '.css',
        '.csv', '.xlsx', '.xls'
    }

    documents = []
    pattern = '**/*' if recursive else '*'

    for file_path in dir_path.glob(pattern):
        if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
            try:
                doc = await upload_document(session, user, str(file_path))
                documents.append(doc)
            except Exception as e:
                print(f"⚠️ Failed to upload {file_path.name}: {e}")

    print(f"\n✅ Uploaded {len(documents)} documents from directory")
    return documents

async def list_user_documents(session: AsyncSession, user: User):
    """List all documents for a user."""
    from sqlalchemy import select
    
    result = await session.execute(
        select(Document).where(Document.user_id == user.id)
    )
    documents = result.scalars().all()
    
    print(f"\n📚 Found {len(documents)} documents:")
    for doc in documents:
        print(f"   - {doc.title} (ID: {doc.id})")
    
    return documents

async def generate_proposal_for_user(
    session: AsyncSession,
    user: User,
    proposal_type: str = 'general',
    focus_areas: list = None,
    additional_context: str = None
):
    """Generate a proposal for a user."""
    print(f"\n🤖 Generating {proposal_type} proposal...")
    print("⏳ This may take 30-60 seconds...")
    
    try:
        result = await proposal_service.generate_proposal(
            db=session,
            user_id=user.id,
            proposal_type=proposal_type,
            focus_areas=focus_areas,
            additional_context=additional_context
        )
        
        if result['success']:
            proposal = result['proposal']
            metadata = result['metadata']
            
            print(f"\n✅ Proposal generated successfully!")
            print(f"\n📊 Metadata:")
            print(f"   Documents Analyzed: {metadata['documents_analyzed']}")
            print(f"   Type: {metadata['proposal_type']}")
            print(f"   Words: {proposal['word_count']:,}")
            print(f"   Model: {metadata['model_used']}")
            
            # Save to file
            output_file = f"proposal_{proposal_type}.md"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(proposal['full_text'])
            
            print(f"\n💾 Proposal saved to: {output_file}")
            print(f"\n📝 Preview (first 500 chars):")
            print("-" * 80)
            print(proposal['full_text'][:500] + "...")
            print("-" * 80)
            
            return result
        else:
            print(f"❌ Proposal generation failed: {result.get('error', 'Unknown error')}")
            return None
            
    except Exception as e:
        print(f"❌ Error generating proposal: {e}")
        import traceback
        traceback.print_exc()
        return None

async def main():
    """Main function."""
    print("=" * 80)
    print("🧙 DRYAD.AI Direct Proposal Generator")
    print("=" * 80)

    # Try to reconnect vector store if Weaviate is now available
    print("\n🔄 Checking vector store connection...")
    from app.core.vector_store import vector_store
    if vector_store.reconnect():
        print("✅ Vector store connected - full semantic search enabled")
    else:
        print("⚠️ Vector store not available - continuing without vector indexing")

    async with AsyncSessionLocal() as session:
        # Get or create test user
        print("\n1️⃣ Setting up test user...")
        user = await get_or_create_test_user(session)
        
        # List existing documents
        print("\n2️⃣ Checking existing documents...")
        documents = await list_user_documents(session, user)

        # Always ask if user wants to upload more documents
        print("\n📤 Upload more documents?")
        print("  1. Upload a single file")
        print("  2. Upload entire directory")
        print("  3. Continue with existing documents")
        if len(documents) == 0:
            print("  (You must upload at least one document)")

        upload_choice = input("\nChoose option (1-3): ").strip()

        if upload_choice == '1':
            file_path = input("Enter file path: ").strip().strip('"')
            try:
                await upload_document(session, user, file_path)
                documents = await list_user_documents(session, user)
            except Exception as e:
                print(f"❌ Upload failed: {e}")
                import traceback
                traceback.print_exc()
                if len(documents) == 0:
                    return
        elif upload_choice == '2':
            dir_path = input("Enter directory path: ").strip().strip('"')
            recursive = input("Include subdirectories? (y/n, default=y): ").strip().lower() != 'n'
            try:
                await upload_directory(session, user, dir_path, recursive)
                documents = await list_user_documents(session, user)
            except Exception as e:
                print(f"❌ Upload failed: {e}")
                import traceback
                traceback.print_exc()
                if len(documents) == 0:
                    return
        elif upload_choice == '3':
            if len(documents) == 0:
                print("❌ Cannot generate proposal without documents. Exiting.")
                return
            print("✅ Continuing with existing documents...")
        else:
            if len(documents) == 0:
                print("❌ Cannot generate proposal without documents. Exiting.")
                return
            print("✅ Continuing with existing documents...")
        
        # Generate proposal
        print("\n3️⃣ Generating proposal...")
        print("\nProposal Types:")
        print("  1. General")
        print("  2. Technical")
        print("  3. Business")
        print("  4. Research")
        
        type_choice = input("Select type (1-4, default=1): ").strip() or '1'
        type_map = {'1': 'general', '2': 'technical', '3': 'business', '4': 'research'}
        proposal_type = type_map.get(type_choice, 'general')
        
        focus = input("Focus areas (comma-separated, optional): ").strip()
        focus_areas = [f.strip() for f in focus.split(',')] if focus else None
        
        context = input("Additional context (optional): ").strip() or None
        
        await generate_proposal_for_user(
            session,
            user,
            proposal_type=proposal_type,
            focus_areas=focus_areas,
            additional_context=context
        )
    
    print("\n" + "=" * 80)
    print("✅ Done!")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())

