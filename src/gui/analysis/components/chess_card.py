"""Chess move card component for the analysis view."""

import tkinter as tk
from tkinter import font
from src.utils import config
from src.gui.analysis.utils.style_utils import ensure_error_icon,set_card_state


class ChessCard:
    """A component that displays a chess move with evaluation and classification."""
    
    def __init__(self, parent, move_eval, move_index, view_instance):
        """Create a modern, high-contrast move card.
        
        Args:
            parent: Parent widget
            move_eval: Move evaluation data
            move_index: Index of this move
            view_instance: The parent view for event handling
        """
        self.parent = parent
        self.move_eval = move_eval
        self.move_index = move_index
        self.view_instance = view_instance
        self.is_white = move_index % 2 == 0
        self.is_error = move_eval["classification"] in ["Erreur", "Grosse erreur"]
        self.error_active = False
        self.selected = False
        self.has_error_icon = False
        self.classification = move_eval["classification"]
        
        # Card styles based on white/black move
        if self.is_white:
            # White move - light theme
            self.bg_color = config.COLORS["white_move_background"]
            self.hover_color = config.COLORS["white_move_hover"]
            self.text_color = config.COLORS["white_move_text"]
            self.secondary_text_color = config.COLORS["white_move_secondary_text"]
            self.border_color = config.COLORS["white_move_border"]
            self.highlight_bg = config.COLORS["white_move_highlight"]
        else:
            # Black move - dark theme
            self.bg_color = config.COLORS["black_move_background"]
            self.hover_color = config.COLORS["black_move_hover"]
            self.text_color = config.COLORS["black_move_text"]
            self.secondary_text_color = config.COLORS["black_move_secondary_text"]
            self.border_color = config.COLORS["black_move_border"]
            self.highlight_bg = config.COLORS["black_move_highlight"]
        
        # Create the card widget
        self.create_card()
    
    def create_card(self):
        """Create the card with all its child widgets."""
        # Create card frame with subtle rounded corners and shadow effect
        self.card = tk.Frame(
            self.parent,
            bg=self.bg_color,
            highlightbackground=self.border_color,
            highlightthickness=1,
            padx=10,
            pady=8
        )
        
        # Store data for selection system
        self.card.move_index = self.move_index
        self.card.original_bg = self.bg_color
        self.card.selected = False
        
        # Store error status for card
        self.card.is_error = self.is_error
        self.card.error_active = False
        self.card.classification = self.classification
        
        # Container for the main move info
        move_container = tk.Frame(self.card, bg=self.bg_color)
        move_container.pack(fill=tk.X, expand=True)
        
        # --- LEFT SIDE: MOVE NOTATION ---
        move_info = tk.Frame(move_container, bg=self.bg_color)
        move_info.pack(side=tk.LEFT, fill=tk.Y, anchor="w")
        
        # Calculate the proper move number for display
        move_number = (self.move_index // 2) + 1
        
        # Check if a move_text is already provided in the evaluation
        if 'move_text' in self.move_eval and self.move_eval['move_text']:
            # Use the existing move_text (from engine analysis)
            display_text = self.move_eval['move_text']
        else:
            # Construct the move text with correct numbering
            move_prefix = f"{move_number}." if self.is_white else f"{move_number}..."
            display_text = f"{move_prefix} {self.move_eval['san']}"
        
        # Move in SAN notation without piece symbol
        move_label = tk.Label(
            move_info,
            text=display_text,
            font=font.Font(**config.FONTS["move_notation"]),
            bg=self.bg_color,
            fg=self.text_color,
            anchor="w"
        )
        move_label.pack(anchor="w")
        
        # --- RIGHT SIDE: EVALUATION & QUALITY ---
        eval_frame = tk.Frame(move_container, bg=self.bg_color)
        eval_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Get quality color, but adjust it for black's dark background
        quality_color = self.view_instance.game_analyzer.get_classification_color(self.classification)
        
        # Quality indicator with colored dot
        quality_frame = tk.Frame(eval_frame, bg=self.bg_color)
        quality_frame.pack(anchor="e", pady=(0, 4))
        
        # Colored dot for quality
        quality_dot = tk.Canvas(
            quality_frame,
            width=10,
            height=10,
            bg=self.bg_color,
            highlightthickness=0
        )
        quality_dot.pack(side=tk.LEFT, padx=(0, 5))

        # Draw the colored oval for quality
        dot_id = quality_dot.create_oval(0, 0, 10, 10, fill=quality_color, outline="")

        # Store the dot_id so we can reference it later
        quality_dot.parent_frame = quality_frame
        
        # Move quality text
        quality_label = tk.Label(
            quality_frame,
            text=self.classification,
            font=font.Font(**config.FONTS["move_quality"]),
            bg=self.bg_color,
            fg=self.text_color if self.is_white else config.COLORS["black_quality_text"]
        )
        quality_label.pack(side=tk.LEFT)
        
        # Format evaluation score
        formatted_score = f"+{abs(self.move_eval['score_after']):.2f}" if self.move_eval['score_after'] >= 0 else f"-{abs(self.move_eval['score_after']):.2f}"
        
        # Evaluation score
        eval_label = tk.Label(
            eval_frame,
            text=formatted_score,
            font=font.Font(**config.FONTS["move_evaluation"]),
            bg=self.bg_color,
            fg=self.text_color
        )
        eval_label.pack(anchor="e")
        
        # If there's a better move, show it below the played move
        best_frame = None
        icon_label = None
        best_label = None
        change_label = None
        
        if self.move_eval["best_move"] and self.move_eval["best_move"] != self.move_eval["san"]:
            # Score change indicator
            change_color = config.COLORS["negative_score"] if self.move_eval["score_change"] < 0 else config.COLORS["positive_score"]
            # For black on dark theme, use brighter colors
            if not self.is_white:
                change_color = config.COLORS["black_negative_score"] if self.move_eval["score_change"] < 0 else config.COLORS["black_positive_score"]
                
            best_frame = tk.Frame(move_info, bg=self.bg_color)
            best_frame.pack(anchor="w", pady=(2, 0))
            
            # Icon or symbol to indicate "better move"
            icon_label = tk.Label(
                best_frame,
                text="→",  # Arrow symbol
                font=font.Font(**config.FONTS["move_details"]),
                bg=self.bg_color,
                fg=self.secondary_text_color
            )
            icon_label.pack(side=tk.LEFT)
            
            # Best move text
            best_label = tk.Label(
                best_frame,
                text=self.move_eval["best_move"],
                font=font.Font(**config.FONTS["move_details"]),
                bg=self.bg_color,
                fg=self.secondary_text_color
            )
            best_label.pack(side=tk.LEFT)
            
            # Format score change
            change_text = f" ({self.move_eval['score_change']:.2f})" if abs(self.move_eval['score_change']) >= 0.1 else ""
            
            # Add score change if significant
            if change_text:
                change_label = tk.Label(
                    best_frame,
                    text=change_text,
                    font=font.Font(**config.FONTS["move_details"]),
                    bg=self.bg_color,
                    fg=change_color
                )
                change_label.pack(side=tk.LEFT)
        
        # Store all labels for highlighting
        self.card.labels = [
            move_label, quality_dot, quality_label, eval_label, move_container,
            move_info, eval_frame
        ]
        
        if best_frame:
            self.card.labels.extend([best_frame, icon_label, best_label])
            if change_label:
                self.card.labels.append(change_label)
        
        # Add error icon if this is an error move
        if self.is_error:
            ensure_error_icon(self.card, self.classification)
        
        # Bind events to card and all its children
        self.bind_events()

    def bind_events(self):
        """Bind mouse and click events to the card and its children."""
        self.card.bind("<Enter>", self.on_enter)
        self.card.bind("<Leave>", self.on_leave)
        self.card.bind("<Button-1>", self.on_click)
        
        for label in self.card.labels:
            if hasattr(label, 'bind'):
                label.bind("<Enter>", self.on_enter)
                label.bind("<Leave>", self.on_leave)
                label.bind("<Button-1>", self.on_click)
    
    def on_enter(self, event):
        """Gère l'entrée de souris sur une carte."""
        set_card_state(self.card, {'hover': True})
    
    def on_leave(self, event):
        """Gère la sortie de souris d'une carte."""
        set_card_state(self.card, {'hover': False})
    
    def on_click(self, event):
        """Handle click event."""
        # Delegate to view instance which manages selection across all cards
        self.view_instance._on_move_selected(event, self.move_index, self.move_eval, self.card)
    
    def pack(self, **kwargs):
        """Pack the card frame."""
        self.card.pack(**kwargs)
    
    def get_widget(self):
        """Return the Tkinter widget for this card."""
        return self.card


def create_move_cards(parent, move_evaluations, view_instance, text_font, card_width=220, card_height=75):
    """Create all move cards for the moves list.
    
    Args:
        parent: Parent frame for cards
        move_evaluations: List of move evaluation data
        view_instance: View instance for event handling
        text_font: Font for text elements
        card_width: Width of each card
        card_height: Height of each card
        
    Returns:
        Tuple of (all_cards, error_cards)
    """
    # Store all cards and error cards for selection management
    all_cards = []
    error_cards = []
    
    # Create rows for moves (paired by white and black)
    current_row = None
    move_number = 1

    for i, move_eval in enumerate(move_evaluations):
        is_white = i % 2 == 0
        
        # Start a new row for each pair (white move)
        if is_white:
            # Create a row with move number and placeholders for white and black moves
            row_frame = tk.Frame(parent, bg=config.COLORS["background"], pady=3)
            row_frame.pack(fill=tk.X)
            
            # Move number
            number_label = tk.Label(
                row_frame,
                text=str(move_number),
                font=text_font,
                bg=config.COLORS["background"],
                fg=config.COLORS["move_number"],
                width=3
            )
            number_label.pack(side=tk.LEFT, anchor="n", padx=(5, 0))
            
            # Fixed-width containers for white and black moves
            white_container = tk.Frame(row_frame, bg=config.COLORS["background"], width=card_width, height=card_height)
            white_container.pack(side=tk.LEFT, padx=5)
            white_container.pack_propagate(False)  # Prevent shrinking to fit content
            
            black_container = tk.Frame(row_frame, bg=config.COLORS["background"], width=card_width, height=card_height)
            black_container.pack(side=tk.LEFT, padx=5)
            black_container.pack_propagate(False)  # Prevent shrinking to fit content
            
            current_row = (white_container, black_container)
            move_number += 1
        
        # Create move card and add to appropriate container
        container = current_row[0] if is_white else current_row[1]
        card = ChessCard(container, move_eval, i, view_instance)
        card.pack(fill=tk.BOTH, expand=True)  # Fill both width and height
        
        # Add to tracking lists
        all_cards.append(card.get_widget())
        
        # Track error cards for navigation
        if move_eval["classification"] in ["Erreur", "Grosse erreur"]:
            error_cards.append(card.get_widget())
    
    return all_cards, error_cards
