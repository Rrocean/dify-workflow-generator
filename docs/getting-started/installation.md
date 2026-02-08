# Installation

## Requirements

- Python 3.9 or higher
- pip or poetry for package management

## Install from PyPI

```bash
pip install dify-workflow-generator
```

## Install with Optional Dependencies

### Web Interface Support
```bash
pip install "dify-workflow-generator[web]"
```

### Interactive Features
```bash
pip install "dify-workflow-generator[interactive]"
```

### All Features
```bash
pip install "dify-workflow-generator[all]"
```

### Development
```bash
pip install "dify-workflow-generator[dev]"
```

## Install from Source

```bash
git clone https://github.com/yourusername/dify-workflow-generator.git
cd dify-workflow-generator
pip install -e ".[dev]"
```

## Verify Installation

```bash
dify-workflow --version
```

## Docker Installation

### Using Docker Compose

```bash
docker-compose up -d
```

### Using Docker

```bash
docker build -t dify-workflow .
docker run -p 8765:8765 dify-workflow
```

## Environment Setup

Create a `.env` file:

```bash
# OpenAI API Key (for AI-powered features)
OPENAI_API_KEY=your_key_here

# Database URL (optional)
DIFY_WORKFLOW_DB_URL=sqlite:///data/workflows.db

# Redis URL (optional, for caching)
REDIS_URL=redis://localhost:6379/0
```
