#!/usr/bin/env python3
"""
Modern Chess GUI application entry point.
Launches the chess application with the Stockfish engine.
"""

import os
import sys
import signal
import tkinter as tk
from tkinter import simpledialog, messagebox
import datetime
from typing import Optional

from src.gui.main_window import ChessApplication
from src.user import UserProfileManager, UserProfile

def handle_sigint(sig, frame):
    """Handle Ctrl+C gracefully by initiating application shutdown."""
    print("\nCtrl+C detected. Shutting down forcibly...")
    # Terminate process immediately without cleaning up threads
    os._exit(0)

def prompt_create_user(manager: UserProfileManager) -> Optional[UserProfile]:
    """Prompts the user to create the first profile."""
    # Use a hidden root window for the dialog
    root = tk.Tk()
    root.withdraw() # Hide the root window

    messagebox.showinfo("Bienvenue !", "Aucun profil utilisateur trouvé. Veuillez en créer un.")
    username = None
    while not username:
        username = simpledialog.askstring("Création du profil", "Entrez votre nom d'utilisateur:", parent=root)
        if username is None: # User cancelled
            messagebox.showwarning("Annulé", "La création d'un profil est nécessaire pour continuer.")
            continue
        if not username.strip():
            messagebox.showerror("Erreur", "Le nom d'utilisateur ne peut pas être vide.")
            username = None # Reset to loop

    try:
        profile = manager.create_profile(username.strip())
        messagebox.showinfo("Succès", f"Profil '{profile.username}' créé avec succès.")
        root.destroy() # Clean up the hidden window
        return profile
    except ValueError as e:
        messagebox.showerror("Erreur", str(e))
        root.destroy()
        return None # Indicate failure
    except Exception as e:
        messagebox.showerror("Erreur", f"Une erreur inattendue est survenue: {e}")
        root.destroy()
        return None # Indicate failure

def main():
    """Main application entry point."""
    # Register SIGINT handler for Ctrl+C
    signal.signal(signal.SIGINT, handle_sigint)
    
    # Default engine path for Windows
    # Surchargeable via la variable d'environnement STOCKFISH_PATH (defaut = machine de dev).
    default_engine_path = os.environ.get(
        'STOCKFISH_PATH',
        r'H:\Ouvertures Echecs\stockfish-windows-x86-64-avx2\stockfish\stockfish-windows-x86-64-avx2.exe',
    )
    
    # Use command line argument if provided
    engine_path = sys.argv[1] if len(sys.argv) > 1 else default_engine_path
    
    # --- User Profile Management ---
    profile_manager = UserProfileManager() # Default directory 'user_profiles'
    current_user: Optional[UserProfile] = None

    if not profile_manager.profiles:
        # No profiles exist, prompt to create one
        current_user = prompt_create_user(profile_manager)
        if current_user is None:
            print("Création du profil annulée ou échouée. Fermeture de l'application.")
            sys.exit(0) # Exit if profile creation failed or was cancelled
    else:
        # Profiles exist, load the first one found (simple approach)
        first_username = list(profile_manager.profiles.keys())[0]
        current_user = profile_manager.get_profile(first_username)
        if current_user:
            print(f"Profil utilisateur '{current_user.username}' chargé.")
            # Update last login time
            current_user.last_login = datetime.datetime.now()
            profile_manager.save_profile(current_user)
        else:
            # Should not happen if profiles dictionary is not empty, but handle defensively
            print(f"Erreur: Impossible de charger le profil {first_username}.")
            # Attempt to create a new one as fallback
            current_user = prompt_create_user(profile_manager)
            if current_user is None:
                print("Création du profil annulée ou échouée. Fermeture de l'application.")
                sys.exit(0)
    # --- End User Profile Management ---

    # Check if engine exists
    if not os.path.isfile(engine_path):
        print(f"Error: Stockfish engine not found at {engine_path}")
        print("Please provide the correct path to the Stockfish engine as a command line argument.")
        print("Example: python main.py /path/to/stockfish")
        sys.exit(1)
    
    # Make app global so signal handler can access it
    global app
    
    try:
        # Launch the application, passing the loaded/created user profile AND the manager
        app = ChessApplication(engine_path, current_user, profile_manager)
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