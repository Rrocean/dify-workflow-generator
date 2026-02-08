"""
Workflow class for building and exporting Dify-compatible DSL files.

This generates YAML files that can be directly imported into Dify.
"""

import json
from typing import Any, Dict, List, Optional, Tuple, Union
import yaml

from .nodes import Node, StartNode, EndNode
from .constants import DSL_VERSION
from .exceptions import ValidationError, ConnectionError
from .logging_config import get_logger

logger = get_logger("workflow")


class Workflow:
    """
    Build Dify workflows programmatically.
    
    Example:
        wf = Workflow("My Workflow", mode="workflow")
        wf.add_node(StartNode(variables=[...]))
        wf.add_node(LLMNode(title="chat", prompt="Hello"))
        wf.connect(start, llm)
        wf.export("workflow.yml")
    
    Args:
        name: Workflow name
        mode: App mode - "workflow" or "advanced-chat"
        description: App description
        icon: App icon (emoji or image path)
        icon_background: Icon background color
    """
    
    def __init__(
        self,
        name: str,
        mode: str = "workflow",
        description: str = "",
        icon: str = "🤖",
        icon_background: str = "#FFEAD5",
    ):
        if mode not in ("workflow", "advanced-chat"):
            raise ValidationError(
                f"Invalid mode: {mode}. Must be 'workflow' or 'advanced-chat'",
                {"mode": mode, "valid_modes": ["workflow", "advanced-chat"]}
            )
        
        self.name = name
        self.mode = mode
        self.description = description
        self.icon = icon
        self.icon_background = icon_background
        
        self.nodes: List[Node] = []
        self.edges: List[Dict[str, Any]] = []
        self.environment_variables: List[Dict[str, Any]] = []
        self.conversation_variables: List[Dict[str, Any]] = []
        self.features: Dict[str, Any] = {}
        
        self._node_counter = 0
        self._edge_counter = 0
    
    def add_node(self, node: Node) -> "Workflow":
        """
        Add a node to the workflow.
        
        Nodes are automatically positioned in a grid layout.
        """
        # Auto-position nodes in a grid
        col = self._node_counter % 3
        row = self._node_counter // 3
        
        node.position_x = 100 + col * 300
        node.position_y = 100 + row * 200
        
        # Special positioning for start node
        if isinstance(node, StartNode):
            node.position_x = 100
            node.position_y = 300
        
        self._node_counter += 1
        self.nodes.append(node)
        return self
    
    def add_nodes(self, nodes: List[Node]) -> "Workflow":
        """Add multiple nodes at once."""
        for node in nodes:
            self.add_node(node)
        return self
    
    def connect(
        self,
        source: Union[Node, str],
        target: Union[Node, str],
        source_handle: str = "source",
        target_handle: str = "target",
    ) -> "Workflow":
        """
        Connect two nodes with an edge.
        
        Args:
            source: Source node or node ID
            target: Target node or node ID
            source_handle: Source handle name (use "true"/"false" for if-else branches)
            target_handle: Target handle name
            
        Raises:
            ConnectionError: If source or target node is not found
        """
        source_id = source.id if isinstance(source, Node) else source
        target_id = target.id if isinstance(target, Node) else target
        
        # Validate nodes exist
        node_ids = {n.id for n in self.nodes}
        if source_id not in node_ids:
            raise ConnectionError(
                f"Source node '{source_id}' not found in workflow",
                source_id=source_id,
                target_id=target_id
            )
        if target_id not in node_ids:
            raise ConnectionError(
                f"Target node '{target_id}' not found in workflow",
                source_id=source_id,
                target_id=target_id
            )
        
        edge = {
            "id": f"edge_{self._edge_counter}",
            "source": source_id,
            "target": target_id,
            "sourceHandle": source_handle,
            "targetHandle": target_handle,
        }
        
        self._edge_counter += 1
        self.edges.append(edge)
        logger.debug(f"Connected {source_id} -> {target_id} ({source_handle})")
        return self
    
    def get_node(self, node_id: str) -> Optional[Node]:
        """Get a node by its ID."""
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None
    
    def get_node_by_title(self, title: str) -> Optional[Node]:
        """Get a node by its title."""
        for node in self.nodes:
            if node.title == title:
                return node
        return None
    
    def add_environment_variable(
        self,
        name: str,
        value: str = "",
        value_type: str = "string",
    ) -> "Workflow":
        """
        Add an environment variable to the workflow.
        
        These are available to all nodes at runtime.
        """
        self.environment_variables.append({
            "name": name,
            "value": value,
            "value_type": value_type,
        })
        return self
    
    def add_conversation_variable(
        self,
        name: str,
        value: Any = "",
        value_type: str = "string",
    ) -> "Workflow":
        """
        Add a conversation variable (for advanced-chat mode).
        
        These persist across conversation turns.
        """
        self.conversation_variables.append({
            "name": name,
            "value": value,
            "value_type": value_type,
        })
        return self
    
    def set_features(self, features: Dict[str, Any]) -> "Workflow":
        """Set workflow features (opening statement, suggested questions, etc.)"""
        self.features = features
        return self
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert workflow to Dify DSL dictionary format.
        
        This is the format that can be imported into Dify.
        """
        return {
            "version": DSL_VERSION,
            "kind": "app",
            "app": {
                "name": self.name,
                "mode": self.mode,
                "icon": self.icon,
                "icon_background": self.icon_background,
                "description": self.description,
                "use_icon_as_answer_icon": False,
            },
            "workflow": {
                "graph": {
                    "nodes": [n.to_dict() for n in self.nodes],
                    "edges": self.edges,
                },
                "features": self.features,
                "environment_variables": self.environment_variables,
                "conversation_variables": self.conversation_variables,
            },
        }
    
    def to_yaml(self) -> str:
        """Export as YAML string (Dify's native format)."""
        return yaml.dump(
            self.to_dict(),
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
        )
    
    def to_json(self) -> str:
        """Export as JSON string."""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)
    
    def export(self, path: str, format: str = "auto") -> None:
        """
        Export workflow to file.
        
        Args:
            path: Output file path
            format: 'yaml', 'json', or 'auto' (detect from extension)
        """
        if format == "auto":
            format = "yaml" if path.endswith((".yml", ".yaml")) else "json"
        
        with open(path, "w", encoding="utf-8") as f:
            if format == "yaml":
                content = self.to_yaml()
            else:
                content = self.to_json()
            f.write(content)
        
        print(f"[OK] Exported workflow to {path}")
    
    def auto_layout(self, start_x: int = 100, start_y: int = 300,
                    horizontal_spacing: int = 300,
                    vertical_spacing: int = 200) -> "Workflow":
        """
        Automatically layout nodes in a grid based on connectivity.
        
        Args:
            start_x: Starting X position
            start_y: Starting Y position
            horizontal_spacing: Horizontal distance between nodes
            vertical_spacing: Vertical distance between nodes
            
        Returns:
            Self for chaining
        """
        from .utils import auto_layout_nodes
        auto_layout_nodes(self.nodes, self.edges, start_x, start_y,
                         horizontal_spacing, vertical_spacing)
        return self

    def get_execution_order(self) -> List[str]:
        """
        Determine the execution order of nodes using topological sort.
        
        Returns:
            List of node IDs in execution order
            
        Raises:
            ValueError: If the workflow contains cycles
        """
        from .utils import find_execution_order
        return find_execution_order(self.nodes, self.edges)

    def find_isolated_nodes(self) -> List[Node]:
        """Find nodes that are not connected to any other nodes."""
        from .utils import find_isolated_nodes
        return find_isolated_nodes(self.nodes, self.edges)

    def clone(self, name: Optional[str] = None) -> "Workflow":
        """
        Create a deep copy of this workflow.
        
        Args:
            name: Optional new name for the cloned workflow
            
        Returns:
            New cloned Workflow
        """
        from .utils import clone_node
        
        new_wf = Workflow(
            name=name or f"{self.name} (Copy)",
            mode=self.mode,
            description=self.description,
            icon=self.icon,
            icon_background=self.icon_background,
        )
        
        # Clone all nodes
        node_map = {}
        for node in self.nodes:
            new_node = clone_node(node)
            node_map[node.id] = new_node
            new_wf.add_node(new_node)
        
        # Clone edges
        for edge in self.edges:
            new_edge = {
                "id": edge["id"],
                "source": node_map.get(edge["source"], edge["source"]).id,
                "target": node_map.get(edge["target"], edge["target"]).id,
                "sourceHandle": edge.get("sourceHandle", "source"),
                "targetHandle": edge.get("targetHandle", "target"),
            }
            new_wf.edges.append(new_edge)
        
        return new_wf

    def validate(self) -> List[str]:
        """
        Validate the workflow structure.
        
        Returns a list of warnings/errors found.
        """
        issues = []
        
        # Check for start node
        start_nodes = [n for n in self.nodes if isinstance(n, StartNode)]
        if len(start_nodes) == 0:
            issues.append("Warning: No start node found")
        elif len(start_nodes) > 1:
            issues.append("Error: Multiple start nodes found")
        
        # Check for end node (for workflow mode)
        if self.mode == "workflow":
            end_nodes = [n for n in self.nodes if isinstance(n, EndNode)]
            if len(end_nodes) == 0:
                issues.append("Warning: No end node found (required for workflow mode)")
        
        # Check for disconnected nodes
        connected_ids = set()
        for edge in self.edges:
            connected_ids.add(edge["source"])
            connected_ids.add(edge["target"])
        
        node_map = {n.id: n for n in self.nodes}
        node_titles = {n.title: n.id for n in self.nodes}
        
        for node in self.nodes:
            if node.id not in connected_ids and not isinstance(node, StartNode):
                issues.append(f"Warning: Node '{node.title}' ({node.id}) is not connected")
                
            # Validate variable references in node data
            # Check {{#node_id.var#}} pattern
            import re
            data_str = str(node.to_dict())
            
            # Pattern for template refs: {{#node_id.var#}}
            refs = re.findall(r"\{\{#([a-zA-Z0-9_]+)\.([a-zA-Z0-9_]+)#\}\}", data_str)
            for ref_node_id, ref_var in refs:
                # Handle title references (if user used title instead of ID)
                if ref_node_id not in node_map and ref_node_id not in node_titles:
                     # It might be a conversation variable or system variable
                     if ref_node_id not in ["sys", "env", "conversation"]:
                        # Also allow special IDs like "start" which is commonly used
                        if ref_node_id != "start":
                            issues.append(f"Error: Node '{node.title}' references unknown node '{ref_node_id}'")
            
            # Pattern for value selectors: ['node_id', 'var']
            # This is harder to regex reliably on string repr, but we can try a basic check
            # Real validation would traverse the dict
            
        return issues
    
    def __repr__(self) -> str:
        return (
            f"Workflow(name='{self.name}', mode='{self.mode}', "
            f"nodes={len(self.nodes)}, edges={len(self.edges)})"
        )
