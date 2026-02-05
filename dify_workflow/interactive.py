"""
Interactive Workflow Builder - AI-powered conversational workflow generator

This module provides an interactive interface that guides users through
creating Dify workflows using natural language.

Features:
- Multi-language support (English, Chinese)
- Multi-turn conversation with follow-up questions
- ASCII visualization of generated workflows
"""

import json
import re
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field

from .workflow import Workflow
from .nodes import (
    StartNode, EndNode, AnswerNode, LLMNode, HTTPNode,
    CodeNode, IfElseNode, TemplateNode, KnowledgeNode,
)


@dataclass
class WorkflowIntent:
    """Parsed user intent for workflow creation"""
    name: str = "My Workflow"
    description: str = ""
    mode: str = "workflow"  # workflow or advanced-chat
    
    # Detected components
    needs_input: bool = True
    input_variables: List[Dict[str, Any]] = field(default_factory=list)
    needs_llm: bool = True
    llm_purpose: str = ""
    llm_prompt: str = ""
    needs_api: bool = False
    api_details: Dict[str, Any] = field(default_factory=dict)
    needs_code: bool = False
    code_purpose: str = ""
    needs_conditions: bool = False
    condition_logic: str = ""
    needs_knowledge: bool = False
    knowledge_purpose: str = ""
    
    # Output
    output_variables: List[str] = field(default_factory=list)


# ============================================================================
# Multi-language support
# ============================================================================

MESSAGES = {
    "en": {
        "welcome": """Welcome to the Dify Workflow Builder!

I'll help you create a workflow step by step. Just answer a few questions.

""",
        "questions": [
            {
                "id": "name",
                "question": "What would you like to name this workflow?",
                "default": "My Workflow",
                "field": "name",
            },
            {
                "id": "purpose",
                "question": "What should this workflow do? (Describe in one sentence)",
                "field": "description",
            },
            {
                "id": "mode",
                "question": "Is this a one-shot workflow or a chat conversation?\n  1. One-shot (workflow)\n  2. Chat (advanced-chat)",
                "options": {"1": "workflow", "2": "advanced-chat"},
                "default": "1",
                "field": "mode",
            },
            {
                "id": "inputs",
                "question": "What inputs does the user need to provide? (comma-separated, e.g., 'text, language')",
                "processor": "parse_inputs",
            },
            {
                "id": "needs_api",
                "question": "Does this workflow need to call external APIs? (y/n)",
                "boolean": True,
                "field": "needs_api",
                "followup": "api_details",
            },
            {
                "id": "needs_code", 
                "question": "Does this workflow need custom code processing? (y/n)",
                "boolean": True,
                "field": "needs_code",
                "followup": "code_details",
            },
            {
                "id": "needs_conditions",
                "question": "Does this workflow need conditional branching (if/else)? (y/n)",
                "boolean": True,
                "field": "needs_conditions",
                "followup": "condition_details",
            },
            {
                "id": "llm_prompt",
                "question": "What instructions should the AI follow? (Leave empty for auto-generate)",
                "field": "llm_prompt",
                "optional": True,
            },
        ],
        "followups": {
            "api_details": "What API will you call? (URL or description)",
            "code_details": "What should the code do?",
            "condition_details": "What condition should be checked?",
        },
        "complete": "Great! I have all the information needed. Generating your workflow...",
        "export_prompt": "Where would you like to save the workflow?",
        "export_default": "Path (default: workflow.yml): ",
        "done": "Done! Import '{path}' into Dify to use your workflow.",
        "cancelled": "Cancelled.",
        "choose_options": "Please choose from the options: {options}",
    },
    "zh": {
        "welcome": """欢迎使用 Dify 工作流生成器！

我会一步步引导你创建工作流，请回答以下问题。

""",
        "questions": [
            {
                "id": "name",
                "question": "请给这个工作流起个名字：",
                "default": "我的工作流",
                "field": "name",
            },
            {
                "id": "purpose",
                "question": "这个工作流要做什么？（用一句话描述）",
                "field": "description",
            },
            {
                "id": "mode",
                "question": "这是单次运行还是对话模式？\n  1. 单次运行（workflow）\n  2. 对话模式（advanced-chat）",
                "options": {"1": "workflow", "2": "advanced-chat"},
                "default": "1",
                "field": "mode",
            },
            {
                "id": "inputs",
                "question": "用户需要提供哪些输入？（用逗号分隔，如：文本, 语言）",
                "processor": "parse_inputs",
            },
            {
                "id": "needs_api",
                "question": "需要调用外部 API 吗？(y/n)",
                "boolean": True,
                "field": "needs_api",
                "followup": "api_details",
            },
            {
                "id": "needs_code",
                "question": "需要自定义代码处理吗？(y/n)",
                "boolean": True,
                "field": "needs_code",
                "followup": "code_details",
            },
            {
                "id": "needs_conditions",
                "question": "需要条件分支（if/else）吗？(y/n)",
                "boolean": True,
                "field": "needs_conditions",
                "followup": "condition_details",
            },
            {
                "id": "llm_prompt",
                "question": "AI 应该遵循什么指令？（留空自动生成）",
                "field": "llm_prompt",
                "optional": True,
            },
        ],
        "followups": {
            "api_details": "要调用什么 API？（URL 或描述）",
            "code_details": "代码需要做什么处理？",
            "condition_details": "需要检查什么条件？",
        },
        "complete": "太好了！信息收集完毕，正在生成工作流...",
        "export_prompt": "想把工作流保存到哪里？",
        "export_default": "路径（默认: workflow.yml）：",
        "done": "完成！将 '{path}' 导入 Dify 即可使用。",
        "cancelled": "已取消。",
        "choose_options": "请从以下选项中选择：{options}",
    },
}


