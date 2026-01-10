"""
Simple seed data script for Dryad tables using raw SQL

Creates sample groves, branches, vessels, observation points, and dialogues
for testing and demonstration purposes.
"""
import sqlite3
from datetime import datetime
from uuid import uuid4
import json

# Database path
DB_PATH = "data/DRYAD.AI.db"


def create_seed_data():
    """Create comprehensive seed data for Dryad"""
    
    print("🌱 Starting Dryad seed data creation...")
    print("=" * 60)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        now = datetime.utcnow().isoformat()
        
        # ========================================
        # 1. Create Groves
        # ========================================
        print("\n📊 Creating Groves...")
        
        grove1_id = str(uuid4())
        grove2_id = str(uuid4())
        grove3_id = str(uuid4())
        
        groves = [
            (grove1_id, "AI Research Project", "Exploring advanced AI architectures and implementations", 
             1, json.dumps({"category": "research", "tags": ["ai", "machine-learning", "research"]}),
             now, now, now),
            (grove2_id, "Web Application Development", "Building a modern web application with FastAPI and React",
             0, json.dumps({"category": "development", "tags": ["web", "fastapi", "react"]}),
             now, now, now),
            (grove3_id, "Documentation Writing", "Creating comprehensive documentation for the project",
             0, json.dumps({"category": "documentation", "tags": ["docs", "writing"]}),
             now, now, now)
        ]
        
        cursor.executemany("""
            INSERT INTO dryad_groves (id, name, description, is_favorite, template_metadata, created_at, updated_at, last_accessed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, groves)
        
        print(f"  ✅ Created 3 groves")
        
        # ========================================
        # 2. Create Branches (Tree Structure)
        # ========================================
        print("\n🌳 Creating Branch Tree...")
        
        # Grove 1: AI Research - Root and children
        branch1_root_id = str(uuid4())
        branch1_child1_id = str(uuid4())
        branch1_child2_id = str(uuid4())
        branch1_child3_id = str(uuid4())
        branch1_grandchild_id = str(uuid4())
        
        # Grove 2: Web Development - Root and children
        branch2_root_id = str(uuid4())
        branch2_child1_id = str(uuid4())
        branch2_child2_id = str(uuid4())
        
        # Grove 3: Documentation - Root only
        branch3_root_id = str(uuid4())
        
        branches = [
            # Grove 1 branches
            (branch1_root_id, grove1_id, None, "Initial Research", "Starting point for AI research exploration", 
             0, "ACTIVE", "HIGHEST", None, now, now),
            (branch1_child1_id, grove1_id, branch1_root_id, "Transformer Architecture", "Exploring transformer-based models for NLP tasks",
             1, "ACTIVE", "HIGH", None, now, now),
            (branch1_child2_id, grove1_id, branch1_root_id, "CNN Architecture", "Investigating convolutional neural networks for image processing",
             1, "ACTIVE", "MEDIUM", None, now, now),
            (branch1_child3_id, grove1_id, branch1_root_id, "Hybrid Approach", "Combining transformers and CNNs for multimodal learning",
             1, "ARCHIVED", "LOW", None, now, now),
            (branch1_grandchild_id, grove1_id, branch1_child1_id, "BERT Implementation", "Implementing BERT for text classification",
             2, "ACTIVE", "HIGHEST", None, now, now),
            
            # Grove 2 branches
            (branch2_root_id, grove2_id, None, "Project Setup", "Initial project setup and architecture decisions",
             0, "ACTIVE", "HIGHEST", None, now, now),
            (branch2_child1_id, grove2_id, branch2_root_id, "Backend API", "Building FastAPI backend with authentication",
             1, "ACTIVE", "HIGH", None, now, now),
            (branch2_child2_id, grove2_id, branch2_root_id, "Frontend UI", "Creating React frontend with Material-UI",
             1, "ACTIVE", "HIGH", None, now, now),
            
            # Grove 3 branches
            (branch3_root_id, grove3_id, None, "Documentation Plan", "Planning comprehensive documentation structure",
             0, "ACTIVE", "MEDIUM", None, now, now),
        ]
        
        cursor.executemany("""
            INSERT INTO dryad_branches (id, grove_id, parent_id, name, description, path_depth, status, priority, observation_point_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, branches)
        
        print(f"  ✅ Created 10 branches with tree structure")
        
        # ========================================
        # 3. Create Observation Points
        # ========================================
        print("\n🔍 Creating Observation Points...")
        
        obs1_id = str(uuid4())
        obs2_id = str(uuid4())
        
        observation_points = [
            (obs1_id, branch1_root_id, "Choose AI architecture approach", 
             "Need to decide between transformer-based or CNN-based architecture",
             "Evaluating different approaches for the AI research project", now),
            (obs2_id, branch2_root_id, "Select frontend framework",
             "Evaluating React vs Vue vs Svelte for the frontend",
             "Need to choose the best framework for our use case", now),
        ]
        
        cursor.executemany("""
            INSERT INTO dryad_observation_points (id, branch_id, name, description, context, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, observation_points)
        
        print(f"  ✅ Created 2 observation points")
        
        # ========================================
        # 4. Create Possibilities
        # ========================================
        print("\n🔀 Creating Possibilities...")
        
        possibilities = [
            (str(uuid4()), obs1_id, "Use pre-trained transformer models (BERT, GPT)", 0.7,
             json.dumps({"pros": ["Fast development", "Good performance"], "cons": ["Large model size"]}), now),
            (str(uuid4()), obs1_id, "Build custom CNN architecture from scratch", 0.3,
             json.dumps({"pros": ["Full control", "Optimized"], "cons": ["Time-consuming"]}), now),
            (str(uuid4()), obs2_id, "Use React with TypeScript", 0.6,
             json.dumps({"pros": ["Type safety", "Large ecosystem"], "cons": ["Steeper learning curve"]}), now),
            (str(uuid4()), obs2_id, "Use Vue 3 with Composition API", 0.4,
             json.dumps({"pros": ["Easier to learn"], "cons": ["Smaller ecosystem"]}), now),
        ]
        
        cursor.executemany("""
            INSERT INTO dryad_possibilities (id, observation_point_id, description, probability_weight, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, possibilities)
        
        print(f"  ✅ Created 4 possibilities")
        
        # ========================================
        # 5. Create Vessels
        # ========================================
        print("\n📦 Creating Vessels...")
        
        vessels = [
            (str(uuid4()), branch1_root_id, f"vessels/{branch1_root_id}.json", "abc123def456",
             json.dumps({"research_papers": ["paper1.pdf", "paper2.pdf"], "code_samples": ["model.py"]}),
             0, "active", now, now),
            (str(uuid4()), branch1_child1_id, f"vessels/{branch1_child1_id}.json", "def456ghi789",
             json.dumps({"implementations": ["bert_model.py", "tokenizer.py"], "datasets": ["train_data.csv"]}),
             0, "active", now, now),
            (str(uuid4()), branch2_root_id, f"vessels/{branch2_root_id}.json", "ghi789jkl012",
             json.dumps({"config": ["package.json", "requirements.txt"], "docs": ["architecture.md"]}),
             0, "active", now, now),
        ]
        
        cursor.executemany("""
            INSERT INTO dryad_vessels (id, branch_id, storage_path, content_hash, file_references, is_compressed, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, vessels)
        
        print(f"  ✅ Created 3 vessels")
        
        # ========================================
        # 6. Create Dialogues and Messages
        # ========================================
        print("\n💬 Creating Dialogues...")
        
        dialogue1_id = str(uuid4())
        
        dialogues = [
            (dialogue1_id, branch1_root_id, "gpt-4",
             json.dumps({"key_points": ["Transformers are state-of-the-art", "Consider computational costs"], 
                        "recommendations": "Start with BERT"}),
             f"dialogues/{branch1_root_id}_dialogue1.json", now),
        ]
        
        cursor.executemany("""
            INSERT INTO dryad_dialogues (id, branch_id, oracle_used, insights, storage_path, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, dialogues)
        
        # Messages for dialogue1
        messages = [
            (str(uuid4()), dialogue1_id, "HUMAN", "What's the best approach for text classification in 2024?", now),
            (str(uuid4()), dialogue1_id, "ORACLE", "For text classification in 2024, transformer-based models like BERT, RoBERTa, or newer variants are the state-of-the-art.", now),
            (str(uuid4()), dialogue1_id, "HUMAN", "What about computational requirements?", now),
            (str(uuid4()), dialogue1_id, "ORACLE", "Transformer models can be computationally intensive. Consider using distilled versions like DistilBERT for production.", now),
        ]
        
        cursor.executemany("""
            INSERT INTO dryad_dialogue_messages (id, dialogue_id, role, content, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, messages)
        
        print(f"  ✅ Created 1 dialogue with 4 messages")
        
        # Commit all changes
        conn.commit()
        
        print("\n" + "=" * 60)
        print("✅ Seed data creation completed successfully!")
        print("\n📊 Summary:")
        print(f"  - Groves: 3")
        print(f"  - Branches: 10 (with tree structure)")
        print(f"  - Observation Points: 2")
        print(f"  - Possibilities: 4")
        print(f"  - Vessels: 3")
        print(f"  - Dialogues: 1")
        print(f"  - Dialogue Messages: 4")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Error creating seed data: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        conn.close()


def clear_seed_data():
    """Clear all seed data (for testing)"""
    print("🗑️  Clearing existing seed data...")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Delete in reverse order of dependencies
        cursor.execute("DELETE FROM dryad_dialogue_messages")
        cursor.execute("DELETE FROM dryad_dialogues")
        cursor.execute("DELETE FROM dryad_vessels")
        cursor.execute("DELETE FROM dryad_possibilities")
        cursor.execute("DELETE FROM dryad_branches")
        cursor.execute("DELETE FROM dryad_observation_points")
        cursor.execute("DELETE FROM dryad_groves")
        
        conn.commit()
        print("✅ Seed data cleared successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error clearing seed data: {e}")
        raise
    finally:
        conn.close()


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Dryad seed data management")
    parser.add_argument(
        "action",
        choices=["create", "clear", "recreate"],
        help="Action to perform: create, clear, or recreate seed data"
    )
    
    args = parser.parse_args()
    
    if args.action == "clear":
        clear_seed_data()
    elif args.action == "create":
        create_seed_data()
    elif args.action == "recreate":
        clear_seed_data()
        print()
        create_seed_data()


if __name__ == "__main__":
    main()

