#!/usr/bin/env python3
"""
Modern Chess GUI application entry point.
Launches the chess application with the Stockfish engine.
"""

import os
import sys
from src.gui.main_window import ChessApplication

def main():
    """Main application entry point."""
    # Default engine path for Windows
    default_engine_path = r'H:\Ouvertures Echecs\stockfish-windows-x86-64-avx2\stockfish\stockfish-windows-x86-64-avx2.exe'
    
    # Use command line argument if provided
    engine_path = sys.argv[1] if len(sys.argv) > 1 else default_engine_path
    
    # Check if engine exists
    if not os.path.isfile(engine_path):
        print(f"Error: Stockfish engine not found at {engine_path}")
        print("Please provide the correct path to the Stockfish engine as a command line argument.")
        print("Example: python main.py /path/to/stockfish")
        sys.exit(1)
    
    # Launch the application
    app = ChessApplication(engine_path)
    app.run()

if __name__ == "__main__":
    main()