# Streamlit Chatbot UI Guide

The SQL Query Agent now includes a **Streamlit chatbot interface** as an alternative to the web UI!

## Features

- 💬 **Chat-based interface** - Natural conversation flow
- 📊 **Live database schema** - View tables and columns in sidebar
- 🎨 **Syntax highlighting** - Formatted SQL queries
- 📝 **Example queries** - Quick start with pre-built examples
- 💡 **Query explanations** - Understand what each query does
- ⚠️ **Safety indicators** - Visual warnings for risky queries
- 📋 **Easy copy** - One-click query copying
- 🔄 **Schema refresh** - Update database structure on demand

## Quick Start

### Option 1: Run Locally

1. **Install dependencies:**
   ```bash
   pip install streamlit
   ```

2. **Start the FastAPI backend** (if not already running):
   ```bash
   docker compose up -d
   # Or manually: uvicorn src.api:app --reload
   ```

3. **Start Streamlit:**
   ```bash
   ./start_streamlit.sh
   # Or: streamlit run streamlit_app.py
   ```

4. **Access the chatbot:**
   ```
   http://localhost:8501
   ```

### Option 2: Run with Docker

The Streamlit app can connect to the Dockerized backend:

```bash
# With backend running in Docker
docker compose up -d

# Run Streamlit locally
./start_streamlit.sh
```

## Using the Chatbot

### 1. View Database Schema

The left sidebar shows:
- Database name
- Number of tables
- Expandable table details with columns and foreign keys

Click "🔄 Refresh Schema" to update.

### 2. Ask Questions

Type natural language queries in the chat input:

**Examples:**
- "Show me all users"
- "List products with price greater than 100"
- "Insert a new user with username 'alice' and email 'alice@example.com'"
- "Update the price of product named 'Laptop' to 1199.99"
- "Delete orders with status 'cancelled'"

### 3. Review Generated Queries

Each response shows:
- **Query Type Badge** - SELECT, INSERT, UPDATE, DELETE
- **Safety Status** - Safe ✅ or Review Required ⚠️
- **Explanation** - What the query does
- **SQL Code** - Syntax-highlighted query
- **Tables Used** - Referenced tables
- **Warnings** - Any safety concerns

### 4. Use Example Queries

Click any example in the sidebar to try it instantly!

### 5. Clear History

Use the "🗑️ Clear Chat History" button at the bottom.

## Interface Comparison

| Feature | Streamlit Chatbot | Web UI |
|---------|-------------------|---------|
| Interface | Chat-based | Form-based |
| Schema View | Sidebar | Expandable cards |
| History | Chat history | Last 10 queries |
| Best For | Interactive exploration | Quick one-off queries |
| Port | 8501 | 8000 |

## Customization

### Change API URL

Edit `streamlit_app.py` line 8:

```python
API_BASE_URL = "http://localhost:8000"
```

### Change Port

```bash
streamlit run streamlit_app.py --server.port 8502
```

### Styling

The chatbot uses custom CSS (in `streamlit_app.py`) for:
- Query type color coding
- Safety badge styling
- SQL syntax highlighting
- Chat message formatting

## Troubleshooting

### "Connection Error"

Make sure the FastAPI backend is running:
```bash
curl http://localhost:8000/health
```

If not running:
```bash
docker compose up -d
```

### "Schema not loading"

Check the API URL in `streamlit_app.py` matches your backend.

### Port already in use

Change the Streamlit port:
```bash
streamlit run streamlit_app.py --server.port 8502
```

## Screenshots

The chatbot provides:

1. **Sidebar Schema Browser**
   - Collapsible table information
   - Column details with types
   - Primary and foreign keys

2. **Chat Interface**
   - Clean message bubbles
   - User questions on right
   - AI responses with formatted SQL

3. **Query Display**
   - Color-coded query types
   - Safety badges
   - Copy-friendly code blocks

4. **Example Queries**
   - Quick-start templates
   - One-click execution

## Tips

- 💡 Start with "Show me all tables" to explore your database
- 🔍 Use the schema sidebar to see available tables before asking
- ⚠️ Always review queries marked as "Review Required"
- 📋 Use the code block's copy button for easy copying
- 🗑️ Clear history when starting a new topic

---

**Remember:** The chatbot only **generates** SQL queries. It never executes them. Always review before running on your database!
