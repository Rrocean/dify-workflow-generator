# Dify Workflow Generator

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

A Python library to programmatically generate [Dify](https://dify.ai) workflow DSL files. Create complex AI workflows with code, natural language, or interactive guidance.

## Features

- 🔧 Generate Dify-compatible YAML DSL from Python code
- 🤖 **AI-powered generation** - Describe what you want in natural language
- 💬 **Interactive builder** - Guided step-by-step workflow creation
- 🧩 Full support for all 14 Dify node types
- 📤 Export workflows ready for direct import into Dify
- ✅ Built-in validation for node configurations
- 🖥️ CLI tool for automation

## Installation

```bash
# Basic installation
pip install -e .

# With AI generation support
pip install -e ".[interactive]"
```

## Quick Start

### 1. Python API

```python
from dify_workflow import Workflow, LLMNode, StartNode, EndNode

wf = Workflow(name="My AI Workflow", mode="workflow")

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

wf.add_nodes([start, llm, end])
wf.connect(start, llm)
wf.connect(llm, end)
wf.export("my_workflow.yml")
```

### 2. Natural Language (AI-powered)

```python
from dify_workflow import from_description

# Just describe what you want!
wf = from_description(
    "Create a translation workflow that takes text and target language as inputs, "
    "uses GPT-4 to translate, and returns the result"
)
wf.export("translator.yml")
```

Or via CLI:
```bash
dify-workflow ai "Create a customer support chatbot that answers questions about products"
```

### 3. Interactive Builder

```bash
dify-workflow interactive
```

The interactive mode guides you through creating a workflow with questions:
```
What would you like to name this workflow?
> Customer Support Bot

What should this workflow do?
> Answer customer questions about our products

What inputs does the user need to provide?
> question, product_category

...
```

## CLI Commands

```bash
# Interactive guided creation
dify-workflow interactive

# AI-powered generation from description
dify-workflow ai "Your workflow description" -o output.yml

# Build from Python file
dify-workflow build my_workflow.py -o workflow.yml

# Validate existing workflow
dify-workflow validate workflow.yml
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

condition = IfElseNode(
    title="check_type",
    conditions=[{
        "variable_selector": ["start", "query"],
        "comparison_operator": "contains",
        "value": "code"
    }]
)

code_llm = LLMNode(title="code_response", prompt="You are a coding expert...")
general_llm = LLMNode(title="general_response", prompt="You are a helpful assistant...")
end = EndNode(...)

wf.add_nodes([start, condition, code_llm, general_llm, end])
wf.connect(start, condition)
wf.connect(condition, code_llm, source_handle="true")
wf.connect(condition, general_llm, source_handle="false")
wf.connect(code_llm, end)
wf.connect(general_llm, end)
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
workflow:
  graph:
    nodes: [...]
    edges: [...]
  features: {}
  environment_variables: []
  conversation_variables: []
```

## Variable References

Dify uses specific syntax for referencing variables:

- `{{#node_id.variable#}}` - In prompts/templates
- `["node_id", "variable"]` - In value_selector fields

## License

MIT

## Contributing

Contributions welcome! Please read the contributing guidelines first.

## Links

- [Dify Documentation](https://docs.dify.ai)
- [Dify GitHub](https://github.com/langgenius/dify)
