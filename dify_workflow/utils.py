"""
Utility functions for Dify Workflow Generator.
"""

import re
from typing import Any, Dict, List, Optional, Tuple, Type, Union

from .nodes import Node


def generate_slug(text: str) -> str:
    """
    Convert text to a URL-friendly slug.
    
    Args:
        text: Input text
        
    Returns:
        URL-friendly slug
        
    Example:
        >>> generate_slug("Hello World!")
        'hello-world'
    """
    # Convert to lowercase
    text = text.lower()
    # Replace non-alphanumeric characters with hyphens
    text = re.sub(r'[^a-z0-9]+', '-', text)
    # Remove leading/trailing hyphens
    text = text.strip('-')
    # Collapse multiple hyphens
    text = re.sub(r'-+', '-', text)
    return text


def validate_variable_name(name: str) -> Tuple[bool, str]:
    """
    Validate a variable name for Dify compatibility.
    
    Args:
        name: Variable name to validate
        
    Returns:
        (is_valid, error_message)
    """
    if not name:
        return False, "Variable name cannot be empty"
    
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name):
        return False, "Variable name must start with letter/underscore and contain only letters, numbers, underscores"
    
    # Reserved keywords
    reserved = {'sys', 'env', 'conversation', 'start', 'end'}
    if name in reserved:
        return False, f"'{name}' is a reserved keyword"
    
    return True, ""


def sanitize_for_prompt(text: str) -> str:
    """
    Sanitize text for use in prompts.
    
    Args:
        text: Input text
        
    Returns:
        Sanitized text
    """
    # Escape Dify template syntax if needed
    # Replace {# with escaped version to prevent parsing issues
    return text.replace('{#', '{ #').replace('#}', '# }')


def extract_variable_references(text: str) -> List[Tuple[str, str]]:
    """
    Extract variable references from a template string.
    
    Args:
        text: Template text containing {{#node.variable#}}
        
    Returns:
        List of (node_id, variable_name) tuples
        
    Example:
        >>> extract_variable_references("{{#start.query#}} to {{#llm.result#}}")
        [('start', 'query'), ('llm', 'result')]
    """
    pattern = r'\{\{#([a-zA-Z0-9_]+)\.([a-zA-Z0-9_]+)#\}\}'
    return re.findall(pattern, text)


def auto_layout_nodes(nodes: List[Node], edges: List[Dict[str, Any]], 
                      start_x: int = 100, start_y: int = 300,
                      horizontal_spacing: int = 300,
                      vertical_spacing: int = 200) -> None:
    """
    Automatically layout nodes in a grid based on connectivity.
    
    Uses a simple BFS-based positioning algorithm.
    
    Args:
        nodes: List of nodes to position
        edges: List of edges defining connectivity
        start_x: Starting X position
        start_y: Starting Y position
        horizontal_spacing: Horizontal distance between nodes
        vertical_spacing: Vertical distance between nodes
    """
    if not nodes:
        return
    
    # Build adjacency list
    adjacency: Dict[str, List[str]] = {}
    reverse_adj: Dict[str, List[str]] = {}
    
    for node in nodes:
        adjacency[node.id] = []
        reverse_adj[node.id] = []
    
    for edge in edges:
        src = edge.get("source")
        tgt = edge.get("target")
        if src in adjacency and tgt in adjacency:
            adjacency[src].append(tgt)
            reverse_adj[tgt].append(src)
    
    # Find start nodes (no incoming edges)
    start_nodes = [n for n in nodes if not reverse_adj[n.id]]
    if not start_nodes:
        start_nodes = [nodes[0]]
    
    # BFS to assign levels
    node_map = {n.id: n for n in nodes}
    levels: Dict[str, int] = {}
    
    queue = [(n.id, 0) for n in start_nodes]
    visited = set()
    
    while queue:
        node_id, level = queue.pop(0)
        if node_id in visited:
            continue
        visited.add(node_id)
        
        # Assign level (max of incoming levels + 1)
        if reverse_adj[node_id]:
            level = max(levels.get(p, 0) + 1 for p in reverse_adj[node_id])
        levels[node_id] = level
        
        for next_id in adjacency[node_id]:
            if next_id not in visited:
                queue.append((next_id, level + 1))
    
    # Group nodes by level
    level_groups: Dict[int, List[str]] = {}
    for node_id, level in levels.items():
        level_groups.setdefault(level, []).append(node_id)
    
    # Position nodes
    for level, node_ids in level_groups.items():
        x = start_x + level * horizontal_spacing
        # Center vertically
        total_height = len(node_ids) * vertical_spacing
        start_y_level = start_y - total_height // 2
        
        for i, node_id in enumerate(node_ids):
            node = node_map[node_id]
            node.position_x = x
            node.position_y = start_y_level + i * vertical_spacing


