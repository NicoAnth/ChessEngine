"""
Opening banner component.
Displays chess opening information (name and ECO code) in an elegant format.
"""

import tkinter as tk
from tkinter import font
from src.utils import config

class OpeningBanner:
    """A modern banner that displays chess opening information."""

    def __init__(self, parent, width=None):
        """
        Initialize the opening banner.

        Args:
            parent: Parent widget
            width: Optional fixed width for the banner frame
        """
        self.parent = parent

        # Banner Container
        self.container = tk.Frame(
            parent,
            bg=config.COLORS.get("background", "#F5F5F5"),  # Use background color from config
            padx=5,
            pady=3  # Reduced padding to make it more compact
        )
        if width:
            self.container.configure(width=width)
            self.container.pack_propagate(False)  # Prevent resizing if width is fixed

        # Banner is initially hidden
        self.is_visible = False

        # Opening label - Use an italic, elegant font for the opening name
        opening_font_config = config.FONTS.get("opening_name", {})
        opening_font = font.Font(
            family=opening_font_config.get("family", "Segoe UI"),
            size=opening_font_config.get("size", 10),
            slant=opening_font_config.get("slant", "italic")
        )
        
        # Text color for the opening - using a subdued color
        opening_color = config.COLORS.get("opening_text", "#546E7A")  # Elegant slate blue-gray
        bg_color = config.COLORS.get("background", "#F5F5F5")

        self.opening_label = tk.Label(
            self.container,
            font=opening_font,
            fg=opening_color,
            bg=bg_color,
            text=""  # Start empty
        )
        self.opening_label.pack(fill=tk.X, expand=True)

        # Initialize with empty data
        self.opening_name = ""
        self.eco_code = ""

    def update_opening(self, name=None, eco_code=None):
        """
        Update the opening information.

        Args:
            name: Name of the opening (optional)
            eco_code: ECO code of the opening (optional)
        """
        # Update stored values if provided
        if name is not None:
            self.opening_name = name
        if eco_code is not None:
            self.eco_code = eco_code

        # Format the display text
        display_text = ""
        if self.eco_code and self.opening_name:
            display_text = f"{self.eco_code}: {self.opening_name}"
        elif self.opening_name:
            display_text = self.opening_name
        elif self.eco_code:
            display_text = f"ECO {self.eco_code}"

        # Update the label text
        self.opening_label.configure(text=display_text)

        # Show the banner if there's text to display, hide it otherwise
        if display_text:
            self.show()
        else:
            self.hide()
            
        # Debug output to help troubleshoot visibility issues
        print(f"Opening display updated: '{display_text}', visible: {self.is_visible}")

    def clear(self):
        """Clear the opening information."""
        self.opening_name = ""
        self.eco_code = ""
        self.opening_label.configure(text="")
        self.hide()

    def show(self):
        """Show the banner."""
        if not self.is_visible:
            # Méthode de placement améliorée pour assurer la visibilité
            # Récupérer tous les widgets du conteneur parent
            parent_widgets = self.parent.winfo_children()
            
            # Si la bannière des joueurs existe et est visible, nous devons nous positionner après elle
            player_banner_visible = False
            player_banner_index = -1
            
            # Identifier la position de la bannière des joueurs si elle existe
            for i, widget in enumerate(parent_widgets):
                if widget.__class__.__name__ == 'PlayerBanner' or hasattr(widget, '_name') and 'playerbanner' in str(widget._name).lower():
                    player_banner_visible = widget.winfo_ismapped()
                    player_banner_index = i
                    break
            
            # Réorganiser le positionnement
            # D'abord, retirer la bannière d'ouverture
            self.container.pack_forget()
            
            # Ensuite, la repositionner au bon endroit
            # Si la bannière des joueurs est visible, nous nous plaçons juste après
            # Sinon, nous nous plaçons en premier
            self.container.pack(fill=tk.X, pady=(0, 5), after=(parent_widgets[player_banner_index] if player_banner_visible and player_banner_index >= 0 else None))
            
            print(f"Opening banner shown - Player banner visible: {player_banner_visible}, index: {player_banner_index}")
            self.is_visible = True

    def hide(self):
        """Hide the banner."""
        if self.is_visible:
            self.container.pack_forget()
            print("Opening banner hidden")
            self.is_visible = False