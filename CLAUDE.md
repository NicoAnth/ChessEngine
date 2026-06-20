# CLAUDE.md — ChessEngine

Guide de travail pour Claude Code sur ce dépôt. Lis-le avant d'agir.

## Vue d'ensemble

Analyseur de parties d'échecs basé sur **python-chess + Stockfish (UCI)**. Le projet est en **bascule d'une application desktop Tkinter** (nom interne « Chessoria », `main.py` + `src/`) **vers une application web** (frontend « Caissa », `web/`).

Le **cœur d'analyse Python** (`src/core`, `src/engine`, `src/analysis`) est **partagé** : il alimente les deux frontends. **La cible de développement actuelle est le web** ; le desktop est en mode legacy (encore fonctionnel mais plus la priorité).

Langue : l'**UI est en français**, le code et les commentaires sont souvent en anglais (incohérence assumée du projet).

## Architecture

```
ChessEngine/
├── main.py              # Point d'entrée DESKTOP (Tkinter) — legacy
├── src/                 # Cœur Python
│   ├── core/            # ChessGame (wrapper chess.Board)            [ACTIF, partagé]
│   ├── engine/          # EngineManager/EngineInstance (Stockfish)   [ACTIF, partagé]
│   ├── analysis/        # MoveClassifier, PlayerStats, OpeningDetector,
│   │                    #   GameAnalyzer, GameDifficulty             [ACTIF, partagé]
│   ├── user/profile.py  # Profils JSON desktop (UserProfileManager)  [LEGACY]
│   ├── gui/             # UI Tkinter (god-files 34–69 KB)            [LEGACY]
│   └── utils/config.py  # Constantes d'analyse + couleurs Tkinter (couplé UI)
├── web/                 # NOUVELLE direction — ⚠️ untracked dans git (voir Git)
│   ├── backend/         # API FastAPI (réutilise src/ via sys.path)  [ACTIF]
│   │   ├── main.py      # app FastAPI, CORS, 3 routers, uvicorn:8000
│   │   ├── config.py    # DEFAULT_ENGINE_PATH (Stockfish) + PROFILE_DIR
│   │   ├── routers/     # game.py (jeu/analyse/import SSE), profiles.py, engine.py
│   │   ├── services/    # analysis.py, difficulty.py, chesscom.py, lichess.py
│   │   └── managers/    # engine_manager, game_manager (sessions EN MÉMOIRE), profile_manager
│   └── frontend/        # SPA React 19 + Vite 7 + TS + Tailwind v4   [ACTIF]
│       └── src/         # hooks/useChessGame.ts = contrôleur central (~710 l.)
│                        # lib/types.ts → API_URL = 'http://localhost:8000' (hardcodé)
├── eco.json/            # DOSSIER : base ECO (ouvertures), ~8 Mo, vendored
└── user_profiles/       # Profils JSON (⚠️ écrits par les DEUX systèmes, voir Pièges)
```

Stack : **backend** = FastAPI / uvicorn / pydantic / python-chess ; **frontend** = React 19 / Vite 7 / chess.js / react-chessboard / axios + fetch(SSE) / framer-motion. **Stockfish** est un binaire externe (non inclus).

## Lancer le projet (dev)

Les serveurs sont configurés dans **`.claude/launch.json`** (commandes validées). Préférer `preview_start` (`backend`, `frontend`) à un lancement manuel.

- **Backend** (port 8000) : se lance **comme module depuis la racine** avec le **Python du venv** :
  `venv\Scripts\python.exe -m uvicorn web.backend.main:app --host 0.0.0.0 --port 8000`
- **Frontend** (port 5173) : `npm --prefix web/frontend run dev`
- **Desktop legacy** : `python main.py [chemin_stockfish]` (app fenêtrée, pas de port).

Vérifs : `GET http://localhost:8000/engine/status` (Stockfish OK ?), UI sur `http://localhost:5173`, Swagger sur `/docs`.

