"""
Workflow Debugger - Step-through debugging with breakpoints
"""
import asyncio
import json
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum


class DebugAction(Enum):
    CONTINUE = "continue"
    STEP_OVER = "step_over"
    STEP_INTO = "step_into"
    STEP_OUT = "step_out"
    PAUSE = "pause"
    STOP = "stop"


class BreakpointType(Enum):
    LINE = "line"  # Break on specific node
    CONDITIONAL = "conditional"  # Break when condition is met
    EXCEPTION = "exception"  # Break on error
    DATA = "data"  # Break when data matches


@dataclass
class Breakpoint:
    """Debugger breakpoint"""
    id: str
    node_id: str
    type: BreakpointType = BreakpointType.LINE
    condition: Optional[str] = None  # For conditional breakpoints
    enabled: bool = True
    hit_count: int = 0
    hit_condition: Optional[str] = None  # e.g., "== 5" or ">= 10"


@dataclass
class StackFrame:
    """Call stack frame"""
    node_id: str
    node_type: str
    node_title: str
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class DebugVariable:
    """Variable in debug scope"""
    name: str
    value: Any
    type: str = "unknown"
    scope: str = "local"  # local, global, input


@dataclass
class ExecutionTrace:
    """Trace of a single execution step"""
    step_number: int
    node_id: str
    node_type: str
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    duration_ms: float
    timestamp: float
    memory_usage: Optional[int] = None


