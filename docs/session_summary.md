# Session Summary - August 4, 2026

This document contains all the critical context, architectural decisions, and next steps from our recent session. Read this before continuing work!

## 1. Automated Testing (Playwright)
*   **The Issue**: Both AI tests were failing intermittently because Playwright runs tests in parallel. Since the backend hardcodes `TEMP_USER_ID`, both tests were writing to the exact same `chat_history` rows simultaneously, completely confusing the LLM's context window.
*   **The Fix**: 
    1. Added a `@app.delete("/clear-chat")` endpoint to `main.py`.
    2. Configured `ai-accuracy.spec.ts` to run **serially**.
    3. Added a `test.beforeEach()` hook to wipe the chat history before every single test, guaranteeing the LLM starts with a clean slate.
    4. Updated the tests to explicitly log the **User Prompt** alongside the AI Reply in the terminal so we can read the exact conversation flow.
*   **Status**: All 6 tests (E2E Mocked + Real AI Integration) are currently passing 100%.

## 2. The Agentic "Map-Reduce" Architecture (V2 Engine)
*   **The Goal**: Minimize token usage on the expensive 70B model while giving it maximum historical context, eliminating the "Lost in the Middle" hallucination problem.
*   **The Implementation**: Built a highly parallelized multi-agent system on a new `/chat-v2` endpoint using `AsyncOpenAI` and `asyncio.gather()`. 
*   **The Workers (Layer 1)**:
    *   `Intent Router`: Checks if the user is missing required schema data (e.g., adding a fish without a size) and *short-circuits* the heavy LLM call to ask the user directly.
    *   `Telemetry Summarizer`: Parses thousands of raw parameter logs into a 2-sentence summary.
    *   `Historian`: Summarizes the tank profile and chat history.
    *   `Knowledge Retriever`: Fetches biological facts based on the user's prompt (e.g., amino acid toxicity for mushroom bleaching).
*   **The Master Diagnostician (Layer 2)**: The 70B model now receives *only* the tiny summaries from the workers, giving it laser-focus to make complex deductions.

## 3. UI Upgrades (Transparency & Metrics)
*   **A/B Testing Toggle**: Added an `Engine: V1 / V2` toggle to the top right of the X-Ray panel in `page.tsx` so we can run identical prompts through both systems and compare accuracy.
*   **Explicit X-Ray Reasoning**: The X-Ray panel was overhauled to display an array of `reasoning_steps`. We can literally read the exact output of every single Layer 1 worker node.
*   **Token Tracking**: The Groq API `usage` object is captured and displayed in the X-Ray, showing exactly how many tokens were spent and saved.
*   **AI Disclaimer**: Added an industry-standard disclaimer below the chat input box stating that the AI can make mistakes and does not control hardware.

## 4. Next Steps (Crucial Order of Operations)
*   Because the `TEMP_USER_ID` is hardcoded, any "Nuanced AI Database Tests" we write (e.g., seeding the database with a massive Alkalinity crash) will pollute your real-life, stable Apex dashboard data!
*   **IMMEDIATE NEXT STEP**: Implement **User Accounts (Supabase Auth)**.
*   Once Auth is built, we will update the Playwright tests to log in as a dummy account (e.g., `TEST-USER-1234`). This creates a sandbox where tests can freely destroy and rebuild the database without ever touching your real tank data.
*   After Auth and Sandbox Testing are complete, we can move on to **Long-Term Tank Memory** (vectorizing historical tank crashes).
