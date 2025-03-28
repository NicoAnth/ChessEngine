"""Moves analysis tab components for chess analysis."""

import tkinter as tk
from tkinter import ttk, font
import chess
from src.utils import config
from src.gui.analysis.mini_board import MiniChessBoard

def _create_moves_tab_content(view_instance, moves_frame_parent, move_evaluations, text_font):
    """Create the detailed moves analysis tab content with a mini-board."""

    # Set fixed card dimensions
    CARD_WIDTH = 220  # Fixed width for consistency
    CARD_HEIGHT = 75  # Minimum height for consistency

    # Create paned window to split the tab
    paned_window = ttk.PanedWindow(moves_frame_parent, orient=tk.HORIZONTAL)
    paned_window.pack(fill=tk.BOTH, expand=True)
    
    # Create frame for move list (left side)
    moves_frame = tk.Frame(paned_window, bg=config.COLORS["background"])
    
    # Create frame for mini-board (right side)
    board_frame = tk.Frame(paned_window, bg=config.COLORS["background"], padx=10, pady=10)
    
    # Add both frames to the paned window
    paned_window.add(moves_frame, weight=1)
    paned_window.add(board_frame, weight=1)
    
    # Count errors and mistakes for the badge
    error_moves = [move for move in move_evaluations 
                  if move["classification"] in ["Erreur", "Grosse erreur"]]
    error_count = len(error_moves)
    
    # Create error badge and navigation bar if errors exist
    error_navigation = None
    if error_count > 0:
        error_navigation = _create_error_navigation(
            moves_frame, error_moves, error_count, view_instance, move_evaluations
        )
    
    # Create scrollable canvas for moves list
    canvas_frame = tk.Frame(moves_frame, bg=config.COLORS["background"])
    canvas_frame.pack(fill=tk.BOTH, expand=True)
    
    moves_canvas = tk.Canvas(
        canvas_frame, 
        bg=config.COLORS["background"],
        highlightthickness=0,
        bd=0
    )
    
    # Modern scrollbar
    scrollbar = tk.Scrollbar(
        canvas_frame, 
        orient="vertical", 
        command=moves_canvas.yview,
        width=8,
        bd=0,
        highlightthickness=0,
        troughcolor="#EAEAEA",
        bg=config.COLORS["background"],
        activebackground=config.COLORS["selected_square"]
    )
    
    # Inner content frame
    content_frame = tk.Frame(moves_canvas, bg=config.COLORS["background"])
    
    # Add mouse wheel scrolling support with boundary checking
    def _on_mousewheel(event):
        # Check if we can scroll in the requested direction
        if (event.delta > 0 and moves_canvas.yview()[0] <= 0) or \
        (event.delta < 0 and moves_canvas.yview()[1] >= 1):
            return  # Prevent scrolling beyond boundaries
        # For Windows
        moves_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def _on_linux_scroll_up(event):
        # Check if at top boundary
        if moves_canvas.yview()[0] <= 0:
            return  # Prevent scrolling up when already at top
        moves_canvas.yview_scroll(-1, "units")
        
    def _on_linux_scroll_down(event):
        # Check if at bottom boundary
        if moves_canvas.yview()[1] >= 1:
            return  # Prevent scrolling down when already at bottom
        moves_canvas.yview_scroll(1, "units")
    
    # Update scroll region function
    def update_scrollregion(event=None):
        # Get the total height of the content
        content_height = content_frame.winfo_reqheight()
        canvas_height = moves_canvas.winfo_height()
        
        # Set minimum scrollregion height to match canvas height
        height = max(content_height, canvas_height)
        
        # Update the scrollregion
        moves_canvas.configure(scrollregion=(0, 0, content_frame.winfo_reqwidth(), height))
        
        # Disable scrollbar if content fits entirely within the canvas
        if content_height <= canvas_height:
            scrollbar.pack_forget()
        else:
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    # Configure content frame to update scroll region
    content_frame.bind("<Configure>", update_scrollregion)
    
    # Add binding for canvas resize
    def resize_canvas(event):
        # Update the width of the scrollable window to match canvas width
        canvas_width = event.width
        moves_canvas.itemconfig(window_id, width=canvas_width)
        
        # Update the scroll region when canvas is resized
        update_scrollregion()
    
    moves_canvas.bind("<Configure>", resize_canvas)
    
    # Bind mouse wheel events
    moves_canvas.bind("<MouseWheel>", _on_mousewheel)
    content_frame.bind("<MouseWheel>", _on_mousewheel)
    moves_canvas.bind("<Button-4>", _on_linux_scroll_up)
    moves_canvas.bind("<Button-5>", _on_linux_scroll_down)
    content_frame.bind("<Button-4>", _on_linux_scroll_up)
    content_frame.bind("<Button-5>", _on_linux_scroll_down)
    
    # Ensure canvas can receive focus for mouse wheel events
    moves_canvas.bind("<Enter>", lambda event: moves_canvas.focus_set())
    
    window_id = moves_canvas.create_window((0, 0), window=content_frame, anchor="nw")
    moves_canvas.configure(yscrollcommand=scrollbar.set)
    
    # Pack the canvas and scrollbar in modern way
    moves_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    # Title for the moves section
    title_frame = tk.Frame(content_frame, bg=config.COLORS["background"], pady=10)
    title_frame.pack(fill=tk.X)
    
    title_label = tk.Label(
        title_frame, 
        text="Coups",
        font=font.Font(**config.FONTS["moves_title"]),
        bg=config.COLORS["background"],
        fg=config.COLORS["primary_text"]
    )
    title_label.pack(side=tk.LEFT, padx=15)
    
    # Create the moves history with a modern design
    moves_list_frame = tk.Frame(content_frame, bg=config.COLORS["background"], padx=15, pady=5)
    moves_list_frame.pack(fill=tk.BOTH, expand=True)
    
    # Header row
    header_frame = tk.Frame(moves_list_frame, bg=config.COLORS["header_background"], padx=10, pady=8)
    header_frame.pack(fill=tk.X)
    
    header_font = font.Font(**config.FONTS["moves_header"])
    
    # Main headers
    tk.Label(
        header_frame,
        text="#",
        font=header_font,
        bg=config.COLORS["header_background"],
        fg=config.COLORS["header_text"],
        width=3
    ).pack(side=tk.LEFT)
    
    # Create two sections - White and Black
    white_section = tk.Frame(header_frame, bg=config.COLORS["header_background"])
    white_section.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(5, 15))
    
    black_section = tk.Frame(header_frame, bg=config.COLORS["header_background"])
    black_section.pack(side=tk.LEFT, expand=True, fill=tk.X)
    
    # White header
    white_header = tk.Label(
        white_section,
        text="♔ Blancs",
        font=header_font,
        bg=config.COLORS["header_background"],
        fg=config.COLORS["header_text"],
        anchor="w"
    )
    white_header.pack(side=tk.LEFT, padx=(0, 10))
    
    # Black header
    black_header = tk.Label(
        black_section,
        text="♚ Noirs",
        font=header_font,
        bg=config.COLORS["header_background"],
        fg=config.COLORS["header_text"],
        anchor="w"
    )
    black_header.pack(side=tk.LEFT, padx=(0, 10))
    
    # Separator below header
    separator = tk.Frame(moves_list_frame, height=1, bg=config.COLORS["separator"])
    separator.pack(fill=tk.X, pady=(0, 5))
    
    # Create the container for move rows
    moves_container = tk.Frame(moves_list_frame, bg=config.COLORS["background"])
    moves_container.pack(fill=tk.BOTH, expand=True)
    
    # Function to create a move card
    def create_move_card(parent, move_eval, move_index):
        """Create a modern, high-contrast move card.
        
        Args:
            parent: Parent widget
            move_eval: Move evaluation data
            move_index: Index of this move
        """
        # Determine if move is white or black
        is_white = move_index % 2 == 0
        
        # Card colors - dramatic contrast between white and black moves
        if is_white:
            # White move - light theme
            bg_color = config.COLORS["white_move_background"]
            hover_color = config.COLORS["white_move_hover"]
            text_color = config.COLORS["white_move_text"]
            secondary_text_color = config.COLORS["white_move_secondary_text"]
            border_color = config.COLORS["white_move_border"]
            highlight_bg = config.COLORS["white_move_highlight"]
        else:
            # Black move - dark theme
            bg_color = config.COLORS["black_move_background"]
            hover_color = config.COLORS["black_move_hover"]
            text_color = config.COLORS["black_move_text"]
            secondary_text_color = config.COLORS["black_move_secondary_text"]
            border_color = config.COLORS["black_move_border"]
            highlight_bg = config.COLORS["black_move_highlight"]
        
        # Create card frame with subtle rounded corners and shadow effect
        card = tk.Frame(
            parent,
            bg=bg_color,
            highlightbackground=border_color,
            highlightthickness=1,
            padx=10,
            pady=8
        )
        
        # Store data for selection system
        card.move_index = move_index
        card.original_bg = bg_color
        card.selected = False
        
        # Store error status for card
        card.is_error_move = move_eval["classification"] in ["Erreur", "Grosse erreur"]
        card.error_mode = False  # Track if currently in error mode
        card.error_color = None  # Store error color if applied
        
        # Container for the main move info
        move_container = tk.Frame(card, bg=bg_color)
        move_container.pack(fill=tk.X, expand=True)
        
        # --- LEFT SIDE: MOVE NOTATION ---
        move_info = tk.Frame(move_container, bg=bg_color)
        move_info.pack(side=tk.LEFT, fill=tk.Y, anchor="w")
        
        # Calculate the proper move number for display
        move_number = (move_index // 2) + 1
        
        # Check if a move_text is already provided in the evaluation
        if 'move_text' in move_eval and move_eval['move_text']:
            # Use the existing move_text (from engine analysis)
            display_text = move_eval['move_text']
        else:
            # Construct the move text with correct numbering
            move_prefix = f"{move_number}." if is_white else f"{move_number}..."
            display_text = f"{move_prefix} {move_eval['san']}"
        
        # Add piece symbol if needed (enhance visual representation)
        if move_eval["san"][0] in ["N", "B", "R", "Q", "K"]:
            if is_white:
                piece_map = {"N": "♘", "B": "♗", "R": "♖", "Q": "♕", "K": "♔"}
                piece_symbol = piece_map.get(move_eval["san"][0], "")
            else:
                piece_map = {"N": "♞", "B": "♝", "R": "♜", "Q": "♛", "K": "♚"}
                piece_symbol = piece_map.get(move_eval["san"][0], "")
            
            # Only modify display text if it doesn't already have a piece symbol
            if piece_symbol and "♔" not in display_text and "♚" not in display_text:
                # Extract the SAN part after the move number
                parts = display_text.split(" ", 1)
                if len(parts) > 1:
                    prefix, san = parts
                    # Replace first character of SAN with piece symbol
                    display_text = f"{prefix} {piece_symbol}{san[1:]}" if len(san) > 1 else f"{prefix} {piece_symbol}"
        
        # Move in SAN notation with piece symbol
        move_label = tk.Label(
            move_info,
            text=display_text,
            font=font.Font(**config.FONTS["move_notation"]),
            bg=bg_color,
            fg=text_color,
            anchor="w"
        )
        move_label.pack(anchor="w")
        
        # --- RIGHT SIDE: EVALUATION & QUALITY ---
        eval_frame = tk.Frame(move_container, bg=bg_color)
        eval_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Get quality color, but adjust it for black's dark background
        quality_color = view_instance.game_analyzer.get_classification_color(move_eval["classification"])
        if not is_white and move_eval["classification"] in ["Imprécision", "Erreur", "Grosse erreur"]:
            # Make error colors brighter on dark background
            quality_color = quality_color  # Already bright enough
        
        # Quality indicator with colored dot
        quality_frame = tk.Frame(eval_frame, bg=bg_color)
        quality_frame.pack(anchor="e", pady=(0, 4))
        
        # Colored dot for quality
        quality_dot = tk.Canvas(
            quality_frame,
            width=10,
            height=10,
            bg=bg_color,
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
            text=move_eval["classification"],
            font=font.Font(**config.FONTS["move_quality"]),
            bg=bg_color,
            fg=text_color if is_white else config.COLORS["black_quality_text"]
        )
        quality_label.pack(side=tk.LEFT)
        
        # Format evaluation score
        formatted_score = f"+{abs(move_eval['score_after']):.2f}" if move_eval['score_after'] >= 0 else f"-{abs(move_eval['score_after']):.2f}"
        
        # Evaluation score
        eval_label = tk.Label(
            eval_frame,
            text=formatted_score,
            font=font.Font(**config.FONTS["move_evaluation"]),
            bg=bg_color,
            fg=text_color
        )
        eval_label.pack(anchor="e")
        
        # If there's a better move, show it below the played move
        if move_eval["best_move"] and move_eval["best_move"] != move_eval["san"]:
            # Score change indicator
            change_color = config.COLORS["negative_score"] if move_eval["score_change"] < 0 else config.COLORS["positive_score"]
            # For black on dark theme, use brighter colors
            if not is_white:
                change_color = config.COLORS["black_negative_score"] if move_eval["score_change"] < 0 else config.COLORS["black_positive_score"]
                
            best_frame = tk.Frame(move_info, bg=bg_color)
            best_frame.pack(anchor="w", pady=(2, 0))
            
            # Icon or symbol to indicate "better move"
            icon_label = tk.Label(
                best_frame,
                text="→",  # Arrow symbol
                font=font.Font(**config.FONTS["move_details"]),
                bg=bg_color,
                fg=secondary_text_color
            )
            icon_label.pack(side=tk.LEFT)
            
            # Best move text
            best_label = tk.Label(
                best_frame,
                text=move_eval["best_move"],
                font=font.Font(**config.FONTS["move_details"]),
                bg=bg_color,
                fg=secondary_text_color
            )
            best_label.pack(side=tk.LEFT)
            
            # Format score change
            change_text = f" ({move_eval['score_change']:.2f})" if abs(move_eval['score_change']) >= 0.1 else ""
            
            # Add score change if significant
            if change_text:
                change_label = tk.Label(
                    best_frame,
                    text=change_text,
                    font=font.Font(**config.FONTS["move_details"]),
                    bg=bg_color,
                    fg=change_color
                )
                change_label.pack(side=tk.LEFT)
        
        # Store all labels for highlighting
        card.labels = [
            move_label, quality_dot, quality_label, eval_label, move_container,
            move_info, eval_frame
        ]
        
        if 'best_frame' in locals():
            card.labels.extend([best_frame, icon_label, best_label])
            if 'change_label' in locals():
                card.labels.append(change_label)
        
        # Hover effect
        def on_enter(e):
            if card.selected:
                return
                
            # If card is in error mode, use a darker version of the error color on hover
            if card.error_mode and card.error_color:
                # Darken the error color slightly for hover effect
                if card.error_color == "#FFCDD2":  # Red for blunder
                    hover_error_color = "#EFBEC3"  # Darker red
                    hover_error_text = "#C62828"   # Darker red text
                else:  # "#FFE0B2" - Orange for error
                    hover_error_color = "#EFD1A3"  # Darker orange
                    hover_error_text = "#E65100"   # Darker orange text
                    
                # Apply hover colors that maintain error context
                card.config(bg=hover_error_color)
                for label in card.labels:
                    if hasattr(label, 'config'):
                        try:
                            # Apply hover background that matches the error theme
                            if label.winfo_class() == "Canvas":
                                label.config(bg=hover_error_color)
                                if hasattr(label, 'parent_frame'):
                                    label.parent_frame.config(bg=hover_error_color)
                            else:
                                label.config(bg=hover_error_color)
                                
                                # Only update text color for labels that aren't special indicators
                                if label.winfo_class() == "Label" and hasattr(label, 'cget'):
                                    # Skip quality label which should keep its red/orange color
                                    label_text = label.cget('text')
                                    if label_text not in ["Erreur", "Grosse erreur"]:
                                        label.config(fg=hover_error_text)
                        except:
                            pass
            else:
                # Normal hover behavior for non-error moves
                card.config(bg=hover_color)
                for label in card.labels:
                    if hasattr(label, 'config'):
                        try:
                            # Special handling for Canvas elements
                            if label.winfo_class() == "Canvas":
                                label.config(bg=hover_color)
                                # Make sure the parent frame changes color too if it exists
                                if hasattr(label, 'parent_frame'):
                                    label.parent_frame.config(bg=hover_color)
                            else:
                                label.config(bg=hover_color)
                        except:
                            pass
        
        def on_leave(e):
            if card.selected:
                return
                
            # If card is in error mode, restore the original error color
            if card.error_mode and card.error_color:
                card.config(bg=card.error_color)
                for label in card.labels:
                    if hasattr(label, 'config'):
                        try:
                            # Restore the error color scheme
                            if label.winfo_class() == "Canvas":
                                label.config(bg=card.error_color)
                                if hasattr(label, 'parent_frame'):
                                    label.parent_frame.config(bg=card.error_color)
                            else:
                                label.config(bg=card.error_color)
                                
                                # Only update text color for labels that aren't special indicators
                                if label.winfo_class() == "Label" and hasattr(label, 'cget'):
                                    # Skip quality label which should keep its red/orange color
                                    label_text = label.cget('text')
                                    if label_text not in ["Erreur", "Grosse erreur"]:
                                        # Restore to the error text color
                                        if card.error_color == "#FFCDD2":  # Red background
                                            label.config(fg="#D32F2F")  # Red text
                                        else:  # Orange background
                                            label.config(fg="#F57C00")  # Orange text
                        except:
                            pass
            else:
                # Normal leave behavior for non-error moves
                card.config(bg=bg_color)
                for label in card.labels:
                    if hasattr(label, 'config'):
                        try:
                            # Special handling for Canvas elements
                            if label.winfo_class() == "Canvas":
                                label.config(bg=bg_color)
                                # Make sure the parent frame changes color too if it exists
                                if hasattr(label, 'parent_frame'):
                                    label.parent_frame.config(bg=bg_color)
                            else:
                                label.config(bg=bg_color)
                        except:
                            pass

        # Click handler for selecting the move
        def on_click(e, idx=move_index, eval=move_eval):
            view_instance._on_move_selected(e, idx, eval, card)
            
            # Update selected state for all cards
            for c in all_cards:
                c.selected = (c == card)
                # Preserve error coloring when deselecting cards in error mode
                if c.selected:
                    # Selected card gets highlight color, but we modify it if it's an error
                    if c.error_mode and c.error_color:
                        # Use a highlighted version of the error color
                        if c.error_color == "#FFCDD2":  # Red for blunder
                            highlight_error_bg = "#EF9A9A"  # Brighter red
                        else:  # "#FFE0B2" - Orange for error 
                            highlight_error_bg = "#FFCC80"  # Brighter orange
                            
                        c.config(bg=highlight_error_bg)
                        for lbl in c.labels:
                            if hasattr(lbl, 'config'):
                                try:
                                    if lbl.winfo_class() == "Canvas":
                                        lbl.config(bg=highlight_error_bg)
                                        if hasattr(lbl, 'parent_frame'):
                                            lbl.parent_frame.config(bg=highlight_error_bg)
                                    else:
                                        lbl.config(bg=highlight_error_bg)
                                except:
                                    pass
                    else:
                        # Normal highlight for non-error cards
                        c.config(bg=highlight_bg)
                        for lbl in c.labels:
                            if hasattr(lbl, 'config'):
                                try:
                                    # Special handling for Canvas elements when selected
                                    if lbl.winfo_class() == "Canvas":
                                        lbl.config(bg=highlight_bg)
                                        # Make sure the parent frame changes color too if it exists
                                        if hasattr(lbl, 'parent_frame'):
                                            lbl.parent_frame.config(bg=highlight_bg)
                                    else:
                                        lbl.config(bg=highlight_bg)
                                except:
                                    pass
                else:
                    # For non-selected cards, restore to appropriate state
                    if c.error_mode and c.error_color:
                        # Restore to error color
                        c.config(bg=c.error_color)
                        for lbl in c.labels:
                            if hasattr(lbl, 'config'):
                                try:
                                    if lbl.winfo_class() == "Canvas":
                                        lbl.config(bg=c.error_color)
                                        if hasattr(lbl, 'parent_frame'):
                                            lbl.parent_frame.config(bg=c.error_color)
                                    else:
                                        lbl.config(bg=c.error_color)
                                except:
                                    pass
                    else:
                        # Reset to original background
                        c.config(bg=c.original_bg)
                        for lbl in c.labels:
                            if hasattr(lbl, 'config'):
                                try:
                                    # Special handling for Canvas elements when deselected
                                    if lbl.winfo_class() == "Canvas":
                                        lbl.config(bg=c.original_bg)
                                        # Make sure the parent frame changes color too if it exists
                                        if hasattr(lbl, 'parent_frame'):
                                            lbl.parent_frame.config(bg=c.original_bg)
                                    else:
                                        lbl.config(bg=c.original_bg)
                                except:
                                    pass
        
        # Bind events to card and all its children
        card.bind("<Enter>", on_enter)
        card.bind("<Leave>", on_leave)
        card.bind("<Button-1>", on_click)
        
        for label in card.labels:
            if hasattr(label, 'bind'):
                label.bind("<Enter>", on_enter)
                label.bind("<Leave>", on_leave)
                label.bind("<Button-1>", on_click)
        
        return card
    
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
            row_frame = tk.Frame(moves_container, bg=config.COLORS["background"], pady=3)
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
            white_container = tk.Frame(row_frame, bg=config.COLORS["background"], width=CARD_WIDTH, height=CARD_HEIGHT)
            white_container.pack(side=tk.LEFT, padx=5)
            white_container.pack_propagate(False)  # Prevent shrinking to fit content
            
            black_container = tk.Frame(row_frame, bg=config.COLORS["background"], width=CARD_WIDTH, height=CARD_HEIGHT)
            black_container.pack(side=tk.LEFT, padx=5)
            black_container.pack_propagate(False)  # Prevent shrinking to fit content
            
            current_row = (white_container, black_container)
            move_number += 1
        
        # Create move card and add to appropriate container
        container = current_row[0] if is_white else current_row[1]
        card = create_move_card(container, move_eval, i)
        card.pack(fill=tk.BOTH, expand=True)  # Fill both width and height
        all_cards.append(card)
        
        # Track error cards for navigation
        if move_eval["classification"] in ["Erreur", "Grosse erreur"]:
            error_cards.append(card)
            # Add error icon to the card
            _add_error_icon(card, move_eval)
    
    # Store error cards in the view instance for navigation
    view_instance.error_cards = error_cards
    view_instance.all_cards = all_cards
    view_instance.current_error_index = 0
    
    # Create mini-board in the right frame
    view_instance._create_mini_board(board_frame, move_evaluations)
    
    # Simple keyboard navigation implementation
    def bind_keyboard_navigation():
        # Store currently selected index for navigation
        nav_state = {'current_index': -1}
        
        # Function to select a specific card by index with improved scrolling
        def select_card_by_index(index):
            if 0 <= index < len(all_cards):
                # Get the card at this index
                card = all_cards[index]
                
                # First scroll to ensure visibility BEFORE triggering the click
                try:
                    # Calculate the row based on index (each row has 2 moves)
                    row = index // 2
                    
                    # Calculate approximate y position based on row number and card height
                    # This is more reliable than trying to use winfo_y()
                    estimated_y = row * (CARD_HEIGHT + 6)  # 6px for padding
                    
                    # Get visible area
                    visible_top = moves_canvas.yview()[0] * content_frame.winfo_height()
                    visible_bottom = visible_top + moves_canvas.winfo_height()
                    
                    # Calculate center of visible area
                    visible_center = visible_top + (moves_canvas.winfo_height() / 2)
                    
                    # Add a buffer to scroll earlier - scroll if card is not in the middle area
                    # This makes scrolling more proactive
                    buffer = moves_canvas.winfo_height() * 0.3  # 30% buffer on either side
                    
                    if (estimated_y < visible_center - buffer) or (estimated_y > visible_center + buffer):
                        # Calculate fraction to position card vertically centered in view
                        fraction = (estimated_y - (moves_canvas.winfo_height() / 2)) / content_frame.winfo_height()
                        fraction = max(0, min(1, fraction))  # Clamp between 0-1
                        
                        # Apply scrolling
                        moves_canvas.yview_moveto(fraction)
                        # Force update to ensure scrolling takes effect immediately
                        moves_canvas.update()
                except Exception as e:
                    # Fail silently to keep navigation working
                    pass
                
                # Now trigger click on this card after scrolling is complete
                card.event_generate('<Button-1>')
                
                # Update our state
                nav_state['current_index'] = index
                return True
            return False
        
        # Handler for arrow key navigation
        def navigate(event):
            # First, ensure we have the most up-to-date selected card
            current = -1
            for i, card in enumerate(all_cards):
                if card.selected:
                    current = i
                    nav_state['current_index'] = i
                    break
            
            # Use the current selection, or -1 if nothing is selected
            current = current if current >= 0 else nav_state['current_index']
            
            # Calculate new index based on key
            if event.keysym in ('Right', 'Down'):
                # Next move
                new_index = current + 1 if current >= 0 else 0
            elif event.keysym in ('Left', 'Up'):
                # Previous move
                new_index = current - 1 if current > 0 else 0
            else:
                return
                
            # Select the card at the new index if valid
            if 0 <= new_index < len(all_cards) and new_index != current:
                select_card_by_index(new_index)
        
        # Add a hook to the original _on_move_selected function to update nav_state
        original_on_move_selected = view_instance._on_move_selected
        
        def on_move_selected_with_nav_tracking(event, idx, eval_data, card):
            # Call the original handler first
            original_on_move_selected(event, idx, eval_data, card)
            
            # Now update our navigation state
            for i, c in enumerate(all_cards):
                if c == card:
                    nav_state['current_index'] = i
                    break
        
        # Replace the handler with our tracking version
        view_instance._on_move_selected = on_move_selected_with_nav_tracking
        
        # Bind keyboard events to the window
        root = moves_frame_parent.winfo_toplevel()
        root.bind('<Left>', navigate)
        root.bind('<Right>', navigate)
        root.bind('<Up>', navigate)
        root.bind('<Down>', navigate)
        
        # Set initial focus
        moves_frame_parent.focus_set()
    
    # Set up navigation
    bind_keyboard_navigation()
    
    # Save references to allow controlling error mode from outside
    view_instance.error_navigation = error_navigation
    
    # Recursively bind mousewheel to all widgets
    view_instance._bind_mousewheel_to_widgets(content_frame, _on_mousewheel, _on_linux_scroll_up, _on_linux_scroll_down)
    
    # Initial update of the scroll region
    content_frame.update_idletasks()  # Ensure content frame has been laid out
    update_scrollregion()

def _create_error_navigation(parent, error_moves, error_count, view_instance, move_evaluations):
    """Create an elegant error navigation bar."""
    # Container for error navigation
    nav_container = tk.Frame(parent, bg=config.COLORS["background"], padx=10, pady=10)
    nav_container.pack(fill=tk.X)
    
    # Error badge with count
    badge_frame = tk.Frame(
        nav_container,
        bg=config.COLORS["blunder"],
        padx=8,
        pady=3,
        bd=0,
        highlightthickness=0
    )
    badge_frame.pack(side=tk.LEFT, padx=(0, 10))
    
    # Badge text
    badge_text = f"{error_count} erreur{'s' if error_count > 1 else ''} détectée{'s' if error_count > 1 else ''}"
    badge_label = tk.Label(
        badge_frame,
        text=badge_text,
        font=font.Font(**config.FONTS["move_quality"]),
        bg=config.COLORS["blunder"],
        fg="white"
    )
    badge_label.pack()
    
    # Navigation controls container
    controls_frame = tk.Frame(nav_container, bg=config.COLORS["background"])
    controls_frame.pack(side=tk.RIGHT)
    
    # Toggle switch for error mode
    toggle_var = tk.BooleanVar(value=False)
    toggle_frame = tk.Frame(controls_frame, bg=config.COLORS["background"])
    toggle_frame.pack(side=tk.LEFT, padx=(0, 15))
    
    # Toggle label
    toggle_label = tk.Label(
        toggle_frame,
        text="Afficher les erreurs",
        font=font.Font(**config.FONTS["move_details"]),
        bg=config.COLORS["background"],
        fg=config.COLORS["primary_text"]
    )
    toggle_label.pack(side=tk.LEFT, padx=(0, 5))
    
    # Add rounded rectangle function to Canvas (tkinter doesn't have this built-in)
    # IMPORTANT: Define this function BEFORE trying to use it
    def _create_rounded_rectangle(self, x1, y1, x2, y2, radius=25, **kwargs):
        points = [
            x1+radius, y1,
            x2-radius, y1,
            x2, y1,
            x2, y1+radius,
            x2, y2-radius,
            x2, y2,
            x2-radius, y2,
            x1+radius, y2,
            x1, y2,
            x1, y2-radius,
            x1, y1+radius,
            x1, y1
        ]
        return self.create_polygon(points, **kwargs, smooth=True)
    
    # Add the method to the Canvas class BEFORE using it
    tk.Canvas.create_rounded_rectangle = _create_rounded_rectangle
    
    # Toggle switch - redesigned with fully rounded shape
    switch_width = 44
    switch_height = 22
    switch_canvas = tk.Canvas(
        toggle_frame, 
        width=switch_width, 
        height=switch_height,
        bg=config.COLORS["background"],
        highlightthickness=0
    )
    switch_canvas.pack(side=tk.LEFT)
    
    # Now we can use the create_rounded_rectangle method
    switch_bg = switch_canvas.create_rounded_rectangle(
        2, 2, switch_width-2, switch_height-2,
        radius=switch_height//2,  # Make radius half the height for fully rounded ends
        fill="#CCCCCC", 
        outline="",
        tags="switch_bg"
    )
    
    # Draw switch knob (smaller than before to fit within the rounded track)
    knob_size = switch_height - 6
    knob_x = 4  # Starting x position (left side)
    knob = switch_canvas.create_oval(
        knob_x, 3, knob_x + knob_size, 3 + knob_size,
        fill="white", outline="", tags="knob"
    )
    
    # Function to update switch appearance
    def update_switch():
        if toggle_var.get():
            # ON state
            switch_canvas.itemconfig(
                "switch_bg", 
                fill=config.COLORS["control_button"]
            )
            # Move knob to right
            switch_canvas.coords(
                "knob", 
                switch_width - knob_size - 4, 3, 
                switch_width - 4, 3 + knob_size
            )
            # Apply error highlighting
            toggle_error_mode(True)
        else:
            # OFF state
            switch_canvas.itemconfig(
                "switch_bg", 
                fill="#CCCCCC"
            )
            # Move knob to left
            switch_canvas.coords("knob", 4, 3, 4 + knob_size, 3 + knob_size)
            # Remove error highlighting
            toggle_error_mode(False)
    
    # Toggle error mode function
    def toggle_error_mode(show_errors):
        for card in view_instance.all_cards:
            if not hasattr(card, 'move_index'):
                continue
                
            move_idx = card.move_index
            if move_idx >= len(move_evaluations):
                continue
                
            move_eval = move_evaluations[move_idx]
            is_error = move_eval["classification"] in ["Erreur", "Grosse erreur"]
            
            if show_errors:
                # Error mode - fade non-errors and highlight errors with color
                if not is_error and not card.selected:
                    _apply_opacity(card, 0.6)
                elif is_error:
                    _apply_opacity(card, 1.0)
                    # Highlight error cards with color instead of pulsing
                    _apply_error_color(card, move_eval["classification"])
            else:
                # Normal mode - restore all cards to original colors
                _apply_opacity(card, 1.0)
                _restore_original_colors(card)
        
        # Update error counter visibility
        counter_label.configure(fg=config.COLORS["primary_text"] if show_errors else "#CCCCCC")
        prev_button.configure(state=tk.NORMAL if show_errors else tk.DISABLED)
        next_button.configure(state=tk.NORMAL if show_errors else tk.DISABLED)
    
    # Click handler for the switch
    def toggle_click(event):
        toggle_var.set(not toggle_var.get())
        update_switch()
    
    # Bind click event to switch
    switch_canvas.bind("<Button-1>", toggle_click)
    
    # Error navigation controls
    nav_buttons_frame = tk.Frame(controls_frame, bg=config.COLORS["background"])
    nav_buttons_frame.pack(side=tk.LEFT)
    
    # Previous error button
    prev_button = tk.Button(
        nav_buttons_frame,
        text="◀",
        font=font.Font(size=10, weight="bold"),
        bg=config.COLORS["background"],
        fg=config.COLORS["primary_text"],
        activebackground=config.COLORS["white_move_hover"],
        bd=0,
        padx=5,
        pady=2,
        state=tk.DISABLED,
        command=lambda: navigate_errors("prev")
    )
    prev_button.pack(side=tk.LEFT)
    
    # Error counter 
    counter_var = tk.StringVar(value="0/0")
    counter_label = tk.Label(
        nav_buttons_frame,
        textvariable=counter_var,
        font=font.Font(**config.FONTS["move_notation"]),
        bg=config.COLORS["background"],
        fg="#CCCCCC",  # Starts disabled
        padx=10
    )
    counter_label.pack(side=tk.LEFT)
    
    # Next error button
    next_button = tk.Button(
        nav_buttons_frame,
        text="▶",
        font=font.Font(size=10, weight="bold"),
        bg=config.COLORS["background"],
        fg=config.COLORS["primary_text"],
        activebackground=config.COLORS["white_move_hover"],
        bd=0,
        padx=5,
        pady=2,
        state=tk.DISABLED,
        command=lambda: navigate_errors("next")
    )
    next_button.pack(side=tk.LEFT)
    
    # Initialize counter
    counter_var.set(f"0/{error_count}")
    
    # Error navigation function
    def navigate_errors(direction):
        if not view_instance.error_cards:
            return
            
        # Update current error index
        if direction == "next":
            view_instance.current_error_index = (view_instance.current_error_index + 1) % len(view_instance.error_cards)
        else: # prev
            view_instance.current_error_index = (view_instance.current_error_index - 1) % len(view_instance.error_cards)
            
        # Get the error card to navigate to
        error_card = view_instance.error_cards[view_instance.current_error_index]
        
        # Select the error card (this will update the board)
        error_card.event_generate('<Button-1>')
        
        # Update counter
        counter_var.set(f"{view_instance.current_error_index + 1}/{error_count}")
        
        # Ensure card is visible by scrolling to it
        _ensure_card_visible(error_card)
    
    # Function to ensure a card is visible in the scrollable area
    def _ensure_card_visible(card):
        # Will be implemented in the actual code
        pass
    
    # Store navigation controls for external access
    nav_controls = {
        "toggle_var": toggle_var,
        "counter_var": counter_var,
        "prev_button": prev_button,
        "next_button": next_button,
        "update_switch": update_switch
    }
    
    return nav_controls

def _apply_opacity(card, opacity):
    """Apply opacity effect to a card without changing its selection state."""
    if not card or not hasattr(card, 'labels') or card.selected:
        return
    
    # Apply graying effect to the card background
    try:
        # Calculate a grayed version of the background color
        original_bg = card.original_bg
        if original_bg.startswith('#'):
            r, g, b = int(original_bg[1:3], 16), int(original_bg[3:5], 16), int(original_bg[5:7], 16)
            # Create grayed background
            gray_level = (r + g + b) // 3
            r = int(r * 0.3 + gray_level * 0.7)
            g = int(g * 0.3 + gray_level * 0.7)
            b = int(b * 0.3 + gray_level * 0.7)
            grayed_bg = f'#{r:02x}{g:02x}{b:02x}'
            card.config(bg=grayed_bg)
        else:
            # For named colors, default to a light gray
            grayed_bg = "#E0E0E0"
            card.config(bg=grayed_bg)
    except Exception as e:
        print(f"Error applying opacity to card background: {e}")
    
    # Apply graying to all labels in the card
    for label in card.labels:
        if hasattr(label, 'config'):
            try:
                # Apply grayed background to match card
                if hasattr(label, 'winfo_class'):
                    if label.winfo_class() == "Canvas":
                        label.config(bg=grayed_bg)
                        if hasattr(label, 'parent_frame'):
                            label.parent_frame.config(bg=grayed_bg)
                    else:
                        label.config(bg=grayed_bg)
                
                # Gray out text colors too
                if hasattr(label, 'cget') and hasattr(label, 'winfo_class'):
                    if label.winfo_class() == "Label":
                        try:
                            current_fg = label.cget('fg')
                            if current_fg.startswith('#'):
                                # Convert hex to RGB, apply graying effect
                                r, g, b = int(current_fg[1:3], 16), int(current_fg[3:5], 16), int(current_fg[5:7], 16)
                                # Make more gray by mixing with gray
                                gray_level = (r + g + b) // 3
                                r = int(r * 0.3 + gray_level * 0.7)
                                g = int(g * 0.3 + gray_level * 0.7)
                                b = int(b * 0.3 + gray_level * 0.7)
                                grayed_text = f'#{r:02x}{g:02x}{b:02x}'
                                label.config(fg=grayed_text)
                        except tk.TclError:
                            pass
            except Exception as e:
                print(f"Error applying opacity to label: {e}")

def _add_error_icon(card, move_eval):
    """Add an error icon to a move card."""
    if not hasattr(card, 'move_container'):
        return
        
    # Create icon based on classification
    icon_text = "❌" if move_eval["classification"] == "Grosse erreur" else "⚠️"
    
    # Find the quality label to place icon next to it
    for label in card.labels:
        if hasattr(label, 'cget') and hasattr(label, 'winfo_class'):
            if label.winfo_class() == "Label" and label.cget('text') == move_eval["classification"]:
                # Get the parent frame
                parent = label.master
                
                # Create icon next to quality label
                icon_label = tk.Label(
                    parent,
                    text=icon_text,
                    font=font.Font(**config.FONTS["move_quality"]),
                    bg=card.original_bg,
                    fg=label.cget('fg')
                )
                icon_label.pack(side=tk.LEFT, padx=(0, 5))
                
                # Add to card labels for highlight management
                card.labels.append(icon_label)
                break

def _apply_error_color(card, classification):
    """Apply consistent error color to a card regardless of white/black."""
    if not card or card.selected:
        return
    
    # Use the same consistent colors for both white and black moves
    if classification == "Grosse erreur":
        # Blunder - for both white and black cards
        error_bg = "#FFCDD2"  # Light red background 
        error_text = "#D32F2F"  # Darker red text
    else:  # "Erreur"
        # Error - for both white and black cards
        error_bg = "#FFE0B2"  # Light orange background
        error_text = "#F57C00"  # Darker orange text
    
    # Store the error color for later reference
    card.error_color = error_bg
    card.error_mode = True
    
    # Apply colors to the card and all its labels
    card.configure(bg=error_bg)
    
    for label in card.labels:
        if hasattr(label, 'config'):
            try:
                # Apply error background to all components
                if label.winfo_class() == "Canvas":
                    label.config(bg=error_bg)
                    if hasattr(label, 'parent_frame'):
                        label.parent_frame.config(bg=error_bg)
                else:
                    label.config(bg=error_bg)
                    
                    # Only update text color for labels that aren't special indicators
                    if label.winfo_class() == "Label" and hasattr(label, 'cget'):
                        label_text = label.cget('text')
                        
                        # Quality label keeps its color based on classification
                        if label_text in ["Excellent", "Bon coup", "Imprécision", "Erreur", "Grosse erreur"]:
                            # Quality color already set correctly, skip
                            pass
                        # Score change label
                        elif label_text.startswith('(') and label_text.endswith(')'):
                            # This is likely a score change, skip as it has special coloring
                            pass
                        # Move notation or best move
                        else:
                            # For best move row which should use secondary text color
                            parent = label.master
                            if hasattr(parent, 'winfo_class') and parent.winfo_class() == "Frame":
                                # Check if this might be the best move container
                                for sibling in parent.winfo_children():
                                    if hasattr(sibling, 'cget') and hasattr(sibling, 'winfo_class'):
                                        if sibling.winfo_class() == "Label" and sibling.cget('text') == "→":
                                            label.config(fg=secondary_text_color)
                                            break
                                else:
                                    # Not part of best move, use primary text
                                    label.config(fg=error_text)
                            else:
                                # Default to primary text color
                                label.config(fg=error_text)
            except:
                pass

def _restore_original_colors(card):
    """Restore a card's original colors."""
    if not card:
        return
    
    # Reset error state
    card.error_mode = False
    card.error_color = None
    
    # Original background
    card.configure(bg=card.original_bg)
    
    # Determine if move is white or black for text color
    is_white = card.move_index % 2 == 0
    text_color = config.COLORS["white_move_text"] if is_white else config.COLORS["black_move_text"]
    secondary_text_color = config.COLORS["white_move_secondary_text"] if is_white else config.COLORS["black_move_secondary_text"]
    
    # Restore all labels
    for label in card.labels:
        if hasattr(label, 'config'):
            try:
                # Restore background color
                if label.winfo_class() == "Canvas":
                    label.config(bg=card.original_bg)
                    if hasattr(label, 'parent_frame'):
                        label.parent_frame.config(bg=card.original_bg)
                else:
                    label.config(bg=card.original_bg)
                    
                # Restore text color with specific handling for different label types
                if label.winfo_class() == "Label" and hasattr(label, 'cget'):
                    label_text = label.cget('text')
                    
                    # Quality label keeps its color based on classification
                    if label_text in ["Excellent", "Bon coup", "Imprécision", "Erreur", "Grosse erreur"]:
                        # Quality color already set correctly, skip
                        pass
                    # Score change label
                    elif label_text.startswith('(') and label_text.endswith(')'):
                        # This is likely a score change, skip as it has special coloring
                        pass
                    # Move notation or best move
                    else:
                        # For best move row which should use secondary text color
                        parent = label.master
                        if hasattr(parent, 'winfo_class') and parent.winfo_class() == "Frame":
                            # Check if this might be the best move container
                            for sibling in parent.winfo_children():
                                if hasattr(sibling, 'cget') and hasattr(sibling, 'winfo_class'):
                                    if sibling.winfo_class() == "Label" and sibling.cget('text') == "→":
                                        label.config(fg=secondary_text_color)
                                        break
                            else:
                                # Not part of best move, use primary text
                                label.config(fg=text_color)
                        else:
                            # Default to primary text color
                            label.config(fg=text_color)
            except:
                pass

# Remove the pulsing effect functions as they're no longer used
def _add_pulsing_effect(card):
    """This function is replaced by direct coloring."""
    # Apply error color immediately instead of pulsing
    if not card or card.selected:
        return
    
    # Find classification to determine error color
    classification = "Erreur"  # Default
    for label in card.labels:
        if hasattr(label, 'winfo_class') and hasattr(label, 'cget'):
            try:
                if label.winfo_class() == "Label":
                    text = label.cget('text')
                    if text in ["Erreur", "Grosse erreur"]:
                        classification = text
                        break
            except:
                continue
    
    # Apply appropriate error color
    _apply_error_color(card, classification)

def _remove_pulsing_effect(card):
    """This function is replaced by color restoration."""
    # Restore original colors
    _restore_original_colors(card)