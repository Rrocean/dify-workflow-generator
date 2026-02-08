"""
Plugin system for Dify Workflow Generator.

Allows extending functionality with custom plugins.
"""

import importlib
import inspect
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Type

from .nodes import Node
from .workflow import Workflow


@dataclass
class PluginMetadata:
    """Metadata for a plugin."""
    name: str
    version: str
    author: str
    description: str
    dependencies: List[str] = field(default_factory=list)


class WorkflowPlugin(ABC):
    """
    Base class for workflow plugins.
    
    Plugins can hook into various stages of workflow creation and processing.
    """
    
    metadata: PluginMetadata
    
    def __init__(self):
        pass
    
    def on_workflow_create(self, workflow: Workflow) -> Workflow:
        """Called when a workflow is created."""
        return workflow
    
    def on_node_add(self, node: Node) -> Node:
        """Called when a node is added."""
        return node
    
    def on_workflow_export(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Called when workflow is exported."""
        return data
    
    def on_workflow_import(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Called when workflow is imported."""
        return data
    
    def on_validate(self, issues: List[str]) -> List[str]:
        """Called during workflow validation."""
        return issues


class PluginManager:
    """Manager for workflow plugins."""
    
    def __init__(self):
        self._plugins: Dict[str, WorkflowPlugin] = {}
        self._hooks: Dict[str, List[Callable]] = {
            "on_workflow_create": [],
            "on_node_add": [],
            "on_workflow_export": [],
            "on_workflow_import": [],
            "on_validate": [],
        }
    
    def register(self, plugin: WorkflowPlugin, name: Optional[str] = None) -> None:
        """
        Register a plugin.
        
        Args:
            plugin: Plugin instance to register
            name: Optional name override
        """
        plugin_name = name or plugin.metadata.name
        self._plugins[plugin_name] = plugin
        
        # Register hooks
        if hasattr(plugin, 'on_workflow_create'):
            self._hooks["on_workflow_create"].append(plugin.on_workflow_create)
        if hasattr(plugin, 'on_node_add'):
            self._hooks["on_node_add"].append(plugin.on_node_add)
        if hasattr(plugin, 'on_workflow_export'):
            self._hooks["on_workflow_export"].append(plugin.on_workflow_export)
        if hasattr(plugin, 'on_workflow_import'):
            self._hooks["on_workflow_import"].append(plugin.on_workflow_import)
        if hasattr(plugin, 'on_validate'):
            self._hooks["on_validate"].append(plugin.on_validate)
    
    def unregister(self, name: str) -> None:
        """Unregister a plugin."""
        if name in self._plugins:
            del self._plugins[name]
            # Note: Hooks remain registered for simplicity
    
    def get_plugin(self, name: str) -> Optional[WorkflowPlugin]:
        """Get a registered plugin."""
        return self._plugins.get(name)
    
    def list_plugins(self) -> List[str]:
        """List all registered plugin names."""
        return list(self._plugins.keys())
    
    def run_hook(self, hook_name: str, data: Any) -> Any:
        """Run all hooks for a given event."""
        for hook in self._hooks.get(hook_name, []):
            data = hook(data)
        return data


# Global plugin manager instance
_global_plugin_manager: Optional[PluginManager] = None


def get_plugin_manager() -> PluginManager:
    """Get the global plugin manager."""
    global _global_plugin_manager
    if _global_plugin_manager is None:
        _global_plugin_manager = PluginManager()
    return _global_plugin_manager


def register_plugin(plugin: WorkflowPlugin, name: Optional[str] = None) -> None:
    """Register a plugin globally."""
    get_plugin_manager().register(plugin, name)


def discover_plugins(module_name: str) -> List[Type[WorkflowPlugin]]:
    """
    Discover plugins in a module.
    
    Args:
        module_name: Module to search for plugins
        
    Returns:
        List of plugin classes
    """
    try:
        module = importlib.import_module(module_name)
    except ImportError:
        return []
    
    plugins = []
    for name in dir(module):
        obj = getattr(module, name)
        if (isinstance(obj, type) and 
            issubclass(obj, WorkflowPlugin) and 
            obj is not WorkflowPlugin and
            not inspect.isabstract(obj)):
            plugins.append(obj)
    
    return plugins


# Example built-in plugins

class AutoLayoutPlugin(WorkflowPlugin):
    """Automatically layouts workflows on creation."""
    
    metadata = PluginMetadata(
        name="auto-layout",
        version="1.0.0",
        author="Dify Workflow Generator",
        description="Automatically layouts workflows on creation"
    )
    
    def on_workflow_create(self, workflow: Workflow) -> Workflow:
        workflow.auto_layout()
        return workflow


class ValidationEnhancerPlugin(WorkflowPlugin):
    """Enhanced validation rules."""
    
    metadata = PluginMetadata(
        name="validation-enhancer",
        version="1.0.0",
        author="Dify Workflow Generator",
        description="Adds enhanced validation rules"
    )
    
    def on_validate(self, issues: List[str]) -> List[str]:
        # Add custom validation rules
        return issues


class NamingConventionPlugin(WorkflowPlugin):
    """Enforces naming conventions."""
    
    metadata = PluginMetadata(
        name="naming-convention",
        version="1.0.0",
        author="Dify Workflow Generator",
        description="Enforces naming conventions for nodes"
    )
    
    def on_node_add(self, node: Node) -> Node:
        # Example: enforce lowercase with underscores
        if node.title and not node.title.replace("_", "").isalnum():
            node.title = node.title.lower().replace(" ", "_")
        return node
