"""Error navigation component for chess analysis."""

import tkinter as tk
import chess
from tkinter import font
from src.utils import config
from src.gui.analysis.utils.style_utils import activate_error_card, deactivate_error_card


class ErrorNavigator:
    """A component for navigating between error moves in a chess game analysis."""
    
    def __init__(self, parent, error_moves, error_count, view_instance):
        """Create an elegant error navigation bar.
        
        Args:
            parent: Parent widget
            error_moves: List of moves classified as errors
            error_count: Total number of errors
            view_instance: The parent view for event handling
        """
        self.parent = parent
        self.error_moves = error_moves
        self.error_count = error_count
        self.view_instance = view_instance
        self.current_error_index = 0
        self.error_mode_active = False
        
        # Create the UI
        self.create_navigation_bar()
    
    def create_navigation_bar(self):
        """Create the error navigation UI components."""
        # Container for error navigation - utiliser side=RIGHT pour l'aligner à droite du titre
        self.nav_container = tk.Frame(self.parent, bg=config.COLORS["background"])
        self.nav_container.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Navigation controls container
        controls_frame = tk.Frame(self.nav_container, bg=config.COLORS["background"])
        controls_frame.pack(side=tk.RIGHT)
        
        # Toggle switch for error mode
        self.toggle_var = tk.BooleanVar(value=False)
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
        
        # Create the rounded rectangle method for Canvas
        self._add_rounded_rectangle_method()
        
        # Toggle switch - redesigned with fully rounded shape
        switch_width = 44
        switch_height = 22
        self.switch_canvas = tk.Canvas(
            toggle_frame, 
            width=switch_width, 
            height=switch_height,
            bg=config.COLORS["background"],
            highlightthickness=0
        )
        self.switch_canvas.pack(side=tk.LEFT)
        
        # Switch background (track)
        self.switch_bg = self.switch_canvas.create_rounded_rectangle(
            2, 2, switch_width-2, switch_height-2,
            radius=switch_height//2,  # Make radius half the height for fully rounded ends
            fill="#CCCCCC", 
            outline="",
            tags="switch_bg"
        )
        
        # Draw switch knob (smaller than before to fit within the rounded track)
        knob_size = switch_height - 6
        knob_x = 4  # Starting x position (left side)
        self.knob = self.switch_canvas.create_oval(
            knob_x, 3, knob_x + knob_size, 3 + knob_size,
            fill="white", outline="", tags="knob"
        )
        
        # Error navigation controls
        nav_buttons_frame = tk.Frame(controls_frame, bg=config.COLORS["background"])
        nav_buttons_frame.pack(side=tk.LEFT)
        
        # Previous error button
        self.prev_button = tk.Button(
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
            command=lambda: self.navigate_errors("prev")
        )
        self.prev_button.pack(side=tk.LEFT)
        
        # Error counter 
        self.counter_var = tk.StringVar(value="0/0")
        self.counter_label = tk.Label(
            nav_buttons_frame,
            textvariable=self.counter_var,
            font=font.Font(**config.FONTS["move_notation"]),
            bg=config.COLORS["background"],
            fg="#CCCCCC",  # Starts disabled
            padx=10
        )
        self.counter_label.pack(side=tk.LEFT)
        
        # Next error button
        self.next_button = tk.Button(
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
            command=lambda: self.navigate_errors("next")
        )
        self.next_button.pack(side=tk.LEFT)
        
        # Initialize counter
        self.counter_var.set(f"0/{self.error_count}")
        
        # Bind click event to switch
        self.switch_canvas.bind("<Button-1>", self.toggle_click)

    def _add_rounded_rectangle_method(self):
        """Add rounded rectangle drawing capability to Canvas."""
        # Define the method
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
        
        # Add the method to the Canvas class
        tk.Canvas.create_rounded_rectangle = _create_rounded_rectangle
    
    def toggle_click(self, event):
        """Handle click on the toggle switch."""
        self.toggle_var.set(not self.toggle_var.get())
        self.update_switch()
    
    def update_switch(self):
        """Update the switch appearance and toggle error mode."""
        if self.toggle_var.get():
            # ON state
            self.switch_canvas.itemconfig(
                "switch_bg", 
                fill=config.COLORS["control_button"]
            )
            # Move knob to right
            self.switch_canvas.coords(
                "knob", 
                44 - (22-6) - 4, 3, 
                44 - 4, 3 + (22-6)
            )
            # Apply error highlighting
            self.toggle_error_mode(True)
        else:
            # OFF state
            self.switch_canvas.itemconfig(
                "switch_bg", 
                fill="#CCCCCC"
            )
            # Move knob to left
            self.switch_canvas.coords("knob", 4, 3, 4 + (22-6), 3 + (22-6))
            # Remove error highlighting
            self.toggle_error_mode(False)
    
    def toggle_error_mode(self, show_errors):
        """Toggle error highlighting mode.
        
        Args:
            show_errors: Boolean indicating whether to show errors
        """
        self.error_mode_active = show_errors
        
        # Apply styling to cards
        for card in self.view_instance.all_cards:
            if not hasattr(card, 'move_index'):
                continue
                
            is_error = card.is_error
            
            if show_errors and is_error:
                # Only modify error cards when showing errors
                activate_error_card(card, card.classification)
                
            else:
                # Reset all cards when hiding errors
                deactivate_error_card(card)
                
        # Update navigation button states
        if show_errors and self.error_count > 0:
            self.prev_button.config(state=tk.NORMAL if self.current_error_index > 0 else tk.DISABLED)
            self.next_button.config(state=tk.NORMAL if self.current_error_index < self.error_count - 1 else tk.DISABLED)
            self.counter_label.config(fg=config.COLORS["primary_text"])
            self.counter_var.set(f"{self.current_error_index + 1}/{self.error_count}")
        else:
            self.prev_button.config(state=tk.DISABLED)
            self.next_button.config(state=tk.DISABLED)
            self.counter_label.config(fg="#CCCCCC")
            self.counter_var.set(f"0/{self.error_count}")
    
    def navigate_errors(self, direction):
        """Navigate to the next or previous error.
        
        Args:
            direction: 'next' or 'prev' to indicate direction
        """
        if not self.error_mode_active or self.error_count == 0:
            return
            
        # Update current error index
        if direction == "next" and self.current_error_index < self.error_count - 1:
            self.current_error_index += 1
        elif direction == "prev" and self.current_error_index > 0:
            self.current_error_index -= 1
        else:
            return  # No change if at boundaries
            
        # Update counter
        self.counter_var.set(f"{self.current_error_index + 1}/{self.error_count}")
        
        # Get the error move at the current index
        error_move = self.error_moves[self.current_error_index]
        
        # Find the corresponding card
        for card in self.view_instance.all_cards:
            if hasattr(card, 'move_index') and card.move_index == error_move.get('move_index', -1):
                # Ensure the card is visible
                self.ensure_card_visible(card)
                
                # Select the card - use event_generate to trigger the click handler
                card.event_generate('<Button-1>')
                break
                
        # Update button states
        self.prev_button.config(state=tk.NORMAL if self.current_error_index > 0 else tk.DISABLED)
        self.next_button.config(state=tk.NORMAL if self.current_error_index < self.error_count - 1 else tk.DISABLED)
    
    def ensure_card_visible(self, card):
        """Ensure a card is visible in the scrollable area."""
        # Find the parent canvas
        parent = card.master
        canvas = None
        
        # Look for canvas in parent hierarchy
        while parent and not isinstance(parent, tk.Canvas):
            parent = parent.master
            
        canvas = parent if isinstance(parent, tk.Canvas) else None
        
        if canvas:
            # Get the card's position relative to the canvas
            x, y = card.winfo_x(), card.winfo_y()
            parent = card.master
            
            # Accumulate position through parent hierarchy until we reach the canvas
            while parent and parent != canvas.master:
                x += parent.winfo_x()
                y += parent.winfo_y()
                parent = parent.master
            
            # Get canvas scroll region and dimensions
            bbox = canvas.bbox(tk.ALL)
            if not bbox:
                return
                
            # Calculate fractions for yview
            canvas_height = canvas.winfo_height()
            card_height = card.winfo_height()
            
            # Get the current view position
            view_top, view_bottom = canvas.yview()
            content_height = bbox[3] - bbox[1]
            
            # Calculate pixel positions
            card_top = y
            card_bottom = y + card_height
            visible_top = view_top * content_height
            visible_bottom = view_bottom * content_height
            
            # Check if card is not fully visible
            if card_top < visible_top or card_bottom > visible_bottom:
                # Calculate fraction to position the card in the center
                fraction = (card_top - (canvas_height / 2) + (card_height / 2)) / content_height
                fraction = max(0.0, min(1.0, fraction))  # Clamp between 0 and 1
                
                # Scroll to the calculated position
                canvas.yview_moveto(fraction)


def create_error_navigation(parent, error_moves, error_count, view_instance):
    """Create the error navigation component.
    
    Args:
        parent: Parent widget
        error_moves: List of moves classified as errors
        error_count: Total number of errors
        view_instance: The parent view for event handling
        
    Returns:
        Dictionary containing references to important UI elements
    """
    navigator = ErrorNavigator(parent, error_moves, error_count, view_instance)
    
    # Return references to important UI elements for external control
    return {
        "toggle_var": navigator.toggle_var,
        "update_switch": navigator.update_switch,
        "next_button": navigator.next_button,
        "prev_button": navigator.prev_button
    }

def on_error_selected(index, error_move_data, view_instance):
    """Handle error selection for visualization."""
    # Get the move index (from metadata or use the index itself as fallback)
    move_index = error_move_data.get("move_index", index)
    
    # Select the card if available - do this first to update the board
    if view_instance.all_cards and 0 <= move_index < len(view_instance.all_cards):
        card = view_instance.all_cards[move_index]
        
        # Generate click event to select this card
        card.event_generate('<Button-1>')
