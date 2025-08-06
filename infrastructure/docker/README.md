# LiteLLM Proxy Docker Setup

This directory contains the Docker Compose configuration for running LiteLLM proxy with PostgreSQL database support.

## Overview

LiteLLM is a unified API proxy that allows you to call 100+ LLM APIs using the same format. This setup provides:

- **LiteLLM Proxy**: Unified interface for multiple LLM providers
- **PostgreSQL**: Persistent storage for API keys and usage tracking
- **Multi-provider support**: OpenAI, Anthropic, Groq, DeepSeek, and more

## Prerequisites

- Docker and Docker Compose installed
- API keys for the LLM providers you want to use

## Quick Start

1. **Copy and configure environment variables:**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add your API keys and configure passwords.

2. **Start the services:**
   ```bash
   docker compose up -d
   ```

3. **Access the LiteLLM proxy:**
   - API Endpoint: `http://localhost:4000`
   - Health Check: `http://localhost:4000/health`
   - Available Models: `http://localhost:4000/models`

## Configuration

### Environment Variables

Key environment variables in `.env`:

- `LITELLM_MASTER_KEY`: Master API key for LiteLLM admin access
- `POSTGRES_PASSWORD`: PostgreSQL password
- `OPENAI_API_KEY`: OpenAI API key
- `ANTHROPIC_API_KEY`: Anthropic API key
- `GROQ_API_KEY`: Groq API key
- `DEEPSEEK_API_KEY`: DeepSeek API key

### Model Configuration

Models are configured in `litellm-config.yaml`. The configuration includes:

- **OpenAI**: GPT-4, GPT-3.5-turbo, O3-mini
- **Anthropic**: Claude 4 Opus/Sonnet, Claude 3.5 Sonnet/Haiku
- **Groq**: Llama 3.3, Gemma 2, Whisper
- **DeepSeek**: DeepSeek Chat and Reasoner

To add or modify models, edit the `model_list` section in `litellm-config.yaml`.

## Usage Examples

### Using the Proxy with curl

```bash
# Set your API key
export LITELLM_API_KEY="sk-1234"  # Use the LITELLM_MASTER_KEY from .env

# Make a request
curl -X POST http://localhost:4000/v1/chat/completions \
  -H "Authorization: Bearer $LITELLM_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

### Using with OpenAI Python SDK

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:4000/v1",
    api_key="sk-1234"  # Your LITELLM_MASTER_KEY
)

response = client.chat.completions.create(
    model="claude-3.5-sonnet",
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response.choices[0].message.content)
```

## Managing the Services

```bash
# Start services
docker compose up -d

# Stop services
docker compose down

# View logs
docker compose logs -f litellm

# Restart services
docker compose restart

# Check service status
docker compose ps
```

## Database Access

PostgreSQL is exposed on `localhost:5440` for debugging:

```bash
# Connect to PostgreSQL
psql -h localhost -p 5440 -U postgres -d litellm
# Password: (from POSTGRES_PASSWORD in .env)
```

## Troubleshooting

1. **Service won't start:**
   - Check if ports 4000 and 5440 are available
   - Verify Docker and Docker Compose are installed
   - Check logs: `docker compose logs`

2. **API calls failing:**
   - Verify API keys are set correctly in `.env`
   - Check model names match configuration
   - Ensure LiteLLM service is running: `docker compose ps`

3. **Database connection issues:**
   - Ensure PostgreSQL is healthy: `docker compose ps`
   - Check PostgreSQL logs: `docker compose logs postgres`

## Backup and Restore

### Backup PostgreSQL data
```bash
docker exec litellm-postgres pg_dump -U postgres litellm > backup.sql
```

### Restore PostgreSQL data
```bash
docker exec -i litellm-postgres psql -U postgres litellm < backup.sql
```

## Additional Resources

- [LiteLLM Documentation](https://docs.litellm.ai/)
- [Supported Models](https://docs.litellm.ai/docs/providers)
- [API Reference](https://docs.litellm.ai/docs/proxy/user_keys)

## Notes

- The master key (`LITELLM_MASTER_KEY`) has full admin access
- PostgreSQL data is persisted in a Docker volume
- All services restart automatically unless stopped manually

## Migration from Langfuse

This setup previously included Langfuse for observability. If you need Langfuse, we recommend:
1. Following the [official Langfuse Docker deployment guide](https://langfuse.com/self-hosting/docker-compose)
2. Cloning the Langfuse repository directly for simpler setup
3. Running Langfuse separately from your LiteLLM proxy