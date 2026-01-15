# AVER Baseline Purple Agent

A simple A2A-compliant agent for testing the AVER benchmark. This is a **baseline agent** - it follows instructions but has minimal error detection capabilities, making it useful for benchmarking.

## Quick Start

### Local Development

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Add your OpenRouter API key
# Get one at: https://openrouter.ai/keys

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the agent
python agent.py
```

The agent will be available at `http://localhost:8001`

### Docker

```bash
# Build image
docker build -t aver-baseline-purple .

# Run container
docker run -d \
  -p 8001:8001 \
  -e OPENROUTER_API_KEY=your_key_here \
  -e AGENT_MODEL=anthropic/claude-3.5-sonnet \
  aver-baseline-purple
```

## A2A Protocol Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/agent-card` | GET | Agent capabilities |
| `/reset` | POST | Reset agent state |
| `/message` | POST | Main message handler |
| `/configure` | POST | Runtime configuration |

## Message Format

Send messages in A2A format:

```json
{
  "role": "user",
  "content": "Your task description here",
  "context_id": "unique-context-id",
  "metadata": {
    "model": "anthropic/claude-3.5-sonnet"
  }
}
```

## Supported Models (via OpenRouter)

- `anthropic/claude-3.5-sonnet` (default)
- `anthropic/claude-3-opus`
- `openai/gpt-4-turbo`
- `openai/gpt-4o`
- `google/gemini-pro`
- `google/gemini-1.5-flash`
- `deepseek/deepseek-coder`
- `meta-llama/llama-3.1-70b-instruct`
- And 100+ more at [OpenRouter Models](https://openrouter.ai/models)

## AgentBeats Integration

To use with AgentBeats:

1. Push Docker image to a public registry:
   ```bash
   docker tag aver-baseline-purple ghcr.io/your-username/aver-baseline-purple:latest
   docker push ghcr.io/your-username/aver-baseline-purple:latest
   ```

2. Register on AgentBeats with the image URL

3. Update your `scenario.toml`:
   ```toml
   [[participants]]
   role = "purple_agent"
   agentbeats_id = "your-agent-id"
   ```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENROUTER_API_KEY` | (required) | Your OpenRouter API key |
| `AGENT_MODEL` | `anthropic/claude-3.5-sonnet` | Default model |
| `AGENT_PORT` | `8001` | Server port |
| `AGENT_NAME` | `AVER Baseline Purple Agent` | Agent identifier |

## License

MIT
