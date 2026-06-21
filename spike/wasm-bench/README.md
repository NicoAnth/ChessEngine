# Spike — Stockfish WASM perf (Étape 2B, gate go/no-go)

But : prouver, **avant** tout port de la logique d'analyse Python→TS, que Stockfish
compilé en WebAssembly est **assez rapide** dans le navigateur pour analyser une
partie complète (la vraie inconnue de l'orientation « app statique sans backend »).

## Méthode

`bench.js` (Node) analyse la **même charge que le backend natif** — 34 positions de
l'Opera Game, `depth 16`, `MultiPV 3` — avec `stockfish@18` (npm). Node + V8 + WASM
single-thread est un **proxy fidèle et conservateur** du navigateur sans COOP/COEP
(le multi-thread navigateur, lui, est plus rapide).

Référence native (binaire Stockfish, via le backend) : **~11.9s, ~362 ms/analyse**.

Rejouer : `npm install && node bench.js` (résumé sur stderr).

## Résultat

| Build WASM (single-thread) | Total | ms/analyse | ~80 demi-coups | vs natif |
|---|---|---|---|---|
| **lite-single** (reco navigateur) | 27.2s | 799 ms | **~64s** | **2.2×** |
| single (NNUE complet) | 50.8s | 1495 ms | ~120s | 4.1× |

## Verdict — perf PASSABLE (gate franchi avec le build *lite*)

- Le build **lite** single-thread = **2.2× le natif** → ~64s pour une partie de 40 coups.
  Le backend natif met déjà ~30s aujourd'hui (attente tolérée avec barre de progression),
  donc ~64s reste **du même ordre de grandeur**, acceptable pour un one-shot par partie.
- Le NNUE **complet** single-thread (4.1×, ~120s) est **trop lent** → ne pas l'utiliser.
- **Multi-thread** (SharedArrayBuffer + en-têtes COOP/COEP sur Vercel/Netlify) exploiterait
  plusieurs cœurs → nettement plus rapide, potentiellement ~natif. **GitHub Pages** (pas de
  contrôle des en-têtes) reste en single-thread (~2.2×, plus lent mais utilisable).
- Leviers si besoin : `depth 14` (≈ moitié du temps, marginal pour de l'amateur), lazy-load.

**Conclusion** : l'orientation client-side WASM est **techniquement VIABLE** (avec le build
lite + idéalement le multi-thread). La perf n'est pas un bloqueur. Le reste du chantier est
le **port ~1100-1400 l. de logique Python→TS** (move_classifier, player_stats, difficulty,
orchestration) — les tests pytest existants (`tests/test_move_classifier`, `test_player_stats`,
`test_difficulty`) servent de **spec d'équivalence** (mêmes entrées → mêmes sorties en TS).
