"""
Web API for Dify Workflow Generator.

A modern FastAPI-based web interface for creating, editing, and managing workflows.
"""

import json
import os
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel, Field

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dify_workflow import Workflow, WorkflowBuilder, visualize
from dify_workflow.nodes import *
from dify_workflow.profiler import analyze_workflow
from dify_workflow.docs import generate_docs


# Pydantic models for API
class VariableSchema(BaseModel):
    name: str
    type: str = "string"
    required: bool = True
    default: Optional[str] = None
    description: Optional[str] = None


class NodeSchema(BaseModel):
    id: Optional[str] = None
    type: str
    title: str
    position: Dict[str, float] = Field(default_factory=lambda: {"x": 100, "y": 100})
    data: Dict[str, Any] = Field(default_factory=dict)


class EdgeSchema(BaseModel):
    id: Optional[str] = None
    source: str
    target: str
    sourceHandle: Optional[str] = "source"
    targetHandle: Optional[str] = "target"


class WorkflowCreateSchema(BaseModel):
    name: str
    mode: str = "workflow"
    description: str = ""
    nodes: List[NodeSchema] = Field(default_factory=list)
    edges: List[EdgeSchema] = Field(default_factory=list)


class WorkflowResponseSchema(BaseModel):
    id: str
    name: str
    mode: str
    description: str
    version: str
    created_at: str
    updated_at: str
    node_count: int
    edge_count: int


class WorkflowDetailSchema(WorkflowResponseSchema):
    nodes: List[NodeSchema]
    edges: List[EdgeSchema]
    yaml: str


class TemplateListSchema(BaseModel):
    id: str
    name: str
    description: str
    category: str


# In-memory storage (replace with database in production)
workflows_db: Dict[str, Dict[str, Any]] = {}


def generate_id() -> str:
    import uuid
    return str(uuid.uuid4())


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting Dify Workflow Generator Web Server...")
    yield
    # Shutdown
    print("Shutting down...")


