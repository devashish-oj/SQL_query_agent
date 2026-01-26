## 💬 Streamlit Chatbot Interface

In addition to the web UI, you can use the Streamlit chatbot for a more interactive experience:

```bash
# 1. Make sure the backend is running
docker compose up -d

# 2. Install Streamlit (if not in Docker)
pip install streamlit

# 3. Start the chatbot
./start_streamlit.sh

# 4. Access at http://localhost:8501
```

Features:
- Chat-based interface
- Live schema viewer in sidebar
- Example queries
- Syntax-highlighted SQL
- Query history in chat format

See [STREAMLIT_GUIDE.md](STREAMLIT_GUIDE.md) for details.
