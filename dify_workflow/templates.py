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
    
    start = StartNode(
        title="Start",
        variables=[{"name": "query", "type": "string", "required": True}]
    )
    
    llm = LLMNode(
        title="LLM",
        prompt="{{#start.query#}}",
        memory={"window": {"enabled": True, "size": 10}}
    )
    
    answer = AnswerNode(
        title="Answer",
        answer="{{#LLM.text#}}"
    )
    
    wf.add_nodes([start, llm, answer])
    wf.connect(start, llm)
    wf.connect(llm, answer)
    return wf


def rag_chat(name="RAG Chat"):
    """Retrieval Augmented Generation chat"""
    wf = Workflow(name=name, mode="advanced-chat")
    
    start = StartNode(
        title="Start",
        variables=[{"name": "query", "type": "string", "required": True}]
    )
    
    retrieval = KnowledgeNode(
        title="Knowledge Retrieval",
        query_variable_selector=["start", "query"],
        dataset_ids=[]  # User needs to fill this
    )
    
    llm = LLMNode(
        title="LLM",
        prompt="""Context:
{{#Knowledge Retrieval.result#}}

Question:
{{#start.query#}}

Answer the question based on the context."""
    )
    
    answer = AnswerNode(
        title="Answer",
        answer="{{#LLM.text#}}"
    )
    
    wf.add_nodes([start, retrieval, llm, answer])
    wf.connect(start, retrieval)
    wf.connect(retrieval, llm)
    wf.connect(llm, answer)
    return wf


def translation(name="Translator"):
    """Text translation workflow"""
    wf = Workflow(name=name, mode="workflow")
    
    start = StartNode(
        title="Start",
        variables=[
            {"name": "text", "type": "string", "required": True},
            {"name": "lang", "type": "string", "default": "English"}
        ]
    )
    
    llm = LLMNode(
        title="Translate",
        prompt="Translate the following text to {{#start.lang#}}:\n\n{{#start.text#}}"
    )
    
    end = EndNode(
        title="End",
        outputs=[
            {"variable": "result", "value_selector": ["Translate", "text"]}
        ]
    )
    
    wf.add_nodes([start, llm, end])
    wf.connect(start, llm)
    wf.connect(llm, end)
    return wf


def article_generator(name="Article Gen"):
    """Generate article from topic"""
    wf = Workflow(name=name, mode="workflow")
    
    start = StartNode(
        title="Start",
        variables=[{"name": "topic", "type": "string"}]
    )
    
    outline = LLMNode(
        title="Generate Outline",
        prompt="Generate an outline for an article about {{#start.topic#}}"
    )
    
    draft = LLMNode(
        title="Write Draft",
        prompt="Write a full article based on this outline:\n{{#Generate Outline.text#}}"
    )
    
    end = EndNode(
        title="End",
        outputs=[
            {"variable": "article", "value_selector": ["Write Draft", "text"]}
        ]
    )
    
    wf.add_nodes([start, outline, draft, end])
    wf.connect(start, outline)
    wf.connect(outline, draft)
    wf.connect(draft, end)
    return wf


def summarizer(name="Summarizer"):
    """Text summarization workflow"""
    wf = Workflow(name=name, mode="workflow")
    
    start = StartNode(
        title="Start",
        variables=[
            {"name": "text", "type": "string", "required": True},
            {"name": "max_length", "type": "number", "default": 100}
        ]
    )
    start.id = "start"
    
    llm = LLMNode(
        title="Summarize",
        prompt="""Summarize the following text in {{#start.max_length#}} words or less:

{{#start.text#}}

Summary:"""
    )
    
    end = EndNode(
        title="End",
        outputs=[{"variable": "summary", "value_selector": ["Summarize", "text"]}]
    )
    
    wf.add_nodes([start, llm, end])
    wf.connect(start, llm)
    wf.connect(llm, end)
    return wf


