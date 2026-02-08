"""
Batch operations for workflows.

Supports bulk creating, modifying, and processing workflows.
"""

from typing import Any, Callable, Dict, List, Optional, Tuple, Iterator
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

from .workflow import Workflow
from .nodes import Node
from .logging_config import get_logger

logger = get_logger("batch")


class BatchProcessor:
    """Process multiple workflows in batch."""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
    
    def map_workflows(
        self,
        func: Callable[[Workflow], Workflow],
        workflows: List[Workflow],
        parallel: bool = False
    ) -> List[Workflow]:
        """
        Apply a function to multiple workflows.
        
        Args:
            func: Function to apply to each workflow
            workflows: List of workflows to process
            parallel: Whether to process in parallel
            
        Returns:
            List of processed workflows
        """
        if not parallel:
            return [func(wf) for wf in workflows]
        
        results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(func, wf): wf for wf in workflows}
            for future in as_completed(futures):
                try:
                    results.append(future.result())
                except Exception as e:
                    logger.error(f"Error processing workflow: {e}")
        
        return results
    
    def export_batch(
        self,
        workflows: List[Workflow],
        output_dir: str,
        format: str = "yaml"
    ) -> List[str]:
        """
        Export multiple workflows to files.
        
        Args:
            workflows: List of workflows to export
            output_dir: Directory to save files
            format: Export format (yaml or json)
            
        Returns:
            List of exported file paths
        """
        import os
        
        os.makedirs(output_dir, exist_ok=True)
        paths = []
        
        for wf in workflows:
            filename = f"{wf.name.replace(' ', '_').lower()}.{format}"
            filepath = os.path.join(output_dir, filename)
            wf.export(filepath, format=format)
            paths.append(filepath)
        
        return paths
    
    def validate_batch(self, workflows: List[Workflow]) -> Dict[str, List[str]]:
        """
        Validate multiple workflows.
        
        Args:
            workflows: List of workflows to validate
            
        Returns:
            Dictionary mapping workflow names to issues
        """
        results = {}
        for wf in workflows:
            issues = wf.validate()
            if issues:
                results[wf.name] = issues
        return results


class WorkflowGenerator:
    """Generate multiple workflows from templates or configs."""
    
    def generate_from_configs(
        self,
        configs: List[Dict[str, Any]]
    ) -> Iterator[Workflow]:
        """
        Generate workflows from configuration dictionaries.
        
        Args:
            configs: List of configuration dictionaries
            
        Yields:
            Workflow objects
        """
        for config in configs:
            yield self._create_from_config(config)
    
    def generate_variations(
        self,
        base_workflow: Workflow,
        variations: List[Dict[str, Any]]
    ) -> Iterator[Workflow]:
        """
        Generate workflow variations.
        
        Args:
            base_workflow: Base workflow to modify
            variations: List of variation specifications
            
        Yields:
            Modified workflow objects
        """
        for i, variation in enumerate(variations):
            wf = base_workflow.clone(name=f"{base_workflow.name} v{i+1}")
            
            # Apply variation changes
            if "model" in variation:
                self._update_model(wf, variation["model"])
            if "prompt_prefix" in variation:
                self._add_prompt_prefix(wf, variation["prompt_prefix"])
            
            yield wf
    
    def _create_from_config(self, config: Dict[str, Any]) -> Workflow:
        """Create a workflow from config dict."""
        from .builder import WorkflowBuilder
        
        builder = WorkflowBuilder(
            name=config.get("name", "Untitled"),
            mode=config.get("mode", "workflow"),
            description=config.get("description", "")
        )
        
        # Add start node
        inputs = config.get("inputs", [{"name": "query", "type": "string"}])
        builder.start_with(inputs)
        
        # Add processing nodes based on config
        for step in config.get("steps", []):
            step_type = step.get("type", "llm")
            
            if step_type == "llm":
                builder.llm(
                    prompt=step.get("prompt", ""),
                    model=step.get("model"),
                    temperature=step.get("temperature", 0.7)
                )
            elif step_type == "http":
                builder.http(
                    url=step.get("url", ""),
                    method=step.get("method", "GET")
                )
            elif step_type == "code":
                builder.code(
                    code=step.get("code", ""),
                    language=step.get("language", "python3")
                )
        
        return builder.end().build()
    
    def _update_model(self, workflow: Workflow, model_config: Dict[str, str]) -> None:
        """Update model configuration for all LLM nodes."""
        for node in workflow.nodes:
            if node._node_type == "llm":
                data = node.to_dict().get("data", {})
                if "model" in data:
                    data["model"].update(model_config)
    
    def _add_prompt_prefix(self, workflow: Workflow, prefix: str) -> None:
        """Add a prefix to all LLM prompts."""
        for node in workflow.nodes:
            if node._node_type == "llm":
                data = node.to_dict().get("data", {})
                templates = data.get("prompt_template", [])
                for template in templates:
                    if "text" in template:
                        template["text"] = prefix + "\n\n" + template["text"]


def bulk_export(
    workflows: List[Workflow],
    output_dir: str,
    format: str = "yaml"
) -> List[str]:
    """Convenience function for bulk export."""
    processor = BatchProcessor()
    return processor.export_batch(workflows, output_dir, format)


def bulk_validate(workflows: List[Workflow]) -> Dict[str, List[str]]:
    """Convenience function for bulk validation."""
    processor = BatchProcessor()
    return processor.validate_batch(workflows)
