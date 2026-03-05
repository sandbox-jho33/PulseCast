# AGENTS.md - PulseCast Development Guide

Guidelines for AI coding agents working on the PulseCast codebase.

## Project Overview

PulseCast transforms web articles into conversational podcasts using AI.
- **Backend**: Python 3.12+ / FastAPI / LangGraph / LangChain
- **Frontend**: React 19 / TypeScript 5.9 / Vite 7 / Tailwind CSS 4

## Development Commands

### Backend (from `backend/` directory)

```bash
uv sync                                    # Install dependencies
uv run uvicorn app.main:app --reload --port 8000  # Run dev server
uv add <package-name>                      # Add dependency
uv run python <script.py>                  # Run a script
uv run mypy app/                           # Type check (if installed)
uv run ruff check app/                     # Lint (if installed)
```

### Frontend (from `frontend/` directory)

```bash
bun install                                # Install dependencies
bun dev                                    # Run dev server
bun run build                              # Build (includes type check)
bun run lint                               # Run linter
```

### Full Stack Development

1. Terminal 1: `cd backend && uv run uvicorn app.main:app --reload --port 8000`
2. Terminal 2: `cd frontend && bun dev`

Frontend proxies `/api` requests to `http://localhost:8000`.

## Environment Configuration

Copy `backend/.env.example` to `backend/.env`:

```bash
LLM_PROVIDER=ollama                        # "ollama" (local) or "openai" (cloud)
OLLAMA_MODEL=llama3.2:1b
OLLAMA_BASE_URL=http://localhost:11434
OPENAI_API_KEY=sk-...                      # Required if LLM_PROVIDER=openai
```

## Code Style Guidelines

### Python (Backend)

**Imports** - Group: future → stdlib → third-party → local (relative)
```python
from __future__ import annotations
import os
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from ...models.state import PodcastState
```

**Type hints** - Always use them. **Pydantic models** - Use Field with descriptions.

**Error handling** - HTTPException in routes; try/except in background tasks:
```python
if not state:
    raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
```

**Naming**: `snake_case` (functions/variables), `PascalCase` (classes/Enums), `UPPER_CASE` (constants), `_private` (helpers).

### TypeScript (Frontend)

**Imports** - Type imports first: `import type { StatusResponse } from '../types/podcast';`

**Types** - `type` for object shapes, `interface` for extensible types.

**Components** - Functional with explicit return types: `function Component({ prop }: Props): JSX.Element`

**Naming**: `camelCase` (functions/variables), `PascalCase` (components/types), `useSomething` (hooks).

## Architecture

```
backend/app/
├── api/routes/     # FastAPI route handlers
├── graph/          # LangGraph workflow nodes (researcher → leo → sarah → director)
├── models/         # Pydantic models (PodcastState)
├── services/       # External integrations (ingestion, audio)
├── storage/        # Persistence layer (repository.py)
├── llm.py          # LLM factory (Ollama/OpenAI)
└── main.py         # FastAPI app factory

frontend/src/
├── api/            # API client functions
├── components/     # React components
├── hooks/          # Custom React hooks
├── types/          # TypeScript type definitions
└── App.tsx         # Main application component
```

**Key Patterns**:
- **PodcastState** - Central state model; matching Pydantic/TypeScript definitions
- **Graph workflow** - LangGraph nodes process state, loop based on `director_decision`
- **Repository pattern** - `storage/repository.py` abstracts persistence (in-memory → Postgres)

## LLM Integration

```python
from app.llm import get_llm
llm = get_llm()  # Returns ChatOllama or ChatOpenAI based on LLM_PROVIDER
response = await llm.ainvoke([HumanMessage(content="Hello")])
```

## Testing

No test framework configured. When adding:
```bash
# Backend
uv add pytest pytest-asyncio
uv run pytest

# Frontend
bun add -d vitest @testing-library/react
bun test
```

## Git Workflow

- Commit messages: concise and descriptive
- Never commit `.env` files
- Run linting before committing
