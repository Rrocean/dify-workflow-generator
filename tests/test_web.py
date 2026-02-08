"""
Tests for Web API.
"""

import pytest
from fastapi.testclient import TestClient

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from web.app import app, workflows_db


client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_db():
    """Clear database before each test."""
    workflows_db.clear()
    yield
    workflows_db.clear()


class TestRoot:
    def test_root_endpoint(self):
        response = client.get("/")
        assert response.status_code == 200
        assert "Dify Workflow Generator" in response.text


class TestWorkflows:
    def test_list_empty_workflows(self):
        response = client.get("/api/workflows")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_workflow(self):
        data = {
            "name": "Test Workflow",
            "mode": "workflow",
            "description": "A test workflow",
            "nodes": [],
            "edges": []
        }
        response = client.post("/api/workflows", json=data)
        assert response.status_code == 200
        result = response.json()
        assert result["name"] == "Test Workflow"
        assert result["mode"] == "workflow"
        assert "id" in result

    def test_get_workflow(self):
        # Create workflow
        data = {"name": "Test", "mode": "workflow", "nodes": [], "edges": []}
        create_resp = client.post("/api/workflows", json=data)
        wf_id = create_resp.json()["id"]
        
        # Get workflow
        response = client.get(f"/api/workflows/{wf_id}")
        assert response.status_code == 200
        result = response.json()
        assert result["name"] == "Test"
        assert "yaml" in result

    def test_get_nonexistent_workflow(self):
        response = client.get("/api/workflows/nonexistent")
        assert response.status_code == 404

    def test_update_workflow(self):
        # Create
        data = {"name": "Original", "mode": "workflow", "nodes": [], "edges": []}
        create_resp = client.post("/api/workflows", json=data)
        wf_id = create_resp.json()["id"]
        
        # Update
        update_data = {"name": "Updated", "mode": "workflow", "nodes": [], "edges": []}
        response = client.put(f"/api/workflows/{wf_id}", json=update_data)
        assert response.status_code == 200
        assert response.json()["name"] == "Updated"

    def test_delete_workflow(self):
        # Create
        data = {"name": "To Delete", "mode": "workflow", "nodes": [], "edges": []}
        create_resp = client.post("/api/workflows", json=data)
        wf_id = create_resp.json()["id"]
        
        # Delete
        response = client.delete(f"/api/workflows/{wf_id}")
        assert response.status_code == 200
        
        # Verify deleted
        get_resp = client.get(f"/api/workflows/{wf_id}")
        assert get_resp.status_code == 404


class TestTemplates:
    def test_list_templates(self):
        response = client.get("/api/templates")
        assert response.status_code == 200
        templates = response.json()
        assert len(templates) > 0
        assert all("id" in t and "name" in t for t in templates)

    def test_create_from_template(self):
        response = client.post("/api/templates/translation/create?name=MyTranslator")
        assert response.status_code == 200
        result = response.json()
        assert "id" in result
        assert "MyTranslator" in result["name"]

    def test_create_from_invalid_template(self):
        response = client.post("/api/templates/nonexistent/create")
        assert response.status_code == 404


class TestValidation:
    def test_validate_workflow(self):
        # Create
        data = {"name": "Test", "mode": "workflow", "nodes": [], "edges": []}
        create_resp = client.post("/api/workflows", json=data)
        wf_id = create_resp.json()["id"]
        
        # Validate
        response = client.post(f"/api/workflows/{wf_id}/validate")
        assert response.status_code == 200
        result = response.json()
        assert "valid" in result
        assert "issues" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