class InteractiveBuilder:
    """
    Guide users through workflow creation with questions.
    
    Supports multiple languages and follow-up questions for details.
    """
    
    def __init__(self, lang: str = "en"):
        """
        Initialize the builder.
        
        Args:
            lang: Language code ("en" or "zh")
        """
        self.lang = lang if lang in MESSAGES else "en"
        self.messages = MESSAGES[self.lang]
        self.questions = self.messages["questions"]
        
        self.intent = WorkflowIntent()
        self.current_step = 0
        self.answers: Dict[str, str] = {}
        
        # For follow-up questions
        self.pending_followup: Optional[str] = None
        self.followup_answers: Dict[str, str] = {}
    
    def get_current_question(self) -> Optional[Dict[str, Any]]:
        """Get the current question to ask"""
        if self.pending_followup:
            return {
                "id": self.pending_followup,
                "question": self.messages["followups"].get(self.pending_followup, ""),
                "is_followup": True,
            }
        
        if self.current_step >= len(self.questions):
            return None
        return self.questions[self.current_step]
    
    def process_answer(self, answer: str) -> Tuple[bool, str]:
        """
        Process user's answer to current question.
        
        Returns: (success, next_message)
        """
        # Handle follow-up questions
        if self.pending_followup:
            self.followup_answers[self.pending_followup] = answer.strip()
            self.pending_followup = None
            self.current_step += 1
            
            next_q = self.get_current_question()
            if next_q:
                return True, next_q["question"]
            return True, self.messages["complete"]
        
        question = self.get_current_question()
        if not question:
            return True, self.messages["complete"]
        
        answer = answer.strip()
        if not answer and "default" in question:
            answer = question["default"]
        
        # Store answer
        self.answers[question["id"]] = answer
        
        # Process based on question type
        if "options" in question:
            if answer in question["options"]:
                setattr(self.intent, question["field"], question["options"][answer])
            else:
                return False, self.messages["choose_options"].format(
                    options=list(question["options"].keys())
                )
        
        elif "boolean" in question:
            value = answer.lower() in ("y", "yes", "true", "1", "是", "要", "需要")
            setattr(self.intent, question["field"], value)
            
            # Check for follow-up
            if value and "followup" in question:
                self.pending_followup = question["followup"]
                return True, self.messages["followups"][question["followup"]]
        
        elif "processor" in question:
            processor = getattr(self, question["processor"])
            processor(answer)
        
        elif "field" in question:
            setattr(self.intent, question["field"], answer)
        
        self.current_step += 1
        
        # Get next question or finish
        next_q = self.get_current_question()
        if next_q:
            return True, next_q["question"]
        else:
            return True, self.messages["complete"]
    
    def parse_inputs(self, answer: str):
        """Parse comma-separated input variables"""
        if not answer:
            default_name = "input" if self.lang == "en" else "输入"
            self.intent.input_variables = [{"name": default_name, "type": "string", "required": True}]
            return
        
        variables = []
        for var in answer.split(","):
            var = var.strip()
            if var:
                # Check for type annotation like "text:string"
                if ":" in var:
                    name, vtype = var.split(":", 1)
                    variables.append({"name": name.strip(), "type": vtype.strip(), "required": True})
                else:
                    variables.append({"name": var, "type": "string", "required": True})
        
        self.intent.input_variables = variables if variables else [
            {"name": "input" if self.lang == "en" else "输入", "type": "string", "required": True}
        ]
    
    def is_complete(self) -> bool:
        """Check if all questions have been answered"""
        return self.current_step >= len(self.questions) and not self.pending_followup
    
    def build_workflow(self) -> Workflow:
        """Build the workflow based on collected intent"""
        wf = Workflow(
            name=self.intent.name,
            mode=self.intent.mode,
            description=self.intent.description,
        )
        
        # Start node
        start = StartNode(
            title="Start" if self.lang == "en" else "开始",
            variables=self.intent.input_variables
        )
        wf.add_node(start)
        
        last_node = start
        
        # Add condition node if needed
        if self.intent.needs_conditions:
            condition = IfElseNode(
                title="condition" if self.lang == "en" else "条件判断",
                conditions=[{
                    "variable_selector": ["start", self.intent.input_variables[0]["name"]],
                    "comparison_operator": "is-not-empty",
                    "value": "",
                }]
            )
            wf.add_node(condition)
            wf.connect(last_node, condition)
            last_node = condition
        
        # Add HTTP node if needed
        if self.intent.needs_api:
            api_url = self.followup_answers.get("api_details", "https://api.example.com")
            http = HTTPNode(
                title="api_call" if self.lang == "en" else "API调用",
                url=api_url if api_url.startswith("http") else "https://api.example.com",
                method="POST",
            )
            wf.add_node(http)
            if self.intent.needs_conditions:
                wf.connect(last_node, http, source_handle="true")
            else:
                wf.connect(last_node, http)
            last_node = http
        
        # Add code node if needed
        if self.intent.needs_code:
            code_purpose = self.followup_answers.get("code_details", "Process the input")
            code = CodeNode(
                title="process" if self.lang == "en" else "代码处理",
                language="python3",
                code=f"""def main(args):
    # {code_purpose}
    result = args.get("input", "")
    return {{"result": result}}
""",
                variables=[{"variable": "input", "value_selector": ["start", self.intent.input_variables[0]["name"]]}],
                outputs=[{"variable": "result", "type": "string"}],
            )
            wf.add_node(code)
            wf.connect(last_node, code)
            last_node = code
        
        # Add LLM node (most workflows need this)
        if self.intent.needs_llm:
            # Build variable references for prompt
            var_refs = "\n".join([
                f"- {v['name']}: {{{{#start.{v['name']}#}}}}"
                for v in self.intent.input_variables
            ])
            
            if self.intent.llm_prompt:
                prompt = f"""{self.intent.llm_prompt}

Input:
{var_refs}"""
            else:
                prompt = f"""{self.intent.description or 'Process the following input:'}

Input:
{var_refs}

Please provide a helpful response."""
            
            llm = LLMNode(
                title="llm" if self.lang == "en" else "AI处理",
                model={"provider": "openai", "name": "gpt-4", "mode": "chat"},
                prompt=prompt,
                temperature=0.7,
            )
            wf.add_node(llm)
            wf.connect(last_node, llm)
            last_node = llm
        
        # End node (for workflow mode) or Answer node (for chat mode)
        if self.intent.mode == "workflow":
            end = EndNode(
                title="End" if self.lang == "en" else "结束",
                outputs=[{"variable": "result", "value_selector": ["llm" if self.lang == "en" else "AI处理", "text"]}]
            )
            wf.add_node(end)
            wf.connect(last_node, end)
        else:
            answer = AnswerNode(
                title="Answer" if self.lang == "en" else "回复",
                answer="{{#llm.text#}}" if self.lang == "en" else "{{#AI处理.text#}}"
            )
            wf.add_node(answer)
            wf.connect(last_node, answer)
        
        return wf
    
    def start_message(self) -> str:
        """Get the initial message to start the conversation"""
        return self.messages["welcome"] + self.questions[0]["question"]


