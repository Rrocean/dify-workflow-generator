"""
Tests for Dify Workflow Generator
"""

import yaml
import pytest
from dify_workflow import (
    Workflow,
    StartNode,
    EndNode,
    LLMNode,
    HTTPNode,
    CodeNode,
    IfElseNode,
)


class TestWorkflow:
    """Test the Workflow class"""
    
    def test_create_workflow(self):
        """Test basic workflow creation"""
        wf = Workflow("Test Workflow", mode="workflow")
        assert wf.name == "Test Workflow"
        assert wf.mode == "workflow"
        assert len(wf.nodes) == 0
        assert len(wf.edges) == 0
    
    def test_add_node(self):
        """Test adding nodes"""
        wf = Workflow("Test")
        start = StartNode()
        wf.add_node(start)
        
        assert len(wf.nodes) == 1
        assert wf.nodes[0] == start
    
    def test_connect_nodes(self):
        """Test connecting nodes"""
        wf = Workflow("Test")
        start = StartNode()
        end = EndNode()
        
        wf.add_nodes([start, end])
        wf.connect(start, end)
        
        assert len(wf.edges) == 1
        assert wf.edges[0]["source"] == start.id
        assert wf.edges[0]["target"] == end.id
    
    def test_to_dict(self):
        """Test DSL export"""
        wf = Workflow("Test", mode="workflow")
        start = StartNode(variables=[{"name": "query", "type": "string"}])
        end = EndNode()
        
        wf.add_nodes([start, end])
        wf.connect(start, end)
        
        data = wf.to_dict()
        
        assert data["version"] == "0.5.0"
        assert data["kind"] == "app"
        assert data["app"]["name"] == "Test"
        assert data["app"]["mode"] == "workflow"
        assert len(data["workflow"]["graph"]["nodes"]) == 2
        assert len(data["workflow"]["graph"]["edges"]) == 1
    
    def test_to_yaml(self):
        """Test YAML export"""
        wf = Workflow("Test")
        wf.add_node(StartNode())
        
        yaml_str = wf.to_yaml()
        data = yaml.safe_load(yaml_str)
        
        assert data["version"] == "0.5.0"
        assert data["app"]["name"] == "Test"
    
    def test_validate_missing_start(self):
        """Test validation catches missing start node"""
        wf = Workflow("Test")
        wf.add_node(EndNode())
        
        issues = wf.validate()
        assert any("start" in i.lower() for i in issues)
    
    def test_validate_missing_end(self):
        """Test validation catches missing end node for workflow mode"""
        wf = Workflow("Test", mode="workflow")
        wf.add_node(StartNode())
        
        issues = wf.validate()
        assert any("end" in i.lower() for i in issues)


class TestNodes:
    """Test node classes"""
    
    def test_start_node(self):
        """Test StartNode"""
        node = StartNode(
            title="Start",
            variables=[
                {"name": "query", "type": "string", "required": True}
            ]
        )
        
        data = node.to_dict()
        assert data["data"]["type"] == "start"
        assert len(data["data"]["variables"]) == 1
        assert data["data"]["variables"][0]["variable"] == "query"
    
    def test_llm_node(self):
        """Test LLMNode"""
        node = LLMNode(
            title="chat",
            model={"provider": "openai", "name": "gpt-4"},
            prompt="Hello {{#start.query#}}",
            temperature=0.5,
        )
        
        data = node.to_dict()
        assert data["data"]["type"] == "llm"
        assert data["data"]["model"]["provider"] == "openai"
        assert "Hello" in data["data"]["prompt_template"][0]["text"]
    
    def test_http_node(self):
        """Test HTTPNode"""
        node = HTTPNode(
            title="API Call",
            url="https://api.example.com",
            method="POST",
        )
        
        data = node.to_dict()
        assert data["data"]["type"] == "http-request"
        assert data["data"]["url"] == "https://api.example.com"
        assert data["data"]["method"] == "POST"
    
    def test_code_node(self):
        """Test CodeNode"""
        node = CodeNode(
            title="Process",
            language="python3",
            code="def main(args): return {'result': 'ok'}",
        )
        
        data = node.to_dict()
        assert data["data"]["type"] == "code"
        assert data["data"]["code_language"] == "python3"
    
    def test_ifelse_node(self):
        """Test IfElseNode"""
        node = IfElseNode(
            title="Check",
            conditions=[
                {
                    "variable_selector": ["start", "query"],
                    "comparison_operator": "contains",
                    "value": "hello",
                }
            ]
        )
        
        data = node.to_dict()
        assert data["data"]["type"] == "if-else"
        assert len(data["data"]["conditions"]) == 1


class TestFullWorkflow:
    """Integration tests for complete workflows"""
    
    def test_complete_workflow(self):
        """Test creating a complete workflow"""
        wf = Workflow("Complete Test", mode="workflow")
        
        start = StartNode(variables=[
            {"name": "input", "type": "string", "required": True}
        ])
        
        llm = LLMNode(
            title="process",
            prompt="Process: {{#start.input#}}"
        )
        
        end = EndNode(outputs=[
            {"variable": "result", "value_selector": ["process", "text"]}
        ])
        
        wf.add_nodes([start, llm, end])
        wf.connect(start, llm)
        wf.connect(llm, end)
        
        # Validate
        issues = wf.validate()
        assert len(issues) == 0, f"Unexpected issues: {issues}"
        
        # Export and verify
        data = wf.to_dict()
        assert len(data["workflow"]["graph"]["nodes"]) == 3
        assert len(data["workflow"]["graph"]["edges"]) == 2
        
        # Verify YAML can be parsed
        yaml_str = wf.to_yaml()
        parsed = yaml.safe_load(yaml_str)
        assert parsed["version"] == "0.5.0"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
