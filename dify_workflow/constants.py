"""
Constants for Dify Workflow Generator.

This module contains all constants used across the package to ensure consistency.
"""

# DSL Version supported by Dify
DSL_VERSION = "0.5.0"

# Node type identifiers used in Dify DSL
class NodeType:
    """Node type constants"""
    START = "start"
    END = "end"
    ANSWER = "answer"
    LLM = "llm"
    HTTP_REQUEST = "http-request"
    CODE = "code"
    IF_ELSE = "if-else"
    VARIABLE_AGGREGATOR = "variable-aggregator"
    TEMPLATE_TRANSFORM = "template-transform"
    ITERATION = "iteration"
    KNOWLEDGE_RETRIEVAL = "knowledge-retrieval"
    QUESTION_CLASSIFIER = "question-classifier"
    PARAMETER_EXTRACTOR = "parameter-extractor"
    TOOL = "tool"
    ASSIGNER = "assigner"
    DOCUMENT_EXTRACTOR = "document-extractor"
    LIST_FILTER = "list-filter"


# Mapping from node type to class name
NODE_CLASS_MAP = {
    NodeType.START: "StartNode",
    NodeType.END: "EndNode",
    NodeType.ANSWER: "AnswerNode",
    NodeType.LLM: "LLMNode",
    NodeType.HTTP_REQUEST: "HTTPNode",
    NodeType.CODE: "CodeNode",
    NodeType.IF_ELSE: "IfElseNode",
    NodeType.VARIABLE_AGGREGATOR: "VariableAggregatorNode",
    NodeType.TEMPLATE_TRANSFORM: "TemplateNode",
    NodeType.ITERATION: "IterationNode",
    NodeType.KNOWLEDGE_RETRIEVAL: "KnowledgeNode",
    NodeType.QUESTION_CLASSIFIER: "QuestionClassifierNode",
    NodeType.PARAMETER_EXTRACTOR: "ParameterExtractorNode",
    NodeType.TOOL: "ToolNode",
    NodeType.ASSIGNER: "AssignerNode",
    NodeType.DOCUMENT_EXTRACTOR: "DocumentExtractorNode",
    NodeType.LIST_FILTER: "ListFilterNode",
}

# Reverse mapping from class name to node type
CLASS_TO_NODE_TYPE = {v: k for k, v in NODE_CLASS_MAP.items()}

# Default model configuration
DEFAULT_MODEL = {
    "provider": "openai",
    "name": "gpt-4",
    "mode": "chat",
    "completion_params": {
        "temperature": 0.7,
    }
}

# Node type icons for visualization
NODE_ICONS = {
    NodeType.START: "[>]",
    NodeType.END: "[=]",
    NodeType.ANSWER: "[<]",
    NodeType.LLM: "[*]",
    NodeType.HTTP_REQUEST: "[@]",
    NodeType.CODE: "[#]",
    NodeType.IF_ELSE: "[?]",
    NodeType.KNOWLEDGE_RETRIEVAL: "[K]",
    NodeType.TEMPLATE_TRANSFORM: "[T]",
    NodeType.ITERATION: "[~]",
    NodeType.VARIABLE_AGGREGATOR: "[&]",
    NodeType.QUESTION_CLASSIFIER: "[Q]",
    NodeType.PARAMETER_EXTRACTOR: "[P]",
    NodeType.TOOL: "[!]",
    NodeType.ASSIGNER: "[=]",
    NodeType.DOCUMENT_EXTRACTOR: "[D]",
    NodeType.LIST_FILTER: "[F]",
}

# Mermaid diagram shapes
MERMAID_SHAPES = {
    NodeType.START: "(({title}))",
    NodeType.END: "[/{title}/]",
    NodeType.ANSWER: "[/{title}/]",
    NodeType.IF_ELSE: "{{{title}}}",
    NodeType.LLM: "[[\"{title}\"]]",
    "default": "[\"{title}\"]",
}