# ============================================================================
# Workflow Visualization
# ============================================================================

class WorkflowVisualizer:
    """Generate ASCII/text visualization of workflows"""
    
    # Box drawing characters (ASCII-safe)
    BOX_H = "-"
    BOX_V = "|"
    BOX_TL = "+"
    BOX_TR = "+"
    BOX_BL = "+"
    BOX_BR = "+"
    ARROW = "-->"
    ARROW_DOWN = "v"
    
    def __init__(self, workflow: Workflow):
        self.workflow = workflow
        self.node_positions: Dict[str, Tuple[int, int]] = {}
    
    def _make_box(self, text: str, width: int = 20) -> List[str]:
        """Create a box around text"""
        text = text[:width-4] if len(text) > width-4 else text
        padding = width - len(text) - 4
        left_pad = padding // 2
        right_pad = padding - left_pad
        
        lines = [
            self.BOX_TL + self.BOX_H * (width-2) + self.BOX_TR,
            self.BOX_V + " " * left_pad + text + " " * right_pad + " " + self.BOX_V,
            self.BOX_BL + self.BOX_H * (width-2) + self.BOX_BR,
        ]
        return lines
    
    def to_ascii(self) -> str:
        """Generate ASCII representation of the workflow"""
        if not self.workflow.nodes:
            return "(empty workflow)"
        
        # Build adjacency list
        adjacency: Dict[str, List[str]] = {n.id: [] for n in self.workflow.nodes}
        for edge in self.workflow.edges:
            adjacency[edge["source"]].append(edge["target"])
        
        # Find start node
        start_node = None
        for node in self.workflow.nodes:
            if node._node_type == "start":
                start_node = node
                break
        
        if not start_node:
            start_node = self.workflow.nodes[0]
        
        # BFS to get node order
        visited = set()
        order = []
        queue = [start_node.id]
        
        while queue:
            node_id = queue.pop(0)
            if node_id in visited:
                continue
            visited.add(node_id)
            order.append(node_id)
            for next_id in adjacency.get(node_id, []):
                if next_id not in visited:
                    queue.append(next_id)
        
        # Add any unvisited nodes
        for node in self.workflow.nodes:
            if node.id not in visited:
                order.append(node.id)
        
        # Get node by ID
        node_map = {n.id: n for n in self.workflow.nodes}
        
        # Generate visualization
        lines = []
        lines.append(f"Workflow: {self.workflow.name}")
        lines.append(f"Mode: {self.workflow.mode}")
        lines.append("=" * 50)
        lines.append("")
        
        for i, node_id in enumerate(order):
            node = node_map[node_id]
            node_type = node._node_type.upper()
            title = node.title or node_type
            
            # Create node box
            box_lines = self._make_box(f"{title}", 24)
            type_label = f"[{node_type}]"
            
            for line in box_lines:
                lines.append("    " + line)
            lines.append(f"    {type_label:^24}")
            
            # Add arrow if not last
            if i < len(order) - 1:
                lines.append("           |")
                lines.append("           v")
            
            lines.append("")
        
        # Add summary
        lines.append("=" * 50)
        lines.append(f"Nodes: {len(self.workflow.nodes)} | Edges: {len(self.workflow.edges)}")
        
        return "\n".join(lines)
    
    def to_mermaid(self) -> str:
        """Generate Mermaid diagram syntax"""
        lines = ["graph TD"]
        
        # Define nodes
        for node in self.workflow.nodes:
            node_type = node._node_type
            title = node.title or node_type
            
            # Different shapes for different types
            if node_type == "start":
                lines.append(f"    {node.id}(({title}))")
            elif node_type in ("end", "answer"):
                lines.append(f"    {node.id}[/{title}/]")
            elif node_type == "if-else":
                lines.append(f"    {node.id}{{{title}}}")
            elif node_type == "llm":
                lines.append(f"    {node.id}[[\"{title}\"]]")
            else:
                lines.append(f"    {node.id}[\"{title}\"]")
        
        lines.append("")
        
        # Define edges
        for edge in self.workflow.edges:
            source = edge["source"]
            target = edge["target"]
            handle = edge.get("sourceHandle", "")
            
            if handle in ("true", "false"):
                lines.append(f"    {source} -->|{handle}| {target}")
            else:
                lines.append(f"    {source} --> {target}")
        
        return "\n".join(lines)
    
    def to_tree(self) -> str:
        """Generate tree-style visualization"""
        if not self.workflow.nodes:
            return "(empty workflow)"
        
        # Build adjacency list
        adjacency: Dict[str, List[Tuple[str, str]]] = {n.id: [] for n in self.workflow.nodes}
        for edge in self.workflow.edges:
            handle = edge.get("sourceHandle", "")
            adjacency[edge["source"]].append((edge["target"], handle))
        
        # Find start node
        start_node = None
        for node in self.workflow.nodes:
            if node._node_type == "start":
                start_node = node
                break
        
        if not start_node:
            start_node = self.workflow.nodes[0]
        
        node_map = {n.id: n for n in self.workflow.nodes}
        
        # Generate tree
        lines = []
        lines.append(f"{self.workflow.name} ({self.workflow.mode})")
        lines.append("")
        
        visited = set()
        
        def render_node(node_id: str, prefix: str = "", is_last: bool = True):
            if node_id in visited:
                return
            visited.add(node_id)
            
            node = node_map[node_id]
            connector = "`-- " if is_last else "|-- "
            node_type = node._node_type
            title = node.title or node_type
            
            # Node type icons
            icons = {
                "start": "[>]",
                "end": "[=]",
                "answer": "[<]",
                "llm": "[*]",
                "http-request": "[@]",
                "code": "[#]",
                "if-else": "[?]",
                "knowledge-retrieval": "[K]",
                "template-transform": "[T]",
                "iteration": "[~]",
            }
            icon = icons.get(node_type, "[+]")
            
            lines.append(f"{prefix}{connector}{icon} {title}")
            
            children = adjacency.get(node_id, [])
            child_prefix = prefix + ("    " if is_last else "|   ")
            
            for i, (child_id, handle) in enumerate(children):
                is_child_last = (i == len(children) - 1)
                if handle:
                    lines.append(f"{child_prefix}    ({handle})")
                render_node(child_id, child_prefix, is_child_last)
        
        render_node(start_node.id)
        
        return "\n".join(lines)


