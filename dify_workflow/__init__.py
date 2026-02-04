"""
Dify Workflow Generator - Programmatically create Dify-compatible workflow DSL files

This library generates YAML files that can be directly imported into Dify.
DSL Version: 0.5.0
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

__version__ = "0.2.0"
__dsl_version__ = "0.5.0"

__all__ = [
    "Workflow",
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
