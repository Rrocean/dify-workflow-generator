"""
Fluent Workflow Builder for creating workflows with a chainable API.

Example:
    wf = (WorkflowBuilder("My Workflow")
          .start_with([{"name": "query", "type": "string"}])
          .llm("Process this: {{#start.query#}}")
          .end()
          .build())
"""

from typing import Any, Dict, List, Optional, Union

from .workflow import Workflow
from .nodes import (
    StartNode, EndNode, AnswerNode, LLMNode, HTTPNode,
    CodeNode, IfElseNode, KnowledgeNode
)
from .constants import DEFAULT_MODEL


class WorkflowBuilder:
    """
    Fluent builder for creating workflows with a chainable API.
    
    This provides a more concise way to create simple workflows compared
    to the explicit node-based approach.
    
    Example:
        wf = (WorkflowBuilder("Translator")
              .start_with([
                  {"name": "text", "type": "string"},
                  {"name": "lang", "type": "string"}
              ])
              .llm("Translate to {{#start.lang#}}: {{#start.text#}}")
              .end()
              .build())
    """
    
    def __init__(self, name: str, mode: str = "workflow", description: str = ""):
        """
        Initialize the builder.
        
        Args:
            name: Workflow name
            mode: "workflow" or "advanced-chat"
            description: Workflow description
        """
        self.workflow = Workflow(name=name, mode=mode, description=description)
        self._last_node = None
        self._start_node = None
        self._llm_count = 0
        self._http_count = 0
        self._code_count = 0
        self._condition_count = 0
    
    def start_with(self, variables: List[Dict[str, Any]]) -> "WorkflowBuilder":
        """
        Add the start node with input variables.
        
        Args:
            variables: List of variable definitions
                      [{"name": "query", "type": "string", "required": True}]
        """
        self._start_node = StartNode(
            title="Start",
            variables=variables
        )
        self._start_node.id = "start"
        self.workflow.add_node(self._start_node)
        self._last_node = self._start_node
        return self
    
    def llm(self, prompt: str, 
            model: Optional[Dict[str, Any]] = None,
            title: Optional[str] = None,
            temperature: float = 0.7) -> "WorkflowBuilder":
        """
        Add an LLM node.
        
        Args:
            prompt: The prompt template
            model: Model configuration (uses default if not specified)
            title: Node title (auto-generated if not specified)
            temperature: Sampling temperature
        """
        self._llm_count += 1
        node_title = title or f"llm_{self._llm_count}" if self._llm_count > 1 else "llm"
        
        node = LLMNode(
            title=node_title,
            model=model or DEFAULT_MODEL.copy(),
            prompt=prompt,
            temperature=temperature
        )
        self.workflow.add_node(node)
        self._connect(node)
        self._last_node = node
        return self
    
    def http(self, url: str, 
             method: str = "GET",
             title: Optional[str] = None,
             headers: str = "",
             body: Optional[Dict[str, Any]] = None) -> "WorkflowBuilder":
        """
        Add an HTTP request node.
        
        Args:
            url: Target URL
            method: HTTP method (GET, POST, PUT, DELETE, PATCH)
            title: Node title
            headers: Request headers as string
            body: Request body configuration
        """
        self._http_count += 1
        node_title = title or f"http_{self._http_count}" if self._http_count > 1 else "http"
        
        node = HTTPNode(
            title=node_title,
            url=url,
            method=method,
            headers=headers,
            body=body
        )
        self.workflow.add_node(node)
        self._connect(node)
        self._last_node = node
        return self
    
    def code(self, code: str,
             language: str = "python3",
             title: Optional[str] = None,
             variables: Optional[List[Dict]] = None,
             outputs: Optional[List[Dict]] = None) -> "WorkflowBuilder":
        """
        Add a code execution node.
        
        Args:
            code: The code to execute
            language: "python3" or "javascript"
            title: Node title
            variables: Input variables
            outputs: Output variable definitions
        """
        self._code_count += 1
        node_title = title or f"code_{self._code_count}" if self._code_count > 1 else "code"
        
        node = CodeNode(
            title=node_title,
            code=code,
            language=language,
            variables=variables or [],
            outputs=outputs or [{"variable": "result", "type": "string"}]
        )
        self.workflow.add_node(node)
        self._connect(node)
        self._last_node = node
        return self
    
    def condition(self, 
                  variable: str,
                  operator: str = "is-not-empty",
                  value: str = "",
                  title: Optional[str] = None) -> "WorkflowBuilder":
        """
        Add a conditional (if/else) node.
        
        Args:
            variable: Variable to check (format: "node.variable" or just "variable")
            operator: Comparison operator
            value: Value to compare against
            title: Node title
        """
        self._condition_count += 1
        node_title = title or f"condition_{self._condition_count}" if self._condition_count > 1 else "condition"
        
        # Parse variable selector
        if "." in variable:
            parts = variable.split(".", 1)
            var_selector = parts
        else:
            var_selector = ["start", variable]
        
        node = IfElseNode(
            title=node_title,
            conditions=[{
                "variable_selector": var_selector,
                "comparison_operator": operator,
                "value": value
            }]
        )
        self.workflow.add_node(node)
        self._connect(node)
        self._last_node = node
        return self
    
    def knowledge(self, 
                  dataset_ids: List[str],
                  query_variable: str = "start.query",
                  title: Optional[str] = None) -> "WorkflowBuilder":
        """
        Add a knowledge retrieval node.
        
        Args:
            dataset_ids: List of knowledge base IDs
            query_variable: Variable containing the query
            title: Node title
        """
        node_title = title or "knowledge"
        
        # Parse variable selector
        if "." in query_variable:
            parts = query_variable.split(".", 1)
            var_selector = parts
        else:
            var_selector = ["start", query_variable]
        
        node = KnowledgeNode(
            title=node_title,
            dataset_ids=dataset_ids,
            query_variable_selector=var_selector
        )
        self.workflow.add_node(node)
        self._connect(node)
        self._last_node = node
        return self
    
    def branch_true(self) -> "WorkflowBuilder":
        """
        Mark that the next node should connect to the 'true' branch of the last condition.
        
        Must be called immediately after a condition() call.
        """
        if not isinstance(self._last_node, IfElseNode):
            raise ValueError("branch_true() must follow a condition()")
        self._pending_branch = "true"
        return self
    
    def branch_false(self) -> "WorkflowBuilder":
        """
        Mark that the next node should connect to the 'false' branch of the last condition.
        
        Must be called immediately after a condition() call.
        """
        if not isinstance(self._last_node, IfElseNode):
            raise ValueError("branch_false() must follow a condition()")
        self._pending_branch = "false"
        return self
    
    def end(self, outputs: Optional[List[Dict[str, Any]]] = None) -> "WorkflowBuilder":
        """
        Add the end node.
        
        Args:
            outputs: Output variable definitions
                    [{"variable": "result", "value_selector": ["llm", "text"]}]
        """
        if self.workflow.mode == "advanced-chat":
            node = AnswerNode(
                title="Answer",
                answer="{{#llm.text#}}"
            )
        else:
            # Auto-generate outputs if not provided
            if outputs is None and self._last_node:
                last_title = self._last_node.title
                outputs = [{"variable": "result", "value_selector": [last_title, "text"]}]
            
            node = EndNode(
                title="End",
                outputs=outputs or []
            )
        
        self.workflow.add_node(node)
        self._connect(node)
        self._last_node = node
        return self
    
    def _connect(self, target) -> None:
        """Connect the last node to the target node."""
        if self._last_node is None:
            return
        
        source_handle = getattr(self, '_pending_branch', "source")
        self.workflow.connect(self._last_node, target, source_handle=source_handle)
        self._pending_branch = "source"
    
    def build(self) -> Workflow:
        """
        Build and return the workflow.
        
        This also applies auto-layout to position nodes nicely.
        """
        self.workflow.auto_layout()
        return self.workflow
    
    def validate(self) -> List[str]:
        """Validate the current workflow."""
        return self.workflow.validate()


