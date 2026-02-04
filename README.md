# Dify Workflow Generator

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

A Python library to programmatically generate [Dify](https://dify.ai) workflow DSL files. Create complex AI workflows with code and import them directly into Dify.

## Features

- 🔧 Generate Dify-compatible YAML DSL from Python code
- 🧩 Full support for all Dify node types (Start, End, LLM, HTTP, Code, Condition, etc.)
- 📤 Export workflows ready for direct import into Dify
- 🔗 Fluent API for easy node connections
- ✅ Built-in validation for node configurations
- 🎯 Auto-positioning of nodes on canvas

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

```python
from dify_workflow import Workflow, LLMNode, StartNode, EndNode

# Create a workflow
wf = Workflow(
    name="My AI Workflow",
    mode="workflow"  # or "advanced-chat"
)

# Add nodes
start = StartNode(variables=[
    {"name": "query", "type": "string", "required": True}
])
llm = LLMNode(
    title="AI Response",
    model={"provider": "openai", "name": "gpt-4"},
    prompt="Please respond to: {{#start.query#}}"
)
end = EndNode(outputs=[
    {"variable": "result", "value_selector": ["llm", "text"]}
])

# Build workflow
wf.add_nodes([start, llm, end])
wf.connect(start, llm)
wf.connect(llm, end)

# Export to YAML (ready for Dify import)
wf.export("my_workflow.yml")
```

## DSL Format

This library generates Dify DSL version `0.5.0` compatible files:

```yaml
version: "0.5.0"
kind: app
app:
  name: My Workflow
  mode: workflow
  icon: "🤖"
  icon_background: "#FFEAD5"
  description: ""
workflow:
  graph:
    nodes: [...]
    edges: [...]
  features: {}
  environment_variables: []
  conversation_variables: []
```

## Supported Node Types

| Node Type | Class | Description |
|-----------|-------|-------------|
| Start | `StartNode` | Workflow entry point with input variables |
| End | `EndNode` | Workflow output |
| Answer | `AnswerNode` | Streaming response for chat apps |
| LLM | `LLMNode` | Large Language Model call |
| HTTP Request | `HTTPNode` | External API calls |
| Code | `CodeNode` | Python/JavaScript execution |
| If/Else | `IfElseNode` | Conditional branching |
| Variable Aggregator | `VariableAggregatorNode` | Combine variables |
| Template Transform | `TemplateNode` | Jinja2 template processing |
| Iteration | `IterationNode` | Loop over arrays |
| Knowledge Retrieval | `KnowledgeNode` | Query knowledge bases |
| Question Classifier | `QuestionClassifierNode` | Route based on intent |
| Parameter Extractor | `ParameterExtractorNode` | Extract structured data |
| Tool | `ToolNode` | Call external tools |

## Examples

### Translation Workflow

```python
from dify_workflow import *

wf = Workflow("Translator", mode="workflow")

start = StartNode(variables=[
    {"name": "text", "type": "string", "required": True},
    {"name": "target_lang", "type": "string", "default": "English"}
])

translate = LLMNode(
    title="translate",
    model={"provider": "openai", "name": "gpt-4"},
    prompt="""Translate to {{#start.target_lang#}}:
{{#start.text#}}

Output ONLY the translation.""",
    temperature=0.3
)

end = EndNode(outputs=[
    {"variable": "translation", "value_selector": ["translate", "text"]}
])

wf.add_nodes([start, translate, end])
wf.connect(start, translate)
wf.connect(translate, end)
wf.export("translator.yml")
```

### Conditional Workflow

```python
from dify_workflow import *

wf = Workflow("Router", mode="workflow")

start = StartNode(variables=[
    {"name": "query", "type": "string", "required": True}
])

# Condition based on query content
condition = IfElseNode(
    title="check_type",
    conditions=[{
        "variable_selector": ["start", "query"],
        "comparison_operator": "contains",
        "value": "code"
    }]
)

# Two different LLM responses
code_llm = LLMNode(title="code_response", ...)
general_llm = LLMNode(title="general_response", ...)

end = EndNode(...)

wf.add_nodes([start, condition, code_llm, general_llm, end])
wf.connect(start, condition)
wf.connect(condition, code_llm, source_handle="true")
wf.connect(condition, general_llm, source_handle="false")
wf.connect(code_llm, end)
wf.connect(general_llm, end)
```

## API Reference

### Workflow

```python
Workflow(
    name: str,
    mode: str = "workflow",  # "workflow" or "advanced-chat"
    description: str = "",
    icon: str = "🤖",
    icon_background: str = "#FFEAD5"
)
```

### Node Methods

- `add_node(node)` - Add a single node
- `add_nodes([nodes])` - Add multiple nodes
- `connect(source, target, source_handle="source", target_handle="target")` - Connect nodes
- `export(path)` - Export to YAML file
- `to_yaml()` - Get YAML string
- `to_dict()` - Get dictionary

## Variable References

Dify uses a specific syntax for referencing variables:

- `{{#node_id.variable#}}` - In prompts/templates
- `["node_id", "variable"]` - In value_selector fields

## License

MIT

## Contributing

Contributions welcome! Please read the contributing guidelines first.

## Links

- [Dify Documentation](https://docs.dify.ai)
- [Dify GitHub](https://github.com/langgenius/dify)