class WorkflowDebugger:
    """
    Interactive workflow debugger
    Supports breakpoints, stepping, and variable inspection
    """

    def __init__(self, workflow):
        self.workflow = workflow
        self.breakpoints: Dict[str, Breakpoint] = {}
        self.is_running = False
        self.is_paused = False
        self.current_node_idx = 0
        self.execution_order = []
        self.call_stack: List[StackFrame] = []
        self.execution_trace: List[ExecutionTrace] = []
        self.variables: Dict[str, DebugVariable] = {}
        self.step_number = 0

        # Event handlers
        self._on_pause: Optional[Callable[[], None]] = None
        self._on_continue: Optional[Callable[[], None]] = None
        self._on_step: Optional[Callable[[ExecutionTrace], None]] = None

        # Execution state
        self._action_queue: List[DebugAction] = []
        self._skip_breakpoints = False

    def add_breakpoint(
        self,
        node_id: str,
        bp_type: BreakpointType = BreakpointType.LINE,
        condition: Optional[str] = None,
        hit_condition: Optional[str] = None
    ) -> Breakpoint:
        """Add a breakpoint"""
        bp = Breakpoint(
            id=f"bp_{len(self.breakpoints)}",
            node_id=node_id,
            type=bp_type,
            condition=condition,
            hit_condition=hit_condition
        )
        self.breakpoints[node_id] = bp
        return bp

    def remove_breakpoint(self, node_id: str) -> bool:
        """Remove a breakpoint"""
        if node_id in self.breakpoints:
            del self.breakpoints[node_id]
            return True
        return False

    def toggle_breakpoint(self, node_id: str) -> bool:
        """Toggle breakpoint enabled state"""
        if node_id in self.breakpoints:
            self.breakpoints[node_id].enabled = not self.breakpoints[node_id].enabled
            return self.breakpoints[node_id].enabled
        return False

    def clear_breakpoints(self):
        """Remove all breakpoints"""
        self.breakpoints.clear()

    async def debug(self, inputs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Start debugging session
        """
        from .utils import find_execution_order

        self.is_running = True
        self.is_paused = False
        self.step_number = 0
        self.execution_trace.clear()
        self.call_stack.clear()
        self.variables.clear()

        # Get execution order
        self.execution_order = find_execution_order(self.workflow)
        self.current_node_idx = 0

        # Set initial inputs as variables
        if inputs:
            for key, value in inputs.items():
                self.variables[f"input.{key}"] = DebugVariable(
                    name=key, value=value, type=type(value).__name__, scope="input"
                )

        try:
            while self.current_node_idx < len(self.execution_order):
                if not self.is_running:
                    break

                node = self.execution_order[self.current_node_idx]

                # Check for breakpoint
                if not self._skip_breakpoints and node.id in self.breakpoints:
                    bp = self.breakpoints[node.id]
                    if bp.enabled and self._should_break(bp, node):
                        await self._pause(DebugAction.STEP_OVER)

                # Wait while paused
                while self.is_paused:
                    await asyncio.sleep(0.1)
                    if not self.is_running:
                        break

                if not self.is_running:
                    break

                # Execute node
                start_time = time.time()

                # Create stack frame
                frame = StackFrame(
                    node_id=node.id,
                    node_type=node.type,
                    node_title=node.title
                )
                self.call_stack.append(frame)

                # Execute (simplified - in real implementation, use actual executor)
                try:
                    # Mock execution for debugging
                    await asyncio.sleep(0.1)  # Simulate work
                    outputs = {"text": f"Output from {node.title}"}
                    frame.outputs = outputs

                    # Add to trace
                    trace = ExecutionTrace(
                        step_number=self.step_number,
                        node_id=node.id,
                        node_type=node.type,
                        inputs=frame.inputs,
                        outputs=outputs,
                        duration_ms=(time.time() - start_time) * 1000,
                        timestamp=time.time()
                    )
                    self.execution_trace.append(trace)
                    self.step_number += 1

                    if self._on_step:
                        self._on_step(trace)

                except Exception as e:
                    # Check for exception breakpoint
                    if any(bp.type == BreakpointType.EXCEPTION for bp in self.breakpoints.values()):
                        await self._pause(DebugAction.STEP_OVER)
                    raise

                finally:
                    self.call_stack.pop()

                self.current_node_idx += 1

                # Process action queue
                if self._action_queue:
                    action = self._action_queue.pop(0)
                    await self._handle_action(action)

            return {
                "status": "completed",
                "trace": self.execution_trace,
                "variables": self.variables
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "trace": self.execution_trace,
                "variables": self.variables
            }

        finally:
            self.is_running = False
            self.is_paused = False

    async def _pause(self, reason: DebugAction):
        """Pause execution"""
        self.is_paused = True
        if self._on_pause:
            self._on_pause()

    def continue_execution(self):
        """Continue execution"""
        self.is_paused = False
        self._skip_breakpoints = False
        if self._on_continue:
            self._on_continue()

    def step_over(self):
        """Step over current node"""
        self._action_queue.append(DebugAction.STEP_OVER)
        self.is_paused = False

    def step_into(self):
        """Step into node (for nested workflows)"""
        self._action_queue.append(DebugAction.STEP_INTO)
        self.is_paused = False

    def step_out(self):
        """Step out of current scope"""
        self._action_queue.append(DebugAction.STEP_OUT)
        self.is_paused = False

    def stop(self):
        """Stop debugging"""
        self.is_running = False
        self.is_paused = False

    def _should_break(self, bp: Breakpoint, node) -> bool:
        """Check if breakpoint should trigger"""
        bp.hit_count += 1

        # Check hit condition
        if bp.hit_condition:
            try:
                condition = f"{bp.hit_count} {bp.hit_condition}"
                if not eval(condition):
                    return False
            except Exception:
                pass

        # Check data condition
        if bp.type == BreakpointType.DATA and bp.condition:
            # Evaluate condition against current variables
            try:
                context = {v.name: v.value for v in self.variables.values()}
                if not eval(bp.condition, {"__builtins__": {}}, context):
                    return False
            except Exception:
                pass

        return True

    async def _handle_action(self, action: DebugAction):
        """Handle debug action"""
        if action == DebugAction.STEP_OVER:
            self._skip_breakpoints = True
        elif action == DebugAction.STOP:
            self.stop()

    def get_variables(self, scope: Optional[str] = None) -> List[DebugVariable]:
        """Get variables in current scope"""
        if scope:
            return [v for v in self.variables.values() if v.scope == scope]
        return list(self.variables.values())

    def evaluate_expression(self, expression: str) -> Any:
        """Evaluate expression in current context"""
        try:
            context = {v.name: v.value for v in self.variables.values()}
            return eval(expression, {"__builtins__": {}}, context)
        except Exception as e:
            return f"Error: {e}"

    def get_call_stack(self) -> List[StackFrame]:
        """Get current call stack"""
        return self.call_stack.copy()

    def get_execution_trace(self) -> List[ExecutionTrace]:
        """Get execution trace"""
        return self.execution_trace.copy()

    def on_pause(self, callback: Callable[[], None]):
        """Set pause handler"""
        self._on_pause = callback

    def on_continue(self, callback: Callable[[], None]):
        """Set continue handler"""
        self._on_continue = callback

    def on_step(self, callback: Callable[[ExecutionTrace], None]):
        """Set step handler"""
        self._on_step = callback

    def export_trace(self, filename: str):
        """Export execution trace to file"""
        trace_data = {
            "workflow": self.workflow.name,
            "steps": [
                {
                    "step": t.step_number,
                    "node": t.node_id,
                    "type": t.node_type,
                    "duration_ms": t.duration_ms,
                    "inputs": t.inputs,
                    "outputs": t.outputs
                }
                for t in self.execution_trace
            ]
        }
        with open(filename, 'w') as f:
            json.dump(trace_data, f, indent=2)
