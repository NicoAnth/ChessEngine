"""Error visualization component using mini chess board."""

import tkinter as tk
from tkinter import font
import chess
from src.utils import config

class ErrorVisualizer:
    """
    Visualizes chess errors with before/after/best move states.
    Uses existing mini board for visualization.
    """
    
    def __init__(self, mini_board, view_instance):
        self.mini_board = mini_board
        self.view_instance = view_instance
        self.current_error = None
        self.state = "before"  # "before", "error", "best"
        self.states = ["before", "error", "best"]
        
        # Store FEN positions for different states
        self.positions = {
            "before": None,
            "error": None, 
            "best": None
        }
        
        # Store move info
        self.moves = {
            "error_uci": None,
            "best_uci": None
        }
        
        # Create control overlay
        self._create_controls()
    
    def _create_controls(self):
        """Create controls for toggling between visualization states."""
        # Get parent of mini board
        parent = self.mini_board.parent
        
        # Create frame for state toggle buttons
        self.controls_frame = tk.Frame(parent, bg=config.COLORS["background"])
        self.controls_frame.pack(fill="x", pady=(10, 5))
        
        # Define button colors
        btn_bg = config.COLORS["button_background"]
        btn_fg = config.COLORS["button_text"]
        active_bg = config.COLORS["button_active"]
        active_fg = config.COLORS["button_text_active"]
        
        # Create state toggle buttons
        self.buttons = {}
        
        # Before Error button
        self.buttons["before"] = tk.Button(
            self.controls_frame,
            text="Position initiale",
            bg=active_bg if self.state == "before" else btn_bg,
            fg=active_fg if self.state == "before" else btn_fg,
            relief="flat",
            bd=0,
            padx=10,
            pady=5,
            font=font.Font(**config.FONTS["button"]),
            command=lambda: self.show_state("before")
        )
        self.buttons["before"].pack(side="left", padx=(0, 5))
        
        # Error Move button
        self.buttons["error"] = tk.Button(
            self.controls_frame,
            text="Erreur",
            bg=btn_bg,
            fg=btn_fg,
            relief="flat",
            bd=0,
            padx=10,
            pady=5,
            font=font.Font(**config.FONTS["button"]),
            command=lambda: self.show_state("error")
        )
        self.buttons["error"].pack(side="left", padx=5)
        
        # Best Move button
        self.buttons["best"] = tk.Button(
            self.controls_frame,
            text="Meilleur coup",
            bg=btn_bg,
            fg=btn_fg,
            relief="flat",
            bd=0,
            padx=10,
            pady=5,
            font=font.Font(**config.FONTS["button"]),
            command=lambda: self.show_state("best")
        )
        self.buttons["best"].pack(side="left", padx=5)
        
        # Create explanation frame
        self.explanation_frame = tk.Frame(parent, bg=config.COLORS["background"])
        self.explanation_frame.pack(fill="x", pady=5)
        
        self.explanation_label = tk.Label(
            self.explanation_frame,
            text="Sélectionnez une erreur pour visualiser les détails",
            wraplength=350,
            justify="left",
            bg=config.COLORS["background"],
            fg=config.COLORS["primary_text"],
            font=font.Font(**config.FONTS["explanation"])
        )
        self.explanation_label.pack(anchor="w", padx=5)
        
        # Hide controls until an error is selected
        self.hide_controls()
    
    def hide_controls(self):
        """Hide the controls when no error is selected."""
        self.controls_frame.pack_forget()
        self.explanation_frame.pack_forget()
    
    def show_controls(self):
        """Show the controls when an error is selected."""
        self.controls_frame.pack(fill="x", pady=(10, 5))
        self.explanation_frame.pack(fill="x", pady=5)
    
    def show_state(self, state):
        """
        Show a specific state of error visualization.
        
        Args:
            state: One of "before", "error", "best"
        """
        if state not in self.states or not self.current_error:
            return
            
        # Update state
        self.state = state
        
        # Update button appearance
        for btn_state, button in self.buttons.items():
            if btn_state == state:
                button.config(
                    bg=config.COLORS["button_active"],
                    fg=config.COLORS["button_text_active"]
                )
            else:
                button.config(
                    bg=config.COLORS["button_background"],
                    fg=config.COLORS["button_text"]
                )
        
        # Update visualization based on state
        if state == "before":
            # Show position before the error
            if self.positions["before"]:
                self.mini_board.update_to_position(self.positions["before"])
                self.mini_board.delete("arrow")  # Remove any arrows
                self._update_explanation("Position avant l'erreur.")
                
        elif state == "error":
            # Show error move
            if self.positions["error"] and self.moves["error_uci"]:
                self.mini_board.update_to_position(self.positions["error"])
                
                # Parse the move and draw red arrow
                try:
                    from_square = chess.parse_square(self.moves["error_uci"][:2])
                    to_square = chess.parse_square(self.moves["error_uci"][2:4])
                    self.mini_board.draw_error_indicator(from_square, to_square, color="#F44336", width=3)
                    
                    # Update explanation
                    eval_change = self.current_error.get("score_change", 0)
                    move_text = self.current_error.get("san", "")
                    self._update_explanation(
                        f"Coup joué: {move_text}\n"
                        f"Changement d'évaluation: {self._format_eval_change(eval_change)}"
                    )
                except Exception as e:
                    print(f"Error showing error move: {e}")
                
        elif state == "best":
            # Show best move
            if self.positions["before"] and self.moves["best_uci"]:
                self.mini_board.update_to_position(self.positions["before"])
                
                # Parse the move and draw green arrow
                try:
                    from_square = chess.parse_square(self.moves["best_uci"][:2])
                    to_square = chess.parse_square(self.moves["best_uci"][2:4])
                    self.mini_board.draw_error_indicator(from_square, to_square, color="#4CAF50", width=3)
                    
                    # Update explanation
                    best_move = self.current_error.get("best_move", "")
                    best_eval = self.current_error.get("best_score", 0)
                    self._update_explanation(
                        f"Meilleur coup: {best_move}\n"
                        f"Évaluation: {self._format_evaluation(best_eval)}"
                    )
                except Exception as e:
                    print(f"Error showing best move: {e}")
    
    def visualize_error(self, error_data, board_position):
        """
        Set up visualization for a specific error.
        
        Args:
            error_data: Dictionary containing error information
            board_position: FEN string of the position before the error
        """
        self.current_error = error_data
        
        # Parse move info
        error_move = error_data.get("uci", "")
        best_move = error_data.get("best_move_uci", "")
        
        # Get board positions
        before_fen = board_position
        
        # Store positions and moves
        self.positions["before"] = before_fen
        self.moves["error_uci"] = error_move
        self.moves["best_uci"] = best_move
        
        # Calculate 'after error' position by making the error move
        try:
            board = chess.Board(before_fen)
            error_chess_move = chess.Move.from_uci(error_move)
            board.push(error_chess_move)
            self.positions["error"] = board.fen()
            
            # Calculate 'best move' position
            best_board = chess.Board(before_fen)
            best_chess_move = chess.Move.from_uci(best_move)
            best_board.push(best_chess_move)
            self.positions["best"] = best_board.fen()
        except Exception as e:
            print(f"Error calculating positions: {e}")
        
        # Show controls
        self.show_controls()
        
        # Start with 'before' state
        self.show_state("before")
    
    def _update_explanation(self, text):
        """Update the explanation text."""
        self.explanation_label.config(text=text)
    
    def _format_eval_change(self, eval_change):
        """Format evaluation change for display."""
        if eval_change > 0:
            return f"+{eval_change:.2f}"
        return f"{eval_change:.2f}"
    
    def _format_evaluation(self, eval_score):
        """Format evaluation score for display."""
        if eval_score > 0:
            return f"+{eval_score:.2f}"
        return f"{eval_score:.2f}"