"""
Tests for utility functions.
"""

import pytest
from dify_workflow.utils import (
    generate_slug,
    validate_variable_name,
    extract_variable_references,
    auto_layout_nodes,
    clone_node,
    find_isolated_nodes,
    find_execution_order,
    estimate_tokens,
)
from dify_workflow import Workflow, StartNode, LLMNode, EndNode


class TestSlugGeneration:
    def test_basic_slug(self):
        assert generate_slug("Hello World") == "hello-world"
    
    def test_slug_with_special_chars(self):
        assert generate_slug("Hello, World!") == "hello-world"
    
    def test_slug_multiple_spaces(self):
        assert generate_slug("Hello    World") == "hello-world"
    
    def test_slug_leading_trailing(self):
        assert generate_slug("  Hello World  ") == "hello-world"


class TestVariableValidation:
    def test_valid_variable(self):
        valid, msg = validate_variable_name("my_variable")
        assert valid
        assert msg == ""
    
    def test_empty_variable(self):
        valid, msg = validate_variable_name("")
        assert not valid
        assert "empty" in msg.lower()
    
    def test_invalid_start(self):
        valid, msg = validate_variable_name("123var")
        assert not valid
    
    def test_reserved_keyword(self):
        valid, msg = validate_variable_name("sys")
        assert not valid
        assert "reserved" in msg.lower()


class TestVariableExtraction:
    def test_single_reference(self):
        refs = extract_variable_references("{{#start.query#}}")
        assert refs == [("start", "query")]
    
    def test_multiple_references(self):
        refs = extract_variable_references("{{#start.a#}} and {{#llm.b#}}")
        assert refs == [("start", "a"), ("llm", "b")]
    
    def test_no_references(self):
        refs = extract_variable_references("plain text")
        assert refs == []


class TestAutoLayout:
    def test_linear_layout(self):
        wf = Workflow("Test")
        start = StartNode()
        llm = LLMNode()
        end = EndNode()
        
        wf.add_nodes([start, llm, end])
        wf.connect(start, llm)
        wf.connect(llm, end)
        
        # Before layout
        assert start.position_x == 100
        
        wf.auto_layout()
        
        # After layout - nodes should have different x positions
        assert llm.position_x > start.position_x
        assert end.position_x > llm.position_x


class TestCloneNode:
    def test_clone_creates_new_id(self):
        node = LLMNode(title="Original")
        cloned = clone_node(node)
        
        assert cloned.id != node.id
        assert cloned.title == node.title
    
    def test_clone_with_new_title(self):
        node = LLMNode(title="Original")
        cloned = clone_node(node, new_title="Copy")
        
        assert cloned.title == "Copy"


class TestFindIsolatedNodes:
    def test_no_isolated(self):
        wf = Workflow("Test")
        start = StartNode()
        end = EndNode()
        
        wf.add_nodes([start, end])
        wf.connect(start, end)
        
        isolated = wf.find_isolated_nodes()
        assert len(isolated) == 0
    
    def test_one_isolated(self):
        wf = Workflow("Test")
        start = StartNode()
        end = EndNode()
        isolated = LLMNode()
        
        wf.add_nodes([start, end, isolated])
        wf.connect(start, end)
        
        isolated_nodes = wf.find_isolated_nodes()
        assert len(isolated_nodes) == 1
        assert isolated_nodes[0].id == isolated.id


class TestExecutionOrder:
    def test_linear_order(self):
        wf = Workflow("Test")
        start = StartNode()
        llm = LLMNode()
        end = EndNode()
        
        wf.add_nodes([start, llm, end])
        wf.connect(start, llm)
        wf.connect(llm, end)
        
        order = wf.get_execution_order()
        
        assert order[0] == start.id
        assert order[1] == llm.id
        assert order[2] == end.id
    
    def test_cyclic_workflow_raises(self):
        wf = Workflow("Test")
        a = StartNode()
        b = LLMNode()
        
        wf.add_nodes([a, b])
        wf.connect(a, b)
        # Create cycle (b -> a)
        wf.connect(b, a)
        
        with pytest.raises(ValueError, match="cycle"):
            wf.get_execution_order()


class TestTokenEstimation:
    def test_empty_text(self):
        assert estimate_tokens("") == 0
    
    def test_english_text(self):
        # Roughly 4 chars per token for English
        assert estimate_tokens("hello world") == 3  # 11 chars / 4 + 1
    
    def test_chinese_text(self):
        # Chinese chars are roughly 1 token each
        # Note: actual tokenization varies by model
        tokens = estimate_tokens("你好世界")
        assert 4 <= tokens <= 6  # Allow some variance


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
