"""
Workflow templates for common use cases.
"""

from .workflow import Workflow
from .nodes import (
    StartNode, EndNode, LLMNode, HTTPNode, 
    KnowledgeNode, IfElseNode, CodeNode, AnswerNode
)

def simple_chat(name="Simple Chat"):
    """Basic chat with memory"""
    wf = Workflow(name=name, mode="advanced-chat")
    
    start = StartNode(variables=[{"name": "query", "type": "string", "required": True}])
    
    llm = LLMNode(
        title="LLM",
        prompt="{{#start.query#}}",
        memory={"window": {"enabled": True, "size": 10}}
    )
    
    answer = AnswerNode(answer="{{#LLM.text#}}")
    
    wf.add_nodes([start, llm, answer])
    wf.connect(start, llm)
    wf.connect(llm, answer)
    return wf

def rag_chat(name="RAG Chat"):
    """Retrieval Augmented Generation chat"""
    wf = Workflow(name=name, mode="advanced-chat")
    
    start = StartNode(variables=[{"name": "query", "type": "string", "required": True}])
    
    retrieval = KnowledgeNode(
        title="Knowledge Retrieval",
        query_variable_selector=["start", "query"],
        dataset_ids=[] # User needs to fill this
    )
    
    llm = LLMNode(
        title="LLM",
        prompt="""Context:
{{#Knowledge Retrieval.result#}}

Question:
{{#start.query#}}

Answer the question based on the context."""
    )
    
    answer = AnswerNode(answer="{{#LLM.text#}}")
    
    wf.add_nodes([start, retrieval, llm, answer])
    wf.connect(start, retrieval)
    wf.connect(retrieval, llm)
    wf.connect(llm, answer)
    return wf

def translation(name="Translator"):
    """Text translation workflow"""
    wf = Workflow(name=name, mode="workflow")
    
    start = StartNode(variables=[
        {"name": "text", "type": "string", "required": True},
        {"name": "lang", "type": "string", "default": "English"}
    ])
    
    llm = LLMNode(
        title="Translate",
        prompt="Translate the following text to {{#start.lang#}}:\n\n{{#start.text#}}"
    )
    
    end = EndNode(outputs=[
        {"variable": "result", "value_selector": ["Translate", "text"]}
    ])
    
    wf.add_nodes([start, llm, end])
    wf.connect(start, llm)
    wf.connect(llm, end)
    return wf

def article_generator(name="Article Gen"):
    """Generate article from topic"""
    wf = Workflow(name=name, mode="workflow")
    
    start = StartNode(variables=[{"name": "topic", "type": "string"}])
    
    outline = LLMNode(
        title="Generate Outline",
        prompt="Generate an outline for an article about {{#start.topic#}}"
    )
    
    draft = LLMNode(
        title="Write Draft",
        prompt="Write a full article based on this outline:\n{{#Generate Outline.text#}}"
    )
    
    end = EndNode(outputs=[
        {"variable": "article", "value_selector": ["Write Draft", "text"]}
    ])
    
    wf.add_nodes([start, outline, draft, end])
    wf.connect(start, outline)
    wf.connect(outline, draft)
    wf.connect(draft, end)
    return wf

TEMPLATES = {
    "simple-chat": simple_chat,
    "rag-chat": rag_chat,
    "translation": translation,
    "article-gen": article_generator,
}
