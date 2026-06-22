# bench/ — filet de mesure perf (Palier 0)

But : **prouver qu'une optimisation accélère l'analyse sans changer les résultats.**
C'est le pré-requis de toute la roadmap perf (cf `OPTIMISATION.md` / audit perf) — on ne
touche au moteur qu'une fois ce filet en place.

## Ce que ça mesure

`perf_bench.py` rejoue **exactement** la boucle d'import de production
(`web/backend/routers/game.py::import_pgn_game`) en appelant le vrai
`compute_move_insight`. Il produit :

1. un **chrono** : temps mur + ms/analyse + nombre de positions uniques (= analyses
   Stockfish réelles, après mémoïsation P-02) ;
2. un **snapshot** des champs déterministes par coup (classification, `score_before`/
   `score_after`, `best_move_uci`, `player_move_rank`, complexité, …) ;
3. la **reproductibilité** bit-à-bit sur N runs (process moteur partagé entre runs →
   test fort du déterminisme `go depth` à Threads=1) ;
4. la comparaison au **snapshot de référence** (`snapshots/baseline.json`).

## L'invariant

> Toute optimisation qui **ne touche pas** depth/multipv (pool d'engines, Hash, build
> BMI2, lock par-instance, cache FEN) doit laisser le snapshot **strictement identique**
> à la baseline. Un seul écart = régression.

Le bench appelle le **code réel** : il reflète donc automatiquement tout changement de
depth/multipv/pool. Quand on change volontairement depth/multipv (Palier 3), le diff est
**attendu** → re-baseliner avec `--update-baseline` et documenter le % de coups reclassés.

## Usage

Depuis la racine, avec le Python du venv :

```powershell
# Pose/rafraîchit la baseline + vérifie la repro (3 runs)
venv\Scripts\python.exe -m bench.perf_bench

# Après une optim à invariant strict (pool, Hash, BMI2…) : doit afficher « INVARIANT : OK »
venv\Scripts\python.exe -m bench.perf_bench

# Après un changement depth/multipv ASSUMÉ : re-pose la référence
venv\Scripts\python.exe -m bench.perf_bench --update-baseline

# Autre partie / autres réglages
venv\Scripts\python.exe -m bench.perf_bench --pgn chemin/partie.pgn --runs 5

# Mode PARALLÈLE : analyse via le pool d'engines (preuve d'invariance + speedup).
# Doit afficher « INVARIANT : OK » (mêmes scores que la baseline séquentielle).
venv\Scripts\python.exe -m bench.perf_bench --mode parallel

# Choisir la taille du pool (défaut 6) :
$env:POOL_SIZE = "8"; venv\Scripts\python.exe -m bench.perf_bench --mode parallel
```

Sortie : code retour **1** si l'invariant est rompu vs baseline (utilisable en CI plus tard).

## Partie de référence

`opera_game.pgn` — le **Jeu de l'Opéra** (Morphy, 1858), 33 demi-coups. Choisi car
court, vérifiable, et **cohérent avec le spike WASM** (`spike/wasm-bench/fens.json` dérive
de cette partie) : le bench natif reconfirme donc au passage la référence ~11,9 s du spike.
Pour une partie ~80 demi-coups, le bench extrapole linéairement (×~2,4).

## Notes

- `snapshots/baseline.json` est **lié au binaire Stockfish + depth/multipv** utilisés
  (SF16/avx2, depth 16, mpv 3 aujourd'hui). Changer de build (ex. BMI2 = autre version) ou
  de depth peut légitimement bouger le snapshot — re-baseliner alors explicitement.
- **Palier 1 (pool) — FAIT.** `--mode parallel` analyse les positions sur un pool de
  `POOL_SIZE` instances (défaut 6). Scaling mesuré sur ce CPU (6 cœurs phys / 12 log.,
  Jeu de l'Opéra) : W=1 ~12,5 s · W=4 ~3,95 s · **W=6 ~3,33 s (≈3,75×)** · W=8 ~3,25 s ·
  W=10 ~3,29 s → plateau dès W=6 (l'HyperThreading n'aide quasi pas un Stockfish
  CPU-bound). L'analyse est **TT-indépendante** (ucinewgame/coup) → le snapshot parallèle
  est bit-à-bit identique à la baseline séquentielle (invariant strict préservé).
- Le bench force `os._exit` à la fin : python-chess garde un thread I/O **non-daemon** qui
  bloquerait la sortie de l'interpréteur même après fermeture des moteurs.
