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
]


def interactive():
    """Start interactive workflow builder session"""
    from .interactive import interactive_session
    return interactive_session()


def from_description(description: str, **kwargs):
    """
    Create workflow from natural language description.
    
    Requires: pip install dify-workflow-generator[interactive]
    
    Args:
        description: Natural language description of the workflow
        **kwargs: Passed to AIWorkflowBuilder (api_key, base_url, model)
    
    Returns:
        Workflow object
    """
    from .interactive import AIWorkflowBuilder
    
    builder = AIWorkflowBuilder(
        api_key=kwargs.get("api_key"),
        base_url=kwargs.get("base_url"),
    )
    return builder.build_from_description(
        description,
        model=kwargs.get("model", "gpt-4"),
    )
