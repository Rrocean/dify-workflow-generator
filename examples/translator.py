"""
Example: Create a translation workflow
"""

from dify_workflow import (
    Workflow,
    StartNode,
    EndNode,
    LLMNode,
)

# Create workflow
wf = Workflow(
    name="Translator",
    description="Translate text to any language"
)

# Define nodes
start = StartNode(inputs=["text", "target_language"])

translate = LLMNode(
    title="translate",
    model="gpt-4",
    prompt="""Translate the following text to {{target_language}}.
Only output the translation, nothing else.

Text: {{text}}""",
    temperature=0.3,
)

end = EndNode(outputs=["translation"])

# Build workflow
wf.add_nodes([start, translate, end])
wf.connect(start, translate)
wf.connect(translate, end)

# Export
wf.export("examples/translator_workflow.yml")
print(wf)
