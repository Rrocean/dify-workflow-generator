"""
Tests for new features: Importer, New Nodes, Templates
"""

import pytest
import os
from dify_workflow import (
    DifyImporter, import_workflow,
    AssignerNode, DocumentExtractorNode, ListFilterNode,
)
from dify_workflow.templates import TEMPLATES


class TestNewNodes:
    def test_assigner_node(self):
        node = AssignerNode(target_variable="res", source_variable_selector=["n1", "out"])
        data = node.to_dict()["data"]
        assert data["type"] == "assigner"
        assert data["variable_selector"] == ["n1", "out"]

    def test_document_extractor_node(self):
        node = DocumentExtractorNode(variable_selector=["start", "file"])
        data = node.to_dict()["data"]
        assert data["type"] == "document-extractor"

    def test_list_filter_node(self):
        node = ListFilterNode(
            variable_selector=["n1", "list"],
            conditions=[{"key": "name", "operator": "contains", "value": "test"}]
        )
        data = node.to_dict()["data"]
        assert data["type"] == "list-filter"
        assert len(data["filter_condition"]["conditions"]) == 1


class TestTemplates:
    def test_list_templates(self):
        assert "simple-chat" in TEMPLATES
        assert "translation" in TEMPLATES
        assert "rag-chat" in TEMPLATES
        assert "article-gen" in TEMPLATES
        assert "summarizer" in TEMPLATES
        assert "code-reviewer" in TEMPLATES

    def test_create_translation_template(self):
        wf = TEMPLATES["translation"]()
        assert len(wf.nodes) == 3
        assert wf.mode == "workflow"
        assert wf.name == "Translator"

    def test_create_chat_template(self):
        wf = TEMPLATES["simple-chat"]()
        assert len(wf.nodes) == 3
        assert wf.mode == "advanced-chat"

    def test_create_rag_template(self):
        wf = TEMPLATES["rag-chat"]()
        assert len(wf.nodes) == 4
        assert wf.mode == "advanced-chat"

    def test_create_summarizer_template(self):
        wf = TEMPLATES["summarizer"]()
        assert len(wf.nodes) == 3
        assert wf.mode == "workflow"
        assert wf.name == "Summarizer"

    def test_create_code_reviewer_template(self):
        wf = TEMPLATES["code-reviewer"]()
        assert len(wf.nodes) == 3
        assert wf.mode == "workflow"

    def test_create_sentiment_analyzer_template(self):
        wf = TEMPLATES["sentiment-analyzer"]()
        assert len(wf.nodes) == 3
        assert wf.mode == "workflow"

    def test_create_qa_bot_template(self):
        wf = TEMPLATES["qa-bot"]()
        assert len(wf.nodes) == 3
        assert wf.mode == "workflow"

    def test_create_email_writer_template(self):
        wf = TEMPLATES["email-writer"]()
        assert len(wf.nodes) == 3
        assert wf.mode == "workflow"


class TestImporter:
    def test_import_yaml(self):
        yaml_content = """
version: 0.5.0
kind: app
app:
  name: Test
workflow:
  graph:
    nodes:
    - id: node1
      data:
        type: start
        title: Start
    - id: node2
      data:
        type: end
        title: End
    edges:
    - source: node1
      target: node2
"""
        importer = DifyImporter(yaml_content)
        code = importer.generate_python_code()
        
        assert "from dify_workflow import *" in code
        assert "StartNode(" in code
        assert "EndNode(" in code
        assert 'wf.connect' in code
        assert 'title="Start"' in code
        assert 'wf.export("test.yml")' in code

    def test_import_llm_node(self):
        yaml_content = """
version: 0.5.0
kind: app
app:
  name: TestLLM
workflow:
  graph:
    nodes:
    - id: start
      data:
        type: start
        title: Start
        variables:
        - variable: query
          type: string
    - id: llm1
      data:
        type: llm
        title: AI
        model:
          provider: openai
          name: gpt-4
        prompt_template:
        - text: Hello {{#start.query#}}
    - id: end
      data:
        type: end
        title: End
    edges:
    - source: start
      target: llm1
    - source: llm1
      target: end
"""
        importer = DifyImporter(yaml_content)
        code = importer.generate_python_code()
        
        assert "LLMNode(" in code
        assert 'title="AI"' in code
        assert "model={" in code
        assert "prompt=r" in code


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
