"""
Dify Workflow Generator - Programmatically create Dify-compatible workflow DSL files

This library generates YAML files that can be directly imported into Dify.
DSL Version: 0.5.0

Features:
- Full node support (17 types)
- Interactive guided builder
- AI-powered natural language workflow generation
- CLI tool for automation

Quick Start:
    >>> from dify_workflow import Workflow, StartNode, LLMNode, EndNode
    >>> wf = Workflow("My Workflow")
    >>> start = StartNode(variables=[{"name": "query", "type": "string"}])
    >>> llm = LLMNode(prompt="{{#start.query#}}")
    >>> end = EndNode(outputs=[{"variable": "result", "value_selector": ["llm", "text"]}])
    >>> wf.add_nodes([start, llm, end])
    >>> wf.connect(start, llm)
    >>> wf.connect(llm, end)
    >>> wf.export("workflow.yml")

AI-Powered:
    >>> from dify_workflow import from_description
    >>> wf = from_description("创建一个翻译工作流，输入文本和目标语言")
    >>> wf.export("translator.yml")
"""

from .constants import DSL_VERSION, NodeType, NODE_CLASS_MAP, DEFAULT_MODEL

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
    AssignerNode,
    DocumentExtractorNode,
    ListFilterNode,
)

from .importer import DifyImporter, import_workflow

from .builder import WorkflowBuilder, quick_workflow, chatbot

from . import utils
from . import decorators

from .plugins import (
    WorkflowPlugin,
    PluginManager,
    PluginMetadata,
    get_plugin_manager,
    register_plugin,
    AutoLayoutPlugin,
    ValidationEnhancerPlugin,
    NamingConventionPlugin,
)

from .profiler import (
    WorkflowProfiler,
    WorkflowProfile,
    NodeProfile,
    analyze_workflow,
)

from .batch import (
    BatchProcessor,
    WorkflowGenerator,
    bulk_export,
    bulk_validate,
)

from .docs import (
    DocumentationGenerator,
    WorkflowDoc,
    NodeDoc,
    generate_docs,
)

from .exceptions import (
    DifyWorkflowError,
    ValidationError,
    NodeError,
    ConnectionError,
    ImportError,
    ExportError,
    AIBuilderError,
    ConfigurationError,
    TemplateError,
)

from .config import Config, get_config, set_config, reset_config

# Database (optional, requires sqlalchemy)
try:
    from .database import WorkflowDatabase, get_database
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False

# Executor (for local workflow testing)
from .executor import (
    WorkflowExecutor,
    WorkflowRunner,
    ExecutionResult,
    ExecutionStatus,
    NodeExecutor,
)

# Marketplace (optional)
try:
    from .marketplace import (
        WorkflowMarketplace,
        WorkflowEntry,
        LocalWorkflowHub,
    )
    MARKETPLACE_AVAILABLE = True
except ImportError:
    MARKETPLACE_AVAILABLE = False

# Collaboration (optional, requires websockets)
try:
    from .collaboration import (
        CollaborationRoom,
        CollaborationClient,
        CollaborationManager,
        collaboration_manager,
        Operation,
        OperationType,
        Cursor,
    )
    COLLABORATION_AVAILABLE = True
except ImportError:
    COLLABORATION_AVAILABLE = False

# Optimizer
from .optimizer import (
    WorkflowOptimizer,
    AIOptimizer,
    OptimizationReport,
    OptimizationSuggestion,
    OptimizationType,
    Severity,
    optimize_workflow,
    analyze_workflow,
)

# Debugger
from .debugger import (
    WorkflowDebugger,
    Breakpoint,
    BreakpointType,
    DebugAction,
    StackFrame,
    DebugVariable,
    ExecutionTrace,
)

# Git Integration
from .git_integration import (
    WorkflowGit,
    WorkflowCommit,
    WorkflowBranch,
    WorkflowDiff,
)

# Shell Completion
from .completion import (
    install_completion,
    get_install_path,
)

