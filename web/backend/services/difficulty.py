import math
from typing import List, Dict, Any

_EARLY_GAME_END_PLY = 30   # End of move 15
_MID_GAME_END_PLY   = 80   # End of move 40

_GOOD_CLASSIFICATIONS      = {"Meilleur coup", "Excellent", "Bon coup", "Super coup", "Coup brillant"}
_BAD_CLASSIFICATIONS       = {"Erreur", "Grosse erreur"}
_INACCURACY_CLASSIFICATIONS = {"Imprécision"}
_BRILLIANT_CLASSIFICATIONS  = {"Super coup", "Coup brillant"}


def _median(values: list) -> float:
    """Return the median of a non-empty list of floats."""
    if not values:
        return 0.0
    s = sorted(values)
    n = len(s)
    if n % 2 == 1:
        return s[n // 2]
    return (s[n // 2 - 1] + s[n // 2]) / 2


def _decision_difficulty(player_evals: list) -> float:
    """
    Estimate how complex the decisions were for one side (1–10).
    """
    if not player_evals:
        return 5.0

    n = len(player_evals)

    # ── Sub-signal 1: median position complexity (0-1) ──
    complexities = [ev.get("position_complexity", 0.5) for ev in player_evals]
    med_complexity = _median(complexities)

    # ── Sub-signal 2: balanced-position ratio ──
    balanced_count = sum(1 for ev in player_evals if abs(ev.get("score_before", 0)) < 1.0)
    balanced_ratio = balanced_count / n

    # ── Sub-signal 3: dominated-position ease ──
    dominated_count = sum(1 for ev in player_evals if abs(ev.get("score_before", 0)) > 2.0)
    dominated_ratio = dominated_count / n
    non_dominated = 1.0 - dominated_ratio

    # ── Sub-signal 4: move discrimination difficulty ──
    eval_drops = [ev.get("top_moves_eval_drop", 1.0) for ev in player_evals]
    med_drop = _median(eval_drops)
    discrimination = max(0.0, min(1.0, 1.0 - (med_drop / 2.0)))
    effective_discrimination = discrimination * non_dominated

    # ── Sub-signal 5: best-move discovery bonus ──
    best_moves = sum(1 for ev in player_evals if ev.get("player_move_rank", -1) == 0)
    best_move_ratio = best_moves / n
    best_move_bonus = best_move_ratio * med_complexity * 1.0

    # ── Combine (weights sum to ~1.0 before floor) ──
    weighted = (
        med_complexity            * 0.25
        + balanced_ratio          * 0.20
        + non_dominated           * 0.20
        + effective_discrimination * 0.20
        + 0.15
    )

    decision = 1.0 + weighted * 9.0 + best_move_bonus
    return min(10.0, max(1.0, decision))


def _precision_bonus(player_evals: list) -> float:
    """
    Bonus for high-precision play (0–3 points).
    """
    if not player_evals or len(player_evals) < 5:
        return 0.0

    n = len(player_evals)
    qualities = [ev.get("move_quality", 0.5) for ev in player_evals]
    med_quality = _median(qualities)

    good_count      = sum(1 for ev in player_evals if ev.get("classification") in _GOOD_CLASSIFICATIONS)
    brilliant_count = sum(1 for ev in player_evals if ev.get("classification") in _BRILLIANT_CLASSIFICATIONS)
    mistake_count   = sum(1 for ev in player_evals if ev.get("classification") in _BAD_CLASSIFICATIONS)

    good_ratio      = good_count / n
    brilliant_ratio = brilliant_count / n
    mistake_ratio   = mistake_count / n

    precision_component = med_quality * 1.5
    good_component      = good_ratio * 1.0
    brilliant_component = brilliant_ratio * 1.5
    length_bonus        = min(1.0, n / 50.0) * 0.3
    mistake_penalty     = (mistake_ratio ** 0.7) * 3.0

    total = precision_component + good_component + brilliant_component + length_bonus - mistake_penalty
    return min(3.0, max(0.0, total))


def _tactical_nerf(opponent_evals: list) -> float:
    """
    Nerf factor (0.1–1.0) based on the *opponent*'s blunders.
    """
    if not opponent_evals:
        return 1.0

    nerf_factors = []

    for ev in opponent_evals:
        sc = ev.get("score_change", 0.0)
        if sc >= -0.8:
            continue

        loss = abs(sc)

        if loss >= 3.0:
            severity = min(loss / 3.0, 3.0)
            base_nerf = max(0.1, 1.0 - severity * 0.3)
        elif loss >= 1.5:
            base_nerf = max(0.4, 1.0 - (loss / 6.0))
        else:
            base_nerf = max(0.85, 1.0 - (loss / 10.0))

        ply = ((ev.get("move_num", 1) - 1) * 2) + (0 if ev.get("side") == "White" else 1)

        mitigation = 0.0
        if ply > _MID_GAME_END_PLY:
            mitigation = 0.6
        elif ply > _EARLY_GAME_END_PLY:
            mitigation = 0.3

        if base_nerf < 1.0:
            reduction = 1.0 - base_nerf
            adjusted = reduction * (1.0 - mitigation)
            final_nerf = 1.0 - adjusted
            final_nerf = max(0.1, min(1.0, final_nerf))
            nerf_factors.append(final_nerf)

    if not nerf_factors:
        return 1.0

    sorted_nerfs = sorted(nerf_factors)
    worst = sorted_nerfs[:3]
    product = 1.0
    for nf in worst:
        product *= nf
    geo_mean = product ** (1.0 / len(worst))

    density = len(nerf_factors) / max(len(opponent_evals), 1)
    density_penalty = max(0.5, 1.0 - density)

    return max(0.1, geo_mean * density_penalty)


def _volatility_bonus(player_evals: list) -> float:
    """
    Bonus for highly tactical, volatile games (0–1.5).
    """
    if len(player_evals) < 3:
        return 0.0

    changes = [abs(ev.get("score_change", 0.0)) for ev in player_evals]
    qualities = [ev.get("move_quality", 0.5) for ev in player_evals]
    n = len(changes)

    mean_c = sum(changes) / n
    variance = sum((c - mean_c) ** 2 for c in changes) / n
    std_c = math.sqrt(variance)

    norm_std = min(1.0, std_c / 2.0)
    critical_ratio = sum(1 for c in changes if c > 1.0) / n
    med_quality = _median(qualities)
    quality_scale = med_quality

    volatility = (norm_std * 0.6 + critical_ratio * 0.4) * 1.5 * quality_scale
    return min(1.5, max(0.0, volatility))


def calculate_difficulty(white_evals: List[Dict[str, Any]], black_evals: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Multi-factor game difficulty estimation.
    """
    def _side(player, opponent):
        if not player:
            return 5.0
        decision  = _decision_difficulty(player)
        precision = _precision_bonus(player)
        nerf      = _tactical_nerf(opponent)
        vol       = _volatility_bonus(player)
        raw = (decision * nerf) + precision + vol
        return round(min(10.0, max(1.0, raw)), 1)

    w = _side(white_evals, black_evals)
    b = _side(black_evals, white_evals)

    return {
        "overall": round((w + b) / 2, 1),
        "white": w,
        "black": b,
    }
