# AVER Baseline Purple Agent
# A2A-compliant agent for benchmark evaluation

FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy agent code
COPY agent.py .

# Default environment variables (override at runtime)
ENV AGENT_PORT=8001
ENV AGENT_MODEL=anthropic/claude-3.5-sonnet
ENV AGENT_NAME="AVER Baseline Purple Agent"

# Expose the agent port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/ || exit 1

# Run the agent
CMD ["python", "agent.py"]
