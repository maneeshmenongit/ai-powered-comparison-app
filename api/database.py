"""api/database.py

SQLAlchemy database setup for PostgreSQL.
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base
from sqlalchemy.pool import NullPool

# Load environment variables
# Railway/production: Use environment variables directly (no .env file)
# Local dev: Priority .env.local > .env.staging > .env
# Only load from files if DATABASE_URL is not already set (not in Railway)
if not os.getenv('DATABASE_URL'):
    if os.path.exists('.env.local'):
        load_dotenv('.env.local', override=True)
    elif os.path.exists('.env.staging'):
        load_dotenv('.env.staging', override=True)
    else:
        load_dotenv()

# Get database URL from environment
DATABASE_URL = os.getenv('DATABASE_URL', '')

# Handle Heroku/Railway postgres:// -> postgresql:// conversion
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

# Create engine
# Use NullPool for serverless environments to avoid connection pool issues
engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool,
    echo=False,  # Set to True for SQL debugging
    connect_args={
        'connect_timeout': 10,
    } if DATABASE_URL else {}
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create scoped session for thread-safe access
db_session = scoped_session(SessionLocal)

# Base class for models
Base = declarative_base()
Base.query = db_session.query_property()


def get_db():
    """
    Get database session.

    Usage in Flask routes:
        db = get_db()
        try:
            # Use db here
            db.commit()
        except Exception as e:
            db.rollback()
            raise
        finally:
            db.close()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database - create all tables."""
    import api.models  # Import models to register them
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")


def close_db():
    """Close database session."""
    db_session.remove()
