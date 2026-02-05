"""
Workflow class for building and exporting Dify-compatible DSL files.

This generates YAML files that can be directly imported into Dify.
"""

import json
from typing import Any, Dict, List, Optional, Tuple, Union
import yaml

from .nodes import Node, StartNode, EndNode

# Current DSL version supported by Dify
DSL_VERSION = "0.5.0"


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
            raise ValueError(f"Invalid mode: {mode}. Must be 'workflow' or 'advanced-chat'")
        
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
        """
        source_id = source.id if isinstance(source, Node) else source
        target_id = target.id if isinstance(target, Node) else target
        
        edge = {
            "id": f"edge_{self._edge_counter}",
            "source": source_id,
            "target": target_id,
            "sourceHandle": source_handle,
            "targetHandle": target_handle,
        }
        
        self._edge_counter += 1
        self.edges.append(edge)
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
                     # It might be a conversation variable
                     if ref_node_id not in ["sys", "env", "conversation"]:
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
