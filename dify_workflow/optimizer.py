"""
AI-Powered Workflow Optimizer
Analyzes workflows and suggests improvements for performance, cost, and quality
"""
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class OptimizationType(Enum):
    PERFORMANCE = "performance"      # Reduce latency
    COST = "cost"                    # Reduce API costs
    QUALITY = "quality"              # Improve output quality
    STRUCTURE = "structure"          # Improve code structure
    SECURITY = "security"            # Security improvements


class Severity(Enum):
    CRITICAL = "critical"            # Must fix
    HIGH = "high"                    # Should fix
    MEDIUM = "medium"                # Consider fixing
    LOW = "low"                      # Nice to have
    INFO = "info"                    # Informational


@dataclass
class OptimizationSuggestion:
    """Single optimization suggestion"""
    id: str
    type: OptimizationType
    severity: Severity
    title: str
    description: str
    node_id: Optional[str] = None
    node_type: Optional[str] = None
    current_value: Any = None
    suggested_value: Any = None
    expected_improvement: str = ""
    auto_applicable: bool = False
    code_changes: Optional[Dict[str, Any]] = None


@dataclass
class OptimizationReport:
    """Complete optimization report"""
    workflow_name: str
    original_score: int
    optimized_score: int
    suggestions: List[OptimizationSuggestion]
    summary: Dict[str, int]


