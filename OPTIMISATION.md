# 📊 Rapport d'Optimisation — ChessEngine (projet entier)

> **⚠️ Mise à jour stratégique (2026-06-20)** : décision d'**abandonner le desktop** et de basculer 100 % web. Plusieurs chantiers de déduplication (`A-01`/`A-02`/`A-03`/`A-05`/`A-06`, `Q-12`, `D-07`) se résolvent désormais par **suppression du côté desktop** plutôt que par refactor à double compatibilité — une étape « retrait du desktop » devient le pivot du plan et précède la déduplication.

> **✅ Avancement (2026-06-20)** — implémenté, testé et poussé sur `origin/master` :
> - **Phase 0** : `M-10` (branche synchronisée), `S-05` (profils PII dé-trackés + gitignore), `S-02`/`M-09` (`AuditPanRetention` extrait dans son propre dépôt), `Q-03` (`.bak` parti avec le desktop).
> - **Phase 1** : `D-01`/`D-02`/`D-03`/`M-04` (requirements), `S-01` (profils web isolés `user_profiles/web/`), `M-01`/`D-08`/`S-06` (`STOCKFISH_PATH`), `M-02` (`VITE_API_URL`), `S-04` (CORS restreint), `P-05` (~12 Mo d'assets morts), `M-06`/`M-08` (README web + `dev.ps1`).
> - **Retrait du desktop** (~14k lignes) → résout `Q-12`, `A-05`, `A-06` et la divergence `A-01`/`A-02`/`A-03`/`D-07` (les versions desktop n'existent plus ; `services/difficulty.py` et `services/analysis.py` sont les seules implémentations).
> - **Phase 2** : `Q-04`/`D-05` (Tailwind v4), `Q-07` (hook conditionnel), `Q-11` (types morts), `M-05` (logging), `Q-08` (palette, résolu par le retrait desktop), `Q-09` (`mate_score`), `Q-10` (clés de config inertes). `Q-01`/`Q-02` laissés volontairement (placeholder « Coup brillant »).
> - **Phase 3** : `M-03` (pytest + CI GitHub Actions, 21 tests), `A-05` (config découplée de tkinter).
> - **Phase 4** : `P-04` (base ECO chargée 1×/processus, partagée), `P-03` (lookup O(1) + borne de détection), `P-02` (mémoïsation par position, **–47 % d'appels moteur** à l'import, ≤0.10 pion de décalage, 0 reclassification). `P-01` (parallélisation) **reporté** — chantier d'archi (couplage singleton/pool).
>
> - **Finalisation** : `D-06` (lifespan FastAPI), `S-03` (bind `127.0.0.1` + API non authentifiée documentée), `M-07` (schéma profil Pydantic `GameRecord`/`StoredProfile`, validation à l'écriture).
>
> **Reste** : `Q-06` (découpe `useChessGame.ts`), `A-04`/`A-08` (façade d'orchestration, en partie caduc), `P-01` (parallélisation import), `P-06`/`P-07` (frontend), `A-07` (renommer le manager moteur web), nettoyage des assets `Images/` desktop.

> Audit read-only mené par fan-out multi-agents (6 dimensions × audit + revérification `fichier:ligne` + synthèse). Le livrable est ce rapport priorisé par **ratio gain/effort** + un plan d'implémentation séquencé. Aucun code n'a été modifié par l'audit.

## Vue d'ensemble du projet

- **Stack** : Python 3.12 (cœur `src/` + desktop Tkinter legacy), backend **FastAPI/uvicorn** (`web/backend`), frontend **React 19 + Vite 7 + TS + Tailwind v4** (`web/frontend`). Moteur **Stockfish** (UCI) externe, `python-chess`, base ECO vendored (`eco.json/`).
- **Architecture** : cœur d'analyse partagé (`src/core`, `src/engine`, `src/analysis`) réimporté par le backend web via `sys.path`. Bascule desktop → web en cours.
- **Périmètre audité** : intégralité du dépôt (cœur, desktop, backend, frontend, deps, config, sécurité/données).
- **Volume** : ~46 constats vérifiés sur les 6 dimensions.

## Résumé exécutif

Santé générale **moyenne** sur une **fondation saine** : le cœur d'analyse est correctement factorisé et réutilisé par le web (à préserver). La dette structurelle majeure vient de la transition : **duplication métier profonde et divergente** (difficulté, analyse de coup, profils, constantes) entre desktop et web. Les risques les plus graves sont (1) **d'intégrité des données** — le `save` desktop écrase silencieusement les parties et liens web du même profil partagé (`S-01`) ; (2) **de reproductibilité** — `requirements.txt` backend incomplet (`requests`/`numpy` manquants), le backend casse sur install propre (`D-01/D-02/M-04`) ; (3) **de portabilité** — chemin Stockfish et `API_URL` hardcodés (`M-01/M-02/D-08`). Côté perf, l'import PGN web **gaspille ~50 % du temps moteur** (double analyse redondante `P-02` + exécution strictement séquentielle sur une instance verrouillée `P-01`, alors qu'un pool parallèle existe déjà). **Aucun test ni CI** (`M-03`) → figer le comportement avant tout gros refactor. Bonne nouvelle : les plus gros gains sont à **faible coût** (compléter requirements, isoler les profils, externaliser les chemins, scinder `config.py` de tkinter).

## Statistiques

| Priorité | Nombre | Effort dominant |
|----------|:------:|-----------------|
| 🔴 Haute    | 17 | XS–S (sauf déduplication cœur en L) |
| 🟠 Moyenne  | 21 | XS–M |
| 🟡 Basse    | 6  | S |
| 💡 Idée     | 2  | — (consigné, non investi) |

---

## Findings

Format : `ID` priorité **titre** — *effort · gain · risque*.

### 1. Qualité du code & code mort

#### `Q-01` 🔴 « Coup brillant » : code mort de bout en bout — *M · élevé · faible*
- **Fichiers** : `src/analysis/move_classifier.py:231-236,278`, `src/analysis/move_analyzer.py:280`, `web/backend/services/analysis.py:97`, `src/analysis/player_stats.py:40,49`, `src/utils/config.py:137,241`, `web/frontend/src/lib/utils.ts:13`, `web/frontend/src/components/GameReport.tsx:591`
- **Problème** : la classification est entièrement commentée (jamais émise), mais toute l'infra qui la sert reste vivante (compteurs, couleurs, labels, ordre). Pire : son seul consommateur `is_move_sacrifice()` (scan coûteux des 64 cases) est calculé à chaque coup côté web **pour rien**.
- **Reco** : trancher — **(a) supprimer** la feature de bout en bout (recommandé, supprime un calcul CPU inutile) ou (b) la réactiver. Ne pas laisser l'état hybride.

#### `Q-02` 🔴 `classify_move` : 4 params + 2 variables locales jamais utilisés — *S · moyen · faible*
- **Fichiers** : `src/analysis/move_classifier.py:167-200`
- **Problème** : `score_diff_from_best`, `is_capture`, `is_sacrifice`, `top_moves` jamais lus ; `winning_threshold`/`position_improved` morts ; docstring tronquée. La signature ment sur les dépendances réelles.
- **Reco** : retirer les params (coordonner les 2 appelants) ou a minima les variables mortes + compléter la docstring. Vérifier les 2 frontends.

#### `Q-03` 🔴 `main_window.py.bak` (1418 l.) tracké — *XS · moyen · faible*
- **Fichiers** : `src/gui/main_window.py.bak`
- **Problème** : seul artefact indésirable réellement suivi par git (doublon ~60 KB). Pollue grep/IDE, éditable par erreur.
- **Reco** : `git rm` (l'historique git EST la sauvegarde). Ajouter `*.bak` au `.gitignore`.

#### `Q-04` 🟠 Tailwind v4 : `tailwind.config.js` + `postcss.config.js` + deps redondants — *S · moyen · faible*
- **Fichiers** : `web/frontend/tailwind.config.js`, `postcss.config.js`, `package.json:13,32,37`, `vite.config.ts:3`
- **Problème** : Tailwind v4 câblé via `@tailwindcss/vite` (voie suffisante), mais résidus v3/PostCSS (`autoprefixer`, `@tailwindcss/postcss`) → deux pipelines déclarés.
- **Reco** : supprimer les 2 configs + `@tailwindcss/postcss`/`autoprefixer`/`postcss`, garder `@tailwindcss/vite` + `tailwindcss`. Vérifier le build.

#### `Q-05` 🟠 `web/package.json` fantôme — *XS · moyen · faible*
- **Fichiers** : `web/package.json` vs `web/frontend/package.json`
- **Problème** : doublon partiel sans `name` ni scripts, rattaché à aucun outil. Deux listes de versions divergentes.
- **Reco** : supprimer `web/package.json` (+ lock + `node_modules`). Racine npm unique = `web/frontend`.

#### `Q-06` 🟠 `useChessGame.ts` (710 l.) : hook monolithique 6 domaines — *L · moyen · moyen*
- **Fichiers** : `web/frontend/src/hooks/useChessGame.ts:24-710`
- **Problème** : ~28 morceaux de state, ~30 valeurs exposées (jeu, moteur, insights, profils, import SSE bas niveau, navigation clavier). Tout consommateur re-rend sur n'importe quel changement.
- **Reco** : découper par domaine — extraire d'abord `useProfiles` (l.136-237) et `useGameImport` (l.374-517), puis `useReplayNavigation` (l.539-612). **Après** le filet de tests.

#### `Q-07` 🟠 `GameReport.tsx` : hook appelé après un early return (rules-of-hooks) — *XS · moyen · faible*
- **Fichiers** : `web/frontend/src/components/GameReport.tsx:32,35`
- **Problème** : `if (!isOpen) return null` (l.32) **avant** `useTheme()` (l.35) → ordre des hooks variable, bug React latent.
- **Reco** : déplacer l'early return après tous les hooks, ou le supprimer (le rendu conditionnel `{isOpen && …}` existe déjà l.38-39).

#### `Q-08` 🟠 Palette de classification dupliquée en 4 sources divergentes — *S · moyen · faible*
- **Fichiers** : `src/utils/config.py:129-139`, `src/analysis/move_classifier.py:268-280`, `web/frontend/src/lib/utils.ts:10-20`, `web/frontend/src/components/GameReport.tsx:585-595`
- **Problème** : mêmes notions, **couleurs différentes** selon l'écran (ex. « Excellent » `#3BD97B` vs `#6BE29B`). Coquille `#A78BFA ` (espace final, `config.py:138`).
- **Reco** : une source par plateforme — desktop : `get_classification_color` = lookup dans `config` ; web : `utils.ts` seule source. Aligner les teintes, corriger la coquille.

#### `Q-09` 🟠 Magic numbers profondeur/`mate_score` dispersés et incohérents (web) — *S · moyen · faible*
- **Fichiers** : `web/backend/services/analysis.py:40-79`, `web/backend/routers/game.py:95,139,149`, `src/utils/config.py:196-213`
- **Problème** : `depth` 16/15 et `mate_score` répété en littéraux — **incohérence réelle** `mate_score=100000` (`game.py:149`) vs `10000` partout ailleurs → échelle de score de mat fausse selon la route.
- **Reco** : module de constantes backend (`ENGINE_DEPTH`, `MATE_SCORE`, `MULTIPV`). Au minimum uniformiser `mate_score`. Nommer `DEPTH_FULL_ANALYSIS = 16` (divergence assumée).

#### `Q-10` 🟡 Clés de config jamais lues (`meilleur_coup_threshold`, `grosse_erreur_threshold`) — *XS · faible · faible*
- **Fichiers** : `src/utils/config.py:218,223`, `src/analysis/move_classifier.py:241-252`
- **Problème** : faux leviers de réglage (décidés par `rank == 0` et le `else` final). **Reco** : supprimer ou brancher réellement.

#### `Q-11` 🟡 `types.ts` : alias mort `ChessComGame` + index signature laxiste sur `GameInfo` — *XS · faible · faible*
- **Fichiers** : `web/frontend/src/lib/types.ts:145-146,54-67`
- **Problème** : alias jamais utilisé ; `[key: string]: string | undefined` (l.66) annule le typage. **Reco** : supprimer l'alias, retirer l'index signature.

#### `Q-12` 💡 God-files GUI desktop (legacy) 800-1460 l. — *XL · faible · élevé*
- **Fichiers** : `src/gui/analysis_view.py` (1464 l.), `main_window.py` (1418 l.), `user/user_profile_window.py` (1394 l.), …
- **Problème/Reco** : dette réelle mais **NE PAS investir** : sous-système gelé (cible = web). Consigner, découper seulement si un écran est porté au web.

### 2. Architecture & duplication structurelle

#### `A-01` 🔴 Difficulté entièrement dupliquée et divergente (incompatible par construction) — *L · élevé · moyen*
- **Fichiers** : `src/analysis/game_difficulty.py:39-434`, `web/backend/services/difficulty.py:24-199`, `web/backend/services/analysis.py:40-45,129-148`
- **Problème** : deux algos indépendants (entropie softmax desktop vs sous-signaux pondérés + `volatility_bonus` web). Le web **ne peut pas** appeler la version desktop (son move-eval ne produit ni `top_moves`, ni `tactical_depth`…). Scores différents pour la même partie.
- **Reco** : service partagé `src/analysis/difficulty/`. **Prérequis** : converger le contrat move-eval (`A-02`). Promouvoir la version web (plus simple, alignée cible) comme référence. Décision produit à trancher avant de coder.

#### `A-02` 🔴 Analyse de coup réimplémentée (profondeur + schéma divergents) — *L · élevé · moyen*
- **Fichiers** : `src/analysis/move_analyzer.py:21-395`, `web/backend/services/analysis.py:11-148`, `src/utils/config.py:198`
- **Problème** : `compute_move_insight` réimplémente `MoveAnalyzer.analyze_move` — `depth=16` (vs 20 desktop), pas de `top_moves`/`tactical_depth`/distances de mat, clés de sortie partiellement différentes. Même `MoveClassifier` partagé → la divergence est dans l'orchestration.
- **Reco** : extraire **une** fonction d'analyse de coup dans `src/analysis` (single-engine, sans pool ni tkinter) produisant le schéma move-eval canonique. `compute_move_insight` devient un adaptateur ; profondeur en paramètre lu depuis `analysis_config`.

#### `A-03` 🔴 Deux gestionnaires de profils à schémas incompatibles, même dossier (corruption) — *M · élevé · moyen*
- **Fichiers** : `src/user/profile.py:549-896`, `web/backend/managers/profile_manager.py:10-270`, `web/backend/routers/game.py:225-232`
- **Problème** : `game_analyses` (desktop) vs `games[]` (web) dans le même `user_profiles/<slug>.json`. `save_profile` desktop réécrit tout à clés fixes → efface `games[]` + comptes chesscom/lichess. Slugs divergents (`username.lower()` vs regex).
- **Reco** : web = source de vérité, **pas de fusion bidirectionnelle**. Figer le format web ; rendre le desktop non destructif (merge préservant les clés inconnues) ou l'isoler. Voir `S-01` (action immédiate).

#### `A-04` 🟠 Orchestration de partie réécrite dans le router web — *M · moyen · moyen*
- **Fichiers** : `src/analysis/game_analyzer.py:73-282`, `web/backend/routers/game.py:193-208,292-317`
- **Problème** : `GameAnalyzer.analyze_game` non réutilisé ; la boucle d'analyse est réécrite (et **dupliquée** entre `import` et `import/stream`). Logique métier dans la couche transport. Le fallback d'ouverture par séquence SAN manque côté web.
- **Reco** : façade d'orchestration sans dépendance UI/HTTP (`src/analysis/game_pipeline`) appelée par les deux. Quick win préalable : factoriser les 2 boucles web identiques.

#### `A-05` 🔴 `config.py` importe tkinter → constantes d'analyse couplées à l'UI — *S · élevé · faible* ⭐
- **Fichiers** : `src/utils/config.py:6,196-243`, `web/backend/services/analysis.py:40-45`, `web/backend/services/difficulty.py:4-5`
- **Problème** : le backend ne peut pas importer `config` sans tirer tkinter → il **recopie les valeurs en dur**. Cause racine systémique des magic numbers et des divergences. Bloque `A-01/A-02/A-04`.
- **Reco** : scinder en `src/utils/analysis_config.py` (zéro import UI) + `src/gui/theme.py`. `config.py` réexporte le temps de la transition. **Clé de voûte, meilleur ratio gain/effort.**

#### `A-06` 🟠 Monkey-patching de `GameAnalyzer` pour la difficulté — *S · moyen · faible*
- **Fichiers** : `src/analysis/game_difficulty.py:518-582`, `src/gui/main_window.py:56`, `src/analysis/__init__.py:9`
- **Problème** : remplace dynamiquement `analyze_game` (injecte `ply` rétroactivement, avale les erreurs en `print`). Couplage caché, ordre-dépendant, non transposable au web.
- **Reco** : supprimer le patch lors de l'extraction de la façade (`A-04`) ; difficulté = étape explicite du pipeline ; `ply` injecté à la source.

#### `A-07` 🟡 Deux `EngineManager` de sémantiques opposées (pool vs singleton) — *S · faible · faible*
- **Fichiers** : `src/engine/engine_manager.py:90-213,43`, `web/backend/managers/engine_manager.py:5-27`
- **Problème** : même nom, contrats différents → confusion. Le singleton web sérialise toutes les requêtes (lock).
- **Reco** : renommer le manager web (`EngineProvider`), documenter la limite. Pool web seulement si latence mesurée (cf `P-01`).

#### `A-08` 🟡 Pas de frontière « package cœur » : imports profonds via `sys.path` — *M · moyen · faible*
- **Fichiers** : `web/backend/config.py:7-8`, `web/backend/services/analysis.py:4-6`, `web/backend/routers/game.py:20-21`
- **Problème** : pas d'API publique de `src/` ; tout déplacement interne casse le web silencieusement (sans tests).
- **Reco** : exposer une façade minimale via un `__init__` de package. Aboutissement naturel de `A-01..A-05`.

### 3. Performance

#### `P-01` 🔴 Analyse PGN strictement séquentielle sur une instance verrouillée — *M · élevé · moyen*
- **Fichiers** : `web/backend/services/analysis.py:40,45`, `web/backend/managers/engine_manager.py:6,13`, `src/engine/engine_manager.py:43,90-131`, `web/backend/routers/game.py:292-317`
- **Problème** : un seul `EngineInstance` (lock) → toute l'analyse en série, **et** deux requêtes concurrentes se bloquent. Le pool parallèle desktop (cappé à 4) n'est pas utilisé.
- **Reco** : instancier le pool `EngineManager` de `src/engine` au démarrage ; router l'import via `ThreadPoolExecutor` (1 moteur/tâche) ; SSE depuis `as_completed`.

#### `P-02` 🔴 Double analyse redondante par coup (~50 % du temps moteur jeté) — *S · élevé · faible* ⭐
- **Fichiers** : `web/backend/services/analysis.py:40,45`, `web/backend/routers/game.py:292-307`
- **Problème** : la position « après coup N » est re-analysée comme « avant coup N+1 ». Sur 80 demi-coups, ~79 positions analysées 2×. Aucune mémoïsation.
- **Reco** : mémoïser l'éval par FEN dans la boucle d'import (réutiliser le score `after` du coup N comme `prev_score` du N+1, comme `game_analyzer.py:198`). Ne dédupliquer que la composante score.

#### `P-03` 🟠 `OpeningDetector` : scan O(n) de toute la base ECO par coup hors-théorie — *S · moyen · faible*
- **Fichiers** : `src/analysis/opening_detector.py:168-173,235-245`, `src/core/chess_game.py:204-212`
- **Problème** : `detect_opening` appelé après chaque coup ; le fallback itère tout le dict ECO (milliers d'entrées) en Python pur. Négligeable devant Stockfish aujourd'hui, goulot dès que `P-01/P-02` accélèrent le moteur.
- **Reco** : pré-indexer par FEN normalisée (lookup O(1)) ; n'appeler la détection que tant qu'on est plausiblement en théorie (≤ ~20 demi-coups).

#### `P-04` 🟠 Base ECO (~3,8 Mo) parsée et dupliquée en RAM à chaque instanciation — *S · moyen · faible*
- **Fichiers** : `src/analysis/opening_detector.py:14-22,34-35,65-90`, `src/core/chess_game.py:17`, `web/backend/managers/game_manager.py:11-16`
- **Problème** : chaque `ChessGame` recharge la base (flag `eco_loaded` par-instance) → N sessions = N copies en RAM + coût parse répété.
- **Reco** : charger la base une fois en cache de module/processus, partager les dicts en lecture seule. Données immuables, risque faible.

#### `P-05` 🟠 ~12 Mo d'icônes PNG inutilisées dans `public/icons/` — *XS · moyen · faible*
- **Fichiers** : `web/frontend/public/icons/`, `web/frontend/src/components/ClassificationIcon.tsx:13-178`
- **Problème** : 9 PNG ~1,3-1,7 Mo jamais référencés (le front est 100 % SVG inline). Gonflent chaque build/déploiement.
- **Reco** : supprimer `public/icons/` + variantes Caissa non référencées (`CaissaNoirev1.png`, `Caissav1.png`, `caissa.webp`).

#### `P-06` 🟠 2 round-trips séquentiels par coup, le 2nd re-télécharge toute l'analyse — *S · moyen · faible*
- **Fichiers** : `web/frontend/src/hooks/useChessGame.ts:310-311,118-134`, `web/backend/routers/game.py:367-408`
- **Problème** : `fetchAnalysis` puis `fetchInsights` en série ; `/insights` recalcule tout et renvoie la liste complète à chaque coup ; `/game/move` ne renvoie pas l'insight déjà calculé.
- **Reco** : `Promise.all` (indépendants) ; faire renvoyer l'insight par `/game/move` pour éviter le re-fetch O(coups).

#### `P-07` 🟡 `useEffect` de timeline rejoue toute la partie à chaque navigation — *S · faible · faible*
- **Fichiers** : `web/frontend/src/hooks/useChessGame.ts:539-569,615-619`
- **Problème** : dépendances trop larges (`reviewPly` inclus) → rejoue tous les coups juste pour naviguer d'un ply.
- **Reco** : séparer reconstruction de timeline (`[initialFen, moveInsights]`) et sélection du ply (`[reviewPly]`). Priorité basse.

### 4. Dépendances & stack

#### `D-01` 🔴 `requests` manquant dans `web/backend/requirements.txt` — *XS · élevé · faible* ⭐
- **Fichiers** : `web/backend/requirements.txt:1-5`, `web/backend/services/lichess.py:1`, `chesscom.py:1`
- **Problème** : import en ligne (chess.com/lichess) plante sur install propre. Ne marche aujourd'hui que parce que `requests` est présent par ailleurs.
- **Reco** : ajouter `requests==2.31.0`.

#### `D-02` 🔴 `numpy` manquant (utilisé par le cœur partagé) — *XS · élevé · faible*
- **Fichiers** : `web/backend/requirements.txt:1-5`, `src/analysis/game_difficulty.py:10,228`
- **Problème** : `np.median`/`np.sign` utilisés ; numpy n'arrive aujourd'hui que via matplotlib (desktop). Backend-only → la difficulté plante.
- **Reco** : déclarer `numpy` explicitement (backend + racine).

#### `D-03` 🟠 Deps backend mortes : `websockets` + `python-multipart` — *XS · moyen · faible*
- **Fichiers** : `web/backend/requirements.txt:4-5`, `web/backend/routers/game.py:358-360`
- **Problème** : aucun WebSocket (SSE) ni endpoint `File/Form`. Surface CVE inutile.
- **Reco** : retirer les 2 lignes (garder `multipart` avec commentaire si upload PGN planifié).

#### `D-04` 🟠 `web/package.json` orphelin + `node_modules` dupliqué — *XS · moyen · faible*
- (fusionné avec `Q-05`) **Reco** : supprimer `web/package.json` + lock + `node_modules`.

#### `D-05` 🟡 Config Tailwind v3 résiduelle — *S · faible · moyen*
- (fusionné avec `Q-04`) **Reco** : un seul canal (`@tailwindcss/vite`), faire quand on touche au build.

#### `D-06` 🟡 `@app.on_event('startup')` déprécié — *S · faible · faible*
- **Fichiers** : `web/backend/main.py:34-37`
- **Reco** : migrer vers `lifespan` (asynccontextmanager). À faire quand on touche au démarrage backend.

#### `D-07` 🟡 Versions épinglées anciennes (`fastapi 0.109.2`, `matplotlib 3.7.1`) — *M · faible · moyen*
- **Fichiers** : `web/backend/requirements.txt:1`, `requirements.txt:3`, `src/gui/analysis/summary_tab.py:5`
- **Reco** : **pas** de bump cosmétique ; bumper fastapi dans la foulée de `D-06`. matplotlib reste dep desktop (ne pas l'inclure côté backend).

#### `D-08` 🟠 Chemin Stockfish hardcodé et dupliqué — *S · moyen · faible*
- (fusionné avec `M-01`/`S-06`) **Reco** : `os.getenv('STOCKFISH_PATH', <défaut>)`, source unique partagée desktop+web.

### 5. Maintenabilité & DX

#### `M-01` 🔴 Chemin Stockfish hardcodé à 2 endroits, non portable — *S · élevé · faible* ⭐
- **Fichiers** : `web/backend/config.py:11`, `main.py:61`, `web/backend/managers/engine_manager.py:13-16`
- **Reco** : `STOCKFISH_PATH` (env) avec fallback ; documenter ; aligner `main.py` (qui accepte déjà `argv[1]`).

#### `M-02` 🔴 `API_URL` frontend hardcodé, sans env ni proxy — *S · élevé · faible* ⭐
- **Fichiers** : `web/frontend/src/lib/types.ts:1`, `vite.config.ts:6-11`, `hooks/useChessGame.ts:6`
- **Reco** : `import.meta.env.VITE_API_URL ?? 'http://localhost:8000'` + `.env.example` ; sortir `API_URL` dans `lib/config.ts`.

#### `M-03` 🔴 Aucun test ni CI sur tout le projet — *M · élevé · faible* ⭐
- **Fichiers** : `src/analysis/*`, `.github/` (absent)
- **Problème** : tout changement du cœur peut casser desktop ET web sans alerte. Prérequis aux gros refactors.
- **Reco** : **minimaliste** — pytest + 5-10 tests de caractérisation sur fonctions pures (classification, ACPL/accuracy, difficulté) figées sur 2-3 PGN, + un smoke test FastAPI `TestClient`. Pas de couverture exhaustive.

#### `M-04` 🔴 `requests`/`pydantic` absents du requirements backend — *XS · élevé · faible*
- (recouvre `D-01`) **Reco** : compléter et auditer tous les imports tiers.

#### `M-05` 🟠 Erreurs par `print()` silencieux, aucun logging — *S · moyen · faible*
- **Fichiers** : 15 `print()` backend (`game.py`, `lichess.py`, `chesscom.py`, `engine_manager.py`), `except` nu `analysis.py:121`
- **Reco** : `logging.getLogger(__name__)` + `basicConfig` dans `main.py` ; remplacer 1-pour-1 par `logger.warning/exception`.

#### `M-06` 🟠 README racine périmé (desktop) + README frontend = template Vite — *S · moyen · faible*
- **Fichiers** : `README.md`, `web/frontend/README.md`
- **Reco** : section « Application Web (cible actuelle) » renvoyant à `launch.json` ; README frontend spécifique (Node, `npm run dev`, `VITE_API_URL`).

#### `M-07` 🟠 Schéma de profil non modélisé (dicts bruts) — *M · moyen · moyen*
- **Fichiers** : `web/backend/managers/profile_manager.py:103-167,194-268`, `web/frontend/src/lib/types.ts:108-167`
- **Reco** : modèles Pydantic (`GameRecord`, `StoredProfile`) comme source de vérité, miroir du TS, validation via `model_dump`. Prérequis utile à `A-03`.

#### `M-08` 🟠 Pas de script unifié pour lancer backend + frontend — *S · moyen · faible*
- **Fichiers** : `.claude/launch.json`, `web/frontend/package.json:6-11`
- **Reco** : un `dev.ps1`/`dev.bat` (ou script npm via `concurrently`) reflétant `launch.json` (bon interpréteur venv).

#### `M-09` 🟠 Hygiène repo : `.bak` tracké + `AuditPanRetention/` + `web/package.json` — *XS · moyen · faible*
- (recouvre `Q-03`, `Q-05`, `S-02`) **Reco** : voir Phase 0.

#### `M-10` 🟠 ~~Branche `master` divergée (ahead 2 / behind 7)~~ ✅ **RÉSOLU cette session**
- Branche rebasée + poussée, synchronisée avec `origin/master`. `CLAUDE.md` (section Git) mis à jour. Restent des changements WIP non liés à trancher par l'auteur.

#### `M-11` 💡 61 `.pyc` sur disque (non committés) — *XS · faible · faible*
- Correctement gitignorés (l'hypothèse « `.pyc` committés » est **fausse**). Nettoyage local optionnel, **non prioritaire**.

### 6. Sécurité & intégrité des données

#### `S-01` 🔴 Le `save` desktop écrase silencieusement les données web du profil partagé — *S · élevé · faible* ⭐
- **Fichiers** : `src/user/profile.py:681-732`, `web/backend/managers/profile_manager.py:30-33`, `user_profiles/nutty_bishops.json`
- **Problème** : risque d'intégrité **le plus grave** du dépôt. Confirmé : `nutty_bishops.json` contient les 2 schémas (`game_analyses`=29 + `games`=56 + comptes externes). Toute sauvegarde desktop détruit les 56 parties web + liens, sans alerte.
- **Reco** : **isoler les fichiers** (ROI max / risque min) — `PROFILE_DIR` web → `user_profiles/web/<slug>.json` (`config.py:14`). A minima : rendre `save_profile` desktop non destructif (merge préservant les clés inconnues).

#### `S-02` 🔴 Échantillons de cartes bancaires (projet sans rapport) dans l'historique git — *S · moyen · moyen*
- **Fichiers** : `AuditPanRetention/audit_sample/panbuster_in/pan*.csv`, …
- **Problème** : projet PANBuster étranger committé. **Données synthétiques** après inspection (pas de PAN réels/Luhn valides) → risque de fuite **faible**, mais forte pollution. ⚠️ Le remote y développe **activement** (6 commits) → ne pas committer la suppression à l'aveugle.
- **Reco** : retirer du suivi (après décision) ; purge d'historique (`git filter-repo`) **seulement** si le dépôt devient public. Idéalement : déplacer PANBuster dans son propre repo.

#### `S-03` 🟠 Aucune authentification sur l'API — *M · moyen · faible*
- **Fichiers** : `web/backend/routers/profiles.py:25-36`, `web/backend/main.py:21-27,45`
- **Problème** : `DELETE /profiles/{username}` sans contrôle ; bind `0.0.0.0`. Acceptable en localhost mono-utilisateur, critique si exposé.
- **Reco** : documenter « localhost only » ; binder `127.0.0.1` (`main.py` + `launch.json`). Audit auth dédié si multi-utilisateurs.

#### `S-04` 🟠 CORS `allow_origins=['*']` + `allow_credentials=True` — *XS · moyen · faible*
- **Fichiers** : `web/backend/main.py:21-27`
- **Problème** : combo contradictoire/dangereux (surface CSRF vers localhost). Coût de correction nul.
- **Reco** : `allow_origins=['http://localhost:5173']`, `allow_credentials=False` (pas de cookies).

#### `S-05` 🟠 Profils utilisateurs (PII) committés — *S · moyen · faible*
- **Fichiers** : `user_profiles/*.json`, `user_profiles/avatars/`, `.gitignore`
- **Problème** : pseudos chess.com/lichess réels, historiques, avatars photo, figés dans git (aucun pattern `user_profiles/`).
- **Reco** : ajouter `user_profiles/*.json` + `avatars/` au `.gitignore`, `git rm --cached`. Garder un exemple anonymisé. À décider **avant** de figer le dépôt.

#### `S-06` 🟠 Chemin absolu Stockfish (couplage machine + exposition d'arborescence) — *S · moyen · faible*
- (fusionné avec `M-01`/`D-08`) **Reco** : variable d'env unique partagée.

#### `S-07` 🟡 Détection de session expirée par `.includes('404')` (fragile) — *S · faible · faible*
- **Fichiers** : `web/frontend/src/hooks/useChessGame.ts:410-413,474-484`
- **Problème** : le retry dépend du formatage du message d'erreur (peut ne pas se déclencher au redémarrage backend). **Reco** : tester `response.status === 404`. À faire lors du découpage du hook.

---

## Suggestions stratégiques

1. **Web = source de vérité unique ; desktop = legacy gelé.** Jamais de fusion bidirectionnelle. Toute déduplication promeut la version web vers `src/` et fait du desktop un consommateur (ou l'isole).
2. **Découpler `config.py` de tkinter (`A-05`) est la clé de voûte** : effort S, risque très faible, déverrouille `A-01/A-02/A-04` et supprime tous les magic numbers hardcodés du backend.
3. **Une seule source de vérité par concept** : palette (`Q-08`), constantes moteur (`Q-09`), schéma profil Pydantic miroir du TS (`M-07`), façade publique du cœur (`A-08`).
4. **Externaliser la config machine** via env + fallback : `STOCKFISH_PATH`, `VITE_API_URL` (+ `.env.example`, doc README).
5. **Filet de tests minimal AVANT les gros refactors** (`M-03`) : caractérisation des fonctions pures à risque + smoke FastAPI. Pas de couverture exhaustive.
6. **Trancher les états hybrides** : supprimer « Coup brillant » (`Q-01`), un seul canal Tailwind (`Q-04`), supprimer `web/package.json` (`Q-05`).
7. **Réutiliser l'existant** : pool d'`EngineInstance` desktop (`P-01`), `GameAnalyzer` (`A-04`), propagation `prev_score` (`P-02`).

## Plan d'implémentation

> Ordre choisi pour **minimiser le risque** : stabiliser le dépôt → quick wins fiabilité → nettoyage → découplage + tests (prérequis) → perf → déduplication du cœur → dette différée. Dépendances critiques : **`A-05` avant `A-01/A-02/A-04`** ; **`M-03` (tests) avant tout refactor de cœur**.

### Phase 0 — Sauvegarde, hygiène & stabilisation git
*But : dépôt sain et reproductible avant tout changement de code.*
- `M-10` ✅ *(fait cette session : branche rebasée + poussée, `CLAUDE.md` à jour)*.
- `Q-03`/`M-09`/`S-02` : committer la suppression d'`AuditPanRetention/` **(après décision — le remote y développe)**, `git rm main_window.py.bak`, `*.bak` au `.gitignore`.
- `Q-05`/`D-04` : supprimer `web/package.json` + lock + `node_modules`.
- `S-05` : `.gitignore` sur `user_profiles/*.json` + `avatars/`, `git rm --cached`, garder un exemple anonymisé.
- **Done quand** : working tree propre, aucun artefact/PII tracké.

### Phase 1 — Quick wins fiabilité & portabilité 🔴 (fort ROI, risque faible)
*But : backend installable, projet lançable partout, corruption de profils neutralisée.*
- `D-01`/`D-02`/`M-04` : compléter `requirements.txt` (`requests`, `numpy`, `pydantic`).
- `D-03` : retirer `websockets`/`python-multipart`.
- `S-01` : isoler `PROFILE_DIR` web → `user_profiles/web/` (ou `save` desktop non destructif).
- `M-01`/`D-08`/`S-06` : `STOCKFISH_PATH` (env, source unique).
- `M-02` : `VITE_API_URL` + `.env.example`.
- `S-04` : CORS explicite + `allow_credentials=False`.
- `P-05` : supprimer `public/icons/` (~12 Mo) + variantes Caissa mortes.
- `M-06`/`M-08` : README web + script `dev` unifié.
- **Done quand** : `pip install -r web/backend/requirements.txt` sur venv neuf → backend fonctionnel ; projet lançable ailleurs via env ; un save desktop ne détruit plus les données web.

### Phase 2 — Nettoyage code mort & sources de vérité uniques 🟠 (risque faible)
- `Q-01` : supprimer « Coup brillant » de bout en bout (+ `is_move_sacrifice`).
- `Q-02`/`Q-10` : nettoyer `classify_move`.
- `Q-04`/`D-05` : un seul canal Tailwind v4.
- `Q-08` : unifier la palette (+ coquille `#A78BFA `).
- `Q-11` : supprimer alias `ChessComGame` + index signature.
- `Q-07` : corriger le hook conditionnel `GameReport.tsx`.
- `M-05` : logging centralisé (remplacer les `print`).
- **Done quand** : plus de référence à « Coup brillant »/`is_move_sacrifice` web ; une palette par plateforme ; build frontend vert ; erreurs backend tracées.

### Phase 3 — Découplage config & filet de tests ⭐ (prérequis aux gros refactors)
- `A-05`/`Q-09` : scinder `config.py` → `analysis_config.py` + `theme.py` ; remplacer les valeurs hardcodées web ; uniformiser `mate_score`.
- `M-03` : pytest + tests de caractérisation + smoke FastAPI.
- `M-07` : modèles Pydantic du schéma de profil.
- **Done quand** : backend importe `analysis_config` **sans** tkinter ; `mate_score` uniforme ; tests verts servant de référence.

### Phase 4 — Performance import PGN 🔴 (fort ROI, réutilise l'existant)
- `P-02` : mémoïsation FEN (`prev_score`). *(dépend de `A-05`)*
- `P-01` : pool `EngineManager` + `ThreadPoolExecutor`. *(dépend de `A-05`, `P-02`)*
- `P-04` : base ECO en cache de processus partagé.
- `P-03` : index ECO O(1) + détection bornée. *(dépend de `P-04`)*
- `P-06`/`P-07` : `Promise.all` + timeline découplée (frontend, priorité basse).
- **Done quand** : import 40 coups notablement plus rapide, sans bloquer les autres requêtes ; ECO chargée 1×.

### Phase 5 — Déduplication du cœur métier (chantiers de fond, sous tests)
- `A-02` : fonction d'analyse de coup canonique unique. *(dépend de `A-05`, `M-03`)*
- `A-04`/`A-06` : façade d'orchestration `game_pipeline`, supprimer le monkey-patch. *(dépend de `A-02`)*
- `A-01` : service de difficulté unique (référence = web). *(dépend de `A-02`, `M-03`)*
- `A-03` : schéma de persistance profil unifié. *(dépend de `S-01`, `M-07`)*
- `A-08` : façade publique du package cœur. *(dépend de `A-01/A-02/A-04`)*
- `A-07` : renommer le manager moteur web. *(dépend de `P-01`)*
- **Done quand** : une seule implémentation par concept (analyse de coup, orchestration, difficulté) ; scores comparables desktop/web ; plus de monkey-patch ; imports web via façade.

### Phase 6 — Dette différée & décisions reportées
- `D-06`/`D-07` : `lifespan` + bump fastapi.
- `S-07` : détection 404 par status. *(au découpage du hook)*
- `Q-06` : découper `useChessGame.ts`. *(dépend de `M-03`)*
- `S-03` : doc « localhost only » + bind `127.0.0.1`.
- `Q-12`/`M-11` : dette consignée, **non investie** (god-files legacy, `.pyc`).

## Les 3 actions à plus haut ROI

1. **Phase 1 fiabilité+portabilité** (XS-S, gain élevé) : compléter `requirements.txt` (`D-01/D-02/M-04`), isoler les profils (`S-01`), externaliser `STOCKFISH_PATH`+`VITE_API_URL` (`M-01/M-02/D-08`). Transforme un backend non installable et un projet non clonable en projet reproductible, et désamorce la corruption de données — pour un coût quasi nul.
2. **Scinder `config.py` de tkinter** (`A-05`, S, risque très faible) : supprime les magic numbers hardcodés (`depth`, `mate_score` incohérent) **et** déverrouille toute la déduplication du cœur. Effet de levier maximal.
3. **Optimiser l'import PGN** : mémoïsation FEN puis parallélisation (`P-02` puis `P-01`, S puis M) : ~50 % du temps moteur aujourd'hui gaspillé, alors que le code parallèle et le pattern `prev_score` **existent déjà** côté desktop.

## Ce qui est déjà bien (à ne pas casser)

- **Cœur d'analyse partagé** (`ChessGame`, `MoveClassifier`, `PlayerStats`, `OpeningDetector`, `EngineInstance`) réimporté par le web sans duplication — bonne frontière de fond.
- **`PlayerStats`** : contrat de sortie stable consommé par les 2 frontends — modèle à répliquer pour difficulté/analyse.
- **Pool `EngineInstance` + `ThreadPoolExecutor`** desktop : archi efficace pour Stockfish — à réutiliser côté web.
- **Frontend** : icônes 100 % SVG inline (`currentColor`), UI optimiste avec rollback, import PGN en **SSE** streamé, validation des coups PGN contre `legal_moves`. Excellents patterns.
- **Stack web moderne et cohérente** (React 19 / Vite 7 / TS 5.9 / Tailwind v4) ; `profile_manager.py` et `compute_move_insight` déjà typés.
- **`CLAUDE.md`** riche, honnête et à jour (documente la dette) — meilleur atout DX. `.gitignore` globalement correct.
- **Sécurité web** : slug normalisé par regex (anti path-traversal), `update_profile` protège les champs structurants. C'est le `save` desktop qui casse la garantie, pas le web.
