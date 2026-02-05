"""
Tests for new features: Importer, New Nodes, Templates
"""

import pytest
import os
from dify_workflow.importer import DifyImporter
from dify_workflow.templates import TEMPLATES
from dify_workflow.nodes import AssignerNode, DocumentExtractorNode, ListFilterNode

class TestNewNodes:
    def test_assigner_node(self):
        node = AssignerNode(target_variable="res", source_variable_selector=["n1", "out"])
        data = node.to_dict()["data"]
        assert data["type"] == "assigner"
        assert data["variable_selector"] == ["n1", "out"]

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

    def test_create_template(self):
        wf = TEMPLATES["translation"]()
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
        
        assert "class StartNode" in code or "StartNode(" in code
        assert "class EndNode" in code or "EndNode(" in code
        assert 'wf.connect' in code
        assert 'title="Start"' in code

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
