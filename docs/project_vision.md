# ReefGPT Project Vision & Core Goal

The overarching goal of ReefGPT is to build a **fully functional, cross-platform application** (usable on both mobile and desktop) that redefines how hobbyists and professionals manage their reef aquariums. 

While it will feature all the standard tracking elements you would expect from a premium aquarium app (graphs, charts, manual logging, tank inhabitants, notes, and a calendar), the true differentiator of ReefGPT is its **Advanced Agentic AI capabilities**.

## The "20-Year LFS Owner" In Your Pocket

The core vision for the AI chatbot is to function exactly like having a Local Fish Store (LFS) owner with 20 years of expert reefing experience standing right next to your tank. 

To achieve this, the AI must possess:
- **Absolute Context**: The AI will maintain full context of your tank's entire history at all times—understanding past parameters, previous livestock, historical crashes, and ongoing treatments.
- **Multi-Step RAG**: The system will utilize a highly efficient multi-step Retrieval-Augmented Generation (RAG) pipeline to maximize diagnostic accuracy while keeping token usage low and response times incredibly fast.
- **Nuanced Expertise**: The AI will be capable of answering highly nuanced, complex reefing questions by cross-referencing your specific tank parameters against a vast, expertly curated vector database of reef knowledge.

## Agentic Capabilities (Database Control)

The AI is not just a passive chatbot; it is an active manager of your tank. Through the chat window, the AI will have the agency to read and mutate the database on your behalf:
- **Adding Livestock**: If you tell the AI you just bought a new Yellow Tang, it will parse that request and automatically propose adding it to your tank profile.
- **Smart Deletion (Soft Deletes)**: If a fish passes away or is rehomed, you can tell the AI. It will remove the fish from your active inhabitants list, but it will *remember* that you once had it for future diagnostic context. (Note: A hard-delete option will remain available for developers to fully purge records if needed).
- **Automated Event Logging**: The AI will log significant events or observations mentioned in chat directly to your tank's timeline.

## Hardware Integration

To close the loop on automation, ReefGPT aims to eventually integrate directly with auto-testing hardware (e.g., Neptune Trident, Mastertronic, ReefBot, etc.). This will allow the system to continuously pull real-time parameter data, enabling the AI to proactively alert the user of dangerous trends before they result in livestock loss.
