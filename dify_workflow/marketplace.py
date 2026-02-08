"""
Workflow marketplace for sharing and discovering workflows
Community-driven workflow hub with ratings, tags, and search
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
import json
import hashlib
import base64
from pathlib import Path

from .workflow import Workflow
from .database import WorkflowDatabase, get_database
from .exceptions import MarketplaceError


@dataclass
class WorkflowEntry:
    """Marketplace workflow entry"""
    id: str
    name: str
    description: str
    author: str
    version: str
    tags: List[str] = field(default_factory=list)
    rating: float = 0.0
    downloads: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    workflow_data: Dict[str, Any] = field(default_factory=dict)
    icon: str = "🤖"
    category: str = "general"
    verified: bool = False


@dataclass
class UserProfile:
    """Marketplace user profile"""
    username: str
    display_name: str
    bio: str = ""
    workflows: List[str] = field(default_factory=list)
    joined_at: datetime = field(default_factory=datetime.utcnow)
    reputation: int = 0


class WorkflowMarketplace:
    """Community workflow marketplace"""

    def __init__(self, db: Optional[WorkflowDatabase] = None):
        self.db = db or get_database()
        self._local_cache: Dict[str, WorkflowEntry] = {}

    def publish_workflow(
        self,
        workflow: Workflow,
        author: str,
        tags: Optional[List[str]] = None,
        category: str = "general",
        icon: str = "🤖"
    ) -> str:
        """Publish workflow to marketplace"""
        try:
            # Generate unique ID
            workflow_json = json.dumps(workflow.to_dict(), sort_keys=True)
            workflow_id = hashlib.md5(
                f"{workflow.name}:{author}:{datetime.utcnow().isoformat()}".encode()
            ).hexdigest()[:12]

            entry = WorkflowEntry(
                id=workflow_id,
                name=workflow.name,
                description=workflow.description or "",
                author=author,
                version="1.0.0",
                tags=tags or [],
                workflow_data=workflow.to_dict(),
                icon=icon,
                category=category
            )

            # Save to database
            self._save_entry(entry)

            return workflow_id

        except Exception as e:
            raise MarketplaceError(f"Failed to publish workflow: {e}")

    def get_workflow(self, workflow_id: str) -> Optional[WorkflowEntry]:
        """Get workflow from marketplace"""
        try:
            # Check cache first
            if workflow_id in self._local_cache:
                return self._local_cache[workflow_id]

            # Load from database
            entry = self._load_entry(workflow_id)
            if entry:
                self._local_cache[workflow_id] = entry

            return entry

        except Exception as e:
            raise MarketplaceError(f"Failed to get workflow: {e}")

    def search_workflows(
        self,
        query: str = "",
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        author: Optional[str] = None,
        min_rating: float = 0.0,
        sort_by: str = "downloads",  # downloads, rating, recent
        limit: int = 50
    ) -> List[WorkflowEntry]:
        """Search marketplace workflows"""
        try:
            results = []

            # Get all workflows from database
            records = self.db.list_workflows(is_public=True, limit=1000)

            for record in records:
                entry = self._record_to_entry(record)

                # Apply filters
                if query and query.lower() not in entry.name.lower() and \
                   query.lower() not in entry.description.lower():
                    continue

                if category and entry.category != category:
                    continue

                if tags and not any(tag in entry.tags for tag in tags):
                    continue

                if author and entry.author != author:
                    continue

                if entry.rating < min_rating:
                    continue

                results.append(entry)

            # Sort results
            if sort_by == "downloads":
                results.sort(key=lambda x: x.downloads, reverse=True)
            elif sort_by == "rating":
                results.sort(key=lambda x: x.rating, reverse=True)
            elif sort_by == "recent":
                results.sort(key=lambda x: x.updated_at, reverse=True)

            return results[:limit]

        except Exception as e:
            raise MarketplaceError(f"Failed to search workflows: {e}")

    def download_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Download workflow from marketplace"""
        try:
            entry = self.get_workflow(workflow_id)
            if not entry:
                return None

            # Increment download count
            self._increment_downloads(workflow_id)

            # Reconstruct workflow
            workflow = Workflow.from_dict(entry.workflow_data)
            return workflow

        except Exception as e:
            raise MarketplaceError(f"Failed to download workflow: {e}")

    def rate_workflow(self, workflow_id: str, rating: float, user: str) -> bool:
        """Rate a workflow (1-5 stars)"""
        if not 1 <= rating <= 5:
            raise ValueError("Rating must be between 1 and 5")

        try:
            entry = self.get_workflow(workflow_id)
            if not entry:
                return False

            # Calculate new rating
            # In real implementation, store individual ratings
            entry.rating = (entry.rating * entry.downloads + rating) / (entry.downloads + 1)
            self._save_entry(entry)

            return True

        except Exception as e:
            raise MarketplaceError(f"Failed to rate workflow: {e}")

    def get_categories(self) -> List[str]:
        """Get available workflow categories"""
        return [
            "chat",
            "nlp",
            "content",
            "developer",
            "productivity",
            "data",
            "integration",
            "general"
        ]

    def get_popular_tags(self, limit: int = 20) -> List[tuple]:
        """Get most popular tags with counts"""
        try:
            tag_counts: Dict[str, int] = {}

            workflows = self.search_workflows(limit=1000)
            for workflow in workflows:
                for tag in workflow.tags:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1

            # Sort by count
            sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
            return sorted_tags[:limit]

        except Exception as e:
            raise MarketplaceError(f"Failed to get popular tags: {e}")

    def get_trending(self, days: int = 7, limit: int = 10) -> List[WorkflowEntry]:
        """Get trending workflows from last N days"""
        # In real implementation, query by recent download velocity
        return self.search_workflows(sort_by="downloads", limit=limit)

    def _save_entry(self, entry: WorkflowEntry):
        """Save entry to database"""
        # Convert to dict and store
        entry_data = {
            "id": entry.id,
            "name": entry.name,
            "description": entry.description,
            "author": entry.author,
            "version": entry.version,
            "tags": json.dumps(entry.tags),
            "rating": entry.rating,
            "downloads": entry.downloads,
            "created_at": entry.created_at.isoformat(),
            "updated_at": entry.updated_at.isoformat(),
            "content": json.dumps(entry.workflow_data),
            "icon": entry.icon,
            "category": entry.category,
            "verified": entry.verified,
            "is_public": 1
        }

        # This would use a dedicated marketplace table
        # For now, using the workflow table with extra metadata
        workflow = Workflow.from_dict(entry.workflow_data)
        workflow.name = f"[MARKETPLACE:{entry.category}] {entry.name}"

        self.db.save_workflow(
            workflow=workflow,
            workflow_id=entry.id,
            created_by=entry.author,
            tags=entry.tags,
            is_public=True
        )

    def _load_entry(self, workflow_id: str) -> Optional[WorkflowEntry]:
        """Load entry from database"""
        record = self.db.load_workflow(workflow_id)
        if not record:
            return None

        return self._record_to_entry(record)

    def _record_to_entry(self, record: Dict[str, Any]) -> WorkflowEntry:
        """Convert database record to WorkflowEntry"""
        return WorkflowEntry(
            id=record["id"],
            name=record["name"],
            description=record.get("description", ""),
            author=record.get("created_by", "unknown"),
            version=str(record.get("version", "1.0.0")),
            tags=record.get("tags", []),
            created_at=datetime.fromisoformat(record["created_at"]),
            updated_at=datetime.fromisoformat(record["updated_at"]),
            workflow_data=record.get("content", {}),
            category="general",
            icon="🤖"
        )

    def _increment_downloads(self, workflow_id: str):
        """Increment download counter"""
        entry = self.get_workflow(workflow_id)
        if entry:
            entry.downloads += 1
            self._save_entry(entry)


class LocalWorkflowHub:
    """Local workflow hub for team sharing"""

    def __init__(self, hub_path: str = "./workflow_hub"):
        self.hub_path = Path(hub_path)
        self.hub_path.mkdir(exist_ok=True)

    def add_workflow(self, workflow: Workflow, filename: str):
        """Add workflow to local hub"""
        filepath = self.hub_path / filename
        workflow.export(str(filepath))

    def list_workflows(self) -> List[Dict[str, Any]]:
        """List all workflows in hub"""
        workflows = []

        for filepath in self.hub_path.glob("*.yml"):
            try:
                from .importer import import_workflow
                workflow = import_workflow(str(filepath))
                workflows.append({
                    "filename": filepath.name,
                    "name": workflow.name,
                    "path": str(filepath)
                })
            except Exception:
                continue

        return workflows

    def install_workflow(self, filename: str, target_dir: str = "./workflows"):
        """Install workflow from hub"""
        source = self.hub_path / filename
        target = Path(target_dir) / filename

        if source.exists():
            target.write_text(source.read_text())
            return True
        return False
