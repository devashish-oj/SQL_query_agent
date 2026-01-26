# 🚀 Quick Start with Docker

This guide will help you run the PostgreSQL Query Agent using Docker and Docker Compose.

## Prerequisites

- Docker installed ([Installation Guide](https://docs.docker.com/get-docker/))
- Docker Compose (included with Docker Desktop)
- Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))

## Quick Start (2 Steps)

### 1. Configure Your Gemini API Key

Edit `compose.yaml` and replace `your_gemini_api_key_here` with your actual Gemini API key:

```yaml
# Google Gemini API Key - REPLACE WITH YOUR ACTUAL KEY
GEMINI_API_KEY: your_actual_gemini_api_key_here
```

**Optional:** You can also change the PostgreSQL credentials in the same file if needed.

### 2. Start the Services

```bash
docker compose up -d
```

This will:
- ✅ Pull the PostgreSQL image
- ✅ Build the application container
- ✅ Create a sample database with test data
- ✅ Start both services

### 3. Access the Application

Open your browser to:

```
http://localhost:8000
```

## What's Included

The `compose.yaml` sets up:

1. **PostgreSQL Database** (port 5432)
   - Username: `queryagent`
   - Password: `secure_password_123`
   - Database: `sampledb`
   - Pre-loaded with sample tables (users, products, orders)

2. **Query Agent Application** (port 8000)
   - Web interface for query generation
   - Google Gemini AI integration
   - MCP client for PostgreSQL

## Useful Commands

### View logs
```bash
# All services
docker compose logs -f

# Just the app
docker compose logs -f query-agent

# Just the database
docker compose logs -f postgres
```

### Stop services
```bash
docker compose down
```

### Stop and remove volumes (⚠️ deletes data)
```bash
docker compose down -v
```

### Rebuild after code changes
```bash
docker compose up -d --build
```

### Access PostgreSQL directly
```bash
docker exec -it query-agent-postgres psql -U queryagent -d sampledb
```

## Sample Queries to Try

Once the application is running, try these natural language queries:

1. **"Show me all users"**
2. **"List products with price greater than 100"**
3. **"Insert a new user with username 'alice' and email 'alice@example.com'"**
4. **"Update the price of product named 'Laptop' to 1199.99"**
5. **"Delete orders with status 'cancelled'"**

## Configuration

### All Credentials in One Place

All credentials are configured in `compose.yaml` under the `environment` section:

```yaml
environment:
  # PostgreSQL Database
  POSTGRES_HOST: postgres
  POSTGRES_PORT: 5432
  POSTGRES_USER: queryagent
  POSTGRES_PASSWORD: secure_password_123
  POSTGRES_DB: sampledb
  
  # Google Gemini API Key - REPLACE WITH YOUR ACTUAL KEY
  GEMINI_API_KEY: your_gemini_api_key_here
```

**To customize:**
1. Open `compose.yaml`
2. Update the values under the `query-agent` service's `environment` section
3. Save and restart: `docker compose up -d`

## Troubleshooting

### "Port already in use"

Change the port mapping in `compose.yaml`:
```yaml
ports:
  - "8001:8000"  # Use 8001 instead of 8000
```

### Application won't start

Check logs:
```bash
docker compose logs query-agent
```

Common issues:
- Missing Gemini API key in `compose.yaml`
- PostgreSQL not ready (wait 30s and check again)

### Database connection failed

Ensure PostgreSQL is healthy:
```bash
docker compose ps
```

You should see both services as "healthy" or "running".

## Sample Database Schema

The `init-db.sql` creates these tables:

- **users** - User accounts (id, username, email, full_name, created_at, is_active)
- **products** - Product catalog (id, name, description, price, stock_quantity, category)
- **orders** - Order records (id, user_id, order_date, total_amount, status)
- **order_items** - Order line items (id, order_id, product_id, quantity, unit_price)

All tables have foreign key relationships and indexes for performance.

## Production Deployment

For production use:

1. **Change default passwords** in `compose.yaml`
2. **Use secrets** instead of environment variables
3. **Set `DEBUG: "False"`** in the compose file
4. **Add SSL/TLS** with a reverse proxy (nginx/traefik)
5. **Use persistent volumes** for PostgreSQL data (already configured)
6. **Set resource limits** in the compose file

## Architecture

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │ :8000
┌──────▼──────────────┐
│  Query Agent App    │
│  (Gemini AI)        │
└──────┬──────────────┘
       │ :5432
┌──────▼──────────────┐
│  PostgreSQL DB      │
│  (Sample Data)      │
└─────────────────────┘
```

## Next Steps

- Browse the database schema in the left sidebar
- Try generating different types of queries
- Review generated SQL before executing
- Copy queries to use in your own database tools

---

**Note:** This application ONLY generates SQL queries. It does NOT execute them on the database. Always review queries before running them.
