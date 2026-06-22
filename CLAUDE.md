# CLAUDE.md — ChessEngine

Guide de travail pour Claude Code sur ce dépôt. Lis-le avant d'agir.

## Vue d'ensemble

Analyseur de parties d'échecs basé sur **python-chess + Stockfish (UCI)**. Le projet **bascule définitivement vers l'application web** (frontend « Caissa », `web/`). **Décision actée : l'app desktop Tkinter (`main.py` + `src/gui`, `src/user/profile.py`) est ABANDONNÉE et destinée à être supprimée** — ne plus y investir, ne plus maintenir la compatibilité desktop.

Le **cœur d'analyse Python** (`src/core`, `src/engine`, `src/analysis`) reste : il alimente le backend web. ⚠️ Mais une partie de `src/analysis` n'est utilisée QUE par le desktop (`game_analyzer.py`, `game_difficulty.py`, `move_analyzer.py`, `tactical_analyzer.py`) — le web réimplémente ces logiques dans `web/backend/services`. Lors du retrait du desktop, ces modules desktop-only et `src/utils/config.py` (couplé à tkinter) partiront aussi ; le web garde `chess_game`, `engine_manager`, `move_classifier`, `player_stats`, `opening_detector`.

Langue : l'**UI est en français**, le code et les commentaires sont souvent en anglais (incohérence assumée du projet).

## Architecture

```
ChessEngine/
├── src/                 # Cœur d'analyse Python (importé par le backend web)
│   ├── core/            # ChessGame (wrapper chess.Board)
│   ├── engine/          # EngineInstance — Stockfish via UCI
│   ├── analysis/        # MoveClassifier, PlayerStats, OpeningDetector
│   └── utils/config.py  # ENGINE_ANALYSIS / MOVE_CLASSIFICATION (sans UI, sans tkinter)
├── web/
│   ├── backend/         # API FastAPI (réutilise src/ via sys.path)
│   │   ├── main.py      # app FastAPI, CORS (CORS_ORIGINS), logging, uvicorn:8000
│   │   ├── config.py    # STOCKFISH_PATH (env) + PROFILE_DIR = user_profiles/web
│   │   ├── routers/     # game.py (jeu/analyse/import SSE), profiles.py, engine.py
│   │   ├── services/    # analysis.py, difficulty.py, chesscom.py, lichess.py
│   │   └── managers/    # engine_manager, game_manager (sessions EN MÉMOIRE), profile_manager
│   └── frontend/        # SPA React 19 + Vite 7 + TS + Tailwind v4
│       └── src/         # hooks/useChessGame.ts = contrôleur central
│                        # lib/types.ts → API_URL via VITE_API_URL (défaut localhost:8000)
├── eco.json/            # DOSSIER : base ECO (ouvertures), ~8 Mo, vendored
└── user_profiles/web/   # Profils JSON web (local, non versionné — PII)
```

Stack : **backend** = FastAPI / uvicorn / pydantic / python-chess ; **frontend** = React 19 / Vite 7 / chess.js / react-chessboard / axios + fetch(SSE) / framer-motion. **Stockfish** est un binaire externe (non inclus).

## Lancer le projet (dev)

Les serveurs sont configurés dans **`.claude/launch.json`** (commandes validées). Préférer `preview_start` (`backend`, `frontend`) à un lancement manuel.

- **Backend** (port 8000) : se lance **comme module depuis la racine** avec le **Python du venv** :
  `venv\Scripts\python.exe -m uvicorn web.backend.main:app --host 127.0.0.1 --port 8000`
- **Frontend** (port 5173) : `npm --prefix web/frontend run dev`
- Ou les deux d'un coup : `./dev.ps1`.
- **Usage « 1 clic »** : `start.bat` (double-clic) lance **un seul serveur** — FastAPI sert l'API + le frontend buildé (`web/frontend/dist`) via un catch-all, et ouvre le navigateur sur `http://127.0.0.1:8000`. En mono-process les appels sont en **même origine** (`API_URL=''`) ; en dev Vite, `web/frontend/.env.development` fixe `VITE_API_URL=http://localhost:8000`. Après une modif d'UI, rebuilder (`npm --prefix web/frontend run build`) pour que `start.bat` la reflète.

Vérifs : `GET http://localhost:8000/engine/status` (Stockfish OK ?), UI sur `http://localhost:5173`, Swagger sur `/docs`.

