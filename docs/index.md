# Dify Workflow Generator

<p align="center">
  <img src="assets/logo.png" alt="Dify Workflow Generator Logo" width="200"/>
</p>

<p align="center">
  <strong>World-class workflow creation and management platform for Dify</strong>
</p>

<p align="center">
  <a href="https://github.com/yourusername/dify-workflow-generator/actions">
    <img src="https://github.com/yourusername/dify-workflow-generator/workflows/CI/badge.svg" alt="CI Status"/>
  </a>
  <a href="https://codecov.io/gh/yourusername/dify-workflow-generator">
    <img src="https://codecov.io/gh/yourusername/dify-workflow-generator/branch/main/graph/badge.svg" alt="Coverage"/>
  </a>
  <a href="https://pypi.org/project/dify-workflow-generator/">
    <img src="https://img.shields.io/pypi/v/dify-workflow-generator.svg" alt="PyPI Version"/>
  </a>
  <a href="https://pypi.org/project/dify-workflow-generator/">
    <img src="https://img.shields.io/pypi/pyversions/dify-workflow-generator.svg" alt="Python Versions"/>
  </a>
  <a href="LICENSE">
    <img src="https://img.shields.io/github/license/yourusername/dify-workflow-generator.svg" alt="License"/>
  </a>
</p>

---

## Features

- **17+ Node Types**: Complete support for all Dify workflow nodes
- **Fluent API**: Intuitive, chainable Python API
- **CLI Tool**: Powerful command-line interface
- **Web UI**: Modern web-based workflow editor
- **Templates**: 9 built-in workflow templates
- **Plugin System**: Extensible architecture
- **Performance Profiling**: Cost and latency estimation
- **Batch Processing**: Generate workflows at scale
- **Type Safety**: Full type hints and validation

## Quick Start

### Installation

```bash
pip install dify-workflow-generator
```

### Create Your First Workflow

```python
from dify_workflow import WorkflowBuilder

# Create a translation workflow
wf = (WorkflowBuilder("Translator")
    .start_with([
        {"name": "text", "type": "string"},
        {"name": "target_language", "type": "string", "default": "English"}
    ])
    .llm("Translate the following text to {{#start.target_language#}}:\n{{#start.text#}}")
    .end(outputs={"translation": "{{#llm_0.text#}}"})
    .build())

# Export to Dify format
wf.export("translator.yml")
```

### CLI Usage

```bash
# List available templates
dify-workflow template list

# Create from template
dify-workflow template create translation --output translator.yml

# Validate workflow
dify-workflow validate translator.yml

# Visualize workflow
dify-workflow visualize translator.yml --format tree
```

## Web Interface

Start the web server:

```bash
dify-workflow web --port 8765
```

Then open http://localhost:8765 in your browser.

## Documentation

- [Installation](getting-started/installation.md)
- [Quick Start Guide](getting-started/quickstart.md)
- [CLI Documentation](getting-started/cli.md)
- [API Reference](api/workflow.md)
- [Advanced Topics](advanced/plugins.md)

## Contributing

We welcome contributions! See our [Contributing Guide](development/contributing.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/yourusername/dify-workflow-generator/blob/main/LICENSE) file for details.

## Support

- GitHub Issues: [Report bugs or request features](https://github.com/yourusername/dify-workflow-generator/issues)
- Discussions: [Ask questions or share ideas](https://github.com/yourusername/dify-workflow-generator/discussions)
