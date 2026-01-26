"""Streamlit Chatbot UI for PostgreSQL Query Generation Agent."""

import streamlit as st
import requests
from typing import Dict, Any, List
import json

# Configuration
API_BASE_URL = "http://localhost:8000"

# Page config
st.set_page_config(
    page_title="SQL Query Agent Chat",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better chatbot styling
st.markdown("""
<style>
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .user-message {
        background-color: #e3f2fd;
    }
    .assistant-message {
        background-color: #f5f5f5;
    }
    .sql-query {
        background-color: #1e1e1e;
        color: #d4d4d4;
        padding: 1rem;
        border-radius: 0.5rem;
        font-family: 'Courier New', monospace;
        margin: 0.5rem 0;
    }
    .query-meta {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 0.25rem;
        margin: 0.25rem;
        font-size: 0.875rem;
        font-weight: 600;
    }
    .meta-select { background-color: #10b981; color: white; }
    .meta-insert { background-color: #3b82f6; color: white; }
    .meta-update { background-color: #f59e0b; color: white; }
    .meta-delete { background-color: #ef4444; color: white; }
    .meta-safe { background-color: #10b981; color: white; }
    .meta-unsafe { background-color: #ef4444; color: white; }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "schema" not in st.session_state:
    st.session_state.schema = None
if "tables" not in st.session_state:
    st.session_state.tables = []

# Helper functions
def fetch_schema():
    """Fetch database schema from API."""
    try:
        response = requests.get(f"{API_BASE_URL}/api/schema")
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Failed to fetch schema: {e}")
        return None

def fetch_tables():
    """Fetch list of tables from API."""
    try:
        response = requests.get(f"{API_BASE_URL}/api/tables")
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        st.error(f"Failed to fetch tables: {e}")
        return []

def generate_query(user_request: str) -> Dict[str, Any]:
    """Generate SQL query from natural language."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/generate-query",
            json={"request": user_request, "conversation_history": None}
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API Error: {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}

def format_query_type(query_type: str) -> str:
    """Format query type badge."""
    icons = {
        "SELECT": "🔍",
        "INSERT": "➕",
        "UPDATE": "✏️",
        "DELETE": "🗑️"
    }
    icon = icons.get(query_type, "📝")
    css_class = f"meta-{query_type.lower()}"
    return f'<span class="query-meta {css_class}">{icon} {query_type}</span>'

def format_safety_badge(is_safe: bool) -> str:
    """Format safety status badge."""
    if is_safe:
        return '<span class="query-meta meta-safe">✅ Safe</span>'
    else:
        return '<span class="query-meta meta-unsafe">⚠️ Review Required</span>'

# Sidebar - Database Schema
with st.sidebar:
    st.title("🗄️ Database Browser")
    
    # Database selector
    try:
        db_response = requests.get(f"{API_BASE_URL}/api/databases")
        if db_response.status_code == 200:
            db_data = db_response.json()
            databases = db_data.get("databases", [])
            current_db = db_data.get("current", "")
            
            if databases:
                st.markdown("### Database")
                selected_db = st.selectbox(
                    "Select Database",
                    databases,
                    index=databases.index(current_db) if current_db in databases else 0,
                    key="database_selector",
                    label_visibility="collapsed"
                )
                
                # Switch database if changed
                if selected_db != current_db:
                    with st.spinner(f"Switching to {selected_db}..."):
                        switch_response = requests.post(
                            f"{API_BASE_URL}/api/switch-database",
                            params={"database": selected_db}
                        )
                        if switch_response.status_code == 200:
                            st.session_state.schema = None  # Force schema refresh
                            st.session_state.tables = [] # Force tables refresh
                            st.success(f"Switched to {selected_db}")
                            st.rerun()
                        else:
                            st.error(f"Failed to switch to {selected_db}")
                
                st.caption(f"📊 {len(databases)} databases available")
                st.divider()
    except Exception as e:
        st.warning(f"Could not load databases: {e}")
    
    # Schema section title
    st.markdown("### Tables")
    
    # Refresh schema button
    if st.button("🔄 Refresh Schema", use_container_width=True):
        with st.spinner("Fetching schema..."):
            st.session_state.schema = fetch_schema()
            st.session_state.tables = fetch_tables()
            if st.session_state.schema:
                st.success("Schema refreshed!")
    
    # Fetch schema on first load
    if st.session_state.schema is None:
        with st.spinner("Loading schema..."):
            st.session_state.schema = fetch_schema()
            st.session_state.tables = fetch_tables()
    
    # Display schema
    if st.session_state.schema and "tables" in st.session_state.schema:
        st.markdown(f"**Database:** {st.session_state.schema.get('database', 'Unknown')}")
        st.markdown(f"**Tables:** {len(st.session_state.schema['tables'])}")
        
        st.divider()
        
        # Display each table
        for table in st.session_state.schema["tables"]:
            with st.expander(f"📊 {table['name']}", expanded=False):
                st.markdown("**Columns:**")
                for col in table["columns"]:
                    pk_marker = " 🔑" if col.get("is_primary_key") else ""
                    null_marker = "NULL" if col.get("nullable") else "NOT NULL"
                    st.text(f"• {col['name']}: {col['type']} {null_marker}{pk_marker}")
                
                if table.get("foreign_keys"):
                    st.markdown("**Foreign Keys:**")
                    for fk in table["foreign_keys"]:
                        st.text(f"🔗 {fk['column']} → {fk['references_table']}.{fk['references_column']}")
    else:
        st.warning("Unable to load schema. Make sure the API is running.")
        st.code(f"API URL: {API_BASE_URL}")

# Main chat interface
st.title("🤖 SQL Query Generation Chat")
st.markdown("Ask me to generate SQL queries in natural language!")

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "user":
            st.markdown(message["content"])
        else:
            # Display assistant response with formatted query
            if "error" in message:
                st.error(f"❌ {message['error']}")
            else:
                # Query metadata badges
                st.markdown(
                    format_query_type(message.get("query_type", "UNKNOWN")) + " " +
                    format_safety_badge(message.get("is_safe", False)),
                    unsafe_allow_html=True
                )
                
                # Explanation
                if message.get("explanation"):
                    st.markdown(f"**Explanation:**\n{message['explanation']}")
                
                # SQL Query
                if message.get("query"):
                    st.markdown("**Generated SQL:**")
                    st.code(message["query"], language="sql")
                    
                    # Copy button
                    st.code(message["query"], language="sql")
                
                # Tables used
                if message.get("tables_used"):
                    st.markdown(f"**Tables:** {', '.join(message['tables_used'])}")
                
                # Warnings
                if message.get("warnings"):
                    st.warning(f"⚠️ **Warning:** {message['warnings']}")
                
                # Safety notice
                if not message.get("is_safe", False):
                    st.error("⚠️ **Important:** This query has potential safety issues. Please review carefully before executing.")
                else:
                    st.info("💡 **Note:** This query has not been executed. Copy and review before running on your database.")

# Chat input
if prompt := st.chat_input("Ask me to generate a SQL query..."):
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate query
    with st.chat_message("assistant"):
        with st.spinner("Generating query..."):
            result = generate_query(prompt)
            
            # Store and display result
            st.session_state.messages.append({
                "role": "assistant",
                **result
            })
            
            if "error" in result:
                st.error(f"❌ {result['error']}")
            else:
                # Query metadata badges
                st.markdown(
                    format_query_type(result.get("query_type", "UNKNOWN")) + " " +
                    format_safety_badge(result.get("is_safe", False)),
                    unsafe_allow_html=True
                )
                
                # Explanation
                if result.get("explanation"):
                    st.markdown(f"**Explanation:**\n{result['explanation']}")
                
                # SQL Query
                if result.get("query"):
                    st.markdown("**Generated SQL:**")
                    st.code(result["query"], language="sql")
                
                # Tables used
                if result.get("tables_used"):
                    st.markdown(f"**Tables:** {', '.join(result['tables_used'])}")
                
                # Warnings
                if result.get("warnings"):
                    st.warning(f"⚠️ **Warning:** {result['warnings']}")
                
                # Safety notice
                if not result.get("is_safe", False):
                    st.error("⚠️ **Important:** This query has potential safety issues. Please review carefully before executing.")
                else:
                    st.info("💡 **Note:** This query has not been executed. Copy and review before running on your database.")

# Clear chat button
if st.session_state.messages:
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🗑️ Clear Chat History", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

# Example queries in sidebar
with st.sidebar:
    st.divider()
    st.markdown("### 💡 Example Queries")
    
    example_queries = [
        "Show me all users",
        "List products with price greater than 100",
        "Insert a new user with username 'alice'",
        "Update the price of product named 'Laptop'",
        "Delete cancelled orders"
    ]
    
    for example in example_queries:
        if st.button(f"📝 {example}", key=example, use_container_width=True):
            # Trigger the example query
            st.session_state.messages.append({"role": "user", "content": example})
            result = generate_query(example)
            st.session_state.messages.append({
                "role": "assistant",
                **result
            })
            st.rerun()

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.875rem;'>
    <p>🤖 SQL Query Generation Agent | Powered by Google Gemini</p>
    <p>⚠️ Queries are generated but NOT executed. Always review before running.</p>
</div>
""", unsafe_allow_html=True)
