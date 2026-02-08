"""
Migration tools for workflows
Migrate between Dify versions and other platforms
"""
import json
import re
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path


class DifyVersionMigrator:
    """Migrate workflows between Dify DSL versions"""

    VERSIONS = ["0.1.0", "0.2.0", "0.3.0", "0.4.0", "0.5.0"]

    def __init__(self):
        self.migrations: Dict[str, Callable] = {
            "0.1.0_0.2.0": self._migrate_010_to_020,
            "0.2.0_0.3.0": self._migrate_020_to_030,
            "0.3.0_0.4.0": self._migrate_030_to_040,
            "0.4.0_0.5.0": self._migrate_040_to_050,
        }

    def migrate(self, workflow_data: Dict[str, Any], target_version: str = "0.5.0") -> Dict[str, Any]:
        """Migrate workflow to target version"""
        current_version = workflow_data.get("version", "0.1.0")

        if current_version == target_version:
            return workflow_data

        # Find migration path
        current_idx = self.VERSIONS.index(current_version)
        target_idx = self.VERSIONS.index(target_version)

        if target_idx < current_idx:
            raise ValueError("Downgrading not supported")

        result = workflow_data.copy()

        for i in range(current_idx, target_idx):
            from_ver = self.VERSIONS[i]
            to_ver = self.VERSIONS[i + 1]
            key = f"{from_ver}_{to_ver}"

            if key in self.migrations:
                print(f"Migrating {from_ver} -> {to_ver}")
                result = self.migrations[key](result)
                result["version"] = to_ver

        return result

    def _migrate_010_to_020(self, data: Dict) -> Dict:
        """Migrate 0.1.0 to 0.2.0"""
        # Add kind field
        data["kind"] = "app"
        return data

    def _migrate_020_to_030(self, data: Dict) -> Dict:
        """Migrate 0.2.0 to 0.3.0"""
        # Restructure app section
        if "app" not in data:
            data["app"] = {}
        data["app"]["use_icon_as_answer_icon"] = False
        return data

    def _migrate_030_to_040(self, data: Dict) -> Dict:
        """Migrate 0.3.0 to 0.4.0"""
        # Add metadata
        if "app" in data:
            data["app"]["tags"] = []
        return data

    def _migrate_040_to_050(self, data: Dict) -> Dict:
        """Migrate 0.4.0 to 0.5.0"""
        # Update node structure
        if "workflow" in data and "graph" in data["workflow"]:
            for node in data["workflow"]["graph"].get("nodes", []):
                # Add default values
                if "data" in node:
                    node["data"]["selected"] = False
        return data


class LangchainMigrator:
    """Migrate Langchain chains to Dify workflows"""

    def migrate(self, langchain_code: str) -> Dict[str, Any]:
        """Convert Langchain code to Dify workflow"""
        workflow = {
            "version": "0.5.0",
            "kind": "app",
            "app": {
                "name": "Migrated from Langchain",
                "mode": "workflow",
                "description": "Auto-migrated from Langchain"
            },
            "workflow": {
                "graph": {
                    "nodes": [],
                    "edges": []
                }
            }
        }

        # Parse LLM chain
        if "LLMChain" in langchain_code or "|" in langchain_code:
            # Simple parsing - extract prompt template
            prompt_match = re.search(r'prompt\s*=\s*[\'"](.+?)[\'"]', langchain_code, re.DOTALL)
            if prompt_match:
                prompt = prompt_match.group(1)
            else:
                prompt = "{{#start.input#}}"

            # Create workflow structure
            workflow["workflow"]["graph"]["nodes"] = [
                {
                    "id": "start",
                    "position": {"x": 100, "y": 300},
                    "data": {
                        "type": "start",
                        "title": "Start",
                        "variables": [{"variable": "input", "type": "string"}]
                    }
                },
                {
                    "id": "llm",
                    "position": {"x": 400, "y": 300},
                    "data": {
                        "type": "llm",
                        "title": "LLM",
                        "prompt": prompt,
                        "model": {"provider": "openai", "name": "gpt-4"}
                    }
                },
                {
                    "id": "end",
                    "position": {"x": 700, "y": 300},
                    "data": {
                        "type": "end",
                        "title": "End",
                        "outputs": [{"variable": "output", "value_selector": ["llm", "text"]}]
                    }
                }
            ]

            workflow["workflow"]["graph"]["edges"] = [
                {"source": "start", "target": "llm"},
                {"source": "llm", "target": "end"}
            ]

        return workflow


