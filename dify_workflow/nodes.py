"""
Node definitions for Dify workflows.

Each node class represents a Dify workflow node type and generates
the correct data structure for the DSL format.
"""

import uuid
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field


def _generate_id() -> str:
    """Generate a short unique ID like Dify uses"""
    return uuid.uuid4().hex[:8]


@dataclass
class Node:
    """Base class for all workflow nodes"""
    
    id: str = field(default_factory=_generate_id)
    title: str = ""
    desc: str = ""
    width: int = 244
    height: int = 54
    position_x: float = 0
    position_y: float = 0
    _node_type: str = "base"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert node to Dify DSL format"""
        return {
            "id": self.id,
            "position": {
                "x": self.position_x,
                "y": self.position_y,
            },
            "width": self.width,
            "height": self.height,
            "data": {
                "type": self._node_type,
                "title": self.title or self._node_type.replace("-", " ").title(),
                "desc": self.desc,
                **self._get_data(),
            },
        }
    
    def _get_data(self) -> Dict[str, Any]:
        """Override in subclasses to provide node-specific data"""
        return {}


@dataclass
class StartNode(Node):
    """
    Workflow entry point.
    
    Args:
        variables: List of input variable definitions
            [{"name": "query", "type": "string", "required": True, "default": ""}]
    """
    
    _node_type: str = "start"
    variables: List[Dict[str, Any]] = field(default_factory=list)
    
    def _get_data(self) -> Dict[str, Any]:
        return {
            "variables": [
                {
                    "variable": v.get("name", v.get("variable", "")),
                    "type": v.get("type", "string"),
                    "label": v.get("label", v.get("name", v.get("variable", ""))),
                    "required": v.get("required", False),
                    "max_length": v.get("max_length", 256),
                    "default": v.get("default", ""),
                    "options": v.get("options", []),
                }
                for v in self.variables
            ]
        }


@dataclass
class EndNode(Node):
    """
    Workflow output node.
    
    Args:
        outputs: List of output definitions
            [{"variable": "result", "value_selector": ["llm", "text"]}]
    """
    
    _node_type: str = "end"
    outputs: List[Dict[str, Any]] = field(default_factory=list)
    
    def _get_data(self) -> Dict[str, Any]:
        return {
            "outputs": [
                {
                    "variable": o.get("variable", "output"),
                    "value_selector": o.get("value_selector", []),
                }
                for o in self.outputs
            ]
        }


@dataclass
class AnswerNode(Node):
    """
    Streaming answer node for chat apps.
    
    Args:
        answer: The answer template with variable references like {{#node.var#}}
    """
    
    _node_type: str = "answer"
    answer: str = ""
    
    def _get_data(self) -> Dict[str, Any]:
        return {
            "answer": self.answer,
        }


@dataclass
class LLMNode(Node):
    """
    Large Language Model node.
    
    Args:
        model: Model configuration {"provider": "openai", "name": "gpt-4", "mode": "chat"}
        prompt: The prompt template
        temperature: Sampling temperature (0-2)
        max_tokens: Maximum tokens to generate
        context: Optional context configuration
        memory: Optional memory configuration for chat
        vision: Vision settings for multimodal models
    """
    
    _node_type: str = "llm"
    model: Dict[str, Any] = field(default_factory=lambda: {
        "provider": "openai",
        "name": "gpt-4",
        "mode": "chat",
        "completion_params": {
            "temperature": 0.7,
        }
    })
    prompt: str = ""
    temperature: float = 0.7
    max_tokens: int = 4096
    context: Optional[Dict[str, Any]] = None
    memory: Optional[Dict[str, Any]] = None
    vision: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        # Set title if not provided
        if not self.title:
            self.title = "LLM"
        # Ensure model has completion_params with temperature
        if "completion_params" not in self.model:
            self.model["completion_params"] = {}
        self.model["completion_params"]["temperature"] = self.temperature
        self.model["completion_params"]["max_tokens"] = self.max_tokens
    
    def _get_data(self) -> Dict[str, Any]:
        data = {
            "model": self.model,
            "prompt_template": [
                {
                    "role": "user",
                    "text": self.prompt,
                }
            ],
        }
        
        if self.context:
            data["context"] = self.context
        if self.memory:
            data["memory"] = self.memory
        if self.vision:
            data["vision"] = self.vision
            
        return data


@dataclass
class HTTPNode(Node):
    """
    HTTP Request node for API calls.
    
    Args:
        url: Target URL (can include variables like {{#node.var#}})
        method: HTTP method (GET, POST, PUT, DELETE, PATCH, HEAD)
        headers: Request headers
        params: Query parameters
        body: Request body configuration
        timeout: Request timeout in seconds
        authorization: Auth configuration
    """
    
    _node_type: str = "http-request"
    url: str = ""
    method: str = "GET"
    headers: str = ""
    params: str = ""
    body: Optional[Dict[str, Any]] = None
    timeout: int = 60
    authorization: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if not self.title:
            self.title = "HTTP Request"
    
    def _get_data(self) -> Dict[str, Any]:
        data = {
            "url": self.url,
            "method": self.method,
            "headers": self.headers,
            "params": self.params,
            "body": self.body or {"type": "none"},
            "timeout": {
                "connect": self.timeout,
                "read": self.timeout,
                "write": self.timeout,
            },
        }
        
        if self.authorization:
            data["authorization"] = self.authorization
        else:
            data["authorization"] = {"type": "no-auth"}
            
        return data


@dataclass
class CodeNode(Node):
    """
    Code execution node.
    
    Args:
        code: The code to execute
        language: Programming language (python3, javascript)
        variables: Input variables [{"variable": "input", "value_selector": [...]}]
        outputs: Output variable definitions [{"variable": "output", "type": "string"}]
    """
    
    _node_type: str = "code"
    code: str = ""
    language: str = "python3"
    variables: List[Dict[str, Any]] = field(default_factory=list)
    outputs: List[Dict[str, Any]] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.title:
            self.title = "Code"
        if not self.code:
            if self.language == "python3":
                self.code = """def main(args):
    return {
        "result": args.get("input", "")
    }
"""
            else:
                self.code = """function main(args) {
    return {
        result: args.input || ""
    };
}
"""
    
    def _get_data(self) -> Dict[str, Any]:
        return {
            "code_language": self.language,
            "code": self.code,
            "variables": self.variables,
            "outputs": [
                {
                    "variable": o.get("variable", "result"),
                    "type": o.get("type", "string"),
                }
                for o in self.outputs
            ] if self.outputs else [{"variable": "result", "type": "string"}],
        }


@dataclass
class IfElseNode(Node):
    """
    Conditional branching node.
    
    Args:
        conditions: List of condition groups
            [{"variable_selector": ["node", "var"], "comparison_operator": "eq", "value": "test"}]
        logical_operator: "and" or "or" for combining conditions
    """
    
    _node_type: str = "if-else"
    conditions: List[Dict[str, Any]] = field(default_factory=list)
    logical_operator: str = "and"
    
    def __post_init__(self):
        if not self.title:
            self.title = "IF/ELSE"
    
    def _get_data(self) -> Dict[str, Any]:
        return {
            "conditions": [
                {
                    "id": _generate_id(),
                    "logical_operator": self.logical_operator,
                    "conditions": [
                        {
                            "id": _generate_id(),
                            "varType": "string",
                            "variable_selector": c.get("variable_selector", []),
                            "comparison_operator": c.get("comparison_operator", "contains"),
                            "value": c.get("value", ""),
                        }
                        for c in self.conditions
                    ],
                }
            ],
        }


@dataclass
class VariableAggregatorNode(Node):
    """
    Variable aggregator node to combine multiple variables.
    
    Args:
        variables: List of variable selectors to aggregate
            [["node1", "var1"], ["node2", "var2"]]
        output_type: Output type (string, array-string, array-object)
    """
    
    _node_type: str = "variable-aggregator"
    variables: List[List[str]] = field(default_factory=list)
    output_type: str = "string"
    
    def __post_init__(self):
        if not self.title:
            self.title = "Variable Aggregator"
    
    def _get_data(self) -> Dict[str, Any]:
        return {
            "variables": self.variables,
            "output_type": self.output_type,
        }


@dataclass
class TemplateNode(Node):
    """
    Jinja2 template transformation node.
    
    Args:
        template: Jinja2 template string
        variables: Input variables [{"variable": "name", "value_selector": [...]}]
    """
    
    _node_type: str = "template-transform"
    template: str = ""
    variables: List[Dict[str, Any]] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.title:
            self.title = "Template"
    
    def _get_data(self) -> Dict[str, Any]:
        return {
            "template": self.template,
            "variables": self.variables,
        }


@dataclass
class IterationNode(Node):
    """
    Iteration node for looping over arrays.
    
    Args:
        iterator_selector: Variable selector for the array to iterate
        output_selector: Variable selector for iteration output
        output_type: Type of each output item
    """
    
    _node_type: str = "iteration"
    iterator_selector: List[str] = field(default_factory=list)
    output_selector: List[str] = field(default_factory=list)
    output_type: str = "string"
    
    def __post_init__(self):
        if not self.title:
            self.title = "Iteration"
    
    def _get_data(self) -> Dict[str, Any]:
        return {
            "iterator_selector": self.iterator_selector,
            "output_selector": self.output_selector,
            "output_type": self.output_type,
            "is_parallel": False,
            "parallel_nums": 10,
        }


@dataclass
class KnowledgeNode(Node):
    """
    Knowledge retrieval node.
    
    Args:
        dataset_ids: List of knowledge base IDs to query
        query_variable_selector: Variable selector for the query
        retrieval_mode: "single" or "multiple"
        top_k: Number of results to retrieve
        score_threshold: Minimum similarity score
    """
    
    _node_type: str = "knowledge-retrieval"
    dataset_ids: List[str] = field(default_factory=list)
    query_variable_selector: List[str] = field(default_factory=list)
    retrieval_mode: str = "multiple"
    top_k: int = 4
    score_threshold: float = 0.5
    
    def __post_init__(self):
        if not self.title:
            self.title = "Knowledge Retrieval"
    
    def _get_data(self) -> Dict[str, Any]:
        return {
            "dataset_ids": self.dataset_ids,
            "query_variable_selector": self.query_variable_selector,
            "retrieval_mode": self.retrieval_mode,
            "multiple_retrieval_config": {
                "top_k": self.top_k,
                "score_threshold": self.score_threshold,
                "reranking_enable": False,
            },
        }


@dataclass
class QuestionClassifierNode(Node):
    """
    Question classifier node for intent routing.
    
    Args:
        model: Model configuration
        query_variable_selector: Variable selector for the query
        classes: Classification categories
            [{"id": "1", "name": "Technical", "description": "Technical questions"}]
    """
    
    _node_type: str = "question-classifier"
    model: Dict[str, Any] = field(default_factory=lambda: {
        "provider": "openai",
        "name": "gpt-4",
        "mode": "chat",
    })
    query_variable_selector: List[str] = field(default_factory=list)
    classes: List[Dict[str, Any]] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.title:
            self.title = "Question Classifier"
    
    def _get_data(self) -> Dict[str, Any]:
        return {
            "model": self.model,
            "query_variable_selector": self.query_variable_selector,
            "classes": [
                {
                    "id": c.get("id", _generate_id()),
                    "name": c.get("name", "Category"),
                }
                for c in self.classes
            ],
            "instruction": "",
        }


@dataclass
class ParameterExtractorNode(Node):
    """
    Parameter extractor node for structured data extraction.
    
    Args:
        model: Model configuration
        query_variable_selector: Variable selector for the input
        parameters: Parameters to extract
            [{"name": "email", "type": "string", "description": "User email", "required": True}]
    """
    
    _node_type: str = "parameter-extractor"
    model: Dict[str, Any] = field(default_factory=lambda: {
        "provider": "openai",
        "name": "gpt-4",
        "mode": "chat",
    })
    query_variable_selector: List[str] = field(default_factory=list)
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    instruction: str = ""
    
    def __post_init__(self):
        if not self.title:
            self.title = "Parameter Extractor"
    
    def _get_data(self) -> Dict[str, Any]:
        return {
            "model": self.model,
            "query": self.query_variable_selector,
            "parameters": [
                {
                    "name": p.get("name", "param"),
                    "type": p.get("type", "string"),
                    "description": p.get("description", ""),
                    "required": p.get("required", False),
                }
                for p in self.parameters
            ],
            "instruction": self.instruction,
            "reasoning_mode": "prompt",
        }


@dataclass
class ToolNode(Node):
    """
    Tool node for calling external tools/plugins.
    
    Args:
        provider_id: Tool provider ID
        provider_type: Provider type (builtin, api, workflow)
        provider_name: Provider display name
        tool_name: Specific tool name
        tool_parameters: Tool input parameters
    """
    
    _node_type: str = "tool"
    provider_id: str = ""
    provider_type: str = "builtin"
    provider_name: str = ""
    tool_name: str = ""
    tool_parameters: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.title:
            self.title = self.tool_name or "Tool"
    
    def _get_data(self) -> Dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "provider_type": self.provider_type,
            "provider_name": self.provider_name,
            "tool_name": self.tool_name,
            "tool_parameters": self.tool_parameters,
        }
