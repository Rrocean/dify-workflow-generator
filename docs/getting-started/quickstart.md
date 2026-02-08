# Quick Start

## 1. Create a Simple Workflow

### Using Python API

```python
from dify_workflow import Workflow, StartNode, EndNode, LLMNode

# Create workflow
wf = Workflow(
    name="Translator",
    mode="workflow",
    description="Translate text to any language"
)

# Add nodes
start = StartNode(
    title="Start",
    variables=[
        {"name": "text", "type": "string", "required": True},
        {"name": "lang", "type": "string", "default": "English"}
    ]
)
start.id = "start"

translate = LLMNode(
    title="Translate",
    prompt="Translate to {{#start.lang#}}: {{#start.text#}}",
    model={"provider": "openai", "name": "gpt-4"}
)

end = EndNode(
    title="End",
    outputs=[{"variable": "result", "value_selector": ["Translate", "text"]}]
)

# Connect nodes
wf.add_nodes([start, translate, end])
wf.connect(start, translate)
wf.connect(translate, end)

# Export
wf.export("translator.yml")
```

### Using Fluent API

```python
from dify_workflow import WorkflowBuilder

wf = (WorkflowBuilder("Translator")
    .start_with([
        {"name": "text", "type": "string"},
        {"name": "lang", "type": "string", "default": "English"}
    ])
    .llm("Translate to {{#start.lang#}}: {{#start.text#}}")
    .end()
    .build())

wf.export("translator.yml")
```

## 2. Use CLI

```bash
# Create from template
dify-workflow template create translation --output translator.yml

# Validate
dify-workflow validate translator.yml

# Visualize
dify-workflow visualize translator.yml
```

## 3. Import to Dify

1. Open Dify platform
2. Go to Studio → Workflows
3. Click Import
4. Select your `translator.yml` file
5. Your workflow is ready to use!

## Next Steps

- Learn about [all node types](../guide/node-types.md)
- Explore [built-in templates](../guide/templates.md)
- Build [custom plugins](../advanced/plugins.md)
