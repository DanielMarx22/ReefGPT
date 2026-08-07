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
1. **Historical Data Backfill (`tlog` & `ilog`)**: The Playwright headless scraper directly logs into Neptune Systems Apex Fusion and intercepts the `tlog` (Trident Logs) and `ilog` (Input Logs) network payloads. This directly bypasses local Apex limitations, grabbing up to 2 weeks of full historical telemetry seamlessly.
2. **Auto-Reload UX**: When the scraper completes its run, the frontend (which polls every 3 seconds) automatically detects the new records via `logsData.data.length > 0` and triggers a seamless `window.location.reload()`, meaning the user never has to manually refresh after their first sync.
3. **Scraper Safeguards**: To prevent Neptune from flagging the account, the backend enforces a strict 10-minute rate limit (`last_scrape_times`) on scraper triggers per user. The Playwright scraper also features a robust 3-minute timeout threshold that gracefully processes partial data if the Neptune dashboard takes too long to render.

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
2. **API Call**: Frontend sends a `POST` request to `/chat-v2` with the `x-user-id` header passed from the `AuthProvider`.
3. **Backend Orchestration (`main.py`)**:
    *   **Sequential Ranked Queue**: The Orchestrator determines which specialized Subagents (Telemetry Summarizer, Historian, Equipment & Notes Analyst, Knowledge Retriever) are most relevant and ranks them in a queue.
    *   **Subagent Execution**: The system iterates through the queue sequentially. Each subagent reads localized data (isolated by `user_id`) to analyze the tank:
        *   **Telemetry**: Checks recent parameter logs (pH, Temp, Alk, Ca, Mg).
        *   **Historian**: Reads the inhabitant profile (including `species` and `size`) and recent chat context.
        *   **Equipment**: Reads the `tank_events` table for equipment failures or specific notes (e.g., "reactor clogging").
    *   **Short-Circuiting**: If any subagent finds a glaring anomaly (e.g., Temperature drop from 78 to 70), it returns `found_issue: true`. The backend instantly breaks the loop to save tokens and prevent other agents from hallucinating conflicting causes.
4. **LLM Master Synthesis**: The Master AI receives the findings from the executed subagents. Because of the short-circuiting, it is forced to provide a highly definitive, data-backed diagnosis rather than generic guesswork.
5. **Database Logging**: Saves both the user's question and the AI's response (along with its "X-ray" JSON reasoning) to the `chat_history` table.
6. **Action Proposals**: If the AI determines an action is needed (like adding a fish to the profile or updating an equipment note), it returns a `proposed_actions` array.
7. **Frontend Render**: Returns the response to the frontend. The frontend displays the chat message, updates the "Agent X-Ray" debug panel (showing exactly which subagents were called), and presents an Action Popup to the user to confirm or dismiss any proposed actions.

---

## 4. Customizable Dashboard & UI Architecture

The frontend is built with React, Next.js, and TailwindCSS. It heavily leverages `framer-motion` for fluid animations and `@dnd-kit` for drag-and-drop customization.

### Dynamic Dashboard Layout
- **Persistence**: The layout order of Telemetry Tiles, Analytics Graphs, and Media Galleries is entirely customizable. The order is automatically saved as JSON in the `tank_settings` table via the `POST /save-layout` endpoint.
- **Aesthetic Overhaul**: The dashboard utilizes a premium glassmorphism design (`backdrop-blur`). The main background features a dynamic mesh gradient that automatically shifts colors based on the ML Model's `STABLE` (Emerald), `WARNING` (Amber), or `CRITICAL` (Crimson) status.
- **Empty States**: Fresh accounts start with a clean UI, displaying stylized "Waiting for Data" components to encourage initial telemetry and layout additions.

### Media Handling & Progression
- **MediaGallery Component**: Users can add "Single Picture" or "Rotating Gallery" cards to their dashboard.
- **Client-Side Compression**: To prevent `QuotaExceededError` in local storage (prior to cloud bucket implementation), the component aggressively resizes and compresses image uploads via an HTML `<canvas>` before base64 encoding.
- **Framer Motion**: The rotating gallery automatically cycles through photos every 5 seconds, using `<AnimatePresence>` for smooth cross-fading transitions.

---

## 5. Current LLM Model & Rationale

**Current Model:** `llama-3.3-70b-versatile` (Accessed via Groq API)

**Why this model?**
1.  **Speed (Groq)**: The Groq API uses specialized hardware (LPUs) that generate tokens incredibly fast. This is crucial for a real-time chatbot experience.
2.  **JSON Adherence**: The backend strictly requires the LLM to output its reasoning in a specific JSON format (the `xray` object for the frontend debug panel). This LLaMA instruct model is highly capable of adhering to strict system schemas without hallucinating markdown or conversational filler outside the JSON blocks.
3.  **Cost & Context**: It provides a large enough context window to swallow the RAG vector data, recent chat history, and parameter telemetry, while remaining cost-effective compared to heavier models like GPT-4o.

