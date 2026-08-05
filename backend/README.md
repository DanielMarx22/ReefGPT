# ReefGPT Backend

This directory contains the Python FastAPI backend for ReefGPT. It acts as the "brain" of the application.

## Key Responsibilities:
- **API Endpoints**: Hosts all REST API routes for the frontend (e.g., `/chat`, `/log-metric`, `/tank-status`).
- **Database Interaction**: Connects to the Supabase PostgreSQL database to store and retrieve user data, telemetry, and chat history.
- **Machine Learning**: Uses a trained XGBoost model (`ml/inference.py`) to classify tank telemetry into Stable, Warning, or Critical states.
- **Agentic RAG System**: Intercepts chat queries, pulls relevant tank metrics and livestock profiles, searches the vector database for reefing knowledge (`rag/rag.py`), and orchestrates the final prompt sent to the LLM (Groq).
- **Hardware Integrations**: Runs `asyncio` background loops to autonomously poll the local Neptune Apex controller for real-time tank data.

## Running the Backend:
```bash
source venv/bin/activate  # (or venv\Scripts\activate on Windows)
python -m uvicorn api.main:app --port 8000 --reload
```