def code_reviewer(name="Code Reviewer"):
    """Automated code review workflow"""
    wf = Workflow(name=name, mode="workflow")
    
    start = StartNode(
        title="Start",
        variables=[
            {"name": "code", "type": "string", "required": True},
            {"name": "language", "type": "string", "default": "python"}
        ]
    )
    start.id = "start"
    
    llm = LLMNode(
        title="Review Code",
        prompt="""Review the following {{#start.language#}} code for:
1. Bugs and errors
2. Security issues
3. Performance problems
4. Style improvements

Code:
```{{#start.language#}}
{{#start.code#}}
```

Provide a detailed review:"""
    )
    
    end = EndNode(
        title="End",
        outputs=[{"variable": "review", "value_selector": ["Review Code", "text"]}]
    )
    
    wf.add_nodes([start, llm, end])
    wf.connect(start, llm)
    wf.connect(llm, end)
    return wf


def sentiment_analyzer(name="Sentiment Analyzer"):
    """Sentiment analysis workflow"""
    wf = Workflow(name=name, mode="workflow")
    
    start = StartNode(
        title="Start",
        variables=[{"name": "text", "type": "string", "required": True}]
    )
    start.id = "start"
    
    llm = LLMNode(
        title="Analyze Sentiment",
        prompt="""Analyze the sentiment of the following text.
Classify as: Positive, Negative, or Neutral.
Also provide a confidence score (0-1).

Text: {{#start.text#}}

Format your response as:
Sentiment: [Positive/Negative/Neutral]
Confidence: [0-1]
Explanation: [Brief explanation]"""
    )
    
    end = EndNode(
        title="End",
        outputs=[{"variable": "analysis", "value_selector": ["Analyze Sentiment", "text"]}]
    )
    
    wf.add_nodes([start, llm, end])
    wf.connect(start, llm)
    wf.connect(llm, end)
    return wf


def question_answerer(name="Q&A Bot"):
    """Question answering workflow with context"""
    wf = Workflow(name=name, mode="workflow")
    
    start = StartNode(
        title="Start",
        variables=[
            {"name": "question", "type": "string", "required": True},
            {"name": "context", "type": "string", "required": True}
        ]
    )
    start.id = "start"
    
    llm = LLMNode(
        title="Answer",
        prompt="""Context:
{{#start.context#}}

Question: {{#start.question#}}

Answer based on the context provided. If the answer cannot be found in the context, say "I don't know based on the given context."""
    )
    
    end = EndNode(
        title="End",
        outputs=[{"variable": "answer", "value_selector": ["Answer", "text"]}]
    )
    
    wf.add_nodes([start, llm, end])
    wf.connect(start, llm)
    wf.connect(llm, end)
    return wf


def email_writer(name="Email Writer"):
    """Email composition workflow"""
    wf = Workflow(name=name, mode="workflow")
    
    start = StartNode(
        title="Start",
        variables=[
            {"name": "recipient", "type": "string", "required": True},
            {"name": "purpose", "type": "string", "required": True},
            {"name": "tone", "type": "string", "default": "professional"},
            {"name": "key_points", "type": "string", "required": False}
        ]
    )
    start.id = "start"
    
    llm = LLMNode(
        title="Compose Email",
        prompt="""Write an email to {{#start.recipient#}}.

Purpose: {{#start.purpose#}}
Tone: {{#start.tone#}}
{% if start.key_points %}Key points to include:
{{#start.key_points#}}{% endif %}

Write a complete, professional email:"""
    )
    
    end = EndNode(
        title="End",
        outputs=[{"variable": "email", "value_selector": ["Compose Email", "text"]}]
    )
    
    wf.add_nodes([start, llm, end])
    wf.connect(start, llm)
    wf.connect(llm, end)
    return wf


TEMPLATES = {
    "simple-chat": simple_chat,
    "rag-chat": rag_chat,
    "translation": translation,
    "article-gen": article_generator,
    "summarizer": summarizer,
    "code-reviewer": code_reviewer,
    "sentiment-analyzer": sentiment_analyzer,
    "qa-bot": question_answerer,
    "email-writer": email_writer,
}
