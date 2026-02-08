"""
Git integration for workflow version control
Track changes, create branches, and collaborate on workflows
"""
import os
import json
import hashlib
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class WorkflowCommit:
    """Git-like commit for workflows"""
    hash: str
    message: str
    author: str
    timestamp: datetime
    parent: Optional[str] = None
    changes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowBranch:
    """Git-like branch"""
    name: str
    head: str  # Commit hash
    created_at: datetime = field(default_factory=datetime.now)


class WorkflowGit:
    """
    Git-like version control for workflows
    Stores history in .difygit directory
    """

    def __init__(self, workflow_path: str):
        self.workflow_path = Path(workflow_path)
        self.git_dir = self.workflow_path.parent / ".difygit"
        self.commits_dir = self.git_dir / "commits"
        self.branches_file = self.git_dir / "branches.json"
        self.head_file = self.git_dir / "HEAD"

        self._ensure_git_dir()

    def _ensure_git_dir(self):
        """Create .difygit directory structure"""
        self.git_dir.mkdir(exist_ok=True)
        self.commits_dir.mkdir(exist_ok=True)

        if not self.branches_file.exists():
            self._save_branches({"main": WorkflowBranch("main", "")})

        if not self.head_file.exists():
            self.head_file.write_text("main")

    def _save_branches(self, branches: Dict[str, WorkflowBranch]):
        """Save branches to file"""
        data = {
            name: {
                "name": b.name,
                "head": b.head,
                "created_at": b.created_at.isoformat()
            }
            for name, b in branches.items()
        }
        self.branches_file.write_text(json.dumps(data, indent=2))

    def _load_branches(self) -> Dict[str, WorkflowBranch]:
        """Load branches from file"""
        if not self.branches_file.exists():
            return {}

        data = json.loads(self.branches_file.read_text())
        return {
            name: WorkflowBranch(
                name=d["name"],
                head=d["head"],
                created_at=datetime.fromisoformat(d["created_at"])
            )
            for name, d in data.items()
        }

    def _get_current_branch(self) -> str:
        """Get current branch name"""
        if self.head_file.exists():
            return self.head_file.read_text().strip()
        return "main"

    def _set_current_branch(self, branch: str):
        """Set current branch"""
        self.head_file.write_text(branch)

    def _compute_hash(self, content: str) -> str:
        """Compute commit hash"""
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _save_commit(self, commit: WorkflowCommit):
        """Save commit to file"""
        commit_file = self.commits_dir / f"{commit.hash}.json"
        data = {
            "hash": commit.hash,
            "message": commit.message,
            "author": commit.author,
            "timestamp": commit.timestamp.isoformat(),
            "parent": commit.parent,
            "changes": commit.changes
        }
        commit_file.write_text(json.dumps(data, indent=2))

    def _load_commit(self, commit_hash: str) -> Optional[WorkflowCommit]:
        """Load commit from file"""
        commit_file = self.commits_dir / f"{commit_hash}.json"
        if not commit_file.exists():
            return None

        data = json.loads(commit_file.read_text())
        return WorkflowCommit(
            hash=data["hash"],
            message=data["message"],
            author=data["author"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            parent=data.get("parent"),
            changes=data.get("changes", {})
        )

    def commit(self, message: str, author: str = "Anonymous") -> str:
        """
        Commit current workflow state
        """
        # Read current workflow content
        content = self.workflow_path.read_text()

        # Compute hash
        commit_hash = self._compute_hash(content + message + str(datetime.now()))

        # Get parent commit
        branches = self._load_branches()
        current_branch = self._get_current_branch()
        parent = branches.get(current_branch, WorkflowBranch("main", "")).head

        # Create commit
        commit = WorkflowCommit(
            hash=commit_hash,
            message=message,
            author=author,
            timestamp=datetime.now(),
            parent=parent,
            changes={"workflow": content}
        )

        # Save commit
        self._save_commit(commit)

        # Update branch head
        branches[current_branch].head = commit_hash
        self._save_branches(branches)

        return commit_hash

    def log(self, branch: Optional[str] = None) -> List[WorkflowCommit]:
        """
        Get commit history
        """
        branches = self._load_branches()
        branch_name = branch or self._get_current_branch()

        if branch_name not in branches:
            return []

        commits = []
        current = branches[branch_name].head

        while current:
            commit = self._load_commit(current)
            if not commit:
                break

            commits.append(commit)
            current = commit.parent

        return commits

    def diff(self, commit1: str, commit2: Optional[str] = None) -> Dict[str, Any]:
        """
        Diff between two commits
        """
        c1 = self._load_commit(commit1)
        c2 = self._load_commit(commit2) if commit2 else None

        if not c1:
            return {"error": f"Commit {commit1} not found"}

        # Simple text diff
        from difflib import unified_diff

        content1 = c1.changes.get("workflow", "").splitlines(keepends=True)
        content2 = (c2.changes.get("workflow", "") if c2 else "").splitlines(keepends=True)

        diff = list(unified_diff(
            content2, content1,
            fromfile=f"commit {commit2 or 'empty'}",
            tofile=f"commit {commit1}",
            lineterm=""
        ))

        return {
            "commit1": commit1,
            "commit2": commit2,
            "diff": "".join(diff)
        }

    def checkout(self, commit_hash: str) -> bool:
        """
        Checkout a specific commit
        """
        commit = self._load_commit(commit_hash)
        if not commit:
            return False

        # Restore workflow content
        content = commit.changes.get("workflow", "")
        self.workflow_path.write_text(content)

        return True

    def create_branch(self, name: str, from_commit: Optional[str] = None) -> bool:
        """
        Create new branch
        """
        branches = self._load_branches()

        if name in branches:
            return False

        current_branch = self._get_current_branch()
        parent_commit = from_commit or branches[current_branch].head

        branches[name] = WorkflowBranch(name, parent_commit)
        self._save_branches(branches)

        return True

    def switch_branch(self, name: str) -> bool:
        """
        Switch to another branch
        """
        branches = self._load_branches()

        if name not in branches:
            return False

        # Checkout branch head
        head = branches[name].head
        if head:
            self.checkout(head)

        self._set_current_branch(name)
        return True

    def list_branches(self) -> List[Dict[str, Any]]:
        """
        List all branches
        """
        branches = self._load_branches()
        current = self._get_current_branch()

        return [
            {
                "name": name,
                "head": b.head,
                "current": name == current,
                "created_at": b.created_at.isoformat()
            }
            for name, b in branches.items()
        ]

    def status(self) -> Dict[str, Any]:
        """
        Get repository status
        """
        branches = self._load_branches()
        current_branch = self._get_current_branch()
        head = branches.get(current_branch, WorkflowBranch("main", "")).head

        # Check if there are uncommitted changes
        if head:
            commit = self._load_commit(head)
            if commit:
                current_content = self.workflow_path.read_text()
                committed_content = commit.changes.get("workflow", "")
                has_changes = current_content != committed_content
            else:
                has_changes = True
        else:
            has_changes = self.workflow_path.exists()

        return {
            "branch": current_branch,
            "head": head,
            "uncommitted_changes": has_changes,
            "commits_ahead": 0,  # Would compare with remote
            "commits_behind": 0
        }

    def merge(self, branch_name: str) -> Dict[str, Any]:
        """
        Merge branch into current branch
        """
        branches = self._load_branches()

        if branch_name not in branches:
            return {"success": False, "error": f"Branch {branch_name} not found"}

        current = self._get_current_branch()
        if branch_name == current:
            return {"success": False, "error": "Cannot merge branch into itself"}

        # Simple merge - just create merge commit
        merge_message = f"Merge branch '{branch_name}' into {current}"
        merge_hash = self.commit(merge_message)

        return {
            "success": True,
            "merge_commit": merge_hash,
            "message": merge_message
        }


class WorkflowDiff:
    """Diff utilities for workflows"""

    @staticmethod
    def structural_diff(workflow1, workflow2) -> Dict[str, Any]:
        """
        Compare structure of two workflows
        """
        changes = {
            "added_nodes": [],
            "removed_nodes": [],
            "modified_nodes": [],
            "added_edges": [],
            "removed_edges": []
        }

        nodes1 = {n.id: n for n in workflow1.nodes}
        nodes2 = {n.id: n for n in workflow2.nodes}

        # Find added/removed nodes
        for node_id in nodes2:
            if node_id not in nodes1:
                changes["added_nodes"].append(node_id)

        for node_id in nodes1:
            if node_id not in nodes2:
                changes["removed_nodes"].append(node_id)

        # Find modified nodes
        for node_id in nodes1:
            if node_id in nodes2:
                n1 = nodes1[node_id]
                n2 = nodes2[node_id]
                if n1.data != n2.data:
                    changes["modified_nodes"].append({
                        "id": node_id,
                        "old": n1.data,
                        "new": n2.data
                    })

        return changes
