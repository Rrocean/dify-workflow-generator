"""
Tests for Interactive Workflow Builder
"""

import pytest
from dify_workflow.interactive import InteractiveBuilder, WorkflowIntent


class TestInteractiveBuilder:
    """Test the InteractiveBuilder class"""
    
    def test_init(self):
        """Test builder initialization"""
        builder = InteractiveBuilder()
        assert builder.current_step == 0
        assert not builder.is_complete()
    
    def test_get_current_question(self):
        """Test getting current question"""
        builder = InteractiveBuilder()
        question = builder.get_current_question()
        assert question is not None
        assert "id" in question
        assert "question" in question
    
    def test_process_name_answer(self):
        """Test processing workflow name"""
        builder = InteractiveBuilder()
        success, _ = builder.process_answer("My Test Workflow")
        
        assert success
        assert builder.intent.name == "My Test Workflow"
        assert builder.current_step == 1
    
    def test_process_all_answers(self):
        """Test processing all questions"""
        builder = InteractiveBuilder()
        
        answers = [
            "Test Workflow",      # name
            "Process user input", # purpose
            "1",                  # mode (workflow)
            "text, language",     # inputs
            "n",                  # needs_api
            "n",                  # needs_code
            "n",                  # needs_conditions
        ]
        
        for answer in answers:
            success, _ = builder.process_answer(answer)
            assert success
        
        assert builder.is_complete()
        assert builder.intent.name == "Test Workflow"
        assert builder.intent.mode == "workflow"
        assert len(builder.intent.input_variables) == 2
    
    def test_build_workflow(self):
        """Test building workflow from collected intent"""
        builder = InteractiveBuilder()
        
        # Set up intent directly
        builder.intent.name = "Test"
        builder.intent.mode = "workflow"
        builder.intent.description = "Test workflow"
        builder.intent.input_variables = [
            {"name": "input", "type": "string", "required": True}
        ]
        builder.intent.needs_llm = True
        builder.current_step = len(builder.QUESTIONS)  # Mark as complete
        
        workflow = builder.build_workflow()
        
        assert workflow.name == "Test"
        assert workflow.mode == "workflow"
        assert len(workflow.nodes) >= 3  # start, llm, end
    
    def test_build_chat_workflow(self):
        """Test building advanced-chat workflow"""
        builder = InteractiveBuilder()
        
        builder.intent.name = "Chatbot"
        builder.intent.mode = "advanced-chat"
        builder.intent.input_variables = [
            {"name": "query", "type": "string", "required": True}
        ]
        builder.current_step = len(builder.QUESTIONS)
        
        workflow = builder.build_workflow()
        
        assert workflow.mode == "advanced-chat"
        # Should have Answer node instead of End node
        node_types = [n._node_type for n in workflow.nodes]
        assert "answer" in node_types
    
    def test_build_with_conditions(self):
        """Test building workflow with conditions"""
        builder = InteractiveBuilder()
        
        builder.intent.name = "Conditional"
        builder.intent.mode = "workflow"
        builder.intent.input_variables = [
            {"name": "input", "type": "string", "required": True}
        ]
        builder.intent.needs_conditions = True
        builder.current_step = len(builder.QUESTIONS)
        
        workflow = builder.build_workflow()
        
        node_types = [n._node_type for n in workflow.nodes]
        assert "if-else" in node_types
    
    def test_parse_inputs_simple(self):
        """Test parsing simple input list"""
        builder = InteractiveBuilder()
        builder.parse_inputs("text, language, format")
        
        assert len(builder.intent.input_variables) == 3
        assert builder.intent.input_variables[0]["name"] == "text"
        assert builder.intent.input_variables[1]["name"] == "language"
    
    def test_parse_inputs_with_types(self):
        """Test parsing inputs with type annotations"""
        builder = InteractiveBuilder()
        builder.parse_inputs("count:number, text:string")
        
        assert len(builder.intent.input_variables) == 2
        assert builder.intent.input_variables[0]["name"] == "count"
        assert builder.intent.input_variables[0]["type"] == "number"
    
    def test_parse_inputs_empty(self):
        """Test parsing empty input defaults to 'input'"""
        builder = InteractiveBuilder()
        builder.parse_inputs("")
        
        assert len(builder.intent.input_variables) == 1
        assert builder.intent.input_variables[0]["name"] == "input"


class TestWorkflowIntent:
    """Test the WorkflowIntent dataclass"""
    
    def test_defaults(self):
        """Test default values"""
        intent = WorkflowIntent()
        
        assert intent.name == "My Workflow"
        assert intent.mode == "workflow"
        assert intent.needs_input == True
        assert intent.needs_llm == True
        assert intent.needs_api == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
