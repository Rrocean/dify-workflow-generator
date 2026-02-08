"""
Tests for Workflow Builder (fluent API).
"""

import pytest
from dify_workflow import WorkflowBuilder, quick_workflow, chatbot
from dify_workflow.nodes import LLMNode, IfElseNode


class TestWorkflowBuilder:
    def test_simple_workflow(self):
        wf = (WorkflowBuilder("Test")
              .start_with([{"name": "query", "type": "string"}])
              .llm("Process: {{#start.query#}}")
              .end()
              .build())
        
        assert wf.name == "Test"
        assert len(wf.nodes) == 3  # start, llm, end
    
    def test_multiple_llm_nodes(self):
        wf = (WorkflowBuilder("Multi-Step")
              .start_with([{"name": "topic", "type": "string"}])
              .llm("Outline for {{#start.topic#}}", title="outline")
              .llm("Write based on {{#outline.text#}}", title="draft")
              .end()
              .build())
        
        assert len(wf.nodes) == 4
    
    def test_http_node(self):
        wf = (WorkflowBuilder("API Caller")
              .start_with([{"name": "url", "type": "string"}])
              .http("{{#start.url#}}", method="GET")
              .end()
              .build())
        
        assert len(wf.nodes) == 3
    
    def test_code_node(self):
        wf = (WorkflowBuilder("Code Processor")
              .start_with([{"name": "data", "type": "string"}])
              .code("def main(args): return {'result': args}")
              .end()
              .build())
        
        assert len(wf.nodes) == 3
    
    def test_condition_node(self):
        wf = (WorkflowBuilder("Conditional")
              .start_with([{"name": "query", "type": "string"}])
              .condition("query", operator="contains", value="test")
              .llm("Handle true case")
              .end()
              .build())
        
        assert len(wf.nodes) == 4
        assert any(isinstance(n, IfElseNode) for n in wf.nodes)
    
    def test_chatbot_mode(self):
        wf = (WorkflowBuilder("Chat", mode="advanced-chat")
              .start_with([{"name": "msg", "type": "string"}])
              .llm("Reply to: {{#start.msg#}}")
              .end()
              .build())
        
        assert wf.mode == "advanced-chat"
        # Should have Answer node instead of End
        node_types = [n._node_type for n in wf.nodes]
        assert "answer" in node_types


class TestQuickWorkflow:
    def test_basic_quick_workflow(self):
        wf = quick_workflow(
            "Summarizer",
            "Summarize: {{#start.text#}}",
            inputs=["text"]
        )
        
        assert wf.name == "Summarizer"
        assert len(wf.nodes) == 3


class TestChatbotHelper:
    def test_basic_chatbot(self):
        wf = chatbot("MyBot", system_prompt="You are helpful")
        
        assert wf.name == "MyBot"
        assert wf.mode == "advanced-chat"
        assert len(wf.nodes) == 3
    
    def test_chatbot_without_memory(self):
        wf = chatbot("NoMemoryBot", with_memory=False)
        
        assert wf.mode == "advanced-chat"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
