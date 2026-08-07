# ReefGPT Future Plans & Architecture Upgrades

This document outlines the roadmap of outstanding tasks for transforming ReefGPT into a hyper-accurate, expert-level reef assistant capable of rivaling a 20-year veteran Local Fish Store (LFS) owner.

---

## ✅ Completed Milestones

### 1. Implement Multi-Step Agentic RAG Architecture
*   **Status**: `COMPLETED`
*   **The Architecture**: The `/chat-v2` endpoint utilizes a Sequential Ranked Queue. The Orchestrator ranks subagents (Telemetry, Historian, Equipment, Knowledge) which then execute one by one. If a subagent flags a glaring issue (`found_issue: true`), the queue short-circuits.
*   **The Benefit**: This forces the Master AI to give definitive, evidence-based diagnoses (e.g. "Temp drop to 70.45") instead of generic guesswork, massively reduces LLM token consumption, and completely prevents hallucinated conflicts between subagents.

### 2. Implement Comprehensive Visual Testing Suite
*   **Status**: `COMPLETED`
*   **Architecture**: Dual-layered Playwright setup with dynamic Authentication.
    *   **Layer 1 (Mocked API)**: Tests frontend components instantly without spending API tokens. Now includes tests for the Clear Chat button, Agent X-Ray rendering, and complex Action Popups.
    *   **Layer 2 (Real API Regression Suite)**: The "Nuanced Database Inference Tests" have been successfully implemented. Using 5 dedicated Sandbox UUIDs (Dev Bypass), the Playwright suite automatically seeds complex tank failures (e.g., Alk drops, Heater failures, Aggressive fish pairings) into the database, prompts the AI with a vague complaint ("Why are my corals shrunk?"), and asserts that the RAG architecture correctly diagnoses the specific root cause without being spoon-fed the data.

---

## 🚀 Upcoming Roadmap (Prioritized)

### 1. Production Server Deployment (Oracle Cloud)
*   **The Goal**: Migrate the local FastAPI backend and Playwright scraper to a 24/7 always-on cloud server.
*   **The Plan**: Deploy the backend repository to the user's Oracle Cloud VPS. Crucially, this deployment will involve setting up a daily background cron job on the server. This script will automatically loop through the `tank_settings` table every night at 2:00 AM, spin up a headless browser, and scrape the Neptune Fusion data for every single user. This guarantees perfectly continuous 24/7 telemetry charts in Supabase, completely eliminating data gaps even if a user doesn't log into the ReefGPT app for months.

### 2. Production Supabase Redirect Whitelisting
*   **The Goal**: Ensure that password reset links and authentication emails correctly route users back to the live production website instead of localhost.
*   **The Plan**: When the Next.js frontend is deployed to a cloud provider (e.g., Vercel) and given a live domain (like `https://www.reefgpt.com`), we MUST go into the Supabase Dashboard -> Authentication -> URL Configuration. We need to add the production URL with a wildcard (`https://www.reefgpt.com/**`) to the **Redirect URLs** whitelist. Failure to do this will result in Supabase blocking the `redirect_to` parameter in the password reset emails, causing live users to be dumped on the default Site URL.

### 3. Agentic Livestock Management
*   **The Goal**: Enable the chatbot to autonomously parse and update database records (like specific coral morphs buried in a single "Zoanthids" note).
*   **The Plan**: We will equip the AI with explicit tools (Function Calling) allowing it to not only search the database but execute `update_inhabitant` and `add_tank_note` mutations. For example, if a user states "My Utter Chaos zoa died", the AI will search for "Utter Chaos", identify it within the notes of the broader "Zoanthids" record, autonomously lower the quantity, rewrite the note to reflect the loss, and create a permanent chronological Tank Note, all in one conversational turn.

### 4. Build Long-Term Tank Memory
*   **The Goal**: Give the AI episodic memory so it remembers historical tank events (e.g., a tank crash 6 months ago).
*   **The Plan**: The system currently logs events to a `tank_events` table. Future work involves summarizing these major tank events and storing them in a dedicated `tank_events_vector_db`. When a user asks a question, the RAG system will search this event memory to connect historical dots.

### 5. Create Advanced Diagnostic Playbooks
*   **The Goal**: Move beyond simple keyword matching into full Diagnostic Decision Trees.
*   **The Plan**: Expand `rag/rag.py`. If a user suspects a disease (e.g., Marine Ich), the Agent should automatically ask a predefined set of diagnostic questions *before* giving a final answer (e.g., "Are there white spots like salt? Is the fish flashing?"). This mimics a veteran LFS owner ruling out false positives.

### 6. Develop Dynamic Tank State Classifier
*   **The Goal**: Make the ML warning thresholds dynamic based on the specific type of tank the user is running.
*   **The Plan**: Update the `tank_settings` table to store a `tank_type` preference (Fish-Only, Soft Coral, or SPS). The backend (`get_model_metrics()`) will dynamically widen or tighten the `IDEAL_RANGES` and `CRITICAL_RANGES`. For example, an Alk swing of 1.0 dKH is STABLE for a Fish-Only tank, but CRITICAL for an SPS tank.

### 7. Cloud Media Storage Architecture
*   **The Goal**: Move away from base64 Local Storage to a persistent Cloud Bucket while maintaining our aggressive client-side optimization.
*   **The Plan**: Right now, the React frontend aggressively downscales and compresses high-res 4K photos using an HTML Canvas (e.g. limiting to 800x800px) *before* saving them as base64 strings to prevent blowing past the browser's `QuotaExceededError` limit. Future work will involve wiring this up to an AWS S3 or Supabase Storage bucket. We will maintain the current client-side downscaling logic because it prevents users from uploading massive raw iPhone photos, saving us extreme bandwidth and storage costs while keeping the app snappy.

### 8. Mobile Responsiveness & UI Formatting
*   **The Goal**: Rebuild the UI constraints so the app is fully usable on mobile phones and narrow vertical screens.
*   **The Plan**: Currently, narrowing the browser window causes elements (like Telemetry tiles) to get squished and hidden because they are constrained by rigid box limits. The desktop layout (chatbox on the right, dashboard on the left) completely breaks on mobile. We will need to design a dedicated mobile layout using Tailwind's breakpoints (`md:`, `lg:`). This will likely involve stacking the chatbot *below* the dashboard on narrow screens, or placing the chatbot behind a togglable floating action button (FAB) / sliding drawer so it doesn't consume all the vertical screen real estate.

### 9. Maintenance To-Do List & Push Notifications
*   **The Goal**: Provide users with a structured maintenance checklist that sends native device notifications for critical tasks.
*   **The Plan**: Implement a task management system where users can schedule recurring maintenance (e.g., water changes, dosing, skimmer cleaning). We will integrate a service like Firebase Cloud Messaging (FCM) or OneSignal (or native Web Push API) to push actual device notifications to users' phones and desktops when a task is due, ensuring critical tank maintenance is never missed.
