"""
CLI for Dify Workflow Generator

Usage:
    dify-workflow interactive    # Guided workflow creation
    dify-workflow interactive --lang zh  # Chinese interface
    dify-workflow build <file>   # Build workflow from Python file
    dify-workflow ai "description"  # AI-powered generation
    dify-workflow visualize <file>  # Visualize workflow
    dify-workflow import <file>  # Import Dify YAML to Python
"""

import argparse
import sys
import os

from .constants import NODE_CLASS_MAP


def cmd_interactive(args):
    """Run interactive workflow builder"""
    from .interactive import interactive_session
    lang = args.lang or "en"
    interactive_session(lang=lang)


def cmd_ai(args):
    """AI-powered workflow generation with multi-turn conversation"""
    from .interactive import AIWorkflowBuilder, visualize
    
    description = args.description
    output = args.output or "workflow.yml"
    lang = args.lang or "en"
    
    builder = AIWorkflowBuilder(
        api_key=args.api_key or os.environ.get("OPENAI_API_KEY"),
        base_url=args.base_url,
        lang=lang,
    )
    
    if lang == "zh":
        print(f"正在分析: {description[:50]}...")
    else:
        print(f"Analyzing: {description[:50]}...")
    
    try:
        complete, response, workflow = builder.chat(
            description,
            model=args.model or "gpt-4",
        )
        
        print(f"\n{response}")
        
        # Multi-turn conversation if needed
        while not complete:
            try:
                if lang == "zh":
                    user_input = input("\n请回答 (或输入 'done' 完成): ").strip()
                else:
                    user_input = input("\nYour response (or 'done' to finish): ").strip()
                
                if user_input.lower() in ('done', '完成', 'quit', 'exit'):
                    if builder.current_intent:
                        workflow = builder._build_from_intent(builder.current_intent)
                        complete = True
                    else:
                        print("Cancelled." if lang == "en" else "已取消。")
                        return
                else:
                    complete, response, workflow = builder.chat(
                        user_input,
                        model=args.model or "gpt-4",
                    )
                    print(f"\n{response}")
                    
            except KeyboardInterrupt:
                print("\n\nCancelled." if lang == "en" else "\n\n已取消。")
                return
        
        if workflow:
            workflow.export(output)
            if lang == "zh":
                print(f"\n[OK] 工作流已保存: {output}")
            else:
                print(f"\n[OK] Workflow saved: {output}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def cmd_import(args):
    """Import Dify YAML to Python"""
    from .importer import import_workflow
    
    input_file = args.file
    output_file = args.output
    
    if not os.path.exists(input_file):
        print(f"Error: File not found: {input_file}")
        sys.exit(1)
        
    if not output_file:
        output_file = os.path.splitext(input_file)[0] + ".py"
        
    try:
        import_workflow(input_file, output_file)
        print(f"[OK] Converted {input_file} -> {output_file}")
    except Exception as e:
        print(f"Error importing workflow: {e}")
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
    from .constants import DSL_VERSION
    
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


def cmd_visualize(args):
    """Visualize a workflow"""
    import yaml
    from .workflow import Workflow
    from .interactive import visualize, WorkflowVisualizer
    from .nodes import (
        StartNode, EndNode, AnswerNode, LLMNode, HTTPNode,
        CodeNode, IfElseNode, TemplateNode, KnowledgeNode,
        VariableAggregatorNode, IterationNode, QuestionClassifierNode,
        ParameterExtractorNode, ToolNode, AssignerNode,
        DocumentExtractorNode, ListFilterNode,
    )
    
    filepath = args.file
    fmt = args.format or "tree"
    
    if not os.path.exists(filepath):
        print(f"Error: File not found: {filepath}")
        sys.exit(1)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    # Reconstruct workflow from YAML
    app = data.get("app", {})
    wf_data = data.get("workflow", {})
    graph = wf_data.get("graph", {})
    
    wf = Workflow(
        name=app.get("name", "Workflow"),
        mode=app.get("mode", "workflow"),
        description=app.get("description", ""),
    )
    
    # Map node types to classes
    node_classes = {
        "start": StartNode,
        "end": EndNode,
        "answer": AnswerNode,
        "llm": LLMNode,
        "http-request": HTTPNode,
        "code": CodeNode,
        "if-else": IfElseNode,
        "template-transform": TemplateNode,
        "knowledge-retrieval": KnowledgeNode,
        "variable-aggregator": VariableAggregatorNode,
        "iteration": IterationNode,
        "question-classifier": QuestionClassifierNode,
        "parameter-extractor": ParameterExtractorNode,
        "tool": ToolNode,
        "assigner": AssignerNode,
        "document-extractor": DocumentExtractorNode,
        "list-filter": ListFilterNode,
    }
    
    # Recreate nodes
    node_map = {}
    for node_data in graph.get("nodes", []):
        node_id = node_data.get("id")
        data_section = node_data.get("data", {})
        node_type = data_section.get("type", "start")
        title = data_section.get("title", node_type)
        
        node_class = node_classes.get(node_type, StartNode)
        node = node_class(title=title)
        node.id = node_id
        node.position_x = node_data.get("position", {}).get("x", 0)
        node.position_y = node_data.get("position", {}).get("y", 0)
        
        wf.nodes.append(node)
        node_map[node_id] = node
    
    # Recreate edges
    wf.edges = graph.get("edges", [])
    
    # Visualize
    output = visualize(wf, fmt)
    print(output)
    
    # Optionally save mermaid to file
    if fmt == "mermaid" and args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"\nSaved to {args.output}")


