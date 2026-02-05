"""
Interactive Workflow Builder - AI-powered conversational workflow generator

This module provides an interactive interface that guides users through
creating Dify workflows using natural language.
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


class InteractiveBuilder:
    """
    Guide users through workflow creation with questions.
    
    Can work standalone (text-based) or with an LLM for natural language understanding.
    """
    
    QUESTIONS = [
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
        },
        {
            "id": "needs_code",
            "question": "Does this workflow need custom code processing? (y/n)",
            "boolean": True,
            "field": "needs_code",
        },
        {
            "id": "needs_conditions",
            "question": "Does this workflow need conditional branching (if/else)? (y/n)",
            "boolean": True,
            "field": "needs_conditions",
        },
    ]
    
    def __init__(self):
        self.intent = WorkflowIntent()
        self.current_step = 0
        self.answers: Dict[str, str] = {}
    
    def get_current_question(self) -> Optional[Dict[str, Any]]:
        """Get the current question to ask"""
        if self.current_step >= len(self.QUESTIONS):
            return None
        return self.QUESTIONS[self.current_step]
    
    def process_answer(self, answer: str) -> Tuple[bool, str]:
        """
        Process user's answer to current question.
        
        Returns: (success, next_message)
        """
        question = self.get_current_question()
        if not question:
            return True, "All questions answered!"
        
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
                return False, f"Please choose from the options: {list(question['options'].keys())}"
        
        elif "boolean" in question:
            value = answer.lower() in ("y", "yes", "true", "1")
            setattr(self.intent, question["field"], value)
        
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
            return True, "Great! I have all the information needed. Generating your workflow..."
    
    def parse_inputs(self, answer: str):
        """Parse comma-separated input variables"""
        if not answer:
            self.intent.input_variables = [{"name": "input", "type": "string", "required": True}]
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
        
        self.intent.input_variables = variables if variables else [{"name": "input", "type": "string", "required": True}]
    
    def is_complete(self) -> bool:
        """Check if all questions have been answered"""
        return self.current_step >= len(self.QUESTIONS)
    
    def build_workflow(self) -> Workflow:
        """Build the workflow based on collected intent"""
        wf = Workflow(
            name=self.intent.name,
            mode=self.intent.mode,
            description=self.intent.description,
        )
        
        # Start node
        start = StartNode(
            title="Start",
            variables=self.intent.input_variables
        )
        wf.add_node(start)
        
        last_node = start
        
        # Add condition node if needed
        if self.intent.needs_conditions:
            condition = IfElseNode(
                title="condition",
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
            http = HTTPNode(
                title="api_call",
                url="https://api.example.com/endpoint",
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
            code = CodeNode(
                title="process",
                language="python3",
                code="""def main(args):
    # Process the input
    result = args.get("input", "")
    return {"result": result}
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
            
            llm = LLMNode(
                title="llm",
                model={"provider": "openai", "name": "gpt-4", "mode": "chat"},
                prompt=f"""{self.intent.description or 'Process the following input:'}

Input:
{var_refs}

Please provide a helpful response.""",
                temperature=0.7,
            )
            wf.add_node(llm)
            wf.connect(last_node, llm)
            last_node = llm
        
        # End node (for workflow mode) or Answer node (for chat mode)
        if self.intent.mode == "workflow":
            end = EndNode(
                title="End",
                outputs=[{"variable": "result", "value_selector": ["llm", "text"]}]
            )
            wf.add_node(end)
            wf.connect(last_node, end)
        else:
            answer = AnswerNode(
                title="Answer",
                answer="{{#llm.text#}}"
            )
            wf.add_node(answer)
            wf.connect(last_node, answer)
        
        return wf
    
    def start_message(self) -> str:
        """Get the initial message to start the conversation"""
        return """Welcome to the Dify Workflow Builder!

I'll help you create a workflow step by step. Just answer a few questions.

""" + self.QUESTIONS[0]["question"]


class AIWorkflowBuilder:
    """
    AI-powered workflow builder using LLM for intent recognition.
    
    This uses an LLM to understand natural language descriptions and
    automatically generate appropriate workflows.
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

Respond in JSON format:
{
    "name": "Workflow Name",
    "description": "What it does",
    "mode": "workflow" or "advanced-chat",
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

Be concise. Only include steps that are actually needed."""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize with OpenAI-compatible API.
        
        Args:
            api_key: API key (or set OPENAI_API_KEY env var)
            base_url: Optional base URL for compatible APIs
        """
        self.api_key = api_key
        self.base_url = base_url
        self._client = None
    
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
    
    def parse_intent(self, user_description: str, model: str = "gpt-4") -> Dict[str, Any]:
        """
        Use LLM to parse user's natural language description into structured intent.
        """
        response = self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": user_description}
            ],
            temperature=0.3,
            response_format={"type": "json_object"},
        )
        
        content = response.choices[0].message.content
        return json.loads(content)
    
    def build_from_description(
        self,
        description: str,
        model: str = "gpt-4",
    ) -> Workflow:
        """
        Build a complete workflow from a natural language description.
        
        Args:
            description: Natural language description of desired workflow
            model: LLM model to use for parsing
            
        Returns:
            Generated Workflow object
        """
        # Parse intent
        intent = self.parse_intent(description, model)
        
        # Create workflow
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
                # Build prompt from inputs
                input_refs = "\n".join([
                    f"{inp['name']}: {{{{#start.{inp['name']}#}}}}"
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
                        "variable_selector": ["start", inputs[0]["name"]],
                        "comparison_operator": "is-not-empty",
                        "value": "",
                    }]
                )
                
            elif step_type == "knowledge":
                node = KnowledgeNode(
                    title=f"knowledge_{i}",
                    query_variable_selector=["start", inputs[0]["name"]],
                )
            
            else:
                continue
            
            wf.add_node(node)
            wf.connect(last_node, node)
            last_node = node
        
        # Add end/answer node
        output_source = ["llm", "text"] if llm_node else ["start", inputs[0]["name"]]
        
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


def interactive_session():
    """Run an interactive CLI session for building workflows"""
    print("=" * 50)
    print("  Dify Workflow Interactive Builder")
    print("=" * 50)
    print()
    
    builder = InteractiveBuilder()
    print(builder.start_message())
    
    while not builder.is_complete():
        try:
            answer = input("\n> ").strip()
            success, message = builder.process_answer(answer)
            print(f"\n{message}")
        except KeyboardInterrupt:
            print("\n\nCancelled.")
            return None
    
    # Build and export
    workflow = builder.build_workflow()
    
    print(f"\nWorkflow created: {workflow}")
    
    # Ask for export path
    print("\nWhere would you like to save the workflow?")
    path = input("Path (default: workflow.yml): ").strip() or "workflow.yml"
    
    workflow.export(path)
    print(f"\nDone! Import '{path}' into Dify to use your workflow.")
    
    return workflow
