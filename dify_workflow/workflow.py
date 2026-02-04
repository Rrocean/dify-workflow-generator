"""
Workflow class for building and exporting Dify workflows
"""

import json
import yaml
from typing import Any, Dict, List, Optional, Tuple, Union
from .nodes import Node, StartNode, EndNode


class Workflow:
    """
    Build Dify workflows programmatically.
    
    Example:
        wf = Workflow("My Workflow")
        wf.add_node(LLMNode("chat", prompt="Hello"))
        wf.export("workflow.yml")
    """
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.nodes: List[Node] = []
        self.edges: List[Tuple[str, str]] = []
        self._node_counter = 0
    
    def add_node(self, node: Node) -> "Workflow":
        """Add a node to the workflow"""
        # Auto-position nodes
        node.position = {
            "x": 200 + (self._node_counter % 3) * 300,
            "y": 100 + (self._node_counter // 3) * 200,
        }
        self._node_counter += 1
        self.nodes.append(node)
        return self
    
    def add_nodes(self, nodes: List[Node]) -> "Workflow":
        """Add multiple nodes"""
        for node in nodes:
            self.add_node(node)
        return self
    
    def connect(
        self, 
        source: Union[Node, str], 
        target: Union[Node, str],
        source_handle: str = "output",
        target_handle: str = "input",
    ) -> "Workflow":
        """Connect two nodes"""
        source_id = source.id if isinstance(source, Node) else source
        target_id = target.id if isinstance(target, Node) else target
        self.edges.append((source_id, target_id, source_handle, target_handle))
        return self
    
    def get_node(self, node_id: str) -> Optional[Node]:
        """Get node by ID"""
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert workflow to Dify-compatible dict"""
        return {
            "app": {
                "name": self.name,
                "description": self.description,
                "mode": "workflow",
            },
            "workflow": {
                "graph": {
                    "nodes": [n.to_dict() for n in self.nodes],
                    "edges": [
                        {
                            "id": f"e{i}",
                            "source": src,
                            "target": tgt,
                            "sourceHandle": sh,
                            "targetHandle": th,
                        }
                        for i, (src, tgt, sh, th) in enumerate(self.edges)
                    ],
                }
            },
        }
    
    def export(self, path: str, format: str = "auto") -> None:
        """
        Export workflow to file.
        
        Args:
            path: Output file path
            format: 'yaml', 'json', or 'auto' (detect from extension)
        """
        data = self.to_dict()
        
        if format == "auto":
            format = "yaml" if path.endswith((".yml", ".yaml")) else "json"
        
        with open(path, "w", encoding="utf-8") as f:
            if format == "yaml":
                yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
            else:
                json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Exported workflow to {path}")
    
    def to_yaml(self) -> str:
        """Export as YAML string"""
        return yaml.dump(self.to_dict(), allow_unicode=True, default_flow_style=False)
    
    def to_json(self) -> str:
        """Export as JSON string"""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)
    
    def __repr__(self) -> str:
        return f"Workflow(name='{self.name}', nodes={len(self.nodes)}, edges={len(self.edges)})"
