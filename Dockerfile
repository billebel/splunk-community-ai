FROM python:3.13-slim

WORKDIR /app

# Install system dependencies including git for pip install from git
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy application code
COPY knowledge-packs/ ./knowledge-packs/
COPY setup.py .
COPY README.md .

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install catalyst_mcp from the external git repository
RUN pip install --no-cache-dir git+https://github.com/billebel/catalyst_mcp.git

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