# Migration
from .migration import (
    WorkflowMigrator,
    DifyVersionMigrator,
    LangchainMigrator,
    MakeMigrator,
    ZapierMigrator,
)

# Testing Framework
from .testing import (
    WorkflowTestSuite,
    WorkflowTest,
    TestReport,
    TestResult,
    WorkflowMock,
    create_test_suite,
    load_test_suite,
    run_tests,
)

# Agent Teams (Opus 4.6)
from .agent_teams import (
    DifyWorkflowAgentTeam,
    AgentConfig,
    AgentRole,
    TaskResult,
    AgentTeamCLI,
    create_workflow_with_agents,
)

__version__ = "0.5.0"
__dsl_version__ = DSL_VERSION

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
    # Importer
    "DifyImporter",
    "import_workflow",
    # Constants
    "DSL_VERSION",
    "NodeType",
    "NODE_CLASS_MAP",
    "DEFAULT_MODEL",
    # Utils
    "utils",
    # Builder
    "WorkflowBuilder",
    "quick_workflow",
    "chatbot",
    # Plugins
    "WorkflowPlugin",
    "PluginManager",
    "PluginMetadata",
    "get_plugin_manager",
    "register_plugin",
    "AutoLayoutPlugin",
    "ValidationEnhancerPlugin",
    "NamingConventionPlugin",
    # Profiler
    "WorkflowProfiler",
    "WorkflowProfile",
    "NodeProfile",
    "analyze_workflow",
    # Batch
    "BatchProcessor",
    "WorkflowGenerator",
    "bulk_export",
    "bulk_validate",
    # Docs
    "DocumentationGenerator",
    "WorkflowDoc",
    "NodeDoc",
    "generate_docs",
    # Exceptions
    "DifyWorkflowError",
    "ValidationError",
    "NodeError",
    "ConnectionError",
    "ImportError",
    "ExportError",
    "AIBuilderError",
    "ConfigurationError",
    "TemplateError",
    "DatabaseError",
    "MarketplaceError",
    "ExecutionError",
    # Config
    "Config",
    "get_config",
    "set_config",
    "reset_config",
    # Database
    "WorkflowDatabase",
    "get_database",
    "DATABASE_AVAILABLE",
    # Executor
    "WorkflowExecutor",
    "WorkflowRunner",
    "ExecutionResult",
    "ExecutionStatus",
    "NodeExecutor",
    # Marketplace
    "WorkflowMarketplace",
    "WorkflowEntry",
    "LocalWorkflowHub",
    "MARKETPLACE_AVAILABLE",
    # Collaboration
    "CollaborationRoom",
    "CollaborationClient",
    "CollaborationManager",
    "collaboration_manager",
    "Operation",
    "OperationType",
    "Cursor",
    "COLLABORATION_AVAILABLE",
    # Optimizer
    "WorkflowOptimizer",
    "AIOptimizer",
    "OptimizationReport",
    "OptimizationSuggestion",
    "OptimizationType",
    "Severity",
    "optimize_workflow",
    "analyze_workflow",
    # Debugger
    "WorkflowDebugger",
    "Breakpoint",
    "BreakpointType",
    "DebugAction",
    "StackFrame",
    "DebugVariable",
    "ExecutionTrace",
    # Git Integration
    "WorkflowGit",
    "WorkflowCommit",
    "WorkflowBranch",
    "WorkflowDiff",
    # Shell Completion
    "install_completion",
    "get_install_path",
    # Migration
    "WorkflowMigrator",
    "DifyVersionMigrator",
    "LangchainMigrator",
    "MakeMigrator",
    "ZapierMigrator",
    # Testing Framework
    "WorkflowTestSuite",
    "WorkflowTest",
    "TestReport",
    "TestResult",
    "WorkflowMock",
    "create_test_suite",
    "load_test_suite",
    "run_tests",
    # Agent Teams (Opus 4.6)
    "DifyWorkflowAgentTeam",
    "AgentConfig",
    "AgentRole",
    "TaskResult",
    "AgentTeamCLI",
    "create_workflow_with_agents",
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
