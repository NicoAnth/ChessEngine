"""
Chess opening detection service.
Detects chess openings using the ECO (Encyclopedia of Chess Openings) database.

The ECO database (~3.8 MB of JSON) is parsed ONCE per process and shared
read-only across all OpeningDetector instances (P-04). Position lookups are O(1)
via a normalized-FEN index (P-03). Only the mutable detection state
(current_opening, last_theoretical_move_*) is kept per instance.
"""

import os
import json
import threading

import chess

# --- Shared, read-only ECO caches (loaded once per process) ---
_ECO_BY_MOVES = {}      # normalized SAN sequence -> {eco, name}
_ECO_BY_FEN = {}        # full FEN -> {eco, name}
_ECO_BY_POSITION = {}   # normalized FEN (4 first fields) -> {eco, name} (first wins)
_ECO_LOADED = False
_ECO_LOCK = threading.Lock()

# Beyond this many half-moves, a fresh ECO match other than an exact FEN hit is
# implausible, so the (cheap) normalized-position lookup is skipped.
_MAX_DETECT_PLIES = 30


def _normalize_moves_str(moves_str):
    """Strip move numbers (e.g. '1.', '2.') from a SAN moves string."""
    return ' '.join(p for p in moves_str.strip().split() if not p.endswith('.'))


def _resolve_eco_folder(eco_folder_path=None):
    if eco_folder_path is not None:
        return eco_folder_path
    if os.path.exists(os.path.join(os.getcwd(), 'eco.json')):
        return os.path.join(os.getcwd(), 'eco.json')
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
    return os.path.join(project_root, 'eco.json')


def _ensure_eco_loaded(eco_folder_path=None):
    """Parse the ECO database once and populate the module caches (thread-safe)."""
    global _ECO_LOADED
    if _ECO_LOADED:
        return True
    with _ECO_LOCK:
        if _ECO_LOADED:
            return True
        folder = _resolve_eco_folder(eco_folder_path)
        if not os.path.exists(folder):
            print(f"ECO database folder not found at {folder}")
            return False
        total = 0
        for section in ['A', 'B', 'C', 'D', 'E']:
            path = os.path.join(folder, f'eco{section}.json')
            if not os.path.exists(path):
                print(f"ECO file not found: {path}")
                continue
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    eco_data = json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                print(f"Error parsing ECO JSON file {path}: {e}")
                continue
            for fen, data in eco_data.items():
                if 'moves' in data and 'name' in data:
                    info = {'eco': data.get('eco', ''), 'name': data['name']}
                    _ECO_BY_MOVES[_normalize_moves_str(data['moves'])] = info
                    _ECO_BY_FEN[fen] = info
                    # First opening wins for a given normalized position,
                    # reproducing the previous position_matches[0] behaviour.
                    _ECO_BY_POSITION.setdefault(' '.join(fen.split(' ')[:4]), info)
                    total += 1
        print(f"ECO database loaded: {total} openings")
        _ECO_LOADED = True
        return True


class OpeningDetector:
    """A service for detecting chess openings from move sequences."""

    def __init__(self):
        # ECO tables are shared, read-only module caches.
        self.openings_by_moves = _ECO_BY_MOVES
        self.openings_by_fen = _ECO_BY_FEN
        self.openings_by_position = _ECO_BY_POSITION
        self.eco_loaded = _ECO_LOADED
        # Mutable detection state — strictly per instance.
        self.current_opening = None
        self.last_theoretical_move_opening = None
        self.last_theoretical_move_index = -1

    def load_eco_database(self, eco_folder_path=None):
        """Ensure the shared ECO database is loaded; rebind the instance views."""
        if _ensure_eco_loaded(eco_folder_path):
            self.openings_by_moves = _ECO_BY_MOVES
            self.openings_by_fen = _ECO_BY_FEN
            self.openings_by_position = _ECO_BY_POSITION
            self.eco_loaded = True
            return True
        return False

    def _normalize_moves(self, moves_str):
        return _normalize_moves_str(moves_str)

    def detect_opening(self, board, force_exact_match=False):
        """
        Detect the chess opening for the current board position.

        Returns a dict with 'eco' and 'name' if an opening is detected, else None.
        """
        if not self.eco_loaded:
            if not self.load_eco_database():
                return None

        previous_opening = self.current_opening
        found_opening = None

        # 1) Exact FEN match (most specific) — always, at any depth.
        current_fen = board.fen()
        if current_fen in self.openings_by_fen:
            found_opening = self.openings_by_fen[current_fen]
            self.current_opening = found_opening
            self.last_theoretical_move_opening = found_opening
            self.last_theoretical_move_index = len(board.move_stack) - 1
            return found_opening

        if force_exact_match:
            self.current_opening = None
            return None

        # Past the opening horizon, only exact FEN hits (handled above) count.
        if len(board.move_stack) > _MAX_DETECT_PLIES:
            self.current_opening = None
            return None

        # 2) Normalized position (ignore move counters) — O(1) lookup.
        position_fen = ' '.join(current_fen.split(' ')[:4])
        match = self.openings_by_position.get(position_fen)
        if match:
            found_opening = match
            self.current_opening = found_opening
            self.last_theoretical_move_opening = found_opening
            self.last_theoretical_move_index = len(board.move_stack) - 1
            return found_opening

        # 3) Move-sequence match — only for short sequences.
        if board.move_stack and len(board.move_stack) <= 15:
            temp_board = chess.Board()
            moves_san = []
            for move in board.move_stack:
                moves_san.append(temp_board.san(move))
                temp_board.push(move)

            while moves_san:
                normalized_candidate = _normalize_moves_str(' '.join(moves_san))
                if normalized_candidate in self.openings_by_moves:
                    found_opening = self.openings_by_moves[normalized_candidate]
                    self.current_opening = found_opening
                    self.last_theoretical_move_opening = found_opening
                    self.last_theoretical_move_index = len(moves_san) - 1
                    return found_opening
                moves_san.pop()

            # 4) Move-by-move match to catch transpositions (very short only).
            if len(board.move_stack) <= 10:
                temp_board = chess.Board()
                for i in range(len(board.move_stack)):
                    temp_board.push(board.move_stack[i])
                    temp_fen = temp_board.fen()
                    if temp_fen in self.openings_by_fen:
                        found_opening = self.openings_by_fen[temp_fen]
                        self.current_opening = found_opening
                        self.last_theoretical_move_opening = found_opening
                        self.last_theoretical_move_index = i
                        return found_opening
                    pos_match = self.openings_by_position.get(' '.join(temp_fen.split(' ')[:4]))
                    if pos_match:
                        found_opening = pos_match
                        self.current_opening = found_opening
                        self.last_theoretical_move_opening = found_opening
                        self.last_theoretical_move_index = i
                        return found_opening

        # No opening found: reset current, keep last theoretical info.
        self.current_opening = None
        if previous_opening and not found_opening:
            pass
        return None

    def get_current_opening(self):
        return self.current_opening

    def get_last_theoretical_move_opening(self):
        if self.last_theoretical_move_opening is None:
            return None
        return {
            "eco": self.last_theoretical_move_opening.get('eco', ''),
            "name": self.last_theoretical_move_opening.get('name', ''),
            "move_index": self.last_theoretical_move_index,
        }

    def reset(self):
        self.current_opening = None
        self.last_theoretical_move_opening = None
        self.last_theoretical_move_index = -1
