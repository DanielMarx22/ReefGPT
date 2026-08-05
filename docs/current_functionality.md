# ReefGPT Current Functionality & Architecture

This document provides a comprehensive overview of the current state of ReefGPT, including running instructions, backend architecture, file interactions, and detailed user flows.

## 1. Running Instructions

### Backend (FastAPI)
1. Navigate to the backend directory: `cd backend`
2. Activate your virtual environment: `source venv/bin/activate` (or `venv\Scripts\activate` on Windows)
3. Install dependencies: `pip install -r requirements.txt`
4. Make sure your `.env` is set up with `SUPABASE_URL`, `SUPABASE_KEY`, and `GROQ_API_KEY`.
5. Run the server: `python -m uvicorn api.main:app --port 8000` (or `python3` on Mac/Linux)

### Frontend (Next.js)
1. Navigate to the frontend directory: `cd frontend`
2. Install dependencies: `npm install`
3. Run the development server: `npm run dev`
4. Access the UI at `http://localhost:3000`

---

## 2. Backend Architecture & Files

The backend is a FastAPI application that serves as the brain of ReefGPT. It integrates machine learning (XGBoost), Retrieval-Augmented Generation (RAG), and a Large Language Model (LLM) to provide expert-level diagnostics.

### Core Files:

*   **`api/main.py`**: The entry point and core controller of the backend. It defines all API endpoints (chat, logging, fetching state, inhabitant management, event logging, image uploads), manages the Supabase database connections, calls the ML models for inference, and orchestrates the final prompt sent to the LLM. It also houses the **Smart Sync Architecture**, running `asyncio` background tasks to automatically fetch and deduplicate telemetry data directly from a Neptune Apex controller.
*   **`ml/inference.py`**: Handles the Machine Learning logic. It uses a trained XGBoost model (and optionally an MLP model) to classify the tank's current state into `STABLE`, `WARNING`, or `CRITICAL` based on parameter readings (pH, Calcium, Magnesium, Alkalinity, Temperature). It also handles data feature engineering and synthetic data loading if real data isn't available.
*   **`rag/rag.py`**: The RAG Diagnostic Router. It acts as an "Expert Override" system. Before sending a query to the LLM, this file applies hardcoded data-science rules to the prompt (e.g., if a user mentions "missing flesh", it forces the LLM to cross-reference livestock compatibility; if "all coral dying", it forces a systemic crash check).
*   **`rag/vector_db.py` & `rag/scraper.py`**: Handles the ingestion and retrieval of external reef-keeping knowledge via a FAISS vector database.

### Autonomous Apex Data Sync:
The backend features a zero-maintenance "Smart Sync" system for Neptune Apex hardware integration:
1. **Catch-Up Sync (Zero Missed Data)**: On server startup, a background task connects to the local Apex's internal memory (`datalog.xml`), calculates exactly how long the ReefGPT server was offline, dynamically fetches the timezone offset, and safely backfills all missing historical data into Supabase as true UTC timestamps.
2. **Smart Polling Loop**: An `asyncio` thread quietly polls the Apex `status.json` every 10 minutes while the server is running. Fast-moving metrics (Temperature, pH) are logged normally, while Trident data (Alkalinity, Calcium, Magnesium) is intelligently deduplicated against the database so that only genuine test updates are plotted on the graphs.

---

## 3. User Interaction Flows (Step-by-Step)

### Flow A: User Logs a New Parameter
1. **Frontend Action**: User enters a parameter (e.g., `pH: 8.2`) and clicks "Add" or "Update".
2. **API Call**: Frontend sends a `POST` request to `/log-metric`.
3. **Backend Processing**: `main.py` receives the request and inserts the new data point into the `metrics_log` table in Supabase.
4. **Realtime Sync**: Supabase emits a `postgres_changes` event. The frontend (via a Supabase Realtime listener in `page.tsx`) instantly detects the insert.
5. **UI Update**: The frontend immediately fires off background requests to `/tank-status` and `/get-logs` to fetch the fresh ML predictions and updated graphs, re-rendering the UI without requiring a page refresh.