app = FastAPI(
    title="Dify Workflow Generator API",
    description="A powerful API for creating and managing Dify workflows",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dify Workflow Generator</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            .container {
                background: rgba(255,255,255,0.1);
                padding: 40px;
                border-radius: 20px;
                backdrop-filter: blur(10px);
            }
            h1 { margin-top: 0; }
            .endpoint {
                background: rgba(255,255,255,0.2);
                padding: 15px;
                margin: 10px 0;
                border-radius: 10px;
            }
            .method { font-weight: bold; color: #4ade80; }
            a { color: #4ade80; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 Dify Workflow Generator</h1>
            <p>World-class workflow creation and management platform</p>
            
            <h2>API Endpoints</h2>
            <div class="endpoint">
                <span class="method">GET</span> /api/workflows - List all workflows
            </div>
            <div class="endpoint">
                <span class="method">POST</span> /api/workflows - Create new workflow
            </div>
            <div class="endpoint">
                <span class="method">GET</span> /api/workflows/{id} - Get workflow details
            </div>
            <div class="endpoint">
                <span class="method">PUT</span> /api/workflows/{id} - Update workflow
            </div>
            <div class="endpoint">
                <span class="method">DELETE</span> /api/workflows/{id} - Delete workflow
            </div>
            <div class="endpoint">
                <span class="method">POST</span> /api/workflows/{id}/export - Export workflow
            </div>
            <div class="endpoint">
                <span class="method">GET</span> /api/workflows/{id}/profile - Profile workflow
            </div>
            <div class="endpoint">
                <span class="method">GET</span> /api/templates - List templates
            </div>
            
            <p><a href="/docs">📚 Interactive API Documentation</a></p>
        </div>
    </body>
    </html>
    """


@app.get("/api/workflows", response_model=List[WorkflowResponseSchema])
async def list_workflows(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """List all workflows with pagination."""
    workflows = []
    for wf_id, wf_data in list(workflows_db.items())[skip:skip+limit]:
        workflows.append(WorkflowResponseSchema(
            id=wf_id,
            name=wf_data["name"],
            mode=wf_data["mode"],
            description=wf_data.get("description", ""),
            version="0.5.0",
            created_at=wf_data.get("created_at", ""),
            updated_at=wf_data.get("updated_at", ""),
            node_count=len(wf_data.get("nodes", [])),
            edge_count=len(wf_data.get("edges", []))
        ))
    return workflows


@app.post("/api/workflows", response_model=WorkflowResponseSchema)
async def create_workflow(workflow: WorkflowCreateSchema):
    """Create a new workflow."""
    wf_id = generate_id()
    now = datetime.utcnow().isoformat()
    
    workflows_db[wf_id] = {
        "id": wf_id,
        "name": workflow.name,
        "mode": workflow.mode,
        "description": workflow.description,
        "nodes": [n.dict() for n in workflow.nodes],
        "edges": [e.dict() for e in workflow.edges],
        "created_at": now,
        "updated_at": now
    }
    
    return WorkflowResponseSchema(
        id=wf_id,
        name=workflow.name,
        mode=workflow.mode,
        description=workflow.description,
        version="0.5.0",
        created_at=now,
        updated_at=now,
        node_count=len(workflow.nodes),
        edge_count=len(workflow.edges)
    )


@app.get("/api/workflows/{workflow_id}", response_model=WorkflowDetailSchema)
async def get_workflow(workflow_id: str):
    """Get detailed information about a workflow."""
    if workflow_id not in workflows_db:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    wf_data = workflows_db[workflow_id]
    
    # Generate YAML
    wf = Workflow(
        name=wf_data["name"],
        mode=wf_data["mode"],
        description=wf_data.get("description", "")
    )
    yaml_content = wf.to_yaml()
    
    return WorkflowDetailSchema(
        id=workflow_id,
        name=wf_data["name"],
        mode=wf_data["mode"],
        description=wf_data.get("description", ""),
        version="0.5.0",
        created_at=wf_data.get("created_at", ""),
        updated_at=wf_data.get("updated_at", ""),
        node_count=len(wf_data.get("nodes", [])),
        edge_count=len(wf_data.get("edges", [])),
        nodes=[NodeSchema(**n) for n in wf_data.get("nodes", [])],
        edges=[EdgeSchema(**e) for e in wf_data.get("edges", [])],
        yaml=yaml_content
    )


@app.put("/api/workflows/{workflow_id}", response_model=WorkflowResponseSchema)
async def update_workflow(workflow_id: str, workflow: WorkflowCreateSchema):
    """Update an existing workflow."""
    if workflow_id not in workflows_db:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    wf_data = workflows_db[workflow_id]
    now = datetime.utcnow().isoformat()
    
    wf_data.update({
        "name": workflow.name,
        "mode": workflow.mode,
        "description": workflow.description,
        "nodes": [n.dict() for n in workflow.nodes],
        "edges": [e.dict() for e in workflow.edges],
        "updated_at": now
    })
    
    return WorkflowResponseSchema(
        id=workflow_id,
        name=workflow.name,
        mode=workflow.mode,
        description=workflow.description,
        version="0.5.0",
        created_at=wf_data.get("created_at", ""),
        updated_at=now,
        node_count=len(workflow.nodes),
        edge_count=len(workflow.edges)
    )


@app.delete("/api/workflows/{workflow_id}")
async def delete_workflow(workflow_id: str):
    """Delete a workflow."""
    if workflow_id not in workflows_db:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    del workflows_db[workflow_id]
    return {"message": "Workflow deleted successfully"}


@app.post("/api/workflows/{workflow_id}/export")
async def export_workflow(workflow_id: str, format: str = "yaml"):
    """Export workflow to YAML or JSON."""
    if workflow_id not in workflows_db:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    wf_data = workflows_db[workflow_id]
    wf = Workflow(
        name=wf_data["name"],
        mode=wf_data["mode"],
        description=wf_data.get("description", "")
    )
    
    if format == "json":
        content = wf.to_json()
        media_type = "application/json"
        filename = f"{wf.name}.json"
    else:
        content = wf.to_yaml()
        media_type = "application/x-yaml"
        filename = f"{wf.name}.yml"
    
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@app.get("/api/workflows/{workflow_id}/profile")
async def profile_workflow(workflow_id: str):
    """Get performance profile of a workflow."""
    if workflow_id not in workflows_db:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    wf_data = workflows_db[workflow_id]
    wf = Workflow(
        name=wf_data["name"],
        mode=wf_data["mode"],
        description=wf_data.get("description", "")
    )
    
    profile = analyze_workflow(wf)
    
    return {
        "workflow_name": profile.workflow_name,
        "total_latency_ms": profile.total_latency_ms,
        "total_cost_usd": profile.total_cost_usd,
        "total_tokens": profile.total_tokens,
        "optimization_score": profile.score,
        "bottleneck_node": profile.bottleneck_node,
        "node_profiles": [
            {
                "node_id": n.node_id,
                "node_type": n.node_type,
                "title": n.title,
                "estimated_latency_ms": n.estimated_latency_ms,
                "estimated_cost_usd": n.estimated_cost_usd
            }
            for n in profile.nodes
        ],
        "suggestions": profile.optimization_suggestions
    }


@app.get("/api/workflows/{workflow_id}/visualize")
async def visualize_workflow(workflow_id: str, format: str = "mermaid"):
    """Get workflow visualization."""
    if workflow_id not in workflows_db:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    wf_data = workflows_db[workflow_id]
    wf = Workflow(
        name=wf_data["name"],
        mode=wf_data["mode"],
        description=wf_data.get("description", "")
    )
    
    diagram = visualize(wf, format=format)
    return {"format": format, "diagram": diagram}


@app.get("/api/templates", response_model=List[TemplateListSchema])
async def list_templates():
    """List all available templates."""
    from dify_workflow.templates import TEMPLATES
    
    templates = []
    categories = {
        "simple-chat": "chat",
        "rag-chat": "chat",
        "translation": "nlp",
        "article-gen": "content",
        "summarizer": "nlp",
        "code-reviewer": "developer",
        "sentiment-analyzer": "nlp",
        "qa-bot": "chat",
        "email-writer": "productivity"
    }
    
    for template_id, func in TEMPLATES.items():
        templates.append(TemplateListSchema(
            id=template_id,
            name=func.__name__.replace("_", " ").title(),
            description=func.__doc__ or "",
            category=categories.get(template_id, "other")
        ))
    
    return templates


@app.post("/api/templates/{template_id}/create")
async def create_from_template(template_id: str, name: Optional[str] = None):
    """Create a workflow from a template."""
    from dify_workflow.templates import TEMPLATES
    
    if template_id not in TEMPLATES:
        raise HTTPException(status_code=404, detail="Template not found")
    
    wf = TEMPLATES[template_id](name=name or template_id)
    
    # Store in database
    wf_id = generate_id()
    now = datetime.utcnow().isoformat()
    
    workflows_db[wf_id] = {
        "id": wf_id,
        "name": wf.name,
        "mode": wf.mode,
        "description": wf.description,
        "nodes": [],
        "edges": [],
        "created_at": now,
        "updated_at": now
    }
    
    return {
        "id": wf_id,
        "name": wf.name,
        "message": f"Workflow created from template '{template_id}'"
    }


@app.post("/api/workflows/{workflow_id}/validate")
async def validate_workflow_api(workflow_id: str):
    """Validate a workflow."""
    if workflow_id not in workflows_db:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    wf_data = workflows_db[workflow_id]
    wf = Workflow(
        name=wf_data["name"],
        mode=wf_data["mode"],
        description=wf_data.get("description", "")
    )
    
    issues = wf.validate()
    
    return {
        "valid": len(issues) == 0,
        "issues": issues
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
