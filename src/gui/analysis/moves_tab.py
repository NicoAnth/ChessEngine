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
        text="Historique",
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
        
        # Container for the main move info
        move_container = tk.Frame(card, bg=bg_color)
        move_container.pack(fill=tk.X, expand=True)
        
        # --- LEFT SIDE: MOVE NOTATION ---
        move_info = tk.Frame(move_container, bg=bg_color)
        move_info.pack(side=tk.LEFT, fill=tk.Y, anchor="w")
        
        # Add piece symbol prefix based on the move
        piece_symbol = ""
        if move_eval["san"][0] in ["N", "B", "R", "Q", "K"]:
            if is_white:
                piece_map = {"N": "♘", "B": "♗", "R": "♖", "Q": "♕", "K": "♔"}
                piece_symbol = piece_map.get(move_eval["san"][0], "")
            else:
                piece_map = {"N": "♞", "B": "♝", "R": "♜", "Q": "♛", "K": "♚"}
                piece_symbol = piece_map.get(move_eval["san"][0], "")
        
        # Move in SAN notation with piece symbol
        move_text = piece_symbol + " " + move_eval["san"] if piece_symbol else move_eval["san"]
        move_label = tk.Label(
            move_info,
            text=move_text,
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
                if c.selected:
                    # Update the selected card with highlight colors
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
                    # Reset non-selected cards to their original background
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
    
    # Store all cards for selection management
    all_cards = []
    
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
    
    # Recursively bind mousewheel to all widgets
    view_instance._bind_mousewheel_to_widgets(content_frame, _on_mousewheel, _on_linux_scroll_up, _on_linux_scroll_down)
    
    # Initial update of the scroll region
    content_frame.update_idletasks()  # Ensure content frame has been laid out
    update_scrollregion()