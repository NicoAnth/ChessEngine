"""
UI controls for the chess application.
Handles buttons, status messages, and other UI controls.
"""

import tkinter as tk
from tkinter import ttk, font
from src.utils import config

class ControlPanel:
    """Manages UI controls for the chess application."""
    
    def __init__(self, parent, callbacks):
        """
        Initialize the control panel.
        
        Args:
            parent: Parent frame or window
            callbacks: Dictionary of callback functions for button actions
        """
        self.parent = parent
        self.callbacks = callbacks
        
        # Set up fonts
        self.button_font = font.Font(family="Segoe UI", size=10)
        
        # Create button frame
        self.button_frame = ttk.Frame(parent, padding=5)
        self.button_frame.pack(fill='x', pady=10)
        
        # Create buttons
        self.create_control_buttons()
        
        # Status message label
        self.status_label = ttk.Label(
            parent,
            text="Nouvelle partie", 
            font=font.Font(family="Segoe UI", size=12),
            background=config.COLORS["background"],
            foreground=config.COLORS["primary_text"]
        )
        self.status_label.pack(pady=10)
    
    def create_control_buttons(self):
        """Create and arrange the control buttons."""
        # Custom button styling
        button_style = {
            "font": self.button_font,
            "width": 12,
            "border": 0,
            "borderwidth": 0,
            "padx": 10,
            "pady": 5,
            "cursor": "hand2"
        }
        
        # Flip board button
        flip_button = tk.Button(
            self.button_frame, 
            text="Flip Board", 
            command=self.callbacks.get("flip_board"),
            bg=config.COLORS["control_button"],
            fg="white",
            activebackground=config.COLORS["control_button_active"],
            **button_style
        )
        flip_button.pack(side=tk.LEFT, padx=5)
        
        # Undo move button
        undo_button = tk.Button(
            self.button_frame, 
            text="Undo Move", 
            command=self.callbacks.get("undo_move"),
            bg=config.COLORS["control_button"],
            fg="white", 
            activebackground=config.COLORS["control_button_active"],
            **button_style
        )
        undo_button.pack(side=tk.LEFT, padx=5)
        
        # New game button
        new_game_button = tk.Button(
            self.button_frame, 
            text="Nouvelle Partie", 
            command=self.callbacks.get("new_game"),
            bg=config.COLORS["new_game_button"],
            fg="white",
            activebackground=config.COLORS["new_game_button_active"],
            **button_style
        )
        new_game_button.pack(side=tk.LEFT, padx=5)
        
        # Game analysis button
        summary_button = tk.Button(
            self.button_frame, 
            text="Bilan de Partie", 
            command=self.callbacks.get("analyze_game"),
            bg=config.COLORS["analysis_button"],
            fg="white",
            activebackground=config.COLORS["analysis_button_active"],
            **button_style
        )
        summary_button.pack(side=tk.LEFT, padx=5)
    
    def display_status_message(self, message, color=None, duration=None):
        """
        Display a status message.
        
        Args:
            message: Message text to display
            color: Text color (defaults to primary text color)
            duration: Time in milliseconds before message is cleared
        """
        if color is None:
            color = config.COLORS["primary_text"]
            
        if duration is None:
            duration = config.STATUS_DURATION
            
        self.status_label.config(text=message, foreground=color)
        self.parent.after(duration, lambda: self.status_label.config(
            text="", foreground=config.COLORS["primary_text"]
        ))


class AnalysisPanel:
    """Displays chess engine analysis information."""
    
    def __init__(self, parent):
        """
        Initialize the analysis panel.
        
        Args:
            parent: Parent frame or window
        """
        self.parent = parent
        
        # Create frame for engine analysis
        self.analysis_frame = ttk.Frame(parent, padding=5)
        self.analysis_frame.pack(fill='x', expand=True)
        
        # Header for analysis section
        self.analysis_header = ttk.Label(
            self.analysis_frame,
            text="ANALYSE MOTEUR",
            font=font.Font(**config.FONTS["button"]),
            background=config.COLORS["background"],
            foreground=config.COLORS["primary_text"]
        )
        self.analysis_header.pack(pady=(0, 5))
        
        # Container for top moves that will be updated
        self.moves_container = ttk.Frame(self.analysis_frame)
        self.moves_container.pack(fill='x', expand=True)
        
        # Game info section
        self.game_info_frame = ttk.Frame(parent, padding=10)
        self.game_info_frame.pack(fill='x', expand=True, pady=10)
        
        # Position info
        self.position_info = ttk.Label(
            self.game_info_frame,
            text="Position: Starting position",
            font=font.Font(**config.FONTS["label"]),
            background=config.COLORS["background"],
            wraplength=250
        )
        self.position_info.pack(pady=5)
        
        # Turn indicator
        self.turn_frame = ttk.Frame(self.game_info_frame)
        self.turn_frame.pack(fill='x', pady=5)
        
        self.turn_label = ttk.Label(
            self.turn_frame,
            text="Tour: Blancs",
            font=font.Font(**config.FONTS["label"]),
            background=config.COLORS["background"]
        )
        self.turn_label.pack(side=tk.LEFT)
        
        self.turn_indicator = tk.Canvas(
            self.turn_frame, 
            width=15, 
            height=15, 
            bg=config.COLORS["background"],
            highlightthickness=0
        )
        self.turn_indicator.pack(side=tk.LEFT, padx=5)
        self.turn_indicator.create_oval(2, 2, 13, 13, fill="white", outline="#333")
    
    def display_top_moves(self, moves):
        """
        Display top moves from the engine analysis.
        
        Args:
            moves: List of (move, score) tuples
        """
        # Clear previous moves
        for widget in self.moves_container.winfo_children():
            widget.destroy()
            
        # Create label for each move
        label_font = font.Font(family="Segoe UI", size=11, weight="bold")
        for move, score in moves:
            text = f"({score}) {move}"
            lbl = ttk.Label(
                self.moves_container, 
                text=text, 
                font=label_font, 
                background=config.COLORS["background"], 
                foreground=config.COLORS["primary_text"]
            )
            lbl.pack(anchor="w", pady=2)
    
    def update_position_info(self, info_text):
        """
        Update the position information text.
        
        Args:
            info_text: Text describing the current position
        """
        self.position_info.config(text=f"Position: {info_text}")
    
    def update_turn_indicator(self, is_white_turn):
        """
        Update the turn indicator to show current side to move.
        
        Args:
            is_white_turn: True if it's white's turn, False for black
        """
        turn_text = "Blancs" if is_white_turn else "Noirs"
        turn_color = "white" if is_white_turn else "black"
        
        self.turn_label.config(text=f"Tour: {turn_text}")
        self.turn_indicator.delete("all")
        self.turn_indicator.create_oval(2, 2, 13, 13, fill=turn_color, outline="#333")