"""
Dify Workflow Generator - Programmatically create Dify-compatible workflow DSL files

This library generates YAML files that can be directly imported into Dify.
DSL Version: 0.5.0

Features:
- Full node support (14 types)
- Interactive guided builder
- AI-powered natural language workflow generation
- CLI tool for automation
"""

from .workflow import Workflow
from .nodes import (
    Node,
    StartNode,
    EndNode,
    AnswerNode,
    LLMNode,
    HTTPNode,
    CodeNode,
    IfElseNode,
    VariableAggregatorNode,
    TemplateNode,
    IterationNode,
    KnowledgeNode,
    QuestionClassifierNode,
    ParameterExtractorNode,
    ToolNode,
)

__version__ = "0.3.0"
__dsl_version__ = "0.5.0"

__all__ = [
    # Core
    "Workflow",
    # Nodes
    "Node",
    "StartNode",
    "EndNode",
    "AnswerNode",
    "LLMNode",
    "HTTPNode",
    "CodeNode",
    "IfElseNode",
    "VariableAggregatorNode",
    "TemplateNode",
    "IterationNode",
    "KnowledgeNode",
    "QuestionClassifierNode",
    "ParameterExtractorNode",
    "ToolNode",
    "AssignerNode",
    "DocumentExtractorNode",
    "ListFilterNode",
    # Functions
    "interactive",
    "from_description",
    "visualize",
]


def interactive(lang: str = "en"):
    """
    Start interactive workflow builder session.
    
    Args:
        lang: Language code ("en" for English, "zh" for Chinese)
    
    Returns:
        Generated Workflow object
    """
    from .interactive import interactive_session
    return interactive_session(lang=lang)


def from_description(description: str, **kwargs):
    """
    Create workflow from natural language description.
    
    Requires: pip install dify-workflow-generator[interactive]
    
    Args:
        description: Natural language description of the workflow
        **kwargs: 
            - api_key: OpenAI API key
            - base_url: Custom API base URL
            - model: LLM model to use (default: gpt-4)
            - lang: Language ("en" or "zh")
    
    Returns:
        Workflow object
    """
    from .interactive import AIWorkflowBuilder
    
    builder = AIWorkflowBuilder(
        api_key=kwargs.get("api_key"),
        base_url=kwargs.get("base_url"),
        lang=kwargs.get("lang", "en"),
    )
    return builder.build_from_description(
        description,
        model=kwargs.get("model", "gpt-4"),
    )


def visualize(workflow, format: str = "ascii") -> str:
    """
    Generate a visualization of the workflow.
    
    Args:
        workflow: The Workflow object to visualize
        format: Output format - "ascii", "tree", or "mermaid"
    
    Returns:
        String visualization
    """
    from .interactive import visualize as _visualize
    return _visualize(workflow, format)
