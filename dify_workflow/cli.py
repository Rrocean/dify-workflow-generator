"""
CLI for Dify Workflow Generator

Usage:
    dify-workflow interactive    # Guided workflow creation
    dify-workflow build <file>   # Build workflow from Python file
    dify-workflow ai "description"  # AI-powered generation
"""

import argparse
import sys
import os


def cmd_interactive(args):
    """Run interactive workflow builder"""
    from .interactive import interactive_session
    interactive_session()


def cmd_ai(args):
    """AI-powered workflow generation"""
    from .interactive import AIWorkflowBuilder
    
    description = args.description
    output = args.output or "workflow.yml"
    
    print(f"Analyzing: {description[:50]}...")
    
    builder = AIWorkflowBuilder(
        api_key=args.api_key or os.environ.get("OPENAI_API_KEY"),
        base_url=args.base_url,
    )
    
    try:
        workflow = builder.build_from_description(
            description,
            model=args.model or "gpt-4",
        )
        
        workflow.export(output)
        print(f"\n[OK] Created workflow: {workflow.name}")
        print(f"Nodes: {len(workflow.nodes)}")
        print(f"Saved to: {output}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def cmd_build(args):
    """Build workflow from Python file"""
    import importlib.util
    
    filepath = args.file
    output = args.output
    
    if not os.path.exists(filepath):
        print(f"Error: File not found: {filepath}")
        sys.exit(1)
    
    # Load the module
    spec = importlib.util.spec_from_file_location("workflow_module", filepath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    # Look for workflow objects or create functions
    workflows = []
    
    for name in dir(module):
        obj = getattr(module, name)
        if hasattr(obj, 'to_yaml') and hasattr(obj, 'nodes'):
            workflows.append((name, obj))
        elif callable(obj) and name.startswith(('create_', 'build_', 'make_')):
            try:
                result = obj()
                if hasattr(result, 'to_yaml'):
                    workflows.append((name, result))
            except:
                pass
    
    if not workflows:
        print("Error: No workflow found in file")
        print("Define a Workflow object or a create_*/build_*/make_* function")
        sys.exit(1)
    
    for name, wf in workflows:
        out_path = output or f"{name}.yml"
        wf.export(out_path)
        print(f"[OK] Exported {name} -> {out_path}")


def cmd_validate(args):
    """Validate a workflow YAML file"""
    import yaml
    from .workflow import DSL_VERSION
    
    filepath = args.file
    
    if not os.path.exists(filepath):
        print(f"Error: File not found: {filepath}")
        sys.exit(1)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    issues = []
    
    # Check version
    if data.get("version") != DSL_VERSION:
        issues.append(f"Warning: Version mismatch (expected {DSL_VERSION}, got {data.get('version')})")
    
    # Check structure
    if "app" not in data:
        issues.append("Error: Missing 'app' section")
    if "workflow" not in data:
        issues.append("Error: Missing 'workflow' section")
    
    # Check nodes
    nodes = data.get("workflow", {}).get("graph", {}).get("nodes", [])
    edges = data.get("workflow", {}).get("graph", {}).get("edges", [])
    
    node_ids = {n.get("id") for n in nodes}
    node_types = [n.get("data", {}).get("type") for n in nodes]
    
    if "start" not in node_types:
        issues.append("Warning: No start node found")
    
    mode = data.get("app", {}).get("mode", "workflow")
    if mode == "workflow" and "end" not in node_types:
        issues.append("Warning: No end node found (required for workflow mode)")
    
    # Check edges
    for edge in edges:
        if edge.get("source") not in node_ids:
            issues.append(f"Error: Edge references unknown source: {edge.get('source')}")
        if edge.get("target") not in node_ids:
            issues.append(f"Error: Edge references unknown target: {edge.get('target')}")
    
    # Report
    if issues:
        print(f"Validation issues for {filepath}:")
        for issue in issues:
            print(f"  - {issue}")
        sys.exit(1 if any("Error" in i for i in issues) else 0)
    else:
        print(f"[OK] {filepath} is valid")
        print(f"  Name: {data.get('app', {}).get('name', 'Unknown')}")
        print(f"  Mode: {mode}")
        print(f"  Nodes: {len(nodes)}")
        print(f"  Edges: {len(edges)}")


def main():
    parser = argparse.ArgumentParser(
        description="Dify Workflow Generator CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  dify-workflow interactive
  dify-workflow ai "Create a translation workflow that takes text and target language"
  dify-workflow build my_workflow.py -o output.yml
  dify-workflow validate workflow.yml
        """,
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Interactive command
    p_interactive = subparsers.add_parser(
        "interactive", aliases=["i"],
        help="Guided interactive workflow creation"
    )
    p_interactive.set_defaults(func=cmd_interactive)
    
    # AI command
    p_ai = subparsers.add_parser(
        "ai",
        help="AI-powered workflow generation from description"
    )
    p_ai.add_argument("description", help="Natural language description of the workflow")
    p_ai.add_argument("-o", "--output", help="Output file path (default: workflow.yml)")
    p_ai.add_argument("--model", help="LLM model to use (default: gpt-4)")
    p_ai.add_argument("--api-key", help="OpenAI API key (or set OPENAI_API_KEY)")
    p_ai.add_argument("--base-url", help="Custom API base URL")
    p_ai.set_defaults(func=cmd_ai)
    
    # Build command
    p_build = subparsers.add_parser(
        "build", aliases=["b"],
        help="Build workflow from Python file"
    )
    p_build.add_argument("file", help="Python file containing workflow definition")
    p_build.add_argument("-o", "--output", help="Output file path")
    p_build.set_defaults(func=cmd_build)
    
    # Validate command
    p_validate = subparsers.add_parser(
        "validate", aliases=["v"],
        help="Validate a workflow YAML file"
    )
    p_validate.add_argument("file", help="YAML file to validate")
    p_validate.set_defaults(func=cmd_validate)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(0)
    
    args.func(args)


if __name__ == "__main__":
    main()