def visualize(workflow: Workflow, format: str = "ascii") -> str:
    """
    Generate a visualization of the workflow.
    
    Args:
        workflow: The workflow to visualize
        format: Output format - "ascii", "tree", or "mermaid"
    
    Returns:
        String visualization
    """
    viz = WorkflowVisualizer(workflow)
    
    if format == "mermaid":
        return viz.to_mermaid()
    elif format == "tree":
        return viz.to_tree()
    else:
        return viz.to_ascii()


# ============================================================================
# AI-powered Builder with Multi-turn Conversation
# ============================================================================

class AIWorkflowBuilder:
    """
    AI-powered workflow builder using LLM for intent recognition.
    
    Supports multi-turn conversation to gather requirements.
    """
    
    SYSTEM_PROMPT = """You are a workflow design assistant. Your job is to understand user requirements and convert them into a structured workflow specification.

When a user describes what they want, extract:
1. Workflow name
2. Purpose/description  
3. Required inputs (variables the user needs to provide)
4. Processing steps needed:
   - LLM calls (for AI processing)
   - API calls (for external services)
   - Code execution (for data processing)
   - Conditions (for branching logic)
   - Knowledge retrieval (for RAG)
5. Expected outputs

If the user's description is unclear or missing important details, ask clarifying questions.
Set "needs_clarification" to true and provide your questions in "clarification_questions".

Respond in JSON format:
{
    "needs_clarification": false,
    "clarification_questions": [],
    "workflow": {
        "name": "Workflow Name",
        "description": "What it does",
        "mode": "workflow",
        "inputs": [{"name": "var_name", "type": "string", "required": true, "description": "what this is"}],
        "steps": [
            {"type": "llm", "purpose": "what the LLM should do", "prompt_hint": "key instructions"},
            {"type": "http", "purpose": "why call API", "url_hint": "example.com/api"},
            {"type": "code", "purpose": "what to process", "language": "python3"},
            {"type": "condition", "purpose": "when to branch", "condition_hint": "if X then Y"},
            {"type": "knowledge", "purpose": "what to retrieve"}
        ],
        "outputs": [{"name": "result", "description": "what this contains"}]
    }
}

Only include steps that are actually needed. Be concise."""

    SYSTEM_PROMPT_ZH = """你是一个工作流设计助手。你的任务是理解用户需求，将其转换为结构化的工作流规范。

当用户描述他们的需求时，提取以下信息：
1. 工作流名称
2. 用途/描述
3. 需要的输入（用户需要提供的变量）
4. 处理步骤：
   - LLM 调用（AI 处理）
   - API 调用（外部服务）
   - 代码执行（数据处理）
   - 条件判断（分支逻辑）
   - 知识检索（RAG）
5. 预期输出

如果用户描述不清楚或缺少重要细节，请提出澄清问题。
将 "needs_clarification" 设为 true，并在 "clarification_questions" 中提供你的问题。

用 JSON 格式回复：
{
    "needs_clarification": false,
    "clarification_questions": [],
    "workflow": {
        "name": "工作流名称",
        "description": "功能描述",
        "mode": "workflow",
        "inputs": [{"name": "变量名", "type": "string", "required": true, "description": "说明"}],
        "steps": [
            {"type": "llm", "purpose": "LLM 要做什么", "prompt_hint": "关键指令"},
            {"type": "http", "purpose": "为什么调 API", "url_hint": "example.com/api"},
            {"type": "code", "purpose": "处理什么", "language": "python3"},
            {"type": "condition", "purpose": "什么条件", "condition_hint": "如果 X 则 Y"},
            {"type": "knowledge", "purpose": "检索什么"}
        ],
        "outputs": [{"name": "result", "description": "包含什么"}]
    }
}

只包含实际需要的步骤。保持简洁。"""

    def __init__(
        self, 
        api_key: Optional[str] = None, 
        base_url: Optional[str] = None,
        lang: str = "en"
    ):
        """
        Initialize with OpenAI-compatible API.
        
        Args:
            api_key: API key (or set OPENAI_API_KEY env var)
            base_url: Optional base URL for compatible APIs
            lang: Language ("en" or "zh")
        """
        self.api_key = api_key
        self.base_url = base_url
        self.lang = lang
        self._client = None
        
        # Conversation history for multi-turn
        self.conversation: List[Dict[str, str]] = []
        self.current_intent: Optional[Dict[str, Any]] = None
    
    @property
    def client(self):
        """Lazy-load OpenAI client"""
        if self._client is None:
            try:
                from openai import OpenAI
            except ImportError:
                raise ImportError(
                    "OpenAI package required for AI builder. "
                    "Install with: pip install dify-workflow-generator[interactive]"
                )
            
            kwargs = {}
            if self.api_key:
                kwargs["api_key"] = self.api_key
            if self.base_url:
                kwargs["base_url"] = self.base_url
            
            self._client = OpenAI(**kwargs)
        return self._client
    
    def chat(self, message: str, model: str = "gpt-4") -> Tuple[bool, str, Optional[Workflow]]:
        """
        Process a message in the conversation.
        
        Args:
            message: User's message
            model: LLM model to use
            
        Returns:
            (is_complete, response_message, workflow_if_complete)
        """
        # Add user message to conversation
        self.conversation.append({"role": "user", "content": message})
        
        # Get system prompt based on language
        system_prompt = self.SYSTEM_PROMPT_ZH if self.lang == "zh" else self.SYSTEM_PROMPT
        
        # Call LLM
        response = self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                *self.conversation
            ],
            temperature=0.3,
            response_format={"type": "json_object"},
        )
        
        content = response.choices[0].message.content
        self.conversation.append({"role": "assistant", "content": content})
        
        try:
            result = json.loads(content)
        except json.JSONDecodeError:
            return False, "Sorry, I couldn't understand that. Please try again.", None
        
        # Check if clarification needed
        if result.get("needs_clarification"):
            questions = result.get("clarification_questions", [])
            if self.lang == "zh":
                response_text = "我需要一些更多信息：\n\n" + "\n".join(f"- {q}" for q in questions)
            else:
                response_text = "I need a bit more information:\n\n" + "\n".join(f"- {q}" for q in questions)
            return False, response_text, None
        
        # Build workflow
        self.current_intent = result.get("workflow", {})
        workflow = self._build_from_intent(self.current_intent)
        
        if self.lang == "zh":
            response_text = f"已生成工作流：{workflow.name}\n\n" + visualize(workflow, "tree")
        else:
            response_text = f"Generated workflow: {workflow.name}\n\n" + visualize(workflow, "tree")
        
        return True, response_text, workflow
    
    def _build_from_intent(self, intent: Dict[str, Any]) -> Workflow:
        """Build workflow from parsed intent"""
        wf = Workflow(
            name=intent.get("name", "Generated Workflow"),
            mode=intent.get("mode", "workflow"),
            description=intent.get("description", ""),
        )
        
        # Add start node with inputs
        inputs = intent.get("inputs", [{"name": "input", "type": "string", "required": True}])
        start = StartNode(title="Start", variables=inputs)
        wf.add_node(start)
        
        last_node = start
        llm_node = None
        
        # Add processing steps
        for i, step in enumerate(intent.get("steps", [])):
            step_type = step.get("type", "llm")
            
            if step_type == "llm":
                input_refs = "\n".join([
                    f"{inp.get('name', 'input')}: {{{{#start.{inp.get('name', 'input')}#}}}}"
                    for inp in inputs
                ])
                
                prompt = f"""{step.get('prompt_hint', step.get('purpose', 'Process the input'))}

{input_refs}"""
                
                node = LLMNode(
                    title=f"llm_{i}" if i > 0 else "llm",
                    model={"provider": "openai", "name": "gpt-4", "mode": "chat"},
                    prompt=prompt,
                )
                llm_node = node
                
            elif step_type == "http":
                node = HTTPNode(
                    title=f"api_{i}",
                    url=step.get("url_hint", "https://api.example.com"),
                    method=step.get("method", "GET"),
                )
                
            elif step_type == "code":
                node = CodeNode(
                    title=f"code_{i}",
                    language=step.get("language", "python3"),
                    code=f"""def main(args):
    # {step.get('purpose', 'Process data')}
    return {{"result": args}}
""",
                )
                
            elif step_type == "condition":
                node = IfElseNode(
                    title=f"condition_{i}",
                    conditions=[{
                        "variable_selector": ["start", inputs[0].get("name", "input")],
                        "comparison_operator": "is-not-empty",
                        "value": "",
                    }]
                )
                
            elif step_type == "knowledge":
                node = KnowledgeNode(
                    title=f"knowledge_{i}",
                    query_variable_selector=["start", inputs[0].get("name", "input")],
                )
            
            else:
                continue
            
            wf.add_node(node)
            wf.connect(last_node, node)
            last_node = node
        
        # Add end/answer node
        output_source = ["llm", "text"] if llm_node else ["start", inputs[0].get("name", "input")]
        
        if intent.get("mode") == "advanced-chat":
            end = AnswerNode(
                title="Answer",
                answer=f"{{{{#{output_source[0]}.{output_source[1]}#}}}}"
            )
        else:
            end = EndNode(
                title="End",
                outputs=[{"variable": "result", "value_selector": output_source}]
            )
        
        wf.add_node(end)
        wf.connect(last_node, end)
        
        return wf
    
    def reset(self):
        """Reset conversation state"""
        self.conversation = []
        self.current_intent = None
    
    def parse_intent(self, user_description: str, model: str = "gpt-4") -> Dict[str, Any]:
        """
        Use LLM to parse user's natural language description into structured intent.
        (For backward compatibility)
        """
        _, _, workflow = self.chat(user_description, model)
        return self.current_intent or {}
    
    def build_from_description(
        self,
        description: str,
        model: str = "gpt-4",
    ) -> Workflow:
        """
        Build a complete workflow from a natural language description.
        (For backward compatibility)
        """
        complete, _, workflow = self.chat(description, model)
        if workflow:
            return workflow
        
        # If needs clarification, build with what we have
        if self.current_intent:
            return self._build_from_intent(self.current_intent)
        
        # Fallback to basic workflow
        return Workflow(name="Generated Workflow", mode="workflow")


def interactive_session(lang: str = "en"):
    """Run an interactive CLI session for building workflows"""
    print("=" * 50)
    if lang == "zh":
        print("  Dify 工作流交互式生成器")
    else:
        print("  Dify Workflow Interactive Builder")
    print("=" * 50)
    print()
    
    builder = InteractiveBuilder(lang=lang)
    print(builder.start_message())
    
    while not builder.is_complete():
        try:
            answer = input("\n> ").strip()
            success, message = builder.process_answer(answer)
            print(f"\n{message}")
        except KeyboardInterrupt:
            print(f"\n\n{builder.messages['cancelled']}")
            return None
    
    # Build and visualize
    workflow = builder.build_workflow()
    
    print("\n" + "=" * 50)
    print(visualize(workflow, "tree"))
    print("=" * 50)
    
    # Ask for export path
    print(f"\n{builder.messages['export_prompt']}")
    path = input(builder.messages['export_default']).strip() or "workflow.yml"
    
    workflow.export(path)
    print(f"\n{builder.messages['done'].format(path=path)}")
    
    return workflow