def cmd_chat(args):
    """Start an AI chat session for workflow building"""
    from .interactive import AIWorkflowBuilder, visualize
    
    lang = args.lang or "en"
    
    builder = AIWorkflowBuilder(
        api_key=args.api_key or os.environ.get("OPENAI_API_KEY"),
        base_url=args.base_url,
        lang=lang,
    )
    
    print("=" * 50)
    if lang == "zh":
        print("  Dify 工作流 AI 助手")
        print("=" * 50)
        print("\n描述你想要的工作流，我会帮你生成。")
        print("输入 'save <文件名>' 保存，'quit' 退出。\n")
    else:
        print("  Dify Workflow AI Assistant")
        print("=" * 50)
        print("\nDescribe the workflow you want, and I'll generate it.")
        print("Type 'save <filename>' to save, 'quit' to exit.\n")
    
    workflow = None
    
    while True:
        try:
            user_input = input("> ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ('quit', 'exit', '退出'):
                break
            
            if user_input.lower().startswith('save'):
                if workflow:
                    parts = user_input.split(maxsplit=1)
                    filename = parts[1] if len(parts) > 1 else "workflow.yml"
                    workflow.export(filename)
                    if lang == "zh":
                        print(f"\n[OK] 已保存到 {filename}\n")
                    else:
                        print(f"\n[OK] Saved to {filename}\n")
                else:
                    if lang == "zh":
                        print("\n还没有生成工作流，请先描述你的需求。\n")
                    else:
                        print("\nNo workflow generated yet. Describe what you need first.\n")
                continue
            
            if user_input.lower() == 'reset':
                builder.reset()
                workflow = None
                if lang == "zh":
                    print("\n已重置，请重新描述你的需求。\n")
                else:
                    print("\nReset. Describe what you need.\n")
                continue
            
            if user_input.lower() in ('show', 'preview', '预览'):
                if workflow:
                    print("\n" + visualize(workflow, "tree") + "\n")
                else:
                    if lang == "zh":
                        print("\n还没有生成工作流。\n")
                    else:
                        print("\nNo workflow generated yet.\n")
                continue
            
            # Chat with AI
            complete, response, wf = builder.chat(
                user_input,
                model=args.model or "gpt-4",
            )
            
            print(f"\n{response}\n")
            
            if wf:
                workflow = wf
                
        except KeyboardInterrupt:
            print("\n")
            break
        except Exception as e:
            print(f"\nError: {e}\n")
    
    if lang == "zh":
        print("再见！")
    else:
        print("Goodbye!")


def cmd_template(args):
    """Manage workflow templates"""
    from .templates import TEMPLATES
    
    if args.action == "list":
        print("Available templates:")
        for name, func in TEMPLATES.items():
            doc = func.__doc__ or "No description"
            print(f"  {name:15} - {doc}")
            
    elif args.action == "create":
        name = args.name
        if name not in TEMPLATES:
            print(f"Error: Template '{name}' not found. Use 'list' to see available templates.")
            sys.exit(1)
            
        wf = TEMPLATES[name]()
        output = args.output or f"{name}.yml"
        wf.export(output)
        print(f"[OK] Created {output} from template '{name}'")


def cmd_analyze(args):
    """Analyze a workflow file"""
    import yaml
    from .constants import DSL_VERSION
    
    filepath = args.file
    
    if not os.path.exists(filepath):
        print(f"Error: File not found: {filepath}")
        sys.exit(1)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    app = data.get("app", {})
    workflow = data.get("workflow", {})
    graph = workflow.get("graph", {})
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    
    print(f"\n{'='*50}")
    print(f"Workflow Analysis: {app.get('name', 'Unknown')}")
    print(f"{'='*50}")
    
    # Basic stats
    print(f"\n[Basic Info]")
    print(f"  Mode: {app.get('mode', 'unknown')}")
    print(f"  Description: {app.get('description', 'N/A')[:60]}")
    print(f"  DSL Version: {data.get('version', 'unknown')}")
    
    # Node stats
    print(f"\n[Nodes] Total: {len(nodes)}")
    node_types = {}
    for node in nodes:
        node_type = node.get("data", {}).get("type", "unknown")
        node_types[node_type] = node_types.get(node_type, 0) + 1
    
    for node_type, count in sorted(node_types.items()):
        print(f"  - {node_type:20}: {count}")
    
    # Edge stats
    print(f"\n[Edges] Total: {len(edges)}")
    
    # Complexity metrics
    print(f"\n[Complexity Metrics]")
    # Cyclomatic complexity approximation (edges - nodes + 2)
    if len(nodes) > 0:
        complexity = len(edges) - len(nodes) + 2
        print(f"  Cyclomatic Complexity: ~{complexity}")
    
    # Check for cycles (simplified)
    node_ids = {n.get("id") for n in nodes}
    adjacency = {nid: [] for nid in node_ids}
    for edge in edges:
        src = edge.get("source")
        tgt = edge.get("target")
        if src in adjacency and tgt in adjacency:
            adjacency[src].append(tgt)
    
    # Find start nodes
    targets = {edge.get("target") for edge in edges}
    start_nodes = [n for n in nodes if n.get("id") not in targets]
    print(f"  Start Nodes: {len(start_nodes)}")
    
    # Find end nodes
    sources = {edge.get("source") for edge in edges}
    end_nodes = [n for n in nodes if n.get("id") not in sources]
    print(f"  End Nodes: {len(end_nodes)}")
    
    print(f"\n{'='*50}\n")


def cmd_docs(args):
    """Generate documentation for a workflow"""
    from .docs import generate_docs
    
    filepath = args.file
    format = args.format or "markdown"
    output = args.output
    
    if not os.path.exists(filepath):
        print(f"Error: File not found: {filepath}")
        sys.exit(1)
    
    # Import the workflow first
    import yaml
    from .workflow import Workflow
    from .nodes import (
        StartNode, EndNode, AnswerNode, LLMNode, HTTPNode,
        CodeNode, IfElseNode, TemplateNode, KnowledgeNode,
        VariableAggregatorNode, IterationNode, QuestionClassifierNode,
        ParameterExtractorNode, ToolNode, AssignerNode,
        DocumentExtractorNode, ListFilterNode,
    )
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    # Reconstruct workflow
    app = data.get("app", {})
    graph = data.get("workflow", {}).get("graph", {})
    
    wf = Workflow(
        name=app.get("name", "Workflow"),
        mode=app.get("mode", "workflow"),
        description=app.get("description", ""),
    )
    
    node_classes = {
        "start": StartNode, "end": EndNode, "answer": AnswerNode,
        "llm": LLMNode, "http-request": HTTPNode, "code": CodeNode,
        "if-else": IfElseNode, "template-transform": TemplateNode,
        "knowledge-retrieval": KnowledgeNode, "variable-aggregator": VariableAggregatorNode,
        "iteration": IterationNode, "question-classifier": QuestionClassifierNode,
        "parameter-extractor": ParameterExtractorNode, "tool": ToolNode,
        "assigner": AssignerNode, "document-extractor": DocumentExtractorNode,
        "list-filter": ListFilterNode,
    }
    
    for node_data in graph.get("nodes", []):
        data_section = node_data.get("data", {})
        node_type = data_section.get("type", "start")
        title = data_section.get("title", node_type)
        
        node_class = node_classes.get(node_type, StartNode)
        node = node_class(title=title)
        node.id = node_data.get("id")
        wf.nodes.append(node)
    
    wf.edges = graph.get("edges", [])
    
    # Generate docs
    docs = generate_docs(wf, format=format)
    
    if output:
        with open(output, 'w', encoding='utf-8') as f:
            f.write(docs)
        print(f"[OK] Documentation saved to {output}")
    else:
        print(docs)


def cmd_profile(args):
    """Profile a workflow for performance analysis"""
    from .profiler import analyze_workflow
    import yaml
    from .workflow import Workflow
    from .nodes import (
        StartNode, EndNode, AnswerNode, LLMNode, HTTPNode,
        CodeNode, IfElseNode, TemplateNode, KnowledgeNode,
        VariableAggregatorNode, IterationNode, QuestionClassifierNode,
        ParameterExtractorNode, ToolNode, AssignerNode,
        DocumentExtractorNode, ListFilterNode,
    )
    
    filepath = args.file
    
    if not os.path.exists(filepath):
        print(f"Error: File not found: {filepath}")
        sys.exit(1)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    # Reconstruct workflow
    app = data.get("app", {})
    graph = data.get("workflow", {}).get("graph", {})
    
    wf = Workflow(
        name=app.get("name", "Workflow"),
        mode=app.get("mode", "workflow"),
        description=app.get("description", ""),
    )
    
    node_classes = {
        "start": StartNode, "end": EndNode, "answer": AnswerNode,
        "llm": LLMNode, "http-request": HTTPNode, "code": CodeNode,
        "if-else": IfElseNode, "template-transform": TemplateNode,
        "knowledge-retrieval": KnowledgeNode, "variable-aggregator": VariableAggregatorNode,
        "iteration": IterationNode, "question-classifier": QuestionClassifierNode,
        "parameter-extractor": ParameterExtractorNode, "tool": ToolNode,
        "assigner": AssignerNode, "document-extractor": DocumentExtractorNode,
        "list-filter": ListFilterNode,
    }
    
    for node_data in graph.get("nodes", []):
        data_section = node_data.get("data", {})
        node_type = data_section.get("type", "start")
        title = data_section.get("title", node_type)
        
        node_class = node_classes.get(node_type, StartNode)
        node = node_class(title=title)
        node.id = node_data.get("id")
        wf.nodes.append(node)
    
    wf.edges = graph.get("edges", [])
    
    # Analyze
    profile = analyze_workflow(wf)
    
    from .profiler import WorkflowProfiler
    profiler = WorkflowProfiler()
    profiler.print_report(profile)


def cmd_diff(args):
    """Compare two workflow files"""
    import yaml
    
    file1, file2 = args.files
    
    if not os.path.exists(file1):
        print(f"Error: File not found: {file1}")
        sys.exit(1)
    if not os.path.exists(file2):
        print(f"Error: File not found: {file2}")
        sys.exit(1)
    
    with open(file1, 'r', encoding='utf-8') as f:
        data1 = yaml.safe_load(f)
    with open(file2, 'r', encoding='utf-8') as f:
        data2 = yaml.safe_load(f)
    
    print(f"\nComparing:")
    print(f"  A: {file1}")
    print(f"  B: {file2}")
    print(f"\n{'='*50}\n")
    
    # Compare names
    name1 = data1.get("app", {}).get("name", "Unknown")
    name2 = data2.get("app", {}).get("name", "Unknown")
    if name1 != name2:
        print(f"[Name] A: '{name1}' vs B: '{name2}'")
    
    # Compare nodes
    nodes1 = {n.get("id"): n for n in data1.get("workflow", {}).get("graph", {}).get("nodes", [])}
    nodes2 = {n.get("id"): n for n in data2.get("workflow", {}).get("graph", {}).get("nodes", [])}
    
    only_in_a = set(nodes1.keys()) - set(nodes2.keys())
    only_in_b = set(nodes2.keys()) - set(nodes1.keys())
    in_both = set(nodes1.keys()) & set(nodes2.keys())
    
    if only_in_a:
        print(f"[Nodes] Only in A: {len(only_in_a)}")
        for nid in only_in_a:
            node_type = nodes1[nid].get("data", {}).get("type", "unknown")
            print(f"  - {nodes1[nid].get('data', {}).get('title', nid)} ({node_type})")
    
    if only_in_b:
        print(f"[Nodes] Only in B: {len(only_in_b)}")
        for nid in only_in_b:
            node_type = nodes2[nid].get("data", {}).get("type", "unknown")
            print(f"  - {nodes2[nid].get('data', {}).get('title', nid)} ({node_type})")
    
    # Compare edges
    edges1 = {(e.get("source"), e.get("target")) for e in data1.get("workflow", {}).get("graph", {}).get("edges", [])}
    edges2 = {(e.get("source"), e.get("target")) for e in data2.get("workflow", {}).get("graph", {}).get("edges", [])}
    
    only_edges_a = edges1 - edges2
    only_edges_b = edges2 - edges1
    
    if only_edges_a:
        print(f"[Edges] Only in A: {len(only_edges_a)}")
    if only_edges_b:
        print(f"[Edges] Only in B: {len(only_edges_b)}")
    
    if not (only_in_a or only_in_b or only_edges_a or only_edges_b):
        print("[Result] Workflows are identical in structure")
    
    print(f"\n{'='*50}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Dify Workflow Generator CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  dify-workflow interactive
  dify-workflow interactive --lang zh
  dify-workflow chat --lang zh
  dify-workflow ai "Create a translation workflow"
  dify-workflow build my_workflow.py -o output.yml
  dify-workflow validate workflow.yml
  dify-workflow visualize workflow.yml --format tree
  dify-workflow import workflow.yml -o workflow.py
  dify-workflow analyze workflow.yml
  dify-workflow diff workflow1.yml workflow2.yml
        """,
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Interactive command
    p_interactive = subparsers.add_parser(
        "interactive", aliases=["i"],
        help="Guided interactive workflow creation"
    )
    p_interactive.add_argument("--lang", "-l", choices=["en", "zh"], 
                               help="Language (en=English, zh=Chinese)")
    p_interactive.set_defaults(func=cmd_interactive)
    
    # Chat command (multi-turn AI conversation)
    p_chat = subparsers.add_parser(
        "chat", aliases=["c"],
        help="AI chat session for workflow building"
    )
    p_chat.add_argument("--lang", "-l", choices=["en", "zh"],
                        help="Language (en=English, zh=Chinese)")
    p_chat.add_argument("--model", help="LLM model to use (default: gpt-4)")
    p_chat.add_argument("--api-key", help="OpenAI API key (or set OPENAI_API_KEY)")
    p_chat.add_argument("--base-url", help="Custom API base URL")
    p_chat.set_defaults(func=cmd_chat)
    
    # Import command
    p_import = subparsers.add_parser(
        "import",
        help="Convert Dify YAML to Python code"
    )
    p_import.add_argument("file", help="YAML file to import")
    p_import.add_argument("-o", "--output", help="Output Python file path")
    p_import.set_defaults(func=cmd_import)
    
    # AI command
    p_ai = subparsers.add_parser(
        "ai",
        help="AI-powered workflow generation from description"
    )
    p_ai.add_argument("description", help="Natural language description of the workflow")
    p_ai.add_argument("-o", "--output", help="Output file path (default: workflow.yml)")
    p_ai.add_argument("--lang", "-l", choices=["en", "zh"],
                      help="Language (en=English, zh=Chinese)")
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
    
    # Visualize command
    p_viz = subparsers.add_parser(
        "visualize", aliases=["viz"],
        help="Visualize a workflow"
    )
    p_viz.add_argument("file", help="YAML file to visualize")
    p_viz.add_argument("-f", "--format", choices=["ascii", "tree", "mermaid"],
                       default="tree", help="Output format (default: tree)")
    p_viz.add_argument("-o", "--output", help="Save visualization to file (for mermaid)")
    p_viz.set_defaults(func=cmd_visualize)
    
    # Template command
    p_tpl = subparsers.add_parser(
        "template", aliases=["tpl"],
        help="Use workflow templates"
    )
    p_tpl_sub = p_tpl.add_subparsers(dest="action", help="Template action")
    
    p_tpl_list = p_tpl_sub.add_parser("list", help="List available templates")
    
    p_tpl_create = p_tpl_sub.add_parser("create", help="Create from template")
    p_tpl_create.add_argument("name", help="Template name")
    p_tpl_create.add_argument("-o", "--output", help="Output file path")
    
    p_tpl.set_defaults(func=cmd_template)
    
    # Analyze command
    p_analyze = subparsers.add_parser(
        "analyze", aliases=["a"],
        help="Analyze a workflow file"
    )
    p_analyze.add_argument("file", help="YAML file to analyze")
    p_analyze.set_defaults(func=cmd_analyze)
    
    # Diff command
    p_diff = subparsers.add_parser(
        "diff", aliases=["d"],
        help="Compare two workflow files"
    )
    p_diff.add_argument("files", nargs=2, help="Two YAML files to compare")
    p_diff.set_defaults(func=cmd_diff)
    
    # Docs command
    p_docs = subparsers.add_parser(
        "docs",
        help="Generate documentation for a workflow"
    )
    p_docs.add_argument("file", help="YAML file to document")
    p_docs.add_argument("-f", "--format", choices=["markdown", "html", "json"],
                        default="markdown", help="Output format")
    p_docs.add_argument("-o", "--output", help="Output file path")
    p_docs.set_defaults(func=cmd_docs)
    
    # Profile command
    p_profile = subparsers.add_parser(
        "profile",
        help="Profile a workflow for performance analysis"
    )
    p_profile.add_argument("file", help="YAML file to profile")
    p_profile.set_defaults(func=cmd_profile)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(0)
    
    args.func(args)


if __name__ == "__main__":
    main()
