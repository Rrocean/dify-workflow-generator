"""
Performance profiling and optimization for workflows.

Analyzes workflows and provides optimization suggestions.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .workflow import Workflow
from .nodes import Node


@dataclass
class NodeProfile:
    """Performance profile for a node."""
    node_id: str
    node_type: str
    title: str
    estimated_latency_ms: float
    estimated_cost_usd: float
    token_usage: int
    suggestions: List[str] = field(default_factory=list)


@dataclass
class WorkflowProfile:
    """Performance profile for an entire workflow."""
    workflow_name: str
    nodes: List[NodeProfile]
    total_latency_ms: float
    total_cost_usd: float
    total_tokens: int
    bottleneck_node: Optional[str] = None
    optimization_suggestions: List[str] = field(default_factory=list)
    score: float = 0.0  # 0-100 optimization score


class WorkflowProfiler:
    """Profiles workflows for performance analysis."""
    
    # Estimated latencies (ms) for different node types
    NODE_LATENCIES = {
        "start": 0,
        "end": 0,
        "answer": 50,
        "llm": 2000,  # 2s for LLM
        "http-request": 500,  # 500ms for HTTP
        "code": 100,
        "if-else": 10,
        "template-transform": 50,
        "knowledge-retrieval": 300,
        "variable-aggregator": 10,
        "iteration": 1000,  # Depends on iterations
        "question-classifier": 1000,
        "parameter-extractor": 1000,
        "tool": 500,
        "assigner": 10,
        "document-extractor": 200,
        "list-filter": 50,
    }
    
    # Estimated costs (USD) per 1K tokens
    MODEL_COSTS = {
        "gpt-4": 0.03,
        "gpt-4-turbo": 0.01,
        "gpt-3.5-turbo": 0.0015,
        "claude-3-opus": 0.015,
        "claude-3-sonnet": 0.003,
    }
    
    def __init__(self):
        pass
    
    def profile_node(self, node: Node) -> NodeProfile:
        """Profile a single node."""
        node_type = node._node_type
        
        # Get base latency
        base_latency = self.NODE_LATENCIES.get(node_type, 100)
        
        # Calculate token usage for LLM nodes
        token_usage = 0
        if node_type == "llm":
            token_usage = self._estimate_llm_tokens(node)
        
        # Calculate cost
        cost = self._estimate_cost(node, token_usage)
        
        # Generate suggestions
        suggestions = self._generate_node_suggestions(node, token_usage)
        
        return NodeProfile(
            node_id=node.id,
            node_type=node_type,
            title=node.title,
            estimated_latency_ms=base_latency,
            estimated_cost_usd=cost,
            token_usage=token_usage,
            suggestions=suggestions
        )
    
    def profile_workflow(self, workflow: Workflow) -> WorkflowProfile:
        """Profile an entire workflow."""
        node_profiles = [self.profile_node(n) for n in workflow.nodes]
        
        total_latency = sum(n.estimated_latency_ms for n in node_profiles)
        total_cost = sum(n.estimated_cost_usd for n in node_profiles)
        total_tokens = sum(n.token_usage for n in node_profiles)
        
        # Find bottleneck
        if node_profiles:
            bottleneck = max(node_profiles, key=lambda x: x.estimated_latency_ms)
            bottleneck_id = bottleneck.node_id
        else:
            bottleneck_id = None
        
        # Generate workflow-level suggestions
        suggestions = self._generate_workflow_suggestions(
            workflow, node_profiles, total_latency
        )
        
        # Calculate optimization score
        score = self._calculate_score(node_profiles, suggestions)
        
        return WorkflowProfile(
            workflow_name=workflow.name,
            nodes=node_profiles,
            total_latency_ms=total_latency,
            total_cost_usd=total_cost,
            total_tokens=total_tokens,
            bottleneck_node=bottleneck_id,
            optimization_suggestions=suggestions,
            score=score
        )
    
    def _estimate_llm_tokens(self, node: Node) -> int:
        """Estimate token usage for LLM node."""
        data = node.to_dict().get("data", {})
        prompt_template = data.get("prompt_template", [])
        
        total_chars = 0
        for template in prompt_template:
            text = template.get("text", "")
            total_chars += len(text)
        
        # Rough estimate: 4 chars per token
        return total_chars // 4
    
    def _estimate_cost(self, node: Node, token_usage: int) -> float:
        """Estimate cost for a node."""
        if node._node_type != "llm":
            return 0.0
        
        data = node.to_dict().get("data", {})
        model = data.get("model", {})
        model_name = model.get("name", "gpt-3.5-turbo")
        
        cost_per_1k = self.MODEL_COSTS.get(model_name, 0.002)
        return (token_usage / 1000) * cost_per_1k
    
    def _generate_node_suggestions(
        self, node: Node, token_usage: int
    ) -> List[str]:
        """Generate optimization suggestions for a node."""
        suggestions = []
        
        if node._node_type == "llm":
            if token_usage > 4000:
                suggestions.append(
                    "Consider reducing prompt length to save costs and improve latency"
                )
            
            data = node.to_dict().get("data", {})
            model = data.get("model", {})
            model_name = model.get("name", "")
            
            if "gpt-4" in model_name and token_usage < 1000:
                suggestions.append(
                    "Consider using gpt-3.5-turbo for simple tasks to reduce costs"
                )
        
        elif node._node_type == "http-request":
            suggestions.append(
                "Consider adding timeout settings for HTTP requests"
            )
        
        elif node._node_type == "iteration":
            suggestions.append(
                "Be careful with large arrays in iteration nodes - can cause timeouts"
            )
        
        return suggestions
    
    def _generate_workflow_suggestions(
        self,
        workflow: Workflow,
        node_profiles: List[NodeProfile],
        total_latency: float
    ) -> List[str]:
        """Generate workflow-level suggestions."""
        suggestions = []
        
        # Check for isolated nodes
        connected = set()
        for edge in workflow.edges:
            connected.add(edge["source"])
            connected.add(edge["target"])
        
        isolated = [n for n in workflow.nodes if n.id not in connected]
        if isolated:
            suggestions.append(
                f"Found {len(isolated)} isolated nodes that will never execute"
            )
        
        # Check for long chains
        if len(workflow.nodes) > 10:
            suggestions.append(
                "Workflow has many nodes - consider breaking into smaller workflows"
            )
        
        # Check latency
        if total_latency > 10000:  # 10 seconds
            suggestions.append(
                "Estimated latency exceeds 10 seconds - consider optimizations"
            )
        
        # Check for missing error handling
        has_conditions = any(
            n._node_type == "if-else" for n in workflow.nodes
        )
        has_http = any(
            n._node_type == "http-request" for n in workflow.nodes
        )
        
        if has_http and not has_conditions:
            suggestions.append(
                "Consider adding error handling for HTTP requests"
            )
        
        return suggestions
    
    def _calculate_score(
        self,
        node_profiles: List[NodeProfile],
        suggestions: List[str]
    ) -> float:
        """Calculate optimization score (0-100)."""
        base_score = 100
        
        # Deduct for suggestions
        base_score -= len(suggestions) * 5
        
        # Deduct for nodes with their own suggestions
        node_issues = sum(len(n.suggestions) for n in node_profiles)
        base_score -= node_issues * 3
        
        return max(0, min(100, base_score))
    
    def print_report(self, profile: WorkflowProfile) -> None:
        """Print a formatted profiling report."""
        print(f"\n{'='*60}")
        print(f"Performance Report: {profile.workflow_name}")
        print(f"{'='*60}")
        
        print(f"\n[Summary]")
        print(f"  Total Latency: {profile.total_latency_ms/1000:.2f}s")
        print(f"  Total Cost: ${profile.total_cost_usd:.4f}")
        print(f"  Total Tokens: {profile.total_tokens:,}")
        print(f"  Optimization Score: {profile.score}/100")
        
        if profile.bottleneck_node:
            print(f"\n[Bottleneck] Node: {profile.bottleneck_node}")
        
        print(f"\n[Node Breakdown]")
        for node in profile.nodes:
            print(f"  {node.title} ({node.node_type})")
            print(f"    Latency: {node.estimated_latency_ms:.0f}ms | Cost: ${node.estimated_cost_usd:.4f}")
            if node.suggestions:
                for sugg in node.suggestions:
                    print(f"    ! {sugg}")
        
        if profile.optimization_suggestions:
            print(f"\n[Optimization Suggestions]")
            for sugg in profile.optimization_suggestions:
                print(f"  • {sugg}")
        
        print(f"\n{'='*60}\n")


def analyze_workflow(workflow: Workflow) -> WorkflowProfile:
    """Convenience function to analyze a workflow."""
    profiler = WorkflowProfiler()
    return profiler.profile_workflow(workflow)
