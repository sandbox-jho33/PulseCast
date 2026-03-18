# Frontend

Frontend-specific setup and development commands for PulseCast. The primary project documentation lives in the root [README](../README.md).

## Quick Commands

```bash
cd frontend
bun install
bun dev
```

## Useful Commands

```bash
bun run build
bun run lint
bun run preview
```

## Notes

- The app is built with React 19, TypeScript, Vite, and Tailwind CSS 4
- The Vite dev server proxies `/api` requests to `http://localhost:8000`
- Start the backend before using the UI locally