### Flow B: User Asks the Chatbot a Question
1. **Frontend Action**: User types a question (e.g., "Why are my zoas closed up?") and hits send.
2. **API Call**: Frontend sends a `POST` request to `/chat`.
3. **Backend Orchestration (`main.py`)**:
    *   **Telemetry Check**: Fetches the most recent logs for key parameters (pH, Temp, Alk, Ca, Mg) to drastically reduce token count while ensuring the AI has the latest data.
    *   **Profile Fetch**: Retrieves the user's livestock profile as a structured list from the `inhabitants` table (replacing the old manual text profile).
    *   **ML Inference**: Calls the XGBoost model to get the official classification (Stable/Warning/Critical) and calculates the variance (swings) in parameters over the last 24-72 hours.
    *   **RAG Routing**: Passes the user's query to `rag.py`. If the query matches specific keywords, expert override rules are generated. It also queries the vector database for relevant documentation.
    *   **Prompt Assembly**: Constructs a massive "System Instruction" prompt containing the ML alerts, RAG context, Tank Data, Livestock, and strict JSON output schema.
4. **LLM Execution**: Sends the assembled prompt to the Groq API.
5. **Database Logging**: Saves both the user's question and the AI's response (along with its "X-ray" JSON reasoning) to the `chat_history` table.
6. **Action Proposals**: If the AI determines an action is needed (like adding a fish to the profile or logging a tank event), it returns a `proposed_actions` array.
7. **Frontend Render**: Returns the response to the frontend. The frontend displays the chat message, updates the "Agent X-Ray" debug panel, and presents an Action Popup to the user to confirm or dismiss any proposed actions.

---

## 4. Current LLM Model & Rationale

**Current Model:** `llama-3.3-70b-versatile` (Accessed via Groq API)

**Why this model?**
1.  **Speed (Groq)**: The Groq API uses specialized hardware (LPUs) that generate tokens incredibly fast. This is crucial for a real-time chatbot experience.
2.  **JSON Adherence**: The backend strictly requires the LLM to output its reasoning in a specific JSON format (the `xray` object for the frontend debug panel). This LLaMA instruct model is highly capable of adhering to strict system schemas without hallucinating markdown or conversational filler outside the JSON blocks.
3.  **Cost & Context**: It provides a large enough context window to swallow the RAG vector data, recent chat history, and parameter telemetry, while remaining cost-effective compared to heavier models like GPT-4o.

---

## 5. Automated Testing Architecture (Playwright)

ReefGPT features a comprehensive, dual-layered automated testing suite built with Playwright. 

**Why are tests split into small scenarios?**
In standard automated testing, it is considered a "bad practice" to write a single massive test that clicks every single button on every single page in one continuous journey. If one button changes, the entire script fails, and it becomes impossible to know what broke. Instead, tests are isolated into highly specific, atomic scenarios. The `agent-mocked` test specifically *only* tests the chatbot interaction and action popup, which is why it doesn't navigate to the Tank Profile afterwards.

### Layer 1: Frontend & UI Suite (Mocked API)
**Location:** `frontend/tests/e2e/`
These tests are incredibly fast and cost **zero tokens**. They do not touch the real database or the LLM. Instead, they intercept network requests (like `/chat` or `/log-metric`) and "fake" the backend's response to ensure the frontend code reacts properly.
1. **`ui.spec.ts`**: Verifies that all major components render correctly without crashing (e.g., checking if the Navbar routing works, and ensuring the Dashboard loads).
2. **`manual-logging.spec.ts`**: Simulates a user selecting a parameter (Alkalinity) from the dropdown, typing a value, and clicking Update. It intercepts the network request to prove the frontend successfully built the correct data payload.
3. **`agent-mocked.spec.ts`**: Simulates the user chatting with the AI about adding livestock. It fakes an AI response containing a JSON action payload to verify that the "Agent Proposed Actions" popup appears and allows the user to click Confirm.

### Layer 2: Full AI Intelligence Suite (Real API)
**Location:** `frontend/tests/ai-integration/`
This is your **Golden Dataset** test runner. It completely ignores the UI and directly hits your real, live FastAPI backend (and the real Groq LLM). 
1. **`ai-accuracy.spec.ts`**:
    * **Scenario A (Complex Livestock Parsing)**: Sends a complex prompt ("I just bought a new Purple Tang...") to the AI and strictly verifies that the LLM successfully parses it into the exact JSON schema required by your database (`action: "add_inhabitant"`, `name: "Purple Tang"`, etc.).
    * **Scenario B (Critical Parameter Triage)**: Sends a paragraph about SPS base peeling and a rapid Alkalinity drop. It verifies that the AI correctly flags the issue as `CRITICAL` in its X-Ray reasoning and mentions key terms like "alkalinity" or "swing" in its final conversational response.
