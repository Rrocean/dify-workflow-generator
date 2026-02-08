"""
Workflow execution engine for local testing
Simulates Dify workflow execution
"""
import asyncio
import json
import time
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum

from .workflow import Workflow
from .nodes import Node
from .exceptions import ExecutionError


class ExecutionStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ExecutionResult:
    """Result of a workflow execution"""
    status: ExecutionStatus
    outputs: Dict[str, Any]
    execution_time: float
    node_results: Dict[str, Any]
    logs: List[str]
    error: Optional[str] = None


class NodeExecutor:
    """Base class for node executors"""

    def __init__(self, node: Node):
        self.node = node

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the node with given inputs"""
        raise NotImplementedError


class StartNodeExecutor(NodeExecutor):
    """Executor for start node"""

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        # Start node just passes through the inputs
        return {"outputs": inputs}


class LLMNodeExecutor(NodeExecutor):
    """Executor for LLM node - simulates LLM response"""

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        # Simulate LLM processing delay
        await asyncio.sleep(0.5)

        # Mock response based on prompt
        prompt = self.node.data.get("prompt", "")

        # Simple mock responses for common patterns
        if "translate" in prompt.lower():
            return {"text": f"[Translated]: {inputs.get('text', 'Sample text')}"}
        elif "summarize" in prompt.lower():
            return {"text": "[Summary]: This is a summary of the provided text."}
        elif "code" in prompt.lower():
            return {"text": "```python\n# Generated code\nprint('Hello World')\n```"}
        else:
            return {"text": f"[LLM Response to: {prompt[:50]}...]"}


class EndNodeExecutor(NodeExecutor):
    """Executor for end node"""

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        return {"outputs": inputs}


class HttpNodeExecutor(NodeExecutor):
    """Executor for HTTP node - simulates HTTP request"""

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        # Simulate network delay
        await asyncio.sleep(0.3)

        url = self.node.data.get("url", "")
        method = self.node.data.get("method", "GET")

        # Mock response
        return {
            "status_code": 200,
            "body": json.dumps({"message": f"Mock {method} response from {url}", "data": inputs}),
            "headers": {"Content-Type": "application/json"}
        }


class CodeNodeExecutor(NodeExecutor):
    """Executor for code node - executes Python code safely"""

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        code = self.node.data.get("code", "")

        # Create safe execution environment
        safe_globals = {
            "__builtins__": {
                "len": len,
                "range": range,
                "enumerate": enumerate,
                "zip": zip,
                "map": map,
                "filter": filter,
                "sum": sum,
                "min": min,
                "max": max,
                "abs": abs,
                "round": round,
                "str": str,
                "int": int,
                "float": float,
                "list": list,
                "dict": dict,
                "set": set,
                "tuple": tuple,
                "json": json,
            },
            "args": inputs,
        }

        try:
            # Execute code in restricted environment
            exec(code, safe_globals)
            result = safe_globals.get("result", {})
            return result if isinstance(result, dict) else {"result": result}
        except Exception as e:
            raise ExecutionError(f"Code execution failed: {e}")


class IfElseNodeExecutor(NodeExecutor):
    """Executor for if/else node"""

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        conditions = self.node.data.get("conditions", [])

        # Evaluate conditions
        result = False
        for condition in conditions:
            # Simple condition evaluation
            # In real implementation, this would be more sophisticated
            result = True  # Mock: always true for simulation
            break

        return {"condition_result": result}


# Node type to executor mapping
EXECUTOR_MAP = {
    "start": StartNodeExecutor,
    "llm": LLMNodeExecutor,
    "end": EndNodeExecutor,
    "http": HttpNodeExecutor,
    "code": CodeNodeExecutor,
    "if-else": IfElseNodeExecutor,
}


class WorkflowExecutor:
    """Workflow execution engine"""

    def __init__(self, workflow: Workflow):
        self.workflow = workflow
        self.execution_context: Dict[str, Any] = {}
        self.node_outputs: Dict[str, Any] = {}
        self.logs: List[str] = []
        self._cancelled = False

    def log(self, message: str):
        """Add log entry"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.logs.append(log_entry)
        print(log_entry)

    async def execute(self, inputs: Optional[Dict[str, Any]] = None,
                      progress_callback: Optional[Callable[[str, float], None]] = None) -> ExecutionResult:
        """Execute the workflow"""
        start_time = time.time()

        try:
            self.log(f"Starting workflow: {self.workflow.name}")

            # Get execution order
            from .utils import find_execution_order
            execution_order = find_execution_order(self.workflow)

            self.log(f"Execution order: {[node.id for node in execution_order]}")

            # Initialize with inputs
            self.node_outputs["start"] = inputs or {}

            # Execute nodes in order
            for i, node in enumerate(execution_order):
                if self._cancelled:
                    return ExecutionResult(
                        status=ExecutionStatus.CANCELLED,
                        outputs={},
                        execution_time=time.time() - start_time,
                        node_results=self.node_outputs,
                        logs=self.logs,
                        error="Execution cancelled by user"
                    )

                progress = (i / len(execution_order)) * 100
                if progress_callback:
                    progress_callback(node.id, progress)

                self.log(f"Executing node: {node.title} ({node.type})")

                # Get executor for node type
                executor_class = EXECUTOR_MAP.get(node.type)
                if not executor_class:
                    self.log(f"Warning: No executor for node type '{node.type}', skipping")
                    continue

                executor = executor_class(node)

                # Get inputs for this node
                node_inputs = self._resolve_node_inputs(node)

                # Execute
                try:
                    output = await executor.execute(node_inputs, self.execution_context)
                    self.node_outputs[node.id] = output
                    self.log(f"Node {node.title} completed successfully")
                except Exception as e:
                    self.log(f"Node {node.title} failed: {e}")
                    raise ExecutionError(f"Node '{node.title}' execution failed: {e}")

            # Get final outputs
            final_outputs = self._get_final_outputs()

            execution_time = time.time() - start_time
            self.log(f"Workflow completed in {execution_time:.2f}s")

            return ExecutionResult(
                status=ExecutionStatus.COMPLETED,
                outputs=final_outputs,
                execution_time=execution_time,
                node_results=self.node_outputs,
                logs=self.logs
            )

        except Exception as e:
            execution_time = time.time() - start_time
            self.log(f"Workflow failed: {e}")

            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                outputs={},
                execution_time=execution_time,
                node_results=self.node_outputs,
                logs=self.logs,
                error=str(e)
            )

    def _resolve_node_inputs(self, node: Node) -> Dict[str, Any]:
        """Resolve inputs for a node based on incoming edges"""
        inputs = {}

        # Find all edges pointing to this node
        for edge in self.workflow.edges:
            if edge.target == node.id:
                # Get output from source node
                source_output = self.node_outputs.get(edge.source, {})
                inputs.update(source_output.get("outputs", {}))
                inputs.update(source_output.get("text", {}))

        return inputs

    def _get_final_outputs(self) -> Dict[str, Any]:
        """Get final workflow outputs from end node"""
        # Find end node
        for node in self.workflow.nodes:
            if node.type == "end":
                end_outputs = self.node_outputs.get(node.id, {})
                return end_outputs.get("outputs", {})

        return {}

    def cancel(self):
        """Cancel workflow execution"""
        self._cancelled = True
        self.log("Cancellation requested")


class WorkflowRunner:
    """High-level interface for running workflows"""

    def __init__(self):
        self._running_executions: Dict[str, WorkflowExecutor] = {}

    async def run(self, workflow: Workflow,
                  inputs: Optional[Dict[str, Any]] = None,
                  execution_id: Optional[str] = None) -> ExecutionResult:
        """Run a workflow"""
        executor = WorkflowExecutor(workflow)

        if execution_id:
            self._running_executions[execution_id] = executor

        try:
            result = await executor.execute(inputs)
            return result
        finally:
            if execution_id:
                del self._running_executions[execution_id]

    def cancel(self, execution_id: str):
        """Cancel a running workflow"""
        if execution_id in self._running_executions:
            self._running_executions[execution_id].cancel()
