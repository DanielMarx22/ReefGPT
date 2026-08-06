# ReefGPT Future Plans & Architecture Upgrades

This document outlines the roadmap of outstanding tasks for transforming ReefGPT into a hyper-accurate, expert-level reef assistant capable of rivaling a 20-year veteran Local Fish Store (LFS) owner.

## Roadmap Overview
1. **Implement Multi-Step Agentic RAG Architecture**
2. **Build Long-Term Tank Memory** (Event Vectorization)
3. **Create Advanced Diagnostic Playbooks** (Decision trees for disease/pests)
4. **Develop Dynamic Tank State Classifier** (Thresholds based on tank type)
5. **[COMPLETED] Implement Comprehensive Visual Testing Suite** (Playwright automated UI/AI testing)
6. **Agentic Livestock Management** (Autonomous intelligent database updates via function calling)
7. **Cloud Media Storage Architecture** (Transitioning from browser-scaling to cloud buckets)
8. **Mobile Responsiveness & UI Overhaul** (Refactoring layout for vertical/mobile screens)

---

## Detailed Implementation Plans

### 1. [COMPLETED] Implement Multi-Step Agentic RAG Architecture
*   **Status**: Successfully built!
*   **The Architecture**: The `/chat-v2` endpoint utilizes a Sequential Ranked Queue. The Orchestrator ranks subagents (Telemetry, Historian, Equipment, Knowledge) which then execute one by one. If a subagent flags a glaring issue (`found_issue: true`), the queue short-circuits.
*   **The Benefit**: This forces the Master AI to give definitive, evidence-based diagnoses (e.g. "Temp drop to 70.45") instead of generic guesswork, massively reduces LLM token consumption, and completely prevents hallucinated conflicts between subagents.

### 2. Build Long-Term Tank Memory
*   **The Goal**: Give the AI episodic memory so it remembers historical tank events (e.g., a tank crash 6 months ago).
*   **The Plan**: The system currently logs events to a `tank_events` table. Future work involves summarizing these major tank events and storing them in a dedicated `tank_events_vector_db`. When a user asks a question, the RAG system will search this event memory to connect historical dots.

### 3. Create Advanced Diagnostic Playbooks
*   **The Goal**: Move beyond simple keyword matching into full Diagnostic Decision Trees.
*   **The Plan**: Expand `rag/rag.py`. If a user suspects a disease (e.g., Marine Ich), the Agent should automatically ask a predefined set of diagnostic questions *before* giving a final answer (e.g., "Are there white spots like salt? Is the fish flashing?"). This mimics a veteran LFS owner ruling out false positives.

### 4. Develop Dynamic Tank State Classifier
*   **The Goal**: Make the ML warning thresholds dynamic based on the specific type of tank the user is running.
*   **The Plan**: Update the `tank_settings` table to store a `tank_type` preference (Fish-Only, Soft Coral, or SPS). The backend (`get_model_metrics()`) will dynamically widen or tighten the `IDEAL_RANGES` and `CRITICAL_RANGES`. For example, an Alk swing of 1.0 dKH is STABLE for a Fish-Only tank, but CRITICAL for an SPS tank.

### 5. [COMPLETED] Implement Comprehensive Visual Testing Suite
*   **Status**: Successfully built!
*   **Architecture**: Dual-layered Playwright setup with dynamic Authentication.
    *   **Layer 1 (Mocked API)**: Tests frontend components instantly without spending API tokens. Now includes tests for the Clear Chat button, Agent X-Ray rendering, and complex Action Popups.
    *   **Layer 2 (Real API Regression Suite)**: The "Nuanced Database Inference Tests" have been successfully implemented. Using 5 dedicated Sandbox UUIDs (Dev Bypass), the Playwright suite automatically seeds complex tank failures (e.g., Alk drops, Heater failures, Aggressive fish pairings) into the database, prompts the AI with a vague complaint ("Why are my corals shrunk?"), and asserts that the RAG architecture correctly diagnoses the specific root cause without being spoon-fed the data.
### 6. Agentic Livestock Management
*   **The Goal**: Enable the chatbot to autonomously parse and update database records (like specific coral morphs buried in a single "Zoanthids" note).
*   **The Plan**: We will equip the AI with explicit tools (Function Calling) allowing it to not only search the database but execute `update_inhabitant` and `add_tank_note` mutations. For example, if a user states "My Utter Chaos zoa died", the AI will search for "Utter Chaos", identify it within the notes of the broader "Zoanthids" record, autonomously lower the quantity, rewrite the note to reflect the loss, and create a permanent chronological Tank Note, all in one conversational turn.

### 7. Cloud Media Storage Architecture
*   **The Goal**: Move away from base64 Local Storage to a persistent Cloud Bucket while maintaining our aggressive client-side optimization.
*   **The Plan**: Right now, the React frontend aggressively downscales and compresses high-res 4K photos using an HTML Canvas (e.g. limiting to 800x800px) *before* saving them as base64 strings to prevent blowing past the browser's `QuotaExceededError` limit. Future work will involve wiring this up to an AWS S3 or Supabase Storage bucket. We will maintain the current client-side downscaling logic because it prevents users from uploading massive raw iPhone photos, saving us extreme bandwidth and storage costs while keeping the app snappy.

### 8. Mobile Responsiveness & UI Formatting
*   **The Goal**: Rebuild the UI constraints so the app is fully usable on mobile phones and narrow vertical screens.
*   **The Plan**: Currently, narrowing the browser window causes elements (like Telemetry tiles) to get squished and hidden because they are constrained by rigid box limits. The desktop layout (chatbox on the right, dashboard on the left) completely breaks on mobile. We will need to design a dedicated mobile layout using Tailwind's breakpoints (`md:`, `lg:`). This will likely involve stacking the chatbot *below* the dashboard on narrow screens, or placing the chatbot behind a togglable floating action button (FAB) / sliding drawer so it doesn't consume all the vertical screen real estate.
