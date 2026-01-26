FROM node:20-alpine

WORKDIR /app

# Install MCP PostgreSQL server
RUN npm install -g @modelcontextprotocol/server-postgres

# Copy entrypoint script
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
