"""
Custom exceptions for Dify Workflow Generator.

This module defines all exceptions used throughout the package
for better error handling and debugging.
"""


class DifyWorkflowError(Exception):
    """Base exception for all Dify Workflow errors."""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ValidationError(DifyWorkflowError):
    """Raised when workflow validation fails."""
    pass


class NodeError(DifyWorkflowError):
    """Raised when there's an error with a node."""
    
    def __init__(self, message: str, node_id: str = None, node_type: str = None):
        super().__init__(message)
        self.node_id = node_id
        self.node_type = node_type


class ConnectionError(DifyWorkflowError):
    """Raised when there's an error connecting nodes."""
    
    def __init__(self, message: str, source_id: str = None, target_id: str = None):
        super().__init__(message)
        self.source_id = source_id
        self.target_id = target_id


class ImportError(DifyWorkflowError):
    """Raised when importing a workflow fails."""
    pass


class ExportError(DifyWorkflowError):
    """Raised when exporting a workflow fails."""
    pass


class AIBuilderError(DifyWorkflowError):
    """Raised when AI workflow builder encounters an error."""
    
    def __init__(self, message: str, api_error: Exception = None):
        super().__init__(message)
        self.api_error = api_error


class ConfigurationError(DifyWorkflowError):
    """Raised when there's a configuration error."""
    pass


class TemplateError(DifyWorkflowError):
    """Raised when there's an error with a template."""
    pass


class DatabaseError(DifyWorkflowError):
    """Raised when there's a database operation error."""
    pass


class MarketplaceError(DifyWorkflowError):
    """Raised when there's a marketplace operation error."""
    pass


class ExecutionError(DifyWorkflowError):
    """Raised when workflow execution fails."""
    pass
