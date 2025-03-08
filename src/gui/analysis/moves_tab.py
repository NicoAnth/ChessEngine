"""Moves analysis tab components for chess analysis."""

import tkinter as tk
from tkinter import ttk, font
import chess
from src.utils import config
from src.gui.analysis.mini_board import MiniChessBoard

def _create_moves_tab_content(view_instance, moves_frame_parent, move_evaluations, text_font):
    """Create the detailed moves analysis tab content with a mini-board."""
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
        width=10,
        bd=0,
        highlightthickness=0,
        troughcolor="#EAEAEA",
        bg=config.COLORS["background"],
        activebackground=config.COLORS["selected_square"]
    )
    
    # Inner content frame
    content_frame = tk.Frame(moves_canvas, bg=config.COLORS["background"], padx=15, pady=5)
    
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
    
    # Header for moves table
    header_font = font.Font(family="Segoe UI", size=10, weight="bold")
    view_instance._create_moves_header(content_frame, header_font)
    
    # List all moves with their evaluations
    for i, eval in enumerate(move_evaluations):
        view_instance._create_move_row(content_frame, eval, i, text_font)
    
    # Create mini-board in the right frame
    view_instance._create_mini_board(board_frame, move_evaluations)
    
    # Recursively bind mousewheel to all widgets
    view_instance._bind_mousewheel_to_widgets(content_frame, _on_mousewheel, _on_linux_scroll_up, _on_linux_scroll_down)
    
    # Initial update of the scroll region
    content_frame.update_idletasks()  # Ensure content frame has been laid out
    update_scrollregion()