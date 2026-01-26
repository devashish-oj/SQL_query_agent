#!/bin/bash

# Start Streamlit Chatbot UI
# This script runs the Streamlit interface for the Query Agent

echo "🚀 Starting SQL Query Agent Chatbot..."
echo ""
echo "Make sure the FastAPI backend is running on http://localhost:8000"
echo ""
echo "Starting Streamlit on http://localhost:8501"
echo ""

streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0