---

## 6. Automated Testing Architecture (Playwright)

ReefGPT features a comprehensive, dual-layered automated testing suite built with Playwright. 

**Why are tests split into small scenarios?**
In standard automated testing, it is considered a "bad practice" to write a single massive test that clicks every single button on every single page in one continuous journey. If one button changes, the entire script fails, and it becomes impossible to know what broke. Instead, tests are isolated into highly specific, atomic scenarios. The `agent-mocked` test specifically *only* tests the chatbot interaction and action popup, which is why it doesn't navigate to the Tank Profile afterwards.

### Layer 1: Frontend & UI Suite (Mocked API)
**Location:** `frontend/tests/e2e/`
These tests are incredibly fast and cost **zero tokens**. They do not touch the real database or the LLM. Instead, they intercept network requests (like `/chat-v2` or `/log-metric`) and "fake" the backend's response to ensure the frontend code reacts properly. Because the app requires authentication, these tests click the "Developer Bypass" sandbox accounts (e.g., `Customer A`) on the `/` route before running assertions.
1. **`ui.spec.ts`**: Verifies that all major components render correctly without crashing (Navbar routing, Dashboard).
2. **`chat-features.spec.ts`**: Simulates user interactions with the chatbot. It mocks the LLM response to verify that:
    * The "Clear Chat History" button appears and successfully clears the UI state after accepting the `window.confirm` dialog.
    * The AI diagnostic text renders correctly, and the Agent X-Ray panel successfully displays internal thoughts.
    * The Action Popup (`proposed_actions`) appears when the mock AI suggests adding an inhabitant or updating equipment, and disappears when confirmed.

### Layer 2: Full AI Intelligence Suite (Real API)
**Location:** `frontend/tests/ai-integration/`
This is your **Golden Dataset** regression test runner. It clicks through the real UI using the Developer Bypass Sandbox accounts, but actually hits your real, live FastAPI backend (and the real Groq LLM). 
1. **`scenarios.spec.ts`**:
    * **Automated Sandbox Testing**: Loops through all 5 sandbox accounts (Customer A through E), logs into each, and asks the AI a diagnostic question (e.g. "Why are my corals shrunk today?").
    * **Definitive Accuracy Verification**: Using regex matchers (e.g. `/alkalinity/i` or `/aggression/i`), it rigorously verifies that the LLM successfully parses the complex biological and telemetry data to diagnose the correct root cause. 
    * **WARNING**: Running this suite consumes real tokens and hits the Groq API sequentially. Be cautious of `429 Rate Limit` errors (100k TPD cap) if running it frequently.
    * **Synthetic Data Profiles**: The automated suite relies on 5 specific seeded profiles (`perfect@reefgpt.com`, `crash@reefgpt.com`, `lowcalc@reefgpt.com`, `hot@reefgpt.com`, `swing@reefgpt.com`). These are generated via a specialized backend script (`seed_test_accounts.py`) that mathematically generates 1,600+ hourly historical records to perfectly emulate complex scenarios (e.g., Alk drops, Heater failures) for RAG accuracy testing.

---

## 7. Authentication & User Management

ReefGPT utilizes a fully custom authentication layer built on top of the Supabase Auth API, designed for maximum flexibility and user experience.

### Custom Login Flow (`login/page.tsx`)
The pre-built `@supabase/auth-ui-react` component was stripped out in favor of a bespoke glassmorphic React form featuring:
- **Tabbed Interface**: Users can seamlessly switch between "Sign In", "Sign Up", and "Forgot Password".
- **Password Visibility**: Integrated `lucide-react` Eye toggles for all password fields.
- **Explicit Error Handling**: The frontend explicitly intercepts the `User already registered` error (if Supabase's "Prevent User Enumeration" is disabled) to present a clear red error message rather than silently failing or providing false success messages.

### Password Reset Flow (`update-password/page.tsx`)
1. User clicks "Forgot Password" and enters their email.
2. Supabase uses its built-in SMTP server to send a secure recovery link.
3. Clicking the link redirects the user to the custom `/update-password` route.
4. The frontend verifies the session token and allows the user to securely set a new password via `supabase.auth.updateUser()`.

### Supabase Configurations for Testing
For rapid development and sandbox testing (e.g. allowing testers to create 10 accounts in a single day), the project uses specific Supabase Auth configurations:
- **Email Confirmations Disabled**: By turning off "Confirm Email" in the Supabase Dashboard, users bypass the free tier's strict 3-emails-per-hour limit for signup confirmations, allowing instant account creation and testing.
