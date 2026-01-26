# PostgreSQL Query Generation Agent 🤖

An intelligent agentic application that connects to PostgreSQL databases via MCP (Model Context Protocol) and generates SQL queries from natural language requests. **Important:** This agent only generates queries—it does NOT execute them, ensuring maximum safety for your database.

![PostgreSQL Query Agent](https://img.shields.io/badge/PostgreSQL-Query_Agent-blue)
![Python](https://img.shields.io/badge/Python-3.9+-green)
![FastAPI](https://img.shields.io/badge/FastAPI-Latest-teal)
![Claude](https://img.shields.io/badge/Claude-AI-purple)

## ✨ Features

- 🔍 **Natural Language to SQL**: Convert plain English requests into valid PostgreSQL queries
- 📊 **Schema Browsing**: Interactive database schema viewer with tables, columns, and relationships
- 🛡️ **Safety First**: Queries are only generated and displayed, never executed automatically
- 🎯 **Smart Query Generation**: Powered by Google Gemini AI for intelligent, context-aware SQL generation
- 📝 **Query History**: Track your recent query requests for easy reuse
- ⚡ **Real-time Validation**: Automatic safety checks for potentially dangerous queries
- 🎨 **Modern UI**: Beautiful, responsive interface with dark theme and glassmorphism effects
- 🐳 **Container Ready**: Easy deployment with Podman/Docker Compose
- 💬 **Streamlit Chatbot**: Alternative chat-based interface for interactive query generation

## 🏗️ Architecture

```
┌─────────────────┐
│  Web Interface  │
└────────┬────────┘
         │
    ┌────▼─────┐
    │ FastAPI  │
    │  Backend │
    └────┬─────┘
         │
    ┌────▼──────────┐
    │ Query Agent   │
    │ (Claude LLM)  │
    └────┬──────────┘
         │
    ┌────▼──────────┐
    │  MCP Client   │
    └────┬──────────┘
         │
    ┌────▼──────────┐
    │  PostgreSQL   │
    │   Database    │
    └───────────────┘
```

## 📋 Prerequisites

- Python 3.9 or higher (for local setup)
- PostgreSQL database
- Node.js and npm (for MCP server)
- Google Gemini API key
- **OR** Docker for containerized deployment

## 🚀 Quick Start with Docker (Recommended)

The fastest way to get started is using Docker Compose:

```bash
# 1. Edit compose.yaml and add your Gemini API key
#    Look for: GEMINI_API_KEY: your_gemini_api_key_here

# 2. Start everything
docker compose up -d

# 3. Open browser to http://localhost:8000
```

**That's it!** All credentials are in `compose.yaml`. The application comes with a pre-configured PostgreSQL database and sample data.

For detailed Docker instructions, see [DOCKER_SETUP.md](DOCKER_SETUP.md).

---

## �️ Manual Setup (Without Containers)

If you prefer to run locally without containers:

### 1. Clone and Navigate

```bash
cd /Users/devashish/AgenticApplications/DB_manipulationAgent
```

### 2. Install Python Dependencies

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your details:

```env
# PostgreSQL Database Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password
POSTGRES_DB=your_database

# Google Gemini API Key
GEMINI_API_KEY=your_gemini_api_key_here

# Application Settings
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=True
```

### 4. Install MCP PostgreSQL Server

The application uses the Model Context Protocol to communicate with PostgreSQL. Install the MCP server:

```bash
npm install -g @modelcontextprotocol/server-postgres
```

## 🎯 Usage

### Start the Application

```bash
# Make sure you're in the project directory and virtual environment is activated
python -m uvicorn src.api:app --reload --host 0.0.0.0 --port 8000
```

### Access the Web Interface

Open your browser and navigate to:

```
http://localhost:8000
```

### Using the Query Agent

1. **Browse Your Schema**: The left sidebar shows all tables and their columns
2. **Ask a Question**: Type your request in natural language, for example:
   - "Show me all users who registered in the last 30 days"
   - "Insert a new product with name 'Widget' and price 29.99"
   - "Update the email for user with id 5 to 'newemail@example.com'"
   - "Delete all orders that are older than 1 year and marked as cancelled"

3. **Review the Generated Query**: The agent will:
   - Generate the SQL query
   - Explain what it does
   - Identify the query type (SELECT, INSERT, UPDATE, DELETE)
   - Show which tables are used
   - Mark it as safe or requiring review

4. **Copy and Execute**: Copy the query to your favorite SQL client to execute it

## 🔒 Security Features

### Queries Are Never Executed

The most important safety feature: **this application only generates SQL queries and displays them**. It never executes them on your database.

### Automatic Safety Checks

The query agent validates generated queries for:

- ❌ DROP TABLE/DATABASE commands
- ❌ TRUNCATE operations
- ❌ ALTER TABLE statements
- ❌ DELETE without WHERE clause
- ❌ UPDATE without WHERE clause
- ❌ Other potentially destructive operations

Queries that fail safety checks are flagged with warnings.

### Read-Only Schema Access

Database schema information is fetched in read-only mode to prevent any accidental modifications.

## 📁 Project Structure

```
DB_manipulationAgent/
├── src/
│   ├── __init__.py           # Package initialization
│   ├── config.py             # Configuration management
│   ├── mcp_client.py         # MCP client for PostgreSQL
│   ├── schema_manager.py     # Schema caching and formatting
│   ├── query_agent.py        # AI-powered query generation
│   └── api.py                # FastAPI web server
├── static/
│   ├── index.html            # Main web interface
│   ├── styles.css            # Modern CSS styling
│   └── app.js                # Frontend JavaScript
├── .env                      # Environment variables (create from .env.example)
├── .env.example              # Environment variables template
├── .gitignore                # Git ignore patterns
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## 🎨 Supported Query Types

### SELECT Queries
```
"Show me all active users"
"Find products with price greater than 100"
"List the top 10 customers by order count"
```

### INSERT Queries
```
"Add a new user with name John and email john@example.com"
"Insert a product called 'Laptop' with price 999.99"
```

### UPDATE Queries
```
"Update the status to 'shipped' for order id 123"
"Change the price to 29.99 for product named 'Widget'"
```

### DELETE Queries
```
"Delete user with id 456"
"Remove all cancelled orders from last year"
```

## 🛠️ API Endpoints

- `GET /` - Web interface
- `GET /health` - Health check
- `GET /api/schema` - Get complete database schema
- `GET /api/tables` - List all table names
- `GET /api/table/{name}` - Get specific table details
- `POST /api/generate-query` - Generate SQL query from natural language
- `POST /api/refresh-schema` - Force schema refresh

## 🐛 Troubleshooting

### Connection Issues

If you see "Connection Error":
1. Check that your PostgreSQL database is running
2. Verify credentials in `.env` file
3. Ensure the database user has read permissions on `information_schema`

### MCP Server Not Found

If MCP connection fails:
```bash
# Install the MCP PostgreSQL server
npm install -g @modelcontextprotocol/server-postgres

# Verify installation
npx @modelcontextprotocol/server-postgres --help
```

### API Key Issues

If query generation fails:
1. Verify your Anthropic API key in `.env`
2. Check that you have API credits available
3. Ensure the key has proper permissions

## 📝 Development

### Running in Development Mode

```bash
# With auto-reload
uvicorn src.api:app --reload --host 0.0.0.0 --port 8000
```

### Running Tests

```bash
pytest
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is open source and available under the MIT License.

## ⚠️ Important Notes

1. **No Automatic Execution**: This application ONLY generates SQL queries. It does not execute them.
2. **Review Before Running**: Always review generated queries before executing them on your database.
3. **Test in Development**: Test queries in a development environment first.
4. **Backup Your Data**: Always maintain regular database backups.

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- AI powered by [Google Gemini](https://ai.google.dev/)
- Database access via [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
- Container deployment with [Docker](https://www.docker.com/)

---

**Made with ❤️ for safe database querying**