class WorkflowOptimizer:
    """
    AI-Powered Workflow Optimizer
    Analyzes workflows and suggests improvements
    """

    def __init__(self):
        self.rules = self._load_optimization_rules()

    def _load_optimization_rules(self) -> List[Dict[str, Any]]:
        """Load built-in optimization rules"""
        return [
            {
                "id": "llm-model-downgrade",
                "type": OptimizationType.COST,
                "severity": Severity.MEDIUM,
                "title": "Consider using cheaper model",
                "description": "For simple tasks, GPT-3.5-Turbo can be 10x cheaper than GPT-4",
                "applies_to": ["llm"],
                "check": lambda node: node.data.get("model", {}).get("name") == "gpt-4",
                "suggestion": "gpt-3.5-turbo"
            },
            {
                "id": "high-temperature",
                "type": OptimizationType.QUALITY,
                "severity": Severity.HIGH,
                "title": "Temperature too high for deterministic tasks",
                "description": "Use lower temperature (0.0-0.3) for tasks requiring consistency",
                "applies_to": ["llm"],
                "check": lambda node: node.data.get("temperature", 0.7) > 0.5,
                "suggestion": 0.2
            },
            {
                "id": "missing-error-handling",
                "type": OptimizationType.STRUCTURE,
                "severity": Severity.CRITICAL,
                "title": "Missing error handling for HTTP node",
                "description": "HTTP nodes should have retry logic and error handling",
                "applies_to": ["http"],
                "check": lambda node: not node.data.get("retry"),
                "suggestion": {"retry": {"max_retries": 3, "timeout": 30}}
            },
            {
                "id": "unused-variables",
                "type": OptimizationType.STRUCTURE,
                "severity": Severity.LOW,
                "title": "Unused workflow variables",
                "description": "Remove variables that are not used in any node",
                "applies_to": ["start"],
                "check": lambda node, workflow: self._check_unused_vars(node, workflow),
                "suggestion": None
            },
            {
                "id": "long-prompt",
                "type": OptimizationType.PERFORMANCE,
                "severity": Severity.MEDIUM,
                "title": "Prompt may be too long",
                "description": "Long prompts increase token costs. Consider chunking or summarization",
                "applies_to": ["llm"],
                "check": lambda node: len(node.data.get("prompt", "")) > 2000,
                "suggestion": "Use variable aggregation or document extraction"
            },
            {
                "id": "parallel-processing",
                "type": OptimizationType.PERFORMANCE,
                "severity": Severity.HIGH,
                "title": "Consider parallel execution",
                "description": "Independent branches can run in parallel to reduce latency",
                "applies_to": ["all"],
                "check": lambda node, workflow: self._check_parallel_opportunity(node, workflow),
                "suggestion": None
            },
            {
                "id": "caching",
                "type": OptimizationType.COST,
                "severity": Severity.MEDIUM,
                "title": "Add caching for repeated operations",
                "description": "Cache expensive LLM calls that have the same inputs",
                "applies_to": ["llm", "http"],
                "check": lambda node: not node.data.get("cache_enabled"),
                "suggestion": {"cache_enabled": True, "cache_ttl": 3600}
            },
            {
                "id": "prompt-injection-risk",
                "type": OptimizationType.SECURITY,
                "severity": Severity.CRITICAL,
                "title": "Potential prompt injection vulnerability",
                "description": "User input is directly inserted into prompt without sanitization",
                "applies_to": ["llm"],
                "check": lambda node: self._check_prompt_injection_risk(node),
                "suggestion": "Add input validation and sanitization"
            }
        ]

    def analyze(self, workflow) -> OptimizationReport:
        """
        Analyze a workflow and generate optimization report
        """
        suggestions = []

        # Run all optimization rules
        for rule in self.rules:
            for node in workflow.nodes:
                if rule["applies_to"] == ["all"] or node.type in rule["applies_to"]:
                    try:
                        # Check if rule applies
                        if "workflow" in rule["check"].__code__.co_varnames:
                            applies = rule["check"](node, workflow)
                        else:
                            applies = rule["check"](node)

                        if applies:
                            suggestion = OptimizationSuggestion(
                                id=rule["id"],
                                type=rule["type"],
                                severity=rule["severity"],
                                title=rule["title"],
                                description=rule["description"],
                                node_id=node.id,
                                node_type=node.type,
                                current_value=self._get_current_value(node, rule),
                                suggested_value=rule.get("suggestion"),
                                expected_improvement=self._calculate_improvement(rule, node),
                                auto_applicable=self._is_auto_applicable(rule)
                            )
                            suggestions.append(suggestion)
                    except Exception:
                        continue

        # Calculate scores
        original_score = self._calculate_score(workflow)
        optimized_score = self._calculate_optimized_score(workflow, suggestions)

        # Group by type
        summary = {
            "critical": len([s for s in suggestions if s.severity == Severity.CRITICAL]),
            "high": len([s for s in suggestions if s.severity == Severity.HIGH]),
            "medium": len([s for s in suggestions if s.severity == Severity.MEDIUM]),
            "low": len([s for s in suggestions if s.severity == Severity.LOW]),
            "info": len([s for s in suggestions if s.severity == Severity.INFO]),
        }

        return OptimizationReport(
            workflow_name=workflow.name,
            original_score=original_score,
            optimized_score=optimized_score,
            suggestions=suggestions,
            summary=summary
        )

    def optimize(self, workflow, auto_apply: bool = False) -> tuple:
        """
        Optimize a workflow by applying suggestions
        Returns (optimized_workflow, report)
        """
        report = self.analyze(workflow)
        optimized = workflow.clone()

        if auto_apply:
            for suggestion in report.suggestions:
                if suggestion.auto_applicable:
                    self._apply_suggestion(optimized, suggestion)

        return optimized, report

    def _apply_suggestion(self, workflow, suggestion: OptimizationSuggestion):
        """Apply a single optimization suggestion"""
        if not suggestion.node_id:
            return

        for node in workflow.nodes:
            if node.id == suggestion.node_id:
                if suggestion.id == "llm-model-downgrade":
                    node.data["model"]["name"] = "gpt-3.5-turbo"
                elif suggestion.id == "high-temperature":
                    node.data["temperature"] = 0.2
                elif suggestion.id == "caching":
                    node.data["cache_enabled"] = True
                    node.data["cache_ttl"] = 3600
                break

    def _get_current_value(self, node, rule: Dict) -> Any:
        """Get current value for a rule"""
        if "llm-model" in rule["id"]:
            return node.data.get("model", {}).get("name")
        elif "temperature" in rule["id"]:
            return node.data.get("temperature")
        return None

    def _is_auto_applicable(self, rule: Dict) -> bool:
        """Check if rule can be auto-applied"""
        auto_applicable_rules = ["llm-model-downgrade", "high-temperature", "caching"]
        return rule["id"] in auto_applicable_rules

    def _calculate_improvement(self, rule: Dict, node) -> str:
        """Calculate expected improvement"""
        improvements = {
            "llm-model-downgrade": "~90% cost reduction",
            "high-temperature": "More consistent outputs",
            "caching": "~50% latency reduction for repeated queries",
            "parallel-processing": "~40% total latency reduction",
            "missing-error-handling": "Improved reliability"
        }
        return improvements.get(rule["id"], "Workflow improvement")

    def _calculate_score(self, workflow) -> int:
        """Calculate workflow quality score (0-100)"""
        score = 100

        # Deduct points for issues
        for node in workflow.nodes:
            if node.type == "llm":
                if node.data.get("temperature", 0.7) > 0.5:
                    score -= 5
                if node.data.get("model", {}).get("name") == "gpt-4":
                    score -= 2  # Not bad, but expensive
            if node.type == "http" and not node.data.get("retry"):
                score -= 10

        return max(0, score)

    def _calculate_optimized_score(self, workflow, suggestions: List[OptimizationSuggestion]) -> int:
        """Calculate potential score after optimizations"""
        base_score = self._calculate_score(workflow)

        for suggestion in suggestions:
            if suggestion.auto_applicable:
                if suggestion.severity == Severity.CRITICAL:
                    base_score += 10
                elif suggestion.severity == Severity.HIGH:
                    base_score += 5
                elif suggestion.severity == Severity.MEDIUM:
                    base_score += 3
                elif suggestion.severity == Severity.LOW:
                    base_score += 1

        return min(100, base_score)

    def _check_unused_vars(self, node, workflow) -> bool:
        """Check for unused variables"""
        # Simplified check - in real implementation, parse all prompts
        return False

    def _check_parallel_opportunity(self, node, workflow) -> bool:
        """Check if node could be parallelized"""
        # Check if this node has multiple independent branches
        return False

    def _check_prompt_injection_risk(self, node) -> bool:
        """Check for potential prompt injection"""
        prompt = node.data.get("prompt", "")
        # Check for direct variable interpolation without sanitization
        dangerous_patterns = ["{{#", "{user_input}"]
        return any(pattern in prompt for pattern in dangerous_patterns)


