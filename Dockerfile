# Multi-stage build for Dify Workflow Generator
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml .
RUN pip install --user --no-cache-dir -e ".[web,interactive,dev]"

# Production stage
FROM python:3.11-slim as production

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY dify_workflow/ ./dify_workflow/
COPY web/ ./web/
COPY examples/ ./examples/
COPY README.md .
COPY LICENSE .

# Create directories for data
RUN mkdir -p /app/data /app/workflows

# Expose ports for web server and API
EXPOSE 8765

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8765/api/templates')" || exit 1

# Default command
CMD ["python", "-m", "uvicorn", "web.app:app", "--host", "0.0.0.0", "--port", "8765"]

# Development stage
FROM production as development

# Install dev dependencies
RUN pip install --user --no-cache-dir pytest pytest-asyncio pytest-cov black ruff mypy

# Copy tests
COPY tests/ ./tests/

ENV PYTHONPATH=/app
ENV DEVELOPMENT=true

CMD ["python", "-m", "uvicorn", "web.app:app", "--host", "0.0.0.0", "--port", "8765", "--reload"]
