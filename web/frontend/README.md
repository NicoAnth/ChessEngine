# Caissa — Frontend (React + Vite + TypeScript)

Client web de ChessEngine : jeu contre Stockfish, analyse coup par coup, import PGN (streaming SSE), rapport de partie et profils (Chess.com / Lichess). Stack : React 19, Vite 7, TypeScript, Tailwind v4, `chess.js` + `react-chessboard`.

## Démarrage

```bash
npm install          # une fois
npm run dev          # serveur de dev sur http://localhost:5173
```

Le frontend appelle l'API backend via `VITE_API_URL` (défaut `http://localhost:8000`). Pour pointer ailleurs, copier `.env.example` en `.env` et ajuster :

```
VITE_API_URL=http://localhost:8000
```

> Le backend FastAPI doit tourner (cf [README racine](../../README.md) ou `./dev.ps1`).

## Scripts

- `npm run dev` — serveur de dev (HMR)
- `npm run build` — type-check + build de production (`tsc -b && vite build`)
- `npm run preview` — sert le build de production
- `npm run lint` — ESLint
