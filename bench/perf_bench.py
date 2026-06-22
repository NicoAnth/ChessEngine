"""
Palier 0 — filet de mesure perf pour l'analyse d'une partie (ChessEngine).

Reproduit FIDELEMENT la boucle d'import de production
(web/backend/routers/game.py::import_pgn_game) en appelant le vrai
`compute_move_insight`, et produit :

  1) un CHRONO du chemin d'analyse natif (temps mur + ms/analyse) ;
  2) un SNAPSHOT JSON des champs d'invariant par coup
     (classification, score_before/after, best_move_uci, player_move_rank, ...) ;
  3) une verif de REPRODUCTIBILITE bit-a-bit sur N runs ;
  4) une comparaison au SNAPSHOT DE REFERENCE (baseline) : detecte toute
     regression fonctionnelle introduite par une optimisation.

INVARIANT — toute optimisation qui NE touche PAS depth/multipv (pool d'engines,
Hash, build BMI2, lock par-instance, cache FEN) doit laisser le snapshot
STRICTEMENT identique a la baseline. Un seul ecart = regression a corriger.
Quand on change volontairement depth/multipv (Palier 3), le diff est ATTENDU :
re-baseliner avec --update-baseline et documenter le % de coups reclasses.

Le bench appelle le code reel : il refletera donc automatiquement tout changement
de depth/multipv/pool fait dans web/backend/services/analysis.py et le moteur.

Usage (depuis la racine, avec le python du venv) :
  venv\\Scripts\\python.exe -m bench.perf_bench
  venv\\Scripts\\python.exe -m bench.perf_bench --pgn bench/opera_game.pgn --runs 3
  venv\\Scripts\\python.exe -m bench.perf_bench --update-baseline   # (re)pose la reference
"""
import argparse
import io
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import chess
import chess.pgn

from src.core.chess_game import ChessGame
from src.utils import config
from web.backend.config import DEFAULT_ENGINE_PATH
from web.backend.managers.engine_manager import EngineManager
from web.backend.services.analysis import (
    compute_move_insight,
    replay_and_snapshot,
    snapshot_fens,
    analyze_fens_parallel,
    build_evaluations,
)

# Sous-ensemble DETERMINISTE de l'insight retenu comme invariant. Tous ces champs
# sont stables a depth/multipv/Threads=1/binaire fixes (scores arrondis, rang
# discret, classification). On les compare a l'identique entre runs et vs baseline.
SNAPSHOT_FIELDS = [
    "move_num", "side", "san", "uci",
    "classification", "move_quality",
    "score_before", "score_after", "score_change",
    "best_move_uci", "player_move_rank",
    "position_complexity", "top_moves_eval_drop", "is_critical",
]

DEFAULT_PGN = PROJECT_ROOT / "bench" / "opera_game.pgn"
DEFAULT_BASELINE = PROJECT_ROOT / "bench" / "snapshots" / "baseline.json"


def run_import(pgn_text):
    """Rejoue exactement la boucle de import_pgn_game.

    Renvoie (snapshot:list[dict], n_engine_calls:int, wall_s:float).
    n_engine_calls == len(score_cache) : chaque FEN unique declenche 1 seul
    analyze_position (memoisation P-02), donc la taille finale du cache est le
    nombre exact d'analyses Stockfish reellement executees.
    """
    parsed = chess.pgn.read_game(io.StringIO(pgn_text))
    if parsed is None:
        raise SystemExit("PGN illisible / vide")

    game = ChessGame()
    game.reset()
    game.board = parsed.board().copy(stack=False)
    game.last_move = None
    game.opening_detector.reset()
    game.current_opening = None

    score_cache = {}
    snapshot = []

    t0 = time.perf_counter()
    for move in parsed.mainline_moves():
        if move not in game.board.legal_moves:
            raise SystemExit(f"Coup illegal dans le PGN : {move.uci()}")
        board_before = game.board.copy()
        side = "White" if game.board.turn == chess.WHITE else "Black"
        game.make_move(move)
        insight = compute_move_insight(game, move, board_before, side, score_cache)
        snapshot.append({k: insight.get(k) for k in SNAPSHOT_FIELDS})
    wall = time.perf_counter() - t0

    return snapshot, len(score_cache), wall


def run_import_parallel(pgn_text):
    """Import via le chemin PARALLELE de production (pool d'engines).

    Phase 1 rejeu sequentiel -> phase 2 analyse concurrente sur le pool -> phase 3
    reconstruction. Renvoie (snapshot, n_unique_positions, wall_s). L'analyse etant
    TT-independante (ucinewgame par coup), le snapshot DOIT etre identique a celui du
    chemin sequentiel (meme baseline) : c'est la preuve que le pool ne change rien.
    """
    parsed = chess.pgn.read_game(io.StringIO(pgn_text))
    if parsed is None:
        raise SystemExit("PGN illisible / vide")

    pool = EngineManager.get_pool()
    if pool is None:
        raise SystemExit("pool moteur indisponible")

    t0 = time.perf_counter()
    game, snapshots = replay_and_snapshot(parsed)
    fens = snapshot_fens(snapshots)
    analyses = analyze_fens_parallel(pool, fens)
    evaluations = build_evaluations(snapshots, analyses)
    wall = time.perf_counter() - t0

    snapshot = [{k: ev.get(k) for k in SNAPSHOT_FIELDS} for ev in evaluations]
    n_unique = len(dict.fromkeys(fens))
    return snapshot, n_unique, wall


def reset_engine_cold():
    """Force un moteur a table de transposition FROIDE (process Stockfish neuf).

    A Threads=1 et 'go depth N', le resultat depend de l'etat de la TT : si le
    process est reutilise, la TT accumulee aux analyses precedentes fait osciller
    l'eval depth-16 (~0.02 pion observe) et casse la reproductibilite bit-a-bit.
    On repart donc froid avant chaque run pour que le snapshot soit canonique et
    deterministe (= 1er import apres demarrage backend). NB : en prod le singleton
    reste chaud entre imports -> determinisme a assurer cote moteur (ucinewgame par
    analyse) avant de brancher le pool, sinon le pool divergera de cette baseline.
    """
    inst = EngineManager._instance
    if inst is not None:
        try:
            inst.quit()
        except Exception:
            pass
        EngineManager._instance = None


def first_diff(a, b):
    """Renvoie une description du 1er ecart entre deux snapshots, ou None si identiques."""
    if len(a) != len(b):
        return f"longueurs differentes : {len(a)} vs {len(b)}"
    for i, (ma, mb) in enumerate(zip(a, b)):
        for field in SNAPSHOT_FIELDS:
            if ma.get(field) != mb.get(field):
                label = f"coup #{i + 1} ({ma.get('side')} {ma.get('san')})"
                return f"{label} champ '{field}' : {mb.get(field)!r} (ref) -> {ma.get(field)!r} (actuel)"
    return None


def main():
    ap = argparse.ArgumentParser(description="Bench perf + snapshot d'invariant (Palier 0).")
    ap.add_argument("--pgn", type=Path, default=DEFAULT_PGN, help="PGN de reference a analyser")
    ap.add_argument("--runs", type=int, default=3, help="nombre de runs (repro bit-a-bit)")
    ap.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE, help="fichier snapshot de reference")
    ap.add_argument("--update-baseline", action="store_true",
                    help="(re)ecrit la baseline avec le snapshot courant (apres un changement depth/multipv assume)")
    ap.add_argument("--mode", choices=["seq", "parallel"], default="seq",
                    help="seq = 1 instance (baseline) ; parallel = pool d'engines (preuve d'invariance + speedup)")
    args = ap.parse_args()

    pgn_text = args.pgn.read_text(encoding="utf-8").strip()
    if not pgn_text:
        raise SystemExit(f"PGN vide : {args.pgn}")

    # Le moteur doit etre dispo, sinon compute_move_insight renvoie un insight
    # degrade ("Inconnu") et le bench ne mesure rien d'utile.
    if not EngineManager.is_available():
        print("ERREUR : Stockfish indisponible.", file=sys.stderr)
        print(f"  Chemin essaye : {DEFAULT_ENGINE_PATH}", file=sys.stderr)
        print(f"  Detail        : {EngineManager.get_error()}", file=sys.stderr)
        print("  -> definir STOCKFISH_PATH ou corriger web/backend/config.py", file=sys.stderr)
        raise SystemExit(2)

    # Quit Stockfish explicitly at the end (try/finally). python-chess runs its
    # engine I/O thread as NON-daemon, so without an explicit quit the interpreter
    # hangs on exit trying to join it — and atexit runs AFTER that join, too late.
    # (The server does this cleanup via the FastAPI lifespan.)
    try:
        exit_code = _run_bench(args, pgn_text)
    finally:
        EngineManager.shutdown()
    # Hard exit: even after quitting the engines, python-chess keeps a non-daemon
    # I/O thread that can stall interpreter shutdown. os._exit bypasses that join.
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(exit_code)


def _run_bench(args, pgn_text) -> int:
    """Run the bench; return 0 on success, 1 if the invariant is broken."""
    threads = config.ENGINE_ANALYSIS.get("engine_threads_per_instance", 1)
    parallel = args.mode == "parallel"

    if parallel:
        pool = EngineManager.get_pool()  # pre-build once so spawn isn't timed
        topo = f"pool de {pool.size} instances (W={pool.size})"
    else:
        topo = "1 instance (singleton)"

    print(f"== Bench perf — {args.pgn.name} | mode={args.mode} ==")
    print(f"Moteur   : {Path(DEFAULT_ENGINE_PATH).name} | Threads/instance={threads} | {topo}")
    print(f"Analyse  : depth=16, multipv=3 ; determinisme via ucinewgame/analyse")
    print(f"Runs     : {args.runs}\n")

    runs = []  # (snapshot, n_calls, wall)
    for r in range(args.runs):
        if parallel:
            # ucinewgame rend chaque analyse TT-independante -> pas besoin de reset.
            snapshot, n_calls, wall = run_import_parallel(pgn_text)
        else:
            reset_engine_cold()  # TT froide -> chaque run sequentiel est comparable
            snapshot, n_calls, wall = run_import(pgn_text)
        per = (wall * 1000.0 / n_calls) if n_calls else 0.0
        runs.append((snapshot, n_calls, wall))
        print(f"  run {r + 1}/{args.runs} : {wall:6.2f}s | {n_calls} analyses | {per:6.1f} ms/analyse")

    plies = len(runs[0][0])
    n_calls = runs[0][1]
    walls = [w for _, _, w in runs]
    best = min(walls)
    median = sorted(walls)[len(walls) // 2]
    per_best = best * 1000.0 / n_calls if n_calls else 0.0

    print()
    print(f"Coups (demi)        : {plies}")
    print(f"Positions uniques   : {n_calls}  (analyses Stockfish reelles, P-02)")
    print(f"Temps mur median    : {median:.2f}s   (meilleur {best:.2f}s)")
    print(f"ms/analyse (best)   : {per_best:.1f} ms")
    print(f"Extrapolation 80 demi-coups : ~{best / plies * 80:.1f}s")

    # 1) Reproductibilite inter-runs (process moteur partage entre runs = test fort)
    print()
    repro = True
    for r in range(1, len(runs)):
        d = first_diff(runs[r][0], runs[0][0])
        if d is not None:
            repro = False
            print(f"REPRO : run {r + 1} != run 1 — {d}")
    if repro:
        print(f"REPRO : OK — les {args.runs} runs sont bit-a-bit identiques (deterministe).")

    # 2) Comparaison a la baseline
    current = runs[0][0]
    print()
    if args.update_baseline or not args.baseline.exists():
        args.baseline.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "_meta": {
                "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "pgn": args.pgn.name,
                "engine": Path(DEFAULT_ENGINE_PATH).name,
                "depth": 16,
                "multipv": 3,
                "threads_per_instance": threads,
                "plies": plies,
                "unique_positions": n_calls,
                "wall_best_s": round(best, 3),
                "ms_per_analysis_best": round(per_best, 1),
            },
            "snapshot": current,
        }
        args.baseline.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        action = "mise a jour" if args.baseline.exists() else "creee"
        print(f"BASELINE : {action} -> {args.baseline.relative_to(PROJECT_ROOT)}")
    else:
        ref = json.loads(args.baseline.read_text(encoding="utf-8"))
        d = first_diff(current, ref.get("snapshot", []))
        if d is None:
            print(f"INVARIANT : OK — snapshot identique a la baseline ({args.baseline.name}). Aucune regression.")
        else:
            print(f"INVARIANT : *** ROMPU *** vs baseline ({args.baseline.name}) :")
            print(f"  {d}")
            print("  -> si le changement de depth/multipv est ASSUME, relancer avec --update-baseline.")
            return 1

    return 0


if __name__ == "__main__":
    main()
