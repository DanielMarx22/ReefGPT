# ReefGPT Future Plans & Architecture Upgrades

This document outlines the roadmap of outstanding tasks for transforming ReefGPT into a hyper-accurate, expert-level reef assistant capable of rivaling a 20-year veteran Local Fish Store (LFS) owner.

## Roadmap Overview
1. **Implement Multi-Step Agentic RAG Architecture**
2. **Build Long-Term Tank Memory** (Event Vectorization)
3. **Create Advanced Diagnostic Playbooks** (Decision trees for disease/pests)
4. **Develop Dynamic Tank State Classifier** (Thresholds based on tank type)
5. **Implement Comprehensive Visual Testing Suite** (Playwright automated UI/AI testing)

---

## Detailed Implementation Plans

### 1. Implement Multi-Step Agentic RAG Architecture
*   **The Goal**: Split the LLM request into multiple highly-optimized steps to reduce token usage and improve factual accuracy.
*   **Step 1 (Triage & Retrieval)**: A small, fast model analyzes the query, fetches the exact historical data needed (ignoring irrelevant data), and formulates a search query for the Vector DB.
*   **Step 2 (Master Diagnostician)**: A heavy reasoning model receives the highly-distilled output from Step 1. With an uncluttered context window, it synthesizes the exact facts into expert advice.
*   **Testing Nuance (TODO)**: Once the multi-layer RAG is implemented, we must upgrade the Playwright `ai-accuracy` suite to perform "Nuanced Database Inference Tests". Instead of explicitly telling the AI "my alk dropped from 9 to 7" in the prompt, the test will seed the `metrics_log` table with a 9-to-7 Alk drop, and then prompt the AI with a vague complaint like "My SPS corals are shrinking a lot". The test will verify if the RAG layers successfully hunt down the log anomalies and diagnose the Alk swing on their own!

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
*   **Architecture**: Dual-layered Playwright setup.
    *   **Layer 1 (Mocked API)**: Tests frontend components instantly without spending API tokens or polluting databases.
    *   **Layer 2 (Real API)**: Evaluates the AI's "brain" directly against the Golden Dataset, proving it can parse complex actions and correctly diagnose critical situations.
