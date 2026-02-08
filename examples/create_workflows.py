"""
Example: Create a translation workflow that can be imported into Dify
"""

from dify_workflow import (
    Workflow,
    StartNode,
    EndNode,
    LLMNode,
)


def create_translator_workflow():
    """Create a simple translation workflow"""
    
    # Create workflow (mode can be "workflow" or "advanced-chat")
    wf = Workflow(
        name="Translator",
        mode="workflow",
        description="Translate text to any language using AI",
        icon="🌐",
        icon_background="#E4FBCC",
    )
    
    # Define start node with input variables
    start = StartNode(
        title="Start",
        variables=[
            {
                "name": "text",
                "type": "string",
                "required": True,
                "label": "Text to translate",
                "max_length": 4096,
            },
            {
                "name": "target_language",
                "type": "string",
                "required": True,
                "label": "Target Language",
                "default": "English",
            },
        ]
    )
    start.id = "start"  # Set explicit ID for easier referencing
    
    # LLM node for translation
    translate = LLMNode(
        title="translate",
        model={
            "provider": "openai",
            "name": "gpt-4",
            "mode": "chat",
            "completion_params": {
                "temperature": 0.3,
                "max_tokens": 4096,
            }
        },
        prompt="""Translate the following text to {{#start.target_language#}}.

Text to translate:
{{#start.text#}}

Important:
- Output ONLY the translation, nothing else
- Preserve the original formatting
- Maintain the original tone and style""",
        temperature=0.3,
    )
    
    # End node with output
    end = EndNode(
        title="End",
        outputs=[
            {
                "variable": "translation",
                "value_selector": ["translate", "text"],
            }
        ]
    )
    
    # Build the workflow
    wf.add_nodes([start, translate, end])
    wf.connect(start, translate)
    wf.connect(translate, end)
    
    # Validate
    issues = wf.validate()
    if issues:
        print("Validation issues:")
        for issue in issues:
            print(f"  - {issue}")
    
    return wf


def create_chatbot_workflow():
    """Create an advanced chat workflow with memory"""
    from dify_workflow import AnswerNode
    
    wf = Workflow(
        name="Smart Chatbot",
        mode="advanced-chat",
        description="An AI chatbot with context awareness",
        icon="💬",
        icon_background="#D3F8DF",
    )
    
    # Start node for chat mode
    start = StartNode(
        title="Start",
        variables=[
            {
                "name": "query",
                "type": "string",
                "required": True,
                "label": "User message",
            },
        ]
    )
    start.id = "start"
    
    # LLM with conversation memory
    llm = LLMNode(
        title="assistant",
        model={
            "provider": "openai",
            "name": "gpt-4",
            "mode": "chat",
            "completion_params": {
                "temperature": 0.7,
            }
        },
        prompt="""You are a helpful AI assistant. Respond to the user's message.

User: {{#start.query#}}""",
        memory={
            "role_prefix": {
                "user": "User",
                "assistant": "Assistant",
            },
            "window": {
                "enabled": True,
                "size": 20,
            }
        }
    )
    
    # Answer node for streaming response
    answer = AnswerNode(
        title="Answer",
        answer="{{#assistant.text#}}",
    )
    
    wf.add_nodes([start, llm, answer])
    wf.connect(start, llm)
    wf.connect(llm, answer)
    
    return wf


def create_conditional_workflow():
    """Create a workflow with conditional branching"""
    from dify_workflow import IfElseNode
    
    wf = Workflow(
        name="Smart Router",
        mode="workflow",
        description="Routes queries to appropriate handlers",
        icon="🔀",
        icon_background="#FFE4E1",
    )
    
    start = StartNode(
        title="Start",
        variables=[
            {"name": "query", "type": "string", "required": True},
        ]
    )
    start.id = "start"
    
    # Condition to check if query is about code
    condition = IfElseNode(
        title="is_code_question",
        conditions=[
            {
                "variable_selector": ["start", "query"],
                "comparison_operator": "contains",
                "value": "code",
            }
        ]
    )
    
    # Two different LLM responses
    code_llm = LLMNode(
        title="code_expert",
        prompt="You are a coding expert. Answer this question:\n{{#start.query#}}",
        temperature=0.2,
    )
    
    general_llm = LLMNode(
        title="general_assistant",
        prompt="You are a helpful assistant. Answer this question:\n{{#start.query#}}",
        temperature=0.7,
    )
    
    end = EndNode(
        title="End",
        outputs=[
            {"variable": "result", "value_selector": ["code_expert", "text"]},
        ]
    )
    
    wf.add_nodes([start, condition, code_llm, general_llm, end])
    wf.connect(start, condition)
    wf.connect(condition, code_llm, source_handle="true")
    wf.connect(condition, general_llm, source_handle="false")
    wf.connect(code_llm, end)
    wf.connect(general_llm, end)
    
    return wf


if __name__ == "__main__":
    import os
    
    # Create examples directory if it doesn't exist
    os.makedirs("examples/output", exist_ok=True)
    
    # Create and export translator workflow
    translator = create_translator_workflow()
    translator.export("examples/output/translator.yml")
    print(f"Created: {translator}")
    
    # Create and export chatbot workflow
    chatbot = create_chatbot_workflow()
    chatbot.export("examples/output/chatbot.yml")
    print(f"Created: {chatbot}")
    
    # Create and export conditional workflow
    router = create_conditional_workflow()
    router.export("examples/output/router.yml")
    print(f"Created: {router}")
    
    print("\n[DONE] All workflows exported to examples/output/")
    print("You can import these YAML files directly into Dify!")
