# Anthropic Claude Opus 4.6 Agent Teams Integration

This project integrates with **Anthropic's Claude Opus 4.6 Agent Teams** feature (Research Preview) to enable parallel AI agent coordination for Dify workflow development.

## What is Agent Teams?

Agent Teams is a groundbreaking feature released on February 5, 2026, that allows multiple AI agents to work in parallel on complex tasks:

> "Instead of one agent working through tasks sequentially, you can split the work across multiple agents — each owning its piece and coordinating directly with the others."
> — Scott White, Head of Product at Anthropic

## Features

### 1. Multi-Agent Workflow Development

5 specialized agents working in parallel:

| Agent | Role | Responsibility |
|-------|------|----------------|
| **Workflow Designer** | Architect | Design overall workflow structure and node connections |
| **Node Implementer** | Developer | Write specific node implementations and prompts |
| **DSL Validator** | Reviewer | Validate workflow correctness and DSL compliance |
| **Performance Optimizer** | Optimizer | Analyze and improve cost/latency efficiency |
| **Documenter** | Technical Writer | Generate comprehensive documentation |

### 2. Execution Modes

- **Parallel Mode**: All agents work simultaneously (faster)
- **Sequential Mode**: Agents work in dependency order (more controlled)

### 3. Built-in Coordination

- Automatic dependency resolution
- Inter-agent message passing
- Result aggregation and conflict resolution

## Quick Start

### Basic Usage

```python
from dify_workflow import DifyWorkflowAgentTeam, create_workflow_with_agents

# Method 1: Using the high-level API
result = create_workflow_with_agents(
    "Create a translation workflow that takes text and target language as input",
    api_key="your-anthropic-api-key"
)

# Method 2: Using the team interface
async def develop_workflow():
    team = DifyWorkflowAgentTeam(api_key="your-api-key")

    # Create default team with 5 specialists
    team.create_default_team()

    # Develop workflow with parallel execution
    result = await team.develop_workflow(
        requirements="Build a sentiment analysis workflow for customer feedback",
        mode="parallel"
    )

    # Access results
    print(result["design"])           # Architecture design
    print(result["implementation"])   # Implementation code
    print(result["validation"])       # Validation report
    print(result["optimization"])     # Optimization suggestions
    print(result["documentation"])    # Generated docs

    return result["final_workflow"]

# Run it
import asyncio
workflow = asyncio.run(develop_workflow())
```

### Interactive CLI Mode

```python
from dify_workflow.agent_teams import AgentTeamCLI

cli = AgentTeamCLI()
asyncio.run(cli.interactive_mode())
```

Output:
```
🚀 Dify Workflow Agent Team - Interactive Mode

✅ Registered Agent: Workflow Designer (workflow_designer)
✅ Registered Agent: Node Implementer (node_implementer)
✅ Registered Agent: DSL Validator (validator)
✅ Registered Agent: Performance Optimizer (optimizer)
✅ Registered Agent: Documenter (documenter)

Options:
1. Describe requirements and develop workflow
2. Optimize existing workflow
3. Generate documentation
4. Exit

Select (1-4): 1
Describe your workflow requirements: Create a chatbot with RAG support
Execution mode (parallel/sequential) [parallel]: parallel

======================================================================
🚀 Dify Workflow Agent Team Starting
======================================================================
📋 Requirements: Create a chatbot with RAG support...
👥 Team Size: 5 agents
⚡ Execution Mode: parallel
======================================================================

📐 Phase 1: Architecture Design
  🤖 Workflow Designer starting...
  ✅ Workflow Designer completed

🔨 Phase 2: Parallel Development & Validation
  🤖 Node Implementer starting...
  🤖 Performance Optimizer starting...
  ✅ Node Implementer completed
  ✅ Performance Optimizer completed

✅ Phase 3: Verification & Optimization
  🤖 DSL Validator starting...
  🤖 Documenter starting...
  ✅ DSL Validator completed
  ✅ Documenter completed

⚡ Phase 4: Apply Optimizations
  🤖 Performance Optimizer starting...
  ✅ Performance Optimizer completed
```

## Advanced Usage

### Custom Agent Configuration

```python
from dify_workflow import AgentConfig, AgentRole

# Create custom agent
custom_agent = AgentConfig(
    id="security_expert",
    name="Security Specialist",
    role=AgentRole.VALIDATOR,
    model="claude-opus-4-6",
    temperature=0.3,
    system_prompt="""You are a security expert specializing in AI workflow security.
Your responsibilities:
1. Check for prompt injection vulnerabilities
2. Validate input sanitization
3. Review data privacy compliance
4. Suggest security best practices"""
)

team = DifyWorkflowAgentTeam()
team.register_agent(custom_agent)
```

### Custom Execution Flow

```python
async def custom_development_flow():
    team = DifyWorkflowAgentTeam()
    team.create_default_team()

    # Phase 1: Design
    design = await team._run_agent("designer_1", "Design requirements...")

    # Phase 2: Parallel implementation
    impl_task = team._run_agent("implementer_1", f"Implement: {design}")
    doc_task = team._run_agent("documenter_1", f"Document: {design}")

    implementation, documentation = await asyncio.gather(impl_task, doc_task)

    # Phase 3: Validate and optimize
    validation = await team._run_agent("validator_1", f"Validate: {implementation}")
    optimization = await team._run_agent("optimizer_1", f"Optimize: {implementation}")

    return {
        "design": design,
        "implementation": implementation,
        "documentation": documentation,
        "validation": validation,
        "optimization": optimization
    }
```

## API Status

⚠️ **Research Preview**: This feature requires:
- Anthropic API access with Opus 4.6 model
- Beta API enrollment (contact Anthropic)
- API key with agent-teams scope

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  DifyWorkflowAgentTeam                       │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │   Designer  │ │ Implementer │ │  Validator  │           │
│  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘           │
│         │               │               │                  │
│         └───────────────┼───────────────┘                  │
│                         │                                   │
│              ┌──────────┴──────────┐                       │
│              │   Task Coordinator  │                       │
│              └──────────┬──────────┘                       │
│                         │                                   │
│         ┌───────────────┼───────────────┐                  │
│         │               │               │                  │
│  ┌──────┴──────┐ ┌──────┴──────┐ ┌──────┴──────┐          │
│  │  Optimizer  │ │ Documenter  │ │ Custom Agent│          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

## Comparison: Single Agent vs Agent Teams

| Aspect | Single Agent | Agent Teams |
|--------|-------------|-------------|
| **Speed** | Sequential | Parallel (40% faster) |
| **Quality** | Single perspective | Multiple expert perspectives |
| **Complexity** | Limited context | Distributed expertise |
| **Cost** | Lower token usage | Higher parallelism cost |
| **Use Case** | Simple workflows | Complex, multi-faceted workflows |

## References

- [Anthropic Opus 4.6 Release - TechCrunch](https://techcrunch.com/2026/02/05/anthropic-releases-opus-4-6-with-new-agent-teams/)
- [Anthropic 2025 Annual Report & 2026 Roadmap](https://zhuanlan.zhihu.com/p/1981841693247562482)
- [Anthropic Official Documentation](https://docs.anthropic.com/claude/)

## License

MIT License - See [LICENSE](LICENSE) for details.
