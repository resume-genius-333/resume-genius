#!/usr/bin/env python
"""
Simple API key management CLI.

Usage:
    python api_keys.py create "Service Name"
    python api_keys.py list
    python api_keys.py revoke <key_id>
"""
import sys
import os
import secrets
import hashlib
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

# Direct import to avoid loading all models
sys.path.insert(0, str(Path(__file__).parent.parent))
from models.auth.api_key import APIKey


def hash_key(key: str) -> str:
    """Hash an API key for secure storage."""
    return hashlib.sha256(key.encode()).hexdigest()


def get_engine():
    """Get database engine."""
    # Load environment variables
    load_dotenv()
    
    # Get database URL
    db_url = os.getenv("DATABASE_SYNC_URL")
    if not db_url:
        print("Error: DATABASE_SYNC_URL not set in environment")
        sys.exit(1)
    
    return create_engine(db_url)


def create_key(name: str):
    """Create a new API key."""
    # Generate key
    raw_key = f"rg_{secrets.token_urlsafe(32)}"
    key_hash = hash_key(raw_key)
    
    # Store in database
    engine = get_engine()
    with Session(engine) as session:
        # Check if name already exists
        existing = session.execute(
            select(APIKey).where(APIKey.name == name)
        ).scalar_one_or_none()
        
        if existing:
            print(f"Error: API key with name '{name}' already exists")
            return
        
        api_key = APIKey(key_hash=key_hash, name=name)
        session.add(api_key)
        session.commit()
        
        print(f"\n{'='*60}")
        print(f"API Key created for: {name}")
        print(f"{'='*60}")
        print(f"\nKey (save this - it won't be shown again):\n")
        print(f"  {raw_key}")
        print(f"\n{'='*60}\n")


def list_keys():
    """List all API keys."""
    engine = get_engine()
    with Session(engine) as session:
        keys = session.execute(
            select(APIKey).order_by(APIKey.created_at.desc())
        ).scalars().all()
        
        if not keys:
            print("No API keys found")
            return
        
        print(f"\n{'='*60}")
        print("API Keys:")
        print(f"{'='*60}")
        
        for key in keys:
            status = "Active" if key.is_active else "Revoked"
            print(f"\nID: {key.id}")
            print(f"Name: {key.name}")
            print(f"Status: {status}")
            print(f"Created: {key.created_at}")
            print("-" * 40)


def revoke_key(key_id: str):
    """Revoke an API key."""
    engine = get_engine()
    with Session(engine) as session:
        try:
            import uuid
            key_uuid = uuid.UUID(key_id)
        except ValueError:
            print(f"Error: Invalid UUID format: {key_id}")
            return
        
        key = session.get(APIKey, key_uuid)
        if not key:
            print(f"Error: API key {key_id} not found")
            return
        
        if not key.is_active:
            print(f"API key '{key.name}' is already revoked")
            return
        
        key.is_active = False
        session.commit()
        print(f"Successfully revoked API key: {key.name}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "create":
        if len(sys.argv) < 3:
            print("Error: Please provide a name for the API key")
            print("Usage: python api_keys.py create \"Service Name\"")
            sys.exit(1)
        create_key(sys.argv[2])
    
    elif command == "list":
        list_keys()
    
    elif command == "revoke":
        if len(sys.argv) < 3:
            print("Error: Please provide the API key ID to revoke")
            print("Usage: python api_keys.py revoke <key_id>")
            sys.exit(1)
        revoke_key(sys.argv[2])
    
    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()