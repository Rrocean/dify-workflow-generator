"""
Database persistence layer for workflows
Supports SQLite, PostgreSQL with async operations
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager
import json
import uuid

try:
    from sqlalchemy import create_engine, Column, String, DateTime, Text, Integer
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker, Session
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False

from .workflow import Workflow
from .exceptions import DatabaseError

Base = declarative_base() if DATABASE_AVAILABLE else None


class WorkflowRecord(Base if DATABASE_AVAILABLE else object):
    """Database model for workflow storage"""
    __tablename__ = "workflows"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    mode = Column(String(50), nullable=False)
    dsl_version = Column(String(20), default="0.5.0")
    content = Column(Text, nullable=False)  # JSON serialized workflow
    tags = Column(Text)  # JSON array
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    version = Column(Integer, default=1)
    created_by = Column(String(100))
    is_public = Column(Integer, default=0)  # 0 = private, 1 = public


class WorkflowDatabase:
    """Database manager for workflow persistence"""

    def __init__(self, database_url: str = "sqlite:///data/workflows.db"):
        if not DATABASE_AVAILABLE:
            raise DatabaseError("Database support not available. Install with: pip install sqlalchemy")

        self.database_url = database_url
        self._engine = None
        self._session_factory = None
        self._init_engine()

    def _init_engine(self):
        """Initialize database engine"""
        if self.database_url.startswith("sqlite"):
            self._engine = create_engine(
                self.database_url,
                connect_args={"check_same_thread": False}
            )
        else:
            self._engine = create_engine(self.database_url)

        Base.metadata.create_all(self._engine)
        self._session_factory = sessionmaker(bind=self._engine)

    @asynccontextmanager
    async def get_session(self):
        """Get async database session"""
        if self.database_url.startswith("sqlite"):
            engine = create_async_engine(
                self.database_url.replace("sqlite://", "sqlite+aiosqlite://"),
                connect_args={"check_same_thread": False}
            )
        else:
            engine = create_async_engine(self.database_url)

        async_session = async_sessionmaker(engine, expire_on_commit=False)
        async with async_session() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    def save_workflow(self, workflow: Workflow,
                      workflow_id: Optional[str] = None,
                      created_by: Optional[str] = None,
                      tags: Optional[List[str]] = None,
                      is_public: bool = False) -> str:
        """Save workflow to database"""
        try:
            session = self._session_factory()

            # Serialize workflow
            content = json.dumps(workflow.to_dict())

            # Check if workflow exists
            if workflow_id:
                record = session.query(WorkflowRecord).filter_by(id=workflow_id).first()
                if record:
                    # Update existing
                    record.name = workflow.name
                    record.description = workflow.description
                    record.content = content
                    record.tags = json.dumps(tags or [])
                    record.updated_at = datetime.utcnow()
                    record.version += 1
                    session.commit()
                    return record.id

            # Create new
            record = WorkflowRecord(
                id=workflow_id or str(uuid.uuid4()),
                name=workflow.name,
                description=workflow.description,
                mode=workflow.mode,
                content=content,
                tags=json.dumps(tags or []),
                created_by=created_by,
                is_public=1 if is_public else 0
            )
            session.add(record)
            session.commit()
            return record.id

        except Exception as e:
            raise DatabaseError(f"Failed to save workflow: {e}")

    def load_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Load workflow from database"""
        try:
            session = self._session_factory()
            record = session.query(WorkflowRecord).filter_by(id=workflow_id).first()

            if not record:
                return None

            return {
                "id": record.id,
                "name": record.name,
                "description": record.description,
                "mode": record.mode,
                "content": json.loads(record.content),
                "tags": json.loads(record.tags) if record.tags else [],
                "created_at": record.created_at.isoformat(),
                "updated_at": record.updated_at.isoformat(),
                "version": record.version,
                "created_by": record.created_by,
                "is_public": bool(record.is_public)
            }

        except Exception as e:
            raise DatabaseError(f"Failed to load workflow: {e}")

    def list_workflows(self, created_by: Optional[str] = None,
                       tags: Optional[List[str]] = None,
                       is_public: Optional[bool] = None,
                       limit: int = 100,
                       offset: int = 0) -> List[Dict[str, Any]]:
        """List workflows with filtering"""
        try:
            session = self._session_factory()
            query = session.query(WorkflowRecord)

            if created_by:
                query = query.filter_by(created_by=created_by)

            if is_public is not None:
                query = query.filter_by(is_public=1 if is_public else 0)

            if tags:
                # Simple tag filtering (can be improved with proper JSON query)
                for tag in tags:
                    query = query.filter(WorkflowRecord.tags.contains(tag))

            records = query.order_by(WorkflowRecord.updated_at.desc()).offset(offset).limit(limit).all()

            return [
                {
                    "id": r.id,
                    "name": r.name,
                    "description": r.description,
                    "mode": r.mode,
                    "tags": json.loads(r.tags) if r.tags else [],
                    "created_at": r.created_at.isoformat(),
                    "updated_at": r.updated_at.isoformat(),
                    "version": r.version,
                    "created_by": r.created_by,
                    "is_public": bool(r.is_public)
                }
                for r in records
            ]

        except Exception as e:
            raise DatabaseError(f"Failed to list workflows: {e}")

    def delete_workflow(self, workflow_id: str, created_by: Optional[str] = None) -> bool:
        """Delete workflow from database"""
        try:
            session = self._session_factory()
            query = session.query(WorkflowRecord).filter_by(id=workflow_id)

            if created_by:
                query = query.filter_by(created_by=created_by)

            record = query.first()
            if not record:
                return False

            session.delete(record)
            session.commit()
            return True

        except Exception as e:
            raise DatabaseError(f"Failed to delete workflow: {e}")

    def search_workflows(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search workflows by name or description"""
        try:
            session = self._session_factory()
            records = session.query(WorkflowRecord).filter(
                WorkflowRecord.name.contains(query) |
                WorkflowRecord.description.contains(query)
            ).limit(limit).all()

            return [
                {
                    "id": r.id,
                    "name": r.name,
                    "description": r.description,
                    "mode": r.mode,
                    "tags": json.loads(r.tags) if r.tags else [],
                    "updated_at": r.updated_at.isoformat()
                }
                for r in records
            ]

        except Exception as e:
            raise DatabaseError(f"Failed to search workflows: {e}")

    def get_workflow_versions(self, workflow_id: str) -> List[Dict[str, Any]]:
        """Get version history of a workflow (placeholder for versioning support)"""
        # This would require a separate versions table
        # For now, just return current version
        workflow = self.load_workflow(workflow_id)
        if workflow:
            return [{
                "version": workflow["version"],
                "updated_at": workflow["updated_at"],
                "current": True
            }]
        return []


# Global database instance
_db_instance: Optional[WorkflowDatabase] = None


def get_database(database_url: Optional[str] = None) -> WorkflowDatabase:
    """Get or create global database instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = WorkflowDatabase(database_url)
    return _db_instance
