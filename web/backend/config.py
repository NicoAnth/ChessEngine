import os
import sys
from pathlib import Path

# --- Path Configuration ---
# Ensure integration with source code (h:\Programmation\ChessEngine)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

# --- Engine Configuration ---
# Chemin du binaire Stockfish, surchargeable via la variable d'environnement
# STOCKFISH_PATH. Le defaut ci-dessous est specifique a la machine de dev et ne
# sert que de fallback (cf M-01/D-08/S-06).
DEFAULT_ENGINE_PATH = os.environ.get(
    "STOCKFISH_PATH",
    r"H:\Ouvertures Echecs\stockfish-windows-x86-64-avx2\stockfish\stockfish-windows-x86-64-avx2.exe",
)

# --- Profile Configuration ---
# Les profils web sont isoles dans un sous-dossier dedie pour ne PAS entrer en
# collision avec les profils de l'app desktop, dont le schema est incompatible
# et dont le save ecrase les donnees web (cf S-01).
PROFILE_DIR = PROJECT_ROOT / "user_profiles" / "web"
