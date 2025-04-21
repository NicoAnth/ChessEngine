"""Moves analysis tab components for chess analysis."""

import tkinter as tk
from tkinter import ttk, font
import chess

from src.utils import config
from src.gui.analysis.mini_board import MiniChessBoard
from src.gui.analysis.components.chess_card import create_move_cards
from src.gui.analysis.components.error_navigation import create_error_navigation
from src.gui.player_banner import PlayerBanner  # Import the PlayerBanner class
from src.user.profile import GameAnalysis  # Add import for GameAnalysis


def _create_moves_tab_content(view_instance, moves_frame_parent, game_analysis, text_font):
    """Create the detailed moves analysis tab content with a mini-board."""

    # Set fixed card dimensions
    CARD_WIDTH = 220  # Fixed width for consistency
    CARD_HEIGHT = 75  # Minimum height for consistency

    # Check for headers in the analysis results
    headers = None
    white_name = "Blancs"
    black_name = "Noirs"
    white_elo = ""
    black_elo = ""

    # Check if analysis_results is a GameAnalysis object
    if isinstance(game_analysis, GameAnalysis):
        # Reconstruct headers from GameAnalysis attributes
        headers = {
            "White": game_analysis.white_player,
            "Black": game_analysis.black_player,
            "Result": game_analysis.result,
            "Date": game_analysis.game_date.strftime('%Y.%m.%d') if game_analysis.game_date else "????.??.??",
            "Event": game_analysis.event or "?",
            "Site": game_analysis.site or "?",
            "Round": game_analysis.round or "?",
            "ECO": game_analysis.eco or "?"
            # Note: ELO is not directly stored in GameAnalysis, might need parsing from PGN or separate storage
        }
        white_name = game_analysis.white_player
        black_name = game_analysis.black_player

    # Fallback for other potential structures (less likely based on error)
    elif hasattr(view_instance, 'analysis_results') and isinstance(view_instance.analysis_results, dict):
        # Try to get headers from multiple possible locations in the analysis results
        if 'headers' in view_instance.analysis_results:
            headers = view_instance.analysis_results['headers']
        elif 'game_info' in view_instance.analysis_results and 'headers' in view_instance.analysis_results['game_info']:
            headers = view_instance.analysis_results['game_info']['headers']
        elif 'pgn_headers' in view_instance.analysis_results:
            headers = view_instance.analysis_results['pgn_headers']

    # Create the player banner at the top level of the parent frame
    view_instance.player_banner = PlayerBanner(moves_frame_parent, top_padding=5)

    # Only show the player banner if headers are available
    if headers:
        view_instance.player_banner.update_from_pgn_headers(headers)
        view_instance.player_banner.show()
    else:
        # If no headers, don't show the banner
        view_instance.player_banner.hide()

    # Create paned window to split the tab
    paned_window = ttk.PanedWindow(moves_frame_parent, orient=tk.HORIZONTAL)
    paned_window.pack(fill=tk.BOTH, expand=True)

    # Create frame for move list (left side)
    moves_frame = tk.Frame(paned_window, bg=config.COLORS["background"])

    # Create frame for mini-board (right side)
    board_frame = tk.Frame(paned_window, bg=config.COLORS["background"], padx=10, pady=10)

    # Add both frames to the paned window with adjusted weights
    # Give the moves frame more space since the board is now larger
    paned_window.add(moves_frame, weight=3)  # Increased from 1 to 3
    paned_window.add(board_frame, weight=2)  # Increased from 1 to 2

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

    # Left: Title
    title_label = tk.Label(
        title_frame,
        text="Coups",
        font=font.Font(**config.FONTS["moves_title"]),
        bg=config.COLORS["background"],
        fg=config.COLORS["primary_text"]
    )
    title_label.pack(side=tk.LEFT, padx=15)

    # Count errors and mistakes for the badge
    error_moves = []
    for idx, move in enumerate(game_analysis.move_evaluations):  # Use game_analysis directly
        if move["classification"] in ["Erreur", "Grosse erreur"]:
            # Add move_index to the error move data for navigation
            move_copy = move.copy()
            move_copy["move_index"] = idx
            error_moves.append(move_copy)

    error_count = len(error_moves)

    # Create error badge and navigation bar on same line as title if errors exist
    error_navigation = None
    if error_count > 0:
        # Create the error navigation directly in the title_frame for alignment
        error_navigation = create_error_navigation(
            title_frame, error_moves, error_count, view_instance
        )

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

    # Create all cards using the ChessCard component
    all_cards, error_cards = create_move_cards(
        moves_container,
        game_analysis.move_evaluations,  # Use game_analysis directly
        view_instance,
        text_font,
        CARD_WIDTH,
        CARD_HEIGHT
    )

    # Store error cards in the view instance for navigation
    view_instance.error_cards = error_cards
    view_instance.all_cards = all_cards
    view_instance.current_error_index = 0

    # Create header with title for mini-board
    board_header_frame = tk.Frame(board_frame, bg=config.COLORS["background"])
    board_header_frame.pack(fill=tk.X, pady=(0, 10))

    # Title for the board section
    board_title_label = tk.Label(
        board_header_frame,
        text="Plateau d'analyse",
        font=font.Font(**config.FONTS["moves_title"]),
        bg=config.COLORS["background"],
        fg=config.COLORS["primary_text"]
    )
    board_title_label.pack(side=tk.LEFT)

    # Ajout du label pour l'ouverture détectée - à droite du titre
    view_instance.opening_label = tk.Label(
        board_header_frame,
        text="",
        font=font.Font(family="Segoe UI", size=10, slant="italic"),
        bg=config.COLORS["background"],
        fg=config.COLORS["secondary_text"]
    )
    view_instance.opening_label.pack(side=tk.RIGHT)

    # Create mini-board in the right frame
    view_instance._create_mini_board(board_frame, game_analysis.move_evaluations, opening_label=view_instance.opening_label)  # Use game_analysis directly

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
