# Caissa — Chess Analysis (Web)

Application web d'analyse de parties d'échecs : jeu contre **Stockfish**, analyse coup par coup, import de PGN (avec analyse en streaming), rapport de partie détaillé et profils liés à Chess.com / Lichess. Cœur d'analyse en Python (`python-chess` + Stockfish), API **FastAPI**, interface **React + Vite**.

> ℹ️ L'ancienne application desktop Tkinter a été retirée — le projet est désormais 100 % web. Son code reste consultable dans l'historique git.

## Fonctionnalités

- Jeu contre Stockfish avec évaluation en temps réel (barre d'éval)
- Analyse coup par coup : classification (Théorie, Meilleur coup, Excellent, Bon coup, Imprécision, Erreur, Grosse erreur, Super coup), précision et ACPL
- Import de PGN avec analyse en **streaming (SSE)** et barre de progression
- Rapport de partie : précision par couleur, graphe d'évaluation, difficulté de partie, ouverture détectée (base ECO)
- Profils utilisateurs liés à **Chess.com** et **Lichess** (récupération et import des parties)

## Architecture

```
ChessEngine/
├── src/                 # Cœur d'analyse Python (importé par le backend)
│   ├── core/            # ChessGame (wrapper python-chess)
│   ├── engine/          # EngineInstance — communication Stockfish (UCI)
│   ├── analysis/        # MoveClassifier, PlayerStats, OpeningDetector
│   └── utils/config.py  # Constantes d'analyse (sans UI)
├── web/
│   ├── backend/         # API FastAPI (routers, services, managers)
│   └── frontend/        # SPA React 19 + Vite 7 + TypeScript + Tailwind v4
├── eco.json/            # Base ECO (ouvertures), vendored
└── user_profiles/web/   # Profils JSON (local, non versionné)
```

## Prérequis

- **Python** (venv du projet) : `pip install -r web/backend/requirements.txt`
- **Node.js** (pour le frontend)
- **Stockfish** (binaire externe) — chemin via la variable d'environnement `STOCKFISH_PATH` (sinon valeur par défaut). Télécharger sur [stockfishchess.org](https://stockfishchess.org).

## Démarrage (dev)

```bash
# Les deux serveurs d'un coup (Windows)
./dev.ps1

# — ou séparément —
# Backend (port 8000) — en module, depuis la racine, avec le Python du venv
venv\Scripts\python.exe -m uvicorn web.backend.main:app --host 0.0.0.0 --port 8000
# Frontend (port 5173)
npm --prefix web/frontend run dev
```

- UI : http://localhost:5173 · API / Swagger : http://localhost:8000/docs
- Le frontend cible le backend via `VITE_API_URL` (défaut `http://localhost:8000`, voir `web/frontend/.env.example`).

Architecture détaillée, conventions et pièges : [CLAUDE.md](CLAUDE.md). Plan d'optimisation : [OPTIMISATION.md](OPTIMISATION.md).

## Licence

MIT — voir le fichier LICENSE.

## Remerciements

- [Stockfish](https://stockfishchess.org) pour le moteur d'échecs
- [python-chess](https://python-chess.readthedocs.io) pour la logique d'échecs
