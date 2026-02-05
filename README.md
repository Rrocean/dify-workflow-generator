# Dify Workflow Generator

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

A Python library to programmatically generate [Dify](https://dify.ai) workflow DSL files. Create complex AI workflows with code, natural language, or interactive guidance.

## Features

- 🔧 Generate Dify-compatible YAML DSL from Python code
- 🤖 **AI-powered generation** - Describe what you want in natural language
- 💬 **Interactive builder** - Guided step-by-step workflow creation
- 🌐 **Multi-language** - English and Chinese interface support
- 🔄 **Multi-turn conversation** - AI asks follow-up questions for clarity
- 📊 **Visualization** - Preview workflows as ASCII art, tree, or Mermaid diagrams
- 🧩 Full support for all 14 Dify node types
- ✅ Built-in validation

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
from dify_workflow import Workflow, LLMNode, StartNode, EndNode, visualize

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

# Preview before export
print(visualize(wf, "tree"))

wf.export("my_workflow.yml")
```

### 2. Natural Language (AI-powered)

```python
from dify_workflow import from_description

# Just describe what you want!
wf = from_description(
    "创建一个翻译工作流，输入文本和目标语言，用 GPT-4 翻译后返回结果",
    lang="zh"
)
wf.export("translator.yml")
```

Or via CLI with multi-turn conversation:
```bash
dify-workflow chat --lang zh
```

### 3. Interactive Builder (中文支持)

```bash
# English
dify-workflow interactive

# 中文
dify-workflow interactive --lang zh
```

Example session:
```
欢迎使用 Dify 工作流生成器！

请给这个工作流起个名字：
> 翻译助手

这个工作流要做什么？
> 将文本翻译成指定语言

用户需要提供哪些输入？
> 文本, 目标语言

需要调用外部 API 吗？(y/n)
> n

...

翻译助手 (workflow)

`-- [>] 开始
    `-- [*] AI处理
        `-- [=] 结束
```

## CLI Commands

```bash
# Interactive guided creation (with language option)
dify-workflow interactive
dify-workflow interactive --lang zh

# AI chat session (multi-turn conversation)
dify-workflow chat
dify-workflow chat --lang zh

# One-shot AI generation
dify-workflow ai "Create a customer support chatbot" -o support.yml

# Build from Python file
dify-workflow build my_workflow.py -o workflow.yml

# Validate existing workflow
dify-workflow validate workflow.yml

# Visualize workflow
dify-workflow visualize workflow.yml --format tree
dify-workflow visualize workflow.yml --format mermaid -o diagram.md
```

## Visualization

Three output formats available:

### Tree View
```
My Workflow (workflow)

`-- [>] Start
    `-- [*] LLM
        `-- [=] End
```

### ASCII Art
```
+----------------------+
|       Start         |
+----------------------+
        [START]
           |
           v
+----------------------+
|        LLM          |
+----------------------+
         [LLM]
           |
           v
+----------------------+
|        End          |
+----------------------+
         [END]
```

### Mermaid Diagram
```mermaid
graph TD
    start((Start))
    llm[["LLM"]]
    end[/End/]

    start --> llm
    llm --> end
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

## Multi-turn AI Conversation

The AI builder asks clarifying questions when your description is ambiguous:

```
> Create a workflow that processes user requests

I need a bit more information:

- What kind of requests should it process?
- Should it call any external APIs?
- What should the output format be?

> It should handle customer complaints, check order status via API, and respond politely

Generated workflow: Customer Service Bot

Customer Service Bot (workflow)

`-- [>] Start
    `-- [@] API Call
        `-- [*] LLM
            `-- [=] End
```

## API Reference

### Main Functions

```python
# Create workflow programmatically
from dify_workflow import Workflow, StartNode, LLMNode, EndNode

# Generate from natural language
from dify_workflow import from_description
wf = from_description("your description", lang="zh", model="gpt-4")

# Start interactive session
from dify_workflow import interactive
wf = interactive(lang="zh")

# Visualize workflow
from dify_workflow import visualize
print(visualize(wf, format="tree"))  # or "ascii" or "mermaid"
```

### Workflow Methods

- `add_node(node)` - Add a single node
- `add_nodes([nodes])` - Add multiple nodes
- `connect(source, target, source_handle, target_handle)` - Connect nodes
- `validate()` - Check for issues
- `export(path)` - Export to YAML/JSON file
- `to_yaml()` / `to_json()` - Get string output

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