class MakeMigrator:
    """Migrate Make (Integromat) scenarios to Dify"""

    def migrate(self, make_scenario: Dict) -> Dict[str, Any]:
        """Convert Make scenario to Dify workflow"""
        workflow = {
            "version": "0.5.0",
            "kind": "app",
            "app": {
                "name": make_scenario.get("name", "Migrated from Make"),
                "mode": "workflow",
                "description": "Auto-migrated from Make"
            },
            "workflow": {
                "graph": {
                    "nodes": [],
                    "edges": []
                }
            }
        }

        nodes = []
        edges = []

        # Map Make modules to Dify nodes
        for i, module in enumerate(make_scenario.get("modules", [])):
            node_id = f"node_{i}"

            # Determine node type
            module_type = module.get("type", "")
            if "http" in module_type.lower():
                dify_type = "http"
            elif "openai" in module_type.lower():
                dify_type = "llm"
            elif "filter" in module_type.lower():
                dify_type = "if-else"
            else:
                dify_type = "code"

            node = {
                "id": node_id,
                "position": {"x": 100 + i * 300, "y": 300},
                "data": {
                    "type": dify_type,
                    "title": module.get("name", f"Node {i}"),
                    "desc": module.get("description", "")
                }
            }

            nodes.append(node)

            # Create edge from previous node
            if i > 0:
                edges.append({
                    "source": f"node_{i-1}",
                    "target": node_id
                })

        workflow["workflow"]["graph"]["nodes"] = nodes
        workflow["workflow"]["graph"]["edges"] = edges

        return workflow


class ZapierMigrator:
    """Migrate Zapier Zaps to Dify workflows"""

    def migrate(self, zap: Dict) -> Dict[str, Any]:
        """Convert Zap to Dify workflow"""
        workflow = {
            "version": "0.5.0",
            "kind": "app",
            "app": {
                "name": zap.get("name", "Migrated from Zapier"),
                "mode": "workflow",
                "description": "Auto-migrated from Zapier"
            },
            "workflow": {
                "graph": {
                    "nodes": [],
                    "edges": []
                }
            }
        }

        nodes = []
        edges = []

        # Trigger
        trigger = zap.get("trigger", {})
        nodes.append({
            "id": "trigger",
            "position": {"x": 100, "y": 300},
            "data": {
                "type": "start",
                "title": trigger.get("type", "Trigger"),
                "variables": [{"variable": "trigger_data", "type": "object"}]
            }
        })

        # Actions
        for i, action in enumerate(zap.get("actions", [])):
            node_id = f"action_{i}"

            action_type = action.get("type", "")
            if "delay" in action_type.lower():
                dify_type = "code"  # No delay node, use code
            elif "filter" in action_type.lower():
                dify_type = "if-else"
            elif "path" in action_type.lower():
                dify_type = "if-else"
            else:
                dify_type = "http"

            nodes.append({
                "id": node_id,
                "position": {"x": 400 + i * 300, "y": 300},
                "data": {
                    "type": dify_type,
                    "title": action.get("type", f"Action {i}")
                }
            })

            # Edge
            prev_id = "trigger" if i == 0 else f"action_{i-1}"
            edges.append({
                "source": prev_id,
                "target": node_id
            })

        # Add end node
        nodes.append({
            "id": "end",
            "position": {"x": 400 + len(zap.get("actions", [])) * 300, "y": 300},
            "data": {"type": "end", "title": "End"}
        })

        if nodes:
            edges.append({
                "source": f"action_{len(zap.get('actions', [])) - 1}" if zap.get("actions") else "trigger",
                "target": "end"
            })

        workflow["workflow"]["graph"]["nodes"] = nodes
        workflow["workflow"]["graph"]["edges"] = edges

        return workflow


class WorkflowMigrator:
    """Main migrator class - routes to specific migrators"""

    def __init__(self):
        self.dify_migrator = DifyVersionMigrator()
        self.langchain_migrator = LangchainMigrator()
        self.make_migrator = MakeMigrator()
        self.zapier_migrator = ZapierMigrator()

    def migrate(
        self,
        source: Any,
        from_format: str,
        to_format: str = "dify",
        **options
    ) -> Dict[str, Any]:
        """
        Migrate workflow from one format to another

        Args:
            source: Source data (dict, str, or file path)
            from_format: Source format (dify, langchain, make, zapier)
            to_format: Target format (dify)
            **options: Additional migration options

        Returns:
            Migrated workflow as dict
        """
        # Load source if file path
        if isinstance(source, (str, Path)) and Path(source).exists():
            with open(source) as f:
                if str(source).endswith('.json'):
                    source = json.load(f)
                else:
                    source = f.read()

        # Convert to Dify format
        if from_format == "dify":
            if isinstance(source, str):
                import yaml
                source = yaml.safe_load(source)
            result = self.dify_migrator.migrate(source, options.get("target_version", "0.5.0"))

        elif from_format == "langchain":
            result = self.langchain_migrator.migrate(source)

        elif from_format == "make":
            result = self.make_migrator.migrate(source)

        elif from_format == "zapier":
            result = self.zapier_migrator.migrate(source)

        else:
            raise ValueError(f"Unsupported source format: {from_format}")

        return result