class AIOptimizer:
    """
    AI-powered optimizer using LLM to suggest improvements
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    async def optimize_with_ai(self, workflow) -> OptimizationReport:
        """
        Use AI to analyze and optimize workflow
        """
        # This would call an LLM to analyze the workflow
        # For now, return base optimizer results
        base_optimizer = WorkflowOptimizer()
        return base_optimizer.analyze(workflow)

    def generate_optimization_prompt(self, workflow) -> str:
        """Generate prompt for AI optimization"""
        workflow_json = json.dumps(workflow.to_dict(), indent=2)

        return f"""Analyze this Dify workflow and suggest optimizations:

{workflow_json}

Please suggest improvements in these categories:
1. Performance - reduce latency
2. Cost - reduce API usage costs
3. Quality - improve output quality
4. Security - identify vulnerabilities
5. Best Practices - coding standards

For each suggestion, provide:
- Category
- Severity (critical/high/medium/low)
- Description of the issue
- Specific code changes to fix it
- Expected improvement
"""


# Convenience functions
def optimize_workflow(workflow, auto_apply: bool = False):
    """Optimize a workflow"""
    optimizer = WorkflowOptimizer()
    return optimizer.optimize(workflow, auto_apply)


def analyze_workflow(workflow) -> OptimizationReport:
    """Analyze a workflow and return report"""
    optimizer = WorkflowOptimizer()
    return optimizer.analyze(workflow)
