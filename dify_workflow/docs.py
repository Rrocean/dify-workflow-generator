"""
Documentation generation for workflows.

Automatically generates documentation from workflow definitions.
"""

import json
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from .workflow import Workflow
from .nodes import Node


@dataclass
class NodeDoc:
    """Documentation for a node."""
    id: str
    type: str
    title: str
    description: str
    inputs: List[Dict[str, Any]] = field(default_factory=list)
    outputs: List[Dict[str, Any]] = field(default_factory=list)
    connected_to: List[str] = field(default_factory=list)
    connected_from: List[str] = field(default_factory=list)


@dataclass
class WorkflowDoc:
    """Documentation for a workflow."""
    name: str
    mode: str
    description: str
    version: str
    total_nodes: int
    node_docs: List[NodeDoc]
    input_variables: List[Dict[str, Any]]
    output_variables: List[Dict[str, Any]]
    execution_flow: List[str]
    mermaid_diagram: str


class DocumentationGenerator:
    """Generates documentation for workflows."""
    
    def __init__(self, include_mermaid: bool = True):
        self.include_mermaid = include_mermaid
    
    def generate(self, workflow: Workflow) -> WorkflowDoc:
        """Generate documentation for a workflow."""
        # Generate node docs
        node_docs = [self._doc_for_node(n, workflow) for n in workflow.nodes]
        
        # Get input/output variables
        inputs = self._extract_inputs(workflow)
        outputs = self._extract_outputs(workflow)
        
        # Get execution flow
        try:
            execution_flow = workflow.get_execution_order()
        except ValueError:
            execution_flow = [n.id for n in workflow.nodes]
        
        # Generate mermaid diagram
        mermaid = ""
        if self.include_mermaid:
            from .interactive import visualize
            mermaid = visualize(workflow, "mermaid")
        
        return WorkflowDoc(
            name=workflow.name,
            mode=workflow.mode,
            description=workflow.description,
            version="0.5.0",
            total_nodes=len(workflow.nodes),
            node_docs=node_docs,
            input_variables=inputs,
            output_variables=outputs,
            execution_flow=execution_flow,
            mermaid_diagram=mermaid
        )
    
    def to_markdown(self, doc: WorkflowDoc) -> str:
        """Convert documentation to Markdown format."""
        lines = [
            f"# {doc.name}",
            "",
            f"**Mode:** {doc.mode}",
            f"**Version:** {doc.version}",
            f"**Total Nodes:** {doc.total_nodes}",
            "",
            "## Description",
            "",
            doc.description or "_No description provided_",
            "",
            "## Input Variables",
            ""
        ]
        
        if doc.input_variables:
            lines.append("| Name | Type | Required | Default |")
            lines.append("|------|------|----------|----------|")
            for var in doc.input_variables:
                lines.append(
                    f"| {var.get('name', 'N/A')} | "
                    f"{var.get('type', 'string')} | "
                    f"{'Yes' if var.get('required') else 'No'} | "
                    f"{var.get('default', '-')} |"
                )
        else:
            lines.append("_No input variables_")
        
        lines.extend(["", "## Output Variables", ""])
        
        if doc.output_variables:
            lines.append("| Variable | Source |")
            lines.append("|----------|--------|")
            for var in doc.output_variables:
                lines.append(
                    f"| {var.get('variable', 'N/A')} | "
                    f"{var.get('value_selector', ['N/A'])} |"
                )
        else:
            lines.append("_No output variables defined_")
        
        lines.extend(["", "## Node Details", ""])
        
        for node_doc in doc.node_docs:
            lines.extend([
                f"### {node_doc.title} ({node_doc.type})",
                "",
                f"**ID:** `{node_doc.id}`",
                "",
                f"**Description:** {node_doc.description or '_No description_'}"
            ])
            
            if node_doc.connected_from:
                lines.append(f"**Input from:** {', '.join(node_doc.connected_from)}")
            
            if node_doc.connected_to:
                lines.append(f"**Output to:** {', '.join(node_doc.connected_to)}")
            
            lines.append("")
        
        lines.extend([
            "",
            "## Execution Flow",
            "",
            "```",
            " → ".join(doc.execution_flow),
            "```",
            ""
        ])
        
        if doc.mermaid_diagram:
            lines.extend([
                "## Flow Diagram",
                "",
                "```mermaid",
                doc.mermaid_diagram,
                "```",
                ""
            ])
        
        return "\n".join(lines)
    
    def to_html(self, doc: WorkflowDoc) -> str:
        """Convert documentation to HTML format."""
        markdown = self.to_markdown(doc)
        # Simple markdown to HTML conversion
        html = markdown.replace("# ", "<h1>").replace("## ", "<h2>").replace("### ", "<h3>")
        html = html.replace("\n\n", "</p><p>")
        html = f"<html><body><p>{html}</p></body></html>"
        return html
    
    def to_json(self, doc: WorkflowDoc) -> str:
        """Convert documentation to JSON format."""
        data = {
            "name": doc.name,
            "mode": doc.mode,
            "description": doc.description,
            "version": doc.version,
            "total_nodes": doc.total_nodes,
            "nodes": [
                {
                    "id": n.id,
                    "type": n.type,
                    "title": n.title,
                    "description": n.description
                }
                for n in doc.node_docs
            ],
            "input_variables": doc.input_variables,
            "output_variables": doc.output_variables,
            "execution_flow": doc.execution_flow
        }
        return json.dumps(data, indent=2)
    
    def _doc_for_node(self, node: Node, workflow: Workflow) -> NodeDoc:
        """Generate documentation for a single node."""
        # Find connections
        connected_to = []
        connected_from = []
        
        for edge in workflow.edges:
            if edge["source"] == node.id:
                connected_to.append(edge["target"])
            if edge["target"] == node.id:
                connected_from.append(edge["source"])
        
        return NodeDoc(
            id=node.id,
            type=node._node_type,
            title=node.title,
            description=node.desc,
            inputs=[],
            outputs=[],
            connected_to=connected_to,
            connected_from=connected_from
        )
    
    def _extract_inputs(self, workflow: Workflow) -> List[Dict[str, Any]]:
        """Extract input variables from workflow."""
        for node in workflow.nodes:
            if node._node_type == "start":
                data = node.to_dict().get("data", {})
                return data.get("variables", [])
        return []
    
    def _extract_outputs(self, workflow: Workflow) -> List[Dict[str, Any]]:
        """Extract output variables from workflow."""
        for node in workflow.nodes:
            if node._node_type == "end":
                data = node.to_dict().get("data", {})
                return data.get("outputs", [])
        return []


def generate_docs(workflow: Workflow, format: str = "markdown") -> str:
    """
    Generate documentation for a workflow.
    
    Args:
        workflow: Workflow to document
        format: Output format (markdown, html, json)
        
    Returns:
        Documentation string
    """
    generator = DocumentationGenerator()
    doc = generator.generate(workflow)
    
    if format == "markdown":
        return generator.to_markdown(doc)
    elif format == "html":
        return generator.to_html(doc)
    elif format == "json":
        return generator.to_json(doc)
    else:
        raise ValueError(f"Unknown format: {format}")