Deux pièges de lancement (déjà gérés dans `launch.json`) :
1. **Plusieurs Python** sur la machine ; seul **`venv/`** a FastAPI/uvicorn. Ne pas compter sur le `python` du PATH.
2. **`python web/backend/main.py` (script isolé) plante** sur un import relatif (`from ..config ...`). Toujours lancer **en mode module** (`-m uvicorn web.backend.main:app`) depuis la racine.

## Workflow Git

- **Commit et push directement autorisés** — pas besoin de demander confirmation avant de committer/pousser le travail demandé. **Pousser directement sur `master` est OK**, mais **toujours `git pull --rebase` avant si le remote a bougé** (rebaser plutôt que créer un merge commit). Une branche reste préférable pour les gros changements, mais ce n'est pas bloquant (les merger en fast-forward dans `master`).
- **NE PAS signer les commits** : **aucun trailer `Co-Authored-By: Claude ...`** dans les messages de commit. Messages concis et factuels.
- État du dépôt : `web/` est désormais **suivi et poussé** sur `origin/master` ; `node_modules`/`dist`/`.claude/settings.local.json` sont gitignorés. La branche est synchronisée avec le remote. Restent en working tree des changements **non commités et non liés** (suppressions de `AuditPanRetention/`, modifs `user_profiles/*.json`, `player_stats.py`) — à trancher par l'auteur ; ne pas committer la suppression d'`AuditPanRetention/` à l'aveugle (le remote y développe activement). Voir `OPTIMISATION.md` pour le plan de nettoyage.

## Pièges critiques (à connaître avant de coder)

- **Chemin Stockfish** : configurable via `STOCKFISH_PATH` (env), fallback machine dans `web/backend/config.py`. Si Stockfish bouge, ajuster la variable.
- **Constantes d'analyse codées en dur côté web** : `services/analysis.py` (depth 16) et `services/difficulty.py` ré-implémentent la logique sans importer `src/utils/config.py` (`ENGINE_ANALYSIS`/`MOVE_CLASSIFICATION`). À unifier (cf `A-01`/`A-02` dans `OPTIMISATION.md`). Incohérence connue : `mate_score` = 100000 dans `routers/game.py` vs 10000 ailleurs.
- **Sessions de jeu en mémoire** (`game_manager.py` = dict) : perdues au redémarrage du backend.
- **Profils** : le web écrit dans `user_profiles/web/<slug>.json` (isolé). Ces fichiers contiennent de la PII et **ne doivent pas être commités** (gitignore à faire — cf `S-05`).
- **API non authentifiée** : les endpoints (dont `DELETE /profiles/{username}`) n'ont aucun contrôle d'accès. Le backend bind `127.0.0.1` (usage local) — ne **jamais** l'exposer au réseau sans ajouter une auth (cf `S-03`).

## Dette technique connue (ne pas s'en étonner)

- **Tests pytest** sous `tests/` (smoke API, move_classifier, player_stats, difficulty) — à lancer **localement avant commit/push** (`venv\Scripts\python.exe -m pytest -q`). **Pas de CI** : volontairement retirée (petit projet perso, les tests tournent en local).
- **God-files** web : `useChessGame.ts` (~710 l.), `GameReport.tsx` (~700 l.) — à découper (cf `Q-06`).
- Résidus desktop encore sur disque (gitignorés) : `ChessEngine.spec`/`main.spec` (PyInstaller, obsolètes), `dist/`/`build/`, `Images/` (assets desktop à nettoyer). `venv/` reste nécessaire (il fait tourner le backend).
- **`AuditPanRetention/`** : projet **sans rapport** committé par erreur, supprimé en working tree mais pas commité — le remote y développe activement, ne pas committer la suppression à l'aveugle.
- `@app.on_event('startup')` déprécié (cf `D-06`).

## Conventions de travail

- Le cœur `src/` (analysis, engine, core) n'a plus qu'un **seul consommateur : le backend web**. Plus de compatibilité desktop à maintenir.
- Toute nouvelle config (chemins, ports, URLs) : viser des **variables d'environnement** plutôt que du hardcodé.
- Respecter le style du fichier voisin (densité de commentaires, nommage). Ne pas reformater du code non touché.
- Plan d'optimisation et dette détaillés dans `OPTIMISATION.md` (findings `Q-`/`A-`/`P-`/`D-`/`M-`/`S-`).
