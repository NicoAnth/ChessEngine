#!/usr/bin/env python3
"""
Modern Chess GUI application entry point.
Launches the chess application with the Stockfish engine.
"""

import os
import sys
import signal
from src.gui.main_window import ChessApplication

def handle_sigint(sig, frame):
    """Handle Ctrl+C gracefully by initiating application shutdown."""
    print("\nCtrl+C detected. Shutting down gracefully...")
    
    # Access the app instance if it exists and initiate cleanup
    if 'app' in globals() and app is not None:
        app.on_closing()
    else:
        # If app isn't available or initialized, exit directly
        sys.exit(0)

def main():
    """Main application entry point."""
    # Register SIGINT handler for Ctrl+C
    signal.signal(signal.SIGINT, handle_sigint)
    
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
    
    # Make app global so signal handler can access it
    global app
    
    try:
        # Launch the application
        app = ChessApplication(engine_path)
        app.run()
    except KeyboardInterrupt:
        # Handle KeyboardInterrupt (Ctrl+C) within the run method
        print("\nKeyboard interrupt received. Shutting down...")
        if 'app' in globals() and app is not None:
            app.on_closing()
    except Exception as e:
        print(f"Unexpected error: {e}")
        # Ensure cleanup on unexpected errors
        if 'app' in globals() and app is not None:
            app.on_closing() 
        raise

if __name__ == "__main__":
    main()