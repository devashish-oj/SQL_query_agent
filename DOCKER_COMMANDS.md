# Docker Quick Reference

## Build and Start

```bash
# Build and start all services
docker compose up -d

# Build and start with forced rebuild
docker compose up -d --build

# View logs
docker compose logs -f

# Stop services
docker compose down

# Stop and remove all data
docker compose down -v
```

## Image Commands

```bash
# Build just the app image
docker compose build query-agent

# View images
docker images

# Remove image
docker rmi query-agent-app
```

## Container Management

```bash
# View running containers
docker compose ps

# Restart a service
docker compose restart query-agent

# Execute command in container
docker exec -it query-agent-app bash

# Access PostgreSQL
docker exec -it query-agent-postgres psql -U queryagent -d sampledb
```

## Logs and Debugging

```bash
# View all logs
docker compose logs

# Follow logs
docker compose logs -f

# Service-specific logs
docker compose logs query-agent
docker compose logs postgres

# Last N lines
docker compose logs --tail=50 query-agent
```

## Configuration

All environment variables are in `compose.yaml`:

- **Database**: POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB
- **API**: GEMINI_API_KEY
- **App**: APP_HOST, APP_PORT, DEBUG

## Health Checks

```bash
# Check container health
docker compose ps

# Test app health endpoint
curl http://localhost:8000/health

# Test database
docker exec query-agent-postgres pg_isready -U queryagent
```

## Production Tips

1. Change default passwords in `compose.yaml`
2. Set `DEBUG: "False"`
3. Use Docker secrets for sensitive data
4. Add resource limits
5. Use docker-compose profiles for different environments

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Port already in use | Change port in `compose.yaml` |
| Can't connect to DB | Check `docker compose logs postgres` |
| App won't start | Check `docker compose logs query-agent` |
| Gemini API error | Verify API key in `compose.yaml` |
