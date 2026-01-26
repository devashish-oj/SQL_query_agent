# Simplified Deployment Guide

## All Credentials in One File! 🎯

No more `.env` files to manage. Everything is in `podman-compose.yaml`.

## Quick Setup

### Step 1: Edit compose.yaml

Open the file and find this section (around line 38-42):

```yaml
# Google Gemini API Key - REPLACE WITH YOUR ACTUAL KEY
GEMINI_API_KEY: your_gemini_api_key_here
```

Replace `your_gemini_api_key_here` with your actual Gemini API key.

### Step 2: (Optional) Customize Database Credentials

If you want to change PostgreSQL credentials, edit these lines (around line 10-12 and 35-39):

```yaml
# PostgreSQL service
POSTGRES_USER: queryagent
POSTGRES_PASSWORD: secure_password_123
POSTGRES_DB: sampledb

# Query Agent app (must match above)
POSTGRES_USER: queryagent
POSTGRES_PASSWORD: secure_password_123
POSTGRES_DB: sampledb
```

### Step 3: Start

```bash
docker compose up -d
```

### Step 4: Access

```
http://localhost:8000
```

## That's It!

No `.env` files, no templates, no confusion. One file has everything.

## All Environment Variables

Here's what's configured in `compose.yaml`:

| Variable | Location | Purpose |
|----------|----------|---------|
| `POSTGRES_USER` | postgres service + app | Database username |
| `POSTGRES_PASSWORD` | postgres service + app | Database password |
| `POSTGRES_DB` | postgres service + app | Database name |
| `GEMINI_API_KEY` | app only | Google Gemini API key |
| `POSTGRES_HOST` | app only | Database hostname (always "postgres") |
| `POSTGRES_PORT` | app only | Database port (always 5432) |
| `APP_HOST` | app only | Application host (always 0.0.0.0) |
| `APP_PORT` | app only | Application port (always 8000) |
| `DEBUG` | app only | Debug mode (True/False) |

## Production Deployment

For production, change these values:

1. **Strong password**: Replace `secure_password_123` with a strong password
2. **Disable debug**: Set `DEBUG: "False"`
3. **Consider secrets**: Use Docker/Kubernetes secrets for sensitive data

## Example: Production-Ready Config

```yaml
environment:
  POSTGRES_USER: queryagent_prod
  POSTGRES_PASSWORD: Xy9$mK2#pL8@qR5!nV3^
  POSTGRES_DB: production_db
  GEMINI_API_KEY: AIzaSyD_actual_key_here_very_long
  DEBUG: "False"
```

---

**Remember**: The application ONLY generates SQL queries. It never executes them!
