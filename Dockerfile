FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy application code
COPY catalyst_mcp/ ./catalyst_mcp/
COPY knowledge-packs/ ./knowledge-packs/
COPY setup.py .

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create minimal README for setup.py
RUN echo "# Catalyst MCP Server" > README.md

# Install the package
RUN pip install -e .

# Expose the port
EXPOSE 8443

# Set environment variables with defaults
ENV SPLUNK_URL=https://localhost:8089
ENV SPLUNK_VERIFY_SSL=false
ENV PYTHONPATH=/app

# Command to run the FastMCP server
CMD ["python", "-m", "catalyst_mcp.main"]