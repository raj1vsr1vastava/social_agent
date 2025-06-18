"""
Database configuration and connection management.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from typing import Generator

from src.models import Base


class DatabaseManager:
    """Manages database connections and sessions."""
    
    def __init__(self, database_url: str = None):
        if database_url is None:
            database_url = os.getenv("DATABASE_URL", "sqlite:///./data/social_agent.db")
        
        self.database_url = database_url
        
        # Create engine with appropriate settings
        if database_url.startswith("sqlite"):
            self.engine = create_engine(
                database_url,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
                echo=os.getenv("DATABASE_ECHO", "False").lower() == "true"
            )
        else:
            self.engine = create_engine(
                database_url,
                echo=os.getenv("DATABASE_ECHO", "False").lower() == "true"
            )
        
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def create_tables(self):
        """Create all database tables."""
        Base.metadata.create_all(bind=self.engine)
    
    def drop_tables(self):
        """Drop all database tables."""
        Base.metadata.drop_all(bind=self.engine)
    
    def get_session(self) -> Session:
        """Get a database session."""
        return self.SessionLocal()
    
    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """Provide a transactional scope around a series of operations."""
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


# Global database manager instance
db_manager = DatabaseManager()


def get_db() -> Generator[Session, None, None]:
    """Dependency for FastAPI to get database session."""
    with db_manager.session_scope() as session:
        yield session


def init_database():
    """Initialize the database with tables."""
    # Ensure data directory exists
    os.makedirs("./data", exist_ok=True)
    
    # Create tables
    db_manager.create_tables()
    print("Database initialized successfully!")


if __name__ == "__main__":
    init_database()
