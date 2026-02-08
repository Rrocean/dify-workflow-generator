"""
Tests for custom exceptions.
"""

import pytest
from dify_workflow import (
    DifyWorkflowError,
    ValidationError,
    NodeError,
    ConnectionError,
    Workflow,
    StartNode,
    LLMNode,
)


class TestExceptions:
    def test_base_exception(self):
        exc = DifyWorkflowError("Test error", {"detail": "info"})
        assert str(exc) == "Test error"
        assert exc.details == {"detail": "info"}
    
    def test_validation_error(self):
        exc = ValidationError("Invalid mode", {"mode": "invalid"})
        assert "Invalid mode" in str(exc)
    
    def test_node_error(self):
        exc = NodeError("Node failed", node_id="abc123", node_type="llm")
        assert exc.node_id == "abc123"
        assert exc.node_type == "llm"
    
    def test_connection_error(self):
        exc = ConnectionError("Connection failed", source_id="a", target_id="b")
        assert exc.source_id == "a"
        assert exc.target_id == "b"


class TestWorkflowValidationError:
    def test_invalid_mode_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            Workflow("Test", mode="invalid")
        
        assert "Invalid mode" in str(exc_info.value)
    
    def test_connect_nonexistent_source(self):
        wf = Workflow("Test")
        start = StartNode()
        wf.add_node(start)
        
        with pytest.raises(ConnectionError) as exc_info:
            wf.connect("nonexistent", start)
        
        assert "nonexistent" in str(exc_info.value)
    
    def test_connect_nonexistent_target(self):
        wf = Workflow("Test")
        start = StartNode()
        wf.add_node(start)
        
        with pytest.raises(ConnectionError) as exc_info:
            wf.connect(start, "nonexistent")
        
        assert "nonexistent" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