def quick_workflow(name: str, prompt: str, inputs: List[str] = None) -> Workflow:
    """
    Create a simple one-step LLM workflow quickly.
    
    Args:
        name: Workflow name
        prompt: The LLM prompt
        inputs: List of input variable names (defaults to ["query"])
        
    Returns:
        Built Workflow
        
    Example:
        wf = quick_workflow(
            "Summarizer",
            "Summarize this: {{#start.text#}}",
            inputs=["text"]
        )
    """
    inputs = inputs or ["query"]
    variables = [{"name": name, "type": "string", "required": True} 
                 for name in inputs]
    
    return (WorkflowBuilder(name)
            .start_with(variables)
            .llm(prompt)
            .end()
            .build())


def chatbot(name: str = "Chatbot", 
            system_prompt: str = "You are a helpful assistant.",
            with_memory: bool = True) -> Workflow:
    """
    Create a simple chatbot workflow.
    
    Args:
        name: Workflow name
        system_prompt: System prompt for the LLM
        with_memory: Whether to enable conversation memory
        
    Returns:
        Built Workflow
    """
    memory = {"window": {"enabled": True, "size": 20}} if with_memory else None
    
    wf = Workflow(name=name, mode="advanced-chat")
    
    start = StartNode(
        title="Start",
        variables=[{"name": "query", "type": "string", "required": True}]
    )
    start.id = "start"
    
    llm = LLMNode(
        title="assistant",
        prompt=f"{system_prompt}\n\nUser: {{#start.query#}}",
        memory=memory
    )
    
    answer = AnswerNode(
        title="Answer",
        answer="{{#assistant.text#}}"
    )
    
    wf.add_nodes([start, llm, answer])
    wf.connect(start, llm)
    wf.connect(llm, answer)
    wf.auto_layout()
    
    return wf
