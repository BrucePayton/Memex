FROM python:3.12-slim

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser -d /home/appuser -s /sbin/nologin appuser \
    && mkdir -p /home/appuser /data /app/logs \
    && chown -R appuser:appuser /home/appuser /data /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /home/appuser

# Copy dependency definitions first (Docker layer cache)
COPY pyproject.toml .
COPY mcp-server/requirements-graph.txt ./mcp-server/

# Install Python dependencies
RUN pip install --no-cache-dir --root-user-action=ignore '.[graph]' 2>/dev/null || \
    pip install --no-cache-dir --root-user-action=ignore 'mcp>=1.2,<2'

# Copy application code
COPY --chown=appuser:appuser dashboard/ ./dashboard/
COPY --chown=appuser:appuser mcp-server/ ./mcp-server/
COPY --chown=appuser:appuser projects.json .
COPY --chown=appuser:appuser CLAUDE.md .
COPY --chown=appuser:appuser README.md .

ENV PYTHONPATH=/home/appuser/dashboard

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/')" || exit 1

CMD ["python3", "-m", "dashboard.server"]
