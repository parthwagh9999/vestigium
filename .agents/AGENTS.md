# Global Architecture Rules for Nexus Intelligence

Welcome to the Nexus Intelligence repository. Whenever you act as a developer, architect, or investigator on this project, you must strictly adhere to the following laws:

## 1. The Zero-Duplicate Graph Law
- **Never create duplicate nodes for the same entity.**
- You must always query the graph first to resolve if an entity exists.
- Return newly discovered entities using the `Entity` and `EntityRelationship` models.
- **Never** turn an inference into a fact. A relationship must have a confidence score.
- Active scanning (tools that touch the target server) must be clearly separated from passive OSINT (tools that touch third-party databases).

## 2. Tech Stack Mandate
- **Backend**: Python 3.10+, FastAPI, SQLAlchemy (Async), SQLite.
- **Frontend**: React, Vite, Tailwind CSS, Zustand.
- **Graph Visualization**: React Flow or vis-network.

## 3. UI/UX Design Aesthetics
- The platform MUST feel like a state-of-the-art cyber-intelligence tool.
- Utilize deep dark themes (`bg-slate-900`, `bg-slate-950`).
- Apply subtle glassmorphism (translucency + backdrop blur) for panels and modals.
- Incorporate micro-animations for interactivity (spinners, hover states, transitions).
- Use `lucide-react` for all iconography.

## 4. Development Protocol
- Always run tests and verify functionality after writing a feature.
- Use the built-in testing scripts in `.agents/skills/...` when developing new tools.
- Do not blindly assume third party API tools (like `amass` or `exiftool`) are installed on the host. Always implement Graceful Degradation.
