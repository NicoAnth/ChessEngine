import os
import sys
from pathlib import Path

# --- Path Configuration ---
# Ensure integration with source code (h:\Programmation\ChessEngine)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

# --- Engine Configuration ---
DEFAULT_ENGINE_PATH = r'H:\Ouvertures Echecs\stockfish-windows-x86-64-avx2\stockfish\stockfish-windows-x86-64-avx2.exe'

# --- Profile Configuration ---
PROFILE_DIR = PROJECT_ROOT / "user_profiles"
