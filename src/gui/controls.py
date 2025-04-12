"""
UI controls for the chess application.
Handles buttons, status messages, and other UI controls.
"""

import tkinter as tk
from tkinter import ttk, font
import os
from src.utils import config, resource_loader

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
        self.button_font = font.Font(family="Segoe UI", size=10, weight="bold")
        self.icon_font = font.Font(family="Segoe UI Symbol", size=12, weight="bold")
        
        # Create main container frame with modern look
        self.container_frame = ttk.Frame(parent, padding=5)
        self.container_frame.pack(fill='x', pady=4)  # Reduced from pady=10
        
        # Create button container with subtle gradient background
        self.button_frame = tk.Frame(
            self.container_frame,
            bg=config.COLORS["background"],
            padx=10,
            pady=4,  # Reduced from pady=8
            relief="flat"
        )
        self.button_frame.pack(fill='x')
        
        # Create buttons with modern styling
        self.create_control_buttons()
        
        # Status message label with modern font
        self.status_container = tk.Frame(parent, bg=config.COLORS["background"])
        self.status_container.pack(fill='x', pady=5)
        
        self.status_label = ttk.Label(
            self.status_container,
            text="Nouvelle partie", 
            font=font.Font(family="Segoe UI", size=12, weight="normal"),
            background=config.COLORS["background"],
            foreground=config.COLORS["primary_text"]
        )
        self.status_label.pack(pady=5)
    
    def create_control_buttons(self):
        """Create and arrange the control buttons with modern styling."""
        # Modern button base style
        button_base_style = {
            "borderwidth": 0,
            "padx": 15,
            "pady": 8,
            "cursor": "hand2",
            "relief": "flat",
            "highlightthickness": 0
        }
        
        # Button hover effect
        def on_hover(e, button, bg_color, hover_color):
            button.config(background=hover_color)
            
        def on_leave(e, button, bg_color):
            button.config(background=bg_color)

        # Create a frame for game control buttons (left side)
        self.game_controls = tk.Frame(self.button_frame, bg=config.COLORS["background"])
        self.game_controls.pack(side=tk.LEFT, fill="y")
        
        # Flip board button with icon
        flip_color = "#4A5568"
        flip_hover = "#3D4852"
        flip_button = tk.Button(
            self.game_controls, 
            text="⟲",  # Unicode rotation symbol
            font=self.icon_font,
            command=self.callbacks.get("flip_board"),
            bg=flip_color,
            fg="white",
            activebackground=flip_hover,
            activeforeground="white",
            **button_base_style
        )
        flip_button.pack(side=tk.LEFT, padx=5)
        flip_button.bind("<Enter>", lambda e: on_hover(e, flip_button, flip_color, flip_hover))
        flip_button.bind("<Leave>", lambda e: on_leave(e, flip_button, flip_color))
        
        # Add tooltip for flip button
        self.create_tooltip(flip_button, "Retourner l'échiquier")
        
        # Undo move button with icon
        undo_color = "#4299E1"
        undo_hover = "#3182CE"
        undo_button = tk.Button(
            self.game_controls, 
            text="↩",  # Unicode undo arrow
            font=self.icon_font,
            command=self.callbacks.get("undo_move"),
            bg=undo_color,
            fg="white", 
            activebackground=undo_hover,
            activeforeground="white",
            **button_base_style
        )
        undo_button.pack(side=tk.LEFT, padx=5)
        undo_button.bind("<Enter>", lambda e: on_hover(e, undo_button, undo_color, undo_hover))
        undo_button.bind("<Leave>", lambda e: on_leave(e, undo_button, undo_color))
        
        # Add tooltip for undo button
        self.create_tooltip(undo_button, "Annuler le dernier coup")
        
        # Create a frame for action buttons (right side)
        self.action_controls = tk.Frame(self.button_frame, bg=config.COLORS["background"])
        self.action_controls.pack(side=tk.RIGHT, fill="y")
        
        # Game analysis button
        analysis_color = "#35C2A0"
        analysis_hover = "#4FD9B4"
        summary_button = tk.Button(
            self.action_controls, 
            text="Bilan de Partie",
            font=self.button_font,
            command=self.callbacks.get("analyze_game"),
            bg=analysis_color,
            fg="white",
            activebackground=analysis_hover,
            activeforeground="white",
            **button_base_style
        )
        summary_button.pack(side=tk.RIGHT, padx=5)
        summary_button.bind("<Enter>", lambda e: on_hover(e, summary_button, analysis_color, analysis_hover))
        summary_button.bind("<Leave>", lambda e: on_leave(e, summary_button, analysis_color))
        
        # New game button
        new_color = "#4FA9E6"
        new_hover = "#69B6F0"
        new_game_button = tk.Button(
            self.action_controls, 
            text="Nouvelle Partie", 
            font=self.button_font,
            command=self.callbacks.get("new_game"),
            bg=new_color,
            fg="white",
            activebackground=new_hover,
            activeforeground="white",
            **button_base_style
        )
        new_game_button.pack(side=tk.RIGHT, padx=5)
        new_game_button.bind("<Enter>", lambda e: on_hover(e, new_game_button, new_color, new_hover))
        new_game_button.bind("<Leave>", lambda e: on_leave(e, new_game_button, new_color))
    
    def create_tooltip(self, widget, text):
        """Create a tooltip for a widget."""
        def enter(event):
            x, y, _, _ = widget.bbox("insert")
            x += widget.winfo_rootx() + 25
            y += widget.winfo_rooty() + 25
            
            # Create a toplevel window
            self.tooltip = tk.Toplevel(widget)
            self.tooltip.wm_overrideredirect(True)
            self.tooltip.wm_geometry(f"+{x}+{y}")
            
            label = tk.Label(self.tooltip, text=text, background="#2D3748", foreground="white",
                           relief="solid", borderwidth=1, padx=5, pady=2, font=("Segoe UI", 9))
            label.pack()
            
        def leave(event):
            if hasattr(self, "tooltip"):
                self.tooltip.destroy()
                
        widget.bind("<Enter>", enter)
        widget.bind("<Leave>", leave)
    
    def display_status_message(self, message, color=None, duration=None):
        """
        Display a status message with animation.
        
        Args:
            message: Message text to display
            color: Text color (defaults to primary text color)
            duration: Time in milliseconds before message is cleared
        """
        if color is None:
            color = config.COLORS["primary_text"]
            
        if duration is None:
            duration = config.STATUS_DURATION
        
        # Animate the status update
        current_text = self.status_label.cget("text")
        
        # Only animate if text is changing
        if current_text != message:
            # Fade out
            def fade_out(alpha):
                if alpha > 0:
                    self.status_label.config(foreground=self._adjust_color_alpha(color, alpha))
                    self.parent.after(20, lambda: fade_out(alpha - 0.1))
                else:
                    self.status_label.config(text=message)
                    fade_in(0)
            
            # Fade in
            def fade_in(alpha):
                if alpha < 1:
                    self.status_label.config(foreground=self._adjust_color_alpha(color, alpha))
                    self.parent.after(20, lambda: fade_in(alpha + 0.1))
                else:
                    self.status_label.config(foreground=color)
                    # Auto-clear after duration
                    if duration > 0:
                        self.parent.after(duration, lambda: self.status_label.config(
                            text="", foreground=config.COLORS["primary_text"]
                        ))
            
            # Start fade animation
            fade_out(1.0)
        else:
            # No animation needed, just set text and color
            self.status_label.config(text=message, foreground=color)
            
            # Auto-clear after duration
            if duration > 0:
                self.parent.after(duration, lambda: self.status_label.config(
                    text="", foreground=config.COLORS["primary_text"]
                ))
    
    def _adjust_color_alpha(self, color, alpha):
        """Adjust color transparency for animation."""
        if color.startswith("#"):
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
            return f"#{r:02x}{g:02x}{b:02x}"
        return color


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
        self.analysis_header.pack(pady=(0, 5), anchor="center")
        
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
            lbl.pack(pady=2, anchor="center")
    
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