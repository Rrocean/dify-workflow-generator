# Dify Workflow Generator

A lightweight Python tool to programmatically generate Dify workflows.

## Features

- 🔧 Generate Dify workflow YAML/JSON from Python code
- 🧩 Support for common node types (LLM, HTTP, Code, Condition, etc.)
- 📤 Export workflows compatible with Dify import
- 🔗 Easy node connection with fluent API

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

```python
from dify_workflow import Workflow, LLMNode, HTTPNode

# Create a workflow
wf = Workflow("My Workflow")

# Add nodes
llm = LLMNode("chat", model="gpt-4", prompt="Hello {{input}}")
http = HTTPNode("api_call", url="https://api.example.com", method="POST")

# Connect nodes
wf.add_node(llm)
wf.add_node(http)
wf.connect(llm, http)

# Export
wf.export("my_workflow.yml")
```

## Supported Node Types

| Node Type | Class | Description |
|-----------|-------|-------------|
| Start | `StartNode` | Workflow entry point |
| LLM | `LLMNode` | Large Language Model call |
| HTTP Request | `HTTPNode` | API calls |
| Code | `CodeNode` | Python/JavaScript execution |
| Condition | `ConditionNode` | If/else branching |
| Variable | `VariableNode` | Variable aggregation |
| End | `EndNode` | Workflow output |

## Example: Translation Workflow

```python
from dify_workflow import *

wf = Workflow("Translator")

start = StartNode(inputs=["text", "target_lang"])
translate = LLMNode(
    "translate",
    model="gpt-4",
    prompt="Translate the following to {{target_lang}}:\n{{text}}"
)
end = EndNode(outputs=["result"])

wf.add_nodes([start, translate, end])
wf.connect(start, translate)
wf.connect(translate, end)

wf.export("translator.yml")
```

## License

MIT