Deux pièges de lancement (déjà gérés dans `launch.json`) :
1. **Plusieurs Python** sur la machine ; seul **`venv/`** a FastAPI/uvicorn. Ne pas compter sur le `python` du PATH.
2. **`python web/backend/main.py` (script isolé) plante** sur un import relatif (`from ..config ...`). Toujours lancer **en mode module** (`-m uvicorn web.backend.main:app`) depuis la racine.

## Workflow Git

- **Commit et push directement autorisés** — pas besoin de demander confirmation avant de committer/pousser le travail demandé. Si on est sur `master`, créer une branche reste préférable pour les gros changements, mais ce n'est pas bloquant.
- **NE PAS signer les commits** : **aucun trailer `Co-Authored-By: Claude ...`** dans les messages de commit. Messages concis et factuels.
- État actuel à surveiller : **`web/` est entièrement untracked** (`?? web/`, 0 fichier suivi) — c'est tout le futur du projet, non sauvegardé. La branche locale `master` est **en retard sur `origin/master`**, avec des suppressions non commitées. **Ne jamais faire `git clean`** tant que `web/` n'est pas commité. Avant de committer `web/`, compléter `.gitignore` (`web/**/node_modules`, `web/**/dist`).

## Pièges critiques (à connaître avant de coder)

- **Collision des profils ⚠️** : `src/user/profile.py` (desktop) et `web/backend/managers/profile_manager.py` (web) écrivent dans le **même** `user_profiles/<slug>.json` avec des **schémas incompatibles**. Le `save_profile()` desktop **écrase silencieusement** les données web (clé `games[]`, comptes chess.com/lichess). → Ne pas tester le desktop sur un profil utilisé par le web (ex. `nutty_bishops.json`).
- **Chemin Stockfish hardcodé** en absolu (`H:\Ouvertures Echecs\...stockfish.exe`) à **deux endroits** : `main.py` et `web/backend/config.py`. À adapter selon la machine.
- **`API_URL` frontend hardcodé** (`http://localhost:8000` dans `lib/types.ts`) : pas d'env ni de proxy Vite → tout déploiement non-local casse sans changement de code.
- **Logique métier dupliquée et DIVERGENTE** desktop vs web :
  - difficulté : `src/analysis/game_difficulty.py` (entropie softmax) ≠ `web/backend/services/difficulty.py` (algo différent) → scores différents pour la même partie.
  - analyse de coup : depth **20** côté desktop vs **16** côté web `services/analysis.py`.
  Si un score diffère entre les deux, **c'est de la dette connue**, pas un bug à « corriger » naïvement.
- **`web/backend/requirements.txt` est incomplet** : `requests` (utilisé par `chesscom.py`/`lichess.py`) y manque.
- **`src/utils/config.py` importe `tkinter`** : le backend web ne peut pas le réutiliser tel quel (raison racine des valeurs codées en dur côté web).
- **Sessions de jeu en mémoire** (`game_manager.py` = dict) : perdues au redémarrage du backend.

## Dette technique connue (ne pas s'en étonner)

- **Aucun test, aucune CI** nulle part.
- **God-files** : `analysis_view.py`/`user_profile_window.py` (~69 KB), `useChessGame.ts` (~710 l.), `GameReport.tsx` (~700 l.).
- Résidus : `src/gui/main_window.py.bak`, doublon de specs PyInstaller, `dist/`/`build/`/`venv/` sur disque, `Images/old/`, `web/package.json` redondant avec `web/frontend/package.json`.
- **`AuditPanRetention/`** : projet **sans rapport** committé par erreur (audit cartes bancaires FR) — en cours de suppression.
- Mineurs : CORS `allow_origins=['*']` + `allow_credentials=True` ; `@app.on_event('startup')` déprécié ; hooks React conditionnels dans `GameReport.tsx`.

## Conventions de travail

- Avant de modifier le cœur (`src/analysis`, `src/engine`), vérifier l'impact **sur les deux frontends** (desktop + web l'importent).
- Toute nouvelle config (chemins, ports, URLs) : viser des **variables d'environnement** plutôt que du hardcodé.
- Respecter le style du fichier voisin (densité de commentaires, nommage). Ne pas reformater du code non touché.
- README racine = vision desktop d'origine, **pas à jour** par rapport au web — se fier à ce CLAUDE.md.
