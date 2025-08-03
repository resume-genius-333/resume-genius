# Langfuse + LiteLLM Docker Setup

This directory contains Docker Compose configuration for running Langfuse (LLM observability platform) and LiteLLM (LLM proxy) together.

## Services

- **Langfuse** (port 3000): LLM observability platform for monitoring, debugging, and analyzing LLM applications
- **LiteLLM** (port 4000): Universal LLM proxy supporting 100+ LLM providers with unified API
- **PostgreSQL**: Database for both Langfuse and LiteLLM
- **ClickHouse**: Analytics database for Langfuse
- **Redis**: Cache for both services
- **MinIO**: S3-compatible object storage for Langfuse media uploads

## Prerequisites

- Docker and Docker Compose installed
- At least 4 CPU cores and 16GB RAM
- 100GB available disk space (recommended)

## Quick Start

1. **Clone and navigate to the directory:**
   ```bash
   cd infrastructure/docker
   ```

2. **Create environment file:**
   ```bash
   cp .env.example .env
   ```

3. **Generate secure keys:**
   ```bash
   # Generate SALT
   openssl rand -base64 32
   
   # Generate ENCRYPTION_KEY
   openssl rand -hex 32
   
   # Generate NEXTAUTH_SECRET
   openssl rand -base64 32
   ```

4. **Update `.env` file:**
   - Replace all placeholder passwords with secure values
   - Add your LLM provider API keys (OpenAI, Anthropic, etc.)
   - Update the generated security keys

5. **Start the services:**
   ```bash
   docker compose up -d
   ```

6. **Access the services:**
   - Langfuse: http://localhost:3000
   - LiteLLM: http://localhost:4000
   - MinIO Console: http://localhost:9001 (login: minio / your-password)

## Configuration

### LiteLLM Configuration

Edit `litellm-config.yaml` to:
- Add/remove LLM providers
- Configure model aliases
- Set up rate limiting
- Configure caching

### Langfuse Integration

After first login to Langfuse:
1. Create a new project
2. Copy the public and secret keys from project settings
3. Update these keys in your `.env` file:
   - `LANGFUSE_PUBLIC_KEY`
   - `LANGFUSE_SECRET_KEY`
4. Restart the LiteLLM container: `docker compose restart litellm`

## Using LiteLLM with Langfuse

Once configured, LiteLLM will automatically send telemetry to Langfuse. Use the LiteLLM proxy endpoint in your applications:

```python
import openai

# Point to LiteLLM proxy
openai.api_base = "http://localhost:4000"
openai.api_key = "your-litellm-master-key"  # From .env

# Use any configured model
response = openai.ChatCompletion.create(
    model="gpt-4",  # or "claude-3-opus", etc.
    messages=[{"role": "user", "content": "Hello!"}]
)
```

## Managing Services

```bash
# Start all services
docker compose up -d

# Stop all services
docker compose down

# View logs
docker compose logs -f [service-name]

# Restart a specific service
docker compose restart [service-name]

# Update to latest versions
docker compose pull
docker compose up -d
```

## Data Persistence

All data is persisted in Docker volumes:
- `langfuse_postgres_data`: PostgreSQL data
- `langfuse_clickhouse_data`: ClickHouse data
- `langfuse_minio_data`: MinIO object storage

To backup, use Docker volume backup commands or database-specific backup tools.

## Security Recommendations

1. **Change all default passwords** in the `.env` file
2. **Use strong, unique values** for all security keys
3. **Restrict network access** - by default, services are bound to localhost
4. **Enable HTTPS** in production using a reverse proxy
5. **Regularly update** Docker images for security patches

## Troubleshooting

### Services not starting
- Check logs: `docker compose logs [service-name]`
- Ensure all required environment variables are set
- Verify port availability

### Connection issues between services
- Services communicate via the `langfuse-network` Docker network
- Use service names (not localhost) for inter-service communication

### Performance issues
- Increase Docker Desktop memory allocation
- Check ClickHouse logs for query performance
- Monitor PostgreSQL connection pool

## Additional Resources

- [Langfuse Documentation](https://langfuse.com/docs)
- [LiteLLM Documentation](https://docs.litellm.ai/)
- [Docker Compose Reference](https://docs.docker.com/compose/)