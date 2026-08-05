# ReefGPT Frontend

This directory contains the Next.js (React) frontend application for ReefGPT. It serves as the user interface and dashboard.

## Key Responsibilities:
- **Dashboard UI**: Renders the modern, glassmorphic UI using TailwindCSS and custom CSS components.
- **Data Visualization**: Utilizes Recharts to draw dynamic, real-time graphs of tank telemetry (pH, Temperature, Alkalinity, etc.).
- **Realtime Sync**: Subscribes to Supabase `postgres_changes` events to instantly update graphs and UI components the moment new data hits the database, without requiring a page refresh.
- **Chat Interface**: Provides the UI for the Agentic AI chatbot, including the "Agent X-Ray" debug panel and actionable popups for agent-proposed database changes.

## Running the Frontend:
```bash
npm install
npm run dev
```
The app will be accessible at `http://localhost:3000`.
