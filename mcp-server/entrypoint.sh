#!/bin/sh

# Build PostgreSQL connection URL from environment variables
DB_URL="postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}"

echo "Starting MCP PostgreSQL Server..."
echo "Connecting to: ${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB} as ${POSTGRES_USER}"

# Start MCP server
exec npx -y @modelcontextprotocol/server-postgres "$DB_URL"