def clone_node(node: Node, new_title: Optional[str] = None) -> Node:
    """
    Create a deep copy of a node with a new ID.
    
    Args:
        node: Node to clone
        new_title: Optional new title for the cloned node
        
    Returns:
        New cloned node
    """
    import copy
    import uuid
    
    # Deep copy the node
    new_node = copy.copy(node)
    new_node.id = uuid.uuid4().hex[:8]
    
    if new_title:
        new_node.title = new_title
    
    return new_node


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable string.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    else:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"


def estimate_tokens(text: str, model: str = "gpt-4") -> int:
    """
    Roughly estimate token count for a text.
    
    This is a simple estimation (1 token ≈ 4 characters for English,
    1 token ≈ 1-2 characters for Chinese).
    
    Args:
        text: Input text
        model: Model name (affects tokenization)
        
    Returns:
        Estimated token count
    """
    if not text:
        return 0
    
    # Count Chinese characters (roughly 1 token each)
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    # Count other characters (roughly 4 chars per token)
    other_chars = len(text) - chinese_chars
    
    return chinese_chars + (other_chars // 4) + 1


def truncate_to_tokens(text: str, max_tokens: int, model: str = "gpt-4") -> str:
    """
    Truncate text to fit within token limit.
    
    Args:
        text: Input text
        max_tokens: Maximum tokens allowed
        model: Model name
        
    Returns:
        Truncated text
    """
    if estimate_tokens(text, model) <= max_tokens:
        return text
    
    # Binary search for truncation point
    low, high = 0, len(text)
    while low < high:
        mid = (low + high + 1) // 2
        if estimate_tokens(text[:mid], model) <= max_tokens:
            low = mid
        else:
            high = mid - 1
    
    return text[:low] + "..."


def merge_workflows(workflows: List[Any], name: str = "Merged Workflow") -> Any:
    """
    Merge multiple workflows into one.
    
    Note: This creates independent copies of all nodes.
    Connections between workflows are not created automatically.
    
    Args:
        workflows: List of Workflow objects to merge
        name: Name for the merged workflow
        
    Returns:
        New merged Workflow
    """
    from .workflow import Workflow
    
    if not workflows:
        return Workflow(name=name)
    
    # Use mode of first workflow
    merged = Workflow(name=name, mode=workflows[0].mode)
    
    # Track ID mappings to avoid conflicts
    id_mapping: Dict[str, str] = {}
    
    for wf in workflows:
        # Clone all nodes with new IDs
        node_map = {}
        for node in wf.nodes:
            new_node = clone_node(node)
            node_map[node.id] = new_node
            id_mapping[node.id] = new_node.id
            merged.add_node(new_node)
        
        # Add edges with updated IDs
        for edge in wf.edges:
            old_src = edge["source"]
            old_tgt = edge["target"]
            
            if old_src in id_mapping and old_tgt in id_mapping:
                new_edge = {
                    "id": edge["id"],
                    "source": id_mapping[old_src],
                    "target": id_mapping[old_tgt],
                    "sourceHandle": edge.get("sourceHandle", "source"),
                    "targetHandle": edge.get("targetHandle", "target"),
                }
                merged.edges.append(new_edge)
    
    return merged


def find_isolated_nodes(nodes: List[Node], edges: List[Dict[str, Any]]) -> List[Node]:
    """
    Find nodes that are not connected to any other nodes.
    
    Args:
        nodes: List of nodes
        edges: List of edges
        
    Returns:
        List of isolated nodes
    """
    connected = set()
    for edge in edges:
        connected.add(edge["source"])
        connected.add(edge["target"])
    
    return [n for n in nodes if n.id not in connected]


def find_execution_order(nodes: List[Node], edges: List[Dict[str, Any]]) -> List[str]:
    """
    Determine the execution order of nodes using topological sort.
    
    Args:
        nodes: List of nodes
        edges: List of edges
        
    Returns:
        List of node IDs in execution order
        
    Raises:
        ValueError: If the workflow contains cycles
    """
    from collections import defaultdict, deque
    
    # Build adjacency and in-degree
    adjacency = defaultdict(list)
    in_degree = defaultdict(int)
    
    for node in nodes:
        in_degree[node.id] = 0
    
    for edge in edges:
        src = edge["source"]
        tgt = edge["target"]
        adjacency[src].append(tgt)
        in_degree[tgt] += 1
    
    # Kahn's algorithm
    queue = deque([n for n in in_degree if in_degree[n] == 0])
    order = []
    
    while queue:
        node_id = queue.popleft()
        order.append(node_id)
        
        for next_id in adjacency[node_id]:
            in_degree[next_id] -= 1
            if in_degree[next_id] == 0:
                queue.append(next_id)
    
    if len(order) != len(nodes):
        raise ValueError("Workflow contains cycles")
    
    return order
