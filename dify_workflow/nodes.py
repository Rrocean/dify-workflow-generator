"""
Node definitions for Dify workflows
"""

import uuid
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class Node:
    """Base class for all workflow nodes"""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    type: str = "base"
    title: str = ""
    position: Dict[str, int] = field(default_factory=lambda: {"x": 0, "y": 0})
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "title": self.title or self.id,
            "position": self.position,
            "data": self._get_data(),
        }
    
    def _get_data(self) -> Dict[str, Any]:
        return {}


@dataclass
class StartNode(Node):
    """Workflow entry point"""
    
    type: str = "start"
    inputs: List[str] = field(default_factory=list)
    
    def _get_data(self) -> Dict[str, Any]:
        return {
            "variables": [
                {"name": inp, "type": "string"} for inp in self.inputs
            ]
        }


@dataclass
class EndNode(Node):
    """Workflow output"""
    
    type: str = "end"
    outputs: List[str] = field(default_factory=list)
    
    def _get_data(self) -> Dict[str, Any]:
        return {
            "outputs": [
                {"name": out, "type": "string"} for out in self.outputs
            ]
        }


@dataclass
class LLMNode(Node):
    """Large Language Model call"""
    
    type: str = "llm"
    model: str = "gpt-4"
    prompt: str = ""
    temperature: float = 0.7
    max_tokens: int = 2048
    
    def __init__(self, title: str = "", **kwargs):
        super().__init__()
        self.title = title
        for k, v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
    
    def _get_data(self) -> Dict[str, Any]:
        return {
            "model": {
                "provider": "openai",
                "name": self.model,
            },
            "prompt_template": self.prompt,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }


@dataclass
class HTTPNode(Node):
    """HTTP Request node"""
    
    type: str = "http-request"
    url: str = ""
    method: str = "GET"
    headers: Dict[str, str] = field(default_factory=dict)
    body: Optional[str] = None
    
    def __init__(self, title: str = "", **kwargs):
        super().__init__()
        self.title = title
        for k, v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
    
    def _get_data(self) -> Dict[str, Any]:
        return {
            "url": self.url,
            "method": self.method,
            "headers": self.headers,
            "body": self.body or "",
        }


@dataclass
class CodeNode(Node):
    """Code execution node"""
    
    type: str = "code"
    language: str = "python3"
    code: str = ""
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    
    def __init__(self, title: str = "", **kwargs):
        super().__init__()
        self.title = title
        for k, v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
    
    def _get_data(self) -> Dict[str, Any]:
        return {
            "language": self.language,
            "code": self.code,
            "variables": [{"name": i, "type": "string"} for i in self.inputs],
            "outputs": [{"name": o, "type": "string"} for o in self.outputs],
        }


@dataclass
class ConditionNode(Node):
    """Conditional branching"""
    
    type: str = "if-else"
    conditions: List[Dict[str, Any]] = field(default_factory=list)
    
    def __init__(self, title: str = "", **kwargs):
        super().__init__()
        self.title = title
        for k, v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
    
    def add_condition(self, variable: str, operator: str, value: Any):
        """Add a condition: variable operator value"""
        self.conditions.append({
            "variable": variable,
            "operator": operator,
            "value": value,
        })
        return self
    
    def _get_data(self) -> Dict[str, Any]:
        return {"conditions": self.conditions}


@dataclass
class VariableNode(Node):
    """Variable aggregation"""
    
    type: str = "variable-aggregator"
    variables: Dict[str, str] = field(default_factory=dict)
    
    def __init__(self, title: str = "", **kwargs):
        super().__init__()
        self.title = title
        for k, v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
    
    def _get_data(self) -> Dict[str, Any]:
        return {"variables": self.variables}
