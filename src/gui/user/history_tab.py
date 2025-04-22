"""
Onglet affichant l'historique des parties analysées de l'utilisateur avec une interface moderne et élégante.
"""

import tkinter as tk
from tkinter import ttk, font as tkFont, messagebox
from src.user import UserProfile, GameAnalysis
from src.utils import config, resource_loader
import datetime
from PIL import Image, ImageTk, ImageDraw
from src.gui.analysis_view import GameAnalysisView
from src.analysis.game_analyzer import GameAnalyzer

def format_time_control(tc_string: str) -> str:
    """Formats a PGN time control string (e.g., '600+5') into 'MM:SS+INC mins'."""
    if not tc_string or tc_string == "?":
        return "Inconnue"

    parts = tc_string.split('+')
    try:
        base_seconds = int(parts[0])
        minutes = base_seconds // 60
        seconds = base_seconds % 60
        formatted_base = f"{minutes:02d}:{seconds:02d}"

        if len(parts) > 1:
            increment = parts[1]
            return f"{formatted_base}+{increment}"
        else:
            return f"{formatted_base}"
    except ValueError:
        # If conversion fails, return the original string
        return tc_string

class GameCard(tk.Frame):
    """Carte représentant une partie d'échecs avec style moderne."""
    
    def __init__(self, parent, game_analysis, user_profile, profile_manager, on_select=None, on_delete=None, **kwargs):
        super().__init__(parent, bg=config.COLORS["profile_card_bg"], padx=15, pady=15, bd=0, **kwargs)
        self.game_analysis = game_analysis
        self.user_profile = user_profile
        self.profile_manager = profile_manager  # Store profile manager
        self.on_select = on_select
        self.on_delete = on_delete  # Callback for deletion
        
        # Shadow effect with a second frame - more subtle shadow by default
        self.shadow = tk.Frame(parent, bg=config.COLORS["profile_card_shadow"], padx=15, pady=15, bd=0)
        
        # Configure style and interaction
        self.configure(cursor="hand2")  # Hand cursor indicates clickable
        self.bind("<Button-1>", self._on_click)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        
        # Store original shadow color for transitions
        self.original_shadow_color = config.COLORS["profile_card_shadow"]
        self.hover_shadow_color = self._darken_color(self.original_shadow_color, 0.15)
        
        # Animation properties - we'll simulate animation with multiple steps
        self.animation_ms = 150  # Total animation duration
        self.animation_steps = 10  # Number of intermediate steps
        self.animation_delay = int(self.animation_ms / self.animation_steps)
        self.animation_active = False
        self.animation_direction = None  # 'in' for hover in, 'out' for hover out

        # --- Game header (players, result) using grid --- 
        header_frame = tk.Frame(self, bg=config.COLORS["profile_card_bg"])
        header_frame.pack(fill="x", expand=True, pady=(0, 5)) # Add some bottom padding

        # Configure grid columns for header_frame
        # Use 'uniform' to make columns 0 and 2 share extra space equally
        header_frame.grid_columnconfigure(0, weight=1, uniform="player_cols") # White player
        header_frame.grid_columnconfigure(1, weight=0) # Result - fixed width, centered
        header_frame.grid_columnconfigure(2, weight=1, uniform="player_cols") # Black player

        # White player label (directly in header_frame)
        white_label = tk.Label(header_frame, text=game_analysis.white_player,
                             font=tkFont.Font(**config.FONTS["profile_stat_value"]),
                             bg=config.COLORS["profile_card_bg"],
                             fg=config.COLORS["profile_text"],
                             anchor="w")
        white_label.grid(row=0, column=0, sticky="w", padx=(0, 10))

        # Result label (directly in header_frame)
        result = game_analysis.result
        result_label = tk.Label(header_frame, text=result,
                              font=tkFont.Font(**config.FONTS["profile_stat_value"]),
                              bg=config.COLORS["profile_card_bg"],
                              fg=config.COLORS["profile_accent"],
                              anchor="center") # Ensure text is centered within the label
        result_label.grid(row=0, column=1, sticky="ew") # Let the label fill the central column horizontally

        # Black player frame (contains label and delete button)
        black_frame = tk.Frame(header_frame, bg=config.COLORS["profile_card_bg"])
        black_frame.grid(row=0, column=2, sticky="e", padx=(10, 0))

        # Create delete button directly in black_frame
        delete_button_font = tkFont.Font(family="Segoe UI Symbol", size=12, weight="bold")
        self.delete_button = tk.Button(black_frame, text="×",
                                     command=self._on_delete_click,
                                     font=delete_button_font,
                                     bg=config.COLORS["profile_card_bg"],
                                     fg="#E81123",
                                     activebackground="#E81123",
                                     activeforeground="white",
                                     relief=tk.FLAT,
                                     borderwidth=0,
                                     cursor="hand2",
                                     width=1,
                                     padx=0, pady=0)
        self.delete_button.pack(side="right", padx=(5, 0))

        # Create and pack black player label
        black_label = tk.Label(black_frame, text=game_analysis.black_player,
                             font=tkFont.Font(**config.FONTS["profile_stat_value"]),
                             bg=config.COLORS["profile_card_bg"],
                             fg=config.COLORS["profile_text"],
                             anchor="e")
        black_label.pack(side="right")
        # --- End of header modifications ---

        # Separator
        separator = ttk.Separator(self, orient="horizontal")
        # Adjust separator padding if needed, or remove if header padding is sufficient
        separator.pack(fill="x", pady=5) 

        # Add Time Control if available - Centered below separator
        if game_analysis.time_control and game_analysis.time_control != "?":
            formatted_tc = format_time_control(game_analysis.time_control)
            self.tc_label = tk.Label(self, text=f"{formatted_tc}", # Use formatted string
                              font=tkFont.Font(**config.FONTS["profile_stat_label"]),
                              bg=config.COLORS["profile_card_bg"],
                              fg=config.COLORS["profile_secondary_text"],
                              anchor="center") # Center the text
            # Pack directly into the card, below separator, before details
            self.tc_label.pack(pady=(0, 5), fill="x")
        else:
            self.tc_label = None # Ensure tc_label exists even if no time control

        # Game details
        details_frame = tk.Frame(self, bg=config.COLORS["profile_card_bg"])
        details_frame.pack(fill="x", expand=True)
        
        # Left column - Game metadata
        left_frame = tk.Frame(details_frame, bg=config.COLORS["profile_card_bg"])
        left_frame.pack(side="left", fill="y", anchor="w")
        
        # Date and event
        date_str = game_analysis.game_date.strftime("%d %b %Y")
        date_label = tk.Label(left_frame, text=f"Date: {date_str}",
                            font=tkFont.Font(**config.FONTS["profile_stat_label"]),
                            bg=config.COLORS["profile_card_bg"],
                            fg=config.COLORS["profile_secondary_text"],
                            anchor="w")
        date_label.pack(anchor="w")
        
        if game_analysis.event:
            event_label = tk.Label(left_frame, text=f"Événement: {game_analysis.event}",
                                 font=tkFont.Font(**config.FONTS["profile_stat_label"]),
                                 bg=config.COLORS["profile_card_bg"],
                                 fg=config.COLORS["profile_secondary_text"],
                                 anchor="w")
            event_label.pack(anchor="w")
            
        if game_analysis.eco:
            eco_label = tk.Label(left_frame, text=f"ECO: {game_analysis.eco}",
                               font=tkFont.Font(**config.FONTS["profile_stat_label"]),
                               bg=config.COLORS["profile_card_bg"],
                               fg=config.COLORS["profile_secondary_text"],
                               anchor="w")
            eco_label.pack(anchor="w")
        
        # Right column - Performance metrics
        right_frame = tk.Frame(details_frame, bg=config.COLORS["profile_card_bg"])
        right_frame.pack(side="right", fill="y", anchor="e")
        
        # Get appropriate player stats based on player name
        player_stats = None
        if self.user_profile.username.lower() == game_analysis.white_player.lower():
            player_stats = game_analysis.white_stats
            color_text = "Blancs"
        elif self.user_profile.username.lower() == game_analysis.black_player.lower():
            player_stats = game_analysis.black_stats
            color_text = "Noirs"
        
        if player_stats:
            # Accuracy
            accuracy = player_stats.get("accuracy", "N/A")
            if isinstance(accuracy, (int, float)):
                accuracy_str = f"{accuracy:.1f}%"
            else:
                accuracy_str = "N/A"
            
            color_label = tk.Label(right_frame, text=f"Joué: {color_text}",
                                 font=tkFont.Font(**config.FONTS["profile_stat_label"]),
                                 bg=config.COLORS["profile_card_bg"],
                                 fg=config.COLORS["profile_secondary_text"],
                                 anchor="e")
            color_label.pack(anchor="e")
                
            accuracy_label = tk.Label(right_frame, text=f"Précision: {accuracy_str}",
                                    font=tkFont.Font(**config.FONTS["profile_stat_value"]),
                                    bg=config.COLORS["profile_card_bg"],
                                    fg=config.COLORS["profile_text"],
                                    anchor="e")
            accuracy_label.pack(anchor="e")
        
        # --- Bind events to all child widgets ---
        # This must be done AFTER all widgets are created
        self.after(10, self._bind_events_to_children)
    
    def grid(self, **kwargs):
        """Positionne à la fois l'ombre et la carte principale."""
        self.shadow.grid(kwargs)
        super().grid(kwargs)
    
    def pack(self, **kwargs):
        """Positionne à la fois l'ombre et la carte principale."""
        padding = kwargs.pop("pady", 5)
        # Extract fill value before passing to shadow
        fill_value = kwargs.pop("fill", None)
        
        if isinstance(padding, tuple):
            shadow_padding = (padding[0], padding[1] + 3)
        else:
            shadow_padding = (padding, padding + 3)
        
        # Pass the fill value separately and explicitly
        self.shadow.pack(pady=shadow_padding, fill=fill_value if fill_value else "x", **kwargs)
        super().pack(pady=padding, fill=fill_value if fill_value else "x", **kwargs)
        self.shadow.lower(self)  # Ensure shadow stays behind
    
    def _bind_events_to_children(self):
        """Bind hover and click events to all child widgets recursively."""
        self._bind_recursive(self)
    
    def _bind_recursive(self, widget):
        """Recursively bind events to a widget and all its children."""
        # Skip binding to delete button to keep its own behavior
        if widget == self.delete_button:
            return
        
        # Bind events to propagate to parent
        widget.bind("<Enter>", lambda e: self._propagate_event(e, self._on_enter), add="+")
        widget.bind("<Leave>", lambda e: self._propagate_event(e, self._on_leave), add="+")
        widget.bind("<Button-1>", lambda e: self._propagate_event(e, self._on_click), add="+")
        
        # Recursively bind to all children
        for child in widget.winfo_children():
            if child != self.delete_button:  # Skip delete button
                self._bind_recursive(child)
    
    def _propagate_event(self, event, handler):
        """Propagate an event from a child widget to this card."""
        # Skip if the event is already on the card itself or on the delete button
        if event.widget == self or event.widget == self.delete_button:
            return
        
        # Create a new event with this card as widget and call the handler
        new_event = type('Event', (), {})()
        new_event.widget = self
        new_event.x = event.x
        new_event.y = event.y
        handler(new_event)
        
        # Don't propagate Enter/Leave events that cross widget boundaries
        # This prevents flickering when moving between child widgets
        return "break"  # Stop event propagation
    
    def _on_delete_click(self):
        """Handles the click on the delete button."""
        if not self.on_delete:
            return

        # Confirmation dialog
        title = "Confirmer la Suppression"
        message = f"Êtes-vous sûr de vouloir supprimer cette partie ?\n\n{self.game_analysis.white_player} vs {self.game_analysis.black_player} ({self.game_analysis.game_date.strftime('%d/%m/%Y')})\n\nCette action est irréversible."
        
        if messagebox.askyesno(title, message, parent=self.winfo_toplevel()):
            try:
                deleted = self.user_profile.delete_game_analysis(self.game_analysis.game_id)
                
                if deleted:
                    self.profile_manager.save_profile(self.user_profile)
                    self.on_delete()
                    print(f"Partie {self.game_analysis.game_id} supprimée et profil sauvegardé.")
                else:
                    messagebox.showerror("Erreur", "Impossible de supprimer la partie du profil.", parent=self.winfo_toplevel())
            except Exception as e:
                messagebox.showerror("Erreur Inattendue", f"Une erreur est survenue lors de la suppression : {e}", parent=self.winfo_toplevel())
                print(f"Error during game deletion process: {e}")
    
    def _on_click(self, event):
        """Appelle la fonction de rappel avec l'analyse de partie, sauf si le clic est sur le bouton supprimer."""
        widget = event.widget
        if widget == self.delete_button:
            return
        
        if self.on_select:
            self.on_select(self.game_analysis)
    
    def _on_enter_card(self, event):
        """Make delete button text more visible on card hover."""
        # Check if the widget still exists
        try:
            # Use a more visible color, but not the final active color
            self.delete_button.configure(fg=config.COLORS["profile_text"])
        except tk.TclError:
            # Widget might have been destroyed
            pass

    def _on_leave_card(self, event):
        """Restore delete button text color when leaving card."""
        # Check if the widget still exists
        try:
            # Restore the initial subtle color
            self.delete_button.configure(fg=config.COLORS["profile_secondary_text"])
        except tk.TclError:
            # Widget might have been destroyed
            pass

    def _on_enter(self, event):
        """Card hover effect - change card background and shadow."""
        # Use a subtle tint of the accent color for hover - more modern look
        hover_bg = self._lighten_color(config.COLORS["profile_accent"], 0.85)
        
        # Configure the card background
        self.configure(bg=hover_bg)
        
        # Enhance shadow for elevation effect
        self.shadow.configure(bg=self.hover_shadow_color)
        
        # Apply to all children except delete button's text color
        self._change_bg_recursive(self, hover_bg, exclude_widget=None)
        
        # Handle delete button separately to maintain red text but update background
        self._update_delete_button_on_hover(hover_bg)
        
        # Start animation transition
        self._start_animation("in")
    
    def _on_leave(self, event):
        """Cancel card hover effect - restore card background and shadow."""
        original_bg = config.COLORS["profile_card_bg"]
        self.configure(bg=original_bg)
        self.shadow.configure(bg=self.original_shadow_color)
        
        # Apply to all children without exclusion
        self._change_bg_recursive(self, original_bg, exclude_widget=None)
        
        # Reset delete button
        self._update_delete_button_on_leave(original_bg)
        
        self._start_animation("out")

    def _update_delete_button_on_hover(self, hover_bg):
        """Update delete button appearance on card hover while keeping red text."""
        try:
            # Update background to match the hover color
            self.delete_button.configure(bg=hover_bg)
            
            # Make the text more visible
            self.delete_button.configure(fg="#E81123")  # Ensure the red is visible on hover
        except tk.TclError:
            # Handle case where widget may have been destroyed
            pass

    def _update_delete_button_on_leave(self, original_bg):
        """Reset delete button appearance when card is not hovered."""
        try:
            # Reset background to original
            self.delete_button.configure(bg=original_bg)
            
            # Reset text color
            self.delete_button.configure(fg="#E81123")  # Keep the red color
        except tk.TclError:
            # Handle case where widget may have been destroyed
            pass

    def _lighten_color(self, hex_color, factor):
        """Lighten a hex color by a given factor (0-1)."""
        r, g, b = self._hex_to_rgb(hex_color)
        # Calculate lighter shade while maintaining color hue
        r = min(255, int(r + (255 - r) * factor))
        g = min(255, int(g + (255 - g) * factor))
        b = min(255, int(b + (255 - b) * factor))
        return f"#{r:02x}{g:02x}{b:02x}"

    def _change_bg_recursive(self, widget, bg_color, exclude_widget=None):
        """
        Recursively change the background color of a widget and its children.
        Optionally exclude a specific widget (and its children).

        Args:
            widget: The widget to modify.
            bg_color: The color to apply.
            exclude_widget: A widget to ignore during the recursive change.
        """
        if widget == exclude_widget:
            return # Skip the excluded widget and its children

        # Check if the current widget is the time control label itself
        is_tc_label = self.tc_label is not None and widget == self.tc_label

        bg_widgets = ('Label', 'Frame', 'Canvas', 'Text', 'Entry')

        # Apply background change if it's a standard widget OR if it's the tc_label
        if widget.winfo_class() in bg_widgets or is_tc_label:
            try:
                # Don't change the background of the delete button itself during card hover
                if widget != self.delete_button:
                    widget.configure(bg=bg_color)
            except tk.TclError:
                # Handle cases where bg cannot be configured (e.g., ttk widgets without style)
                pass

        # Recursively call for children, excluding the delete button
        for child in widget.winfo_children():
            # Ensure we don't recurse into the delete button's children if it's excluded
            if exclude_widget and child == exclude_widget:
                continue
            self._change_bg_recursive(child, bg_color, exclude_widget)

    def _start_animation(self, direction):
        """Start hover animation for shadow."""
        if self.animation_active:
            return

        self.animation_active = True
        self.animation_direction = direction
        self._animate_shadow(0)

    def _animate_shadow(self, step):
        """Animate shadow color transition."""
        if step >= self.animation_steps:
            self.animation_active = False
            return

        factor = step / self.animation_steps
        if self.animation_direction == "out":
            factor = 1 - factor

        # Create a slightly elevated effect with shadow positioning when hovering
        if self.animation_direction == "in":
            self.shadow.configure(pady=15 - (factor * 2), padx=15 - (factor * 1))
        else:
            self.shadow.configure(pady=13 + (factor * 2), padx=14 + (factor * 1))

        # Blend colors for smooth transition
        new_color = self._blend_colors(self.original_shadow_color, self.hover_shadow_color, factor)
        self.shadow.configure(bg=new_color)
        
        # Schedule next step if animation is still active
        self.after(self.animation_delay, lambda: self._animate_shadow(step + 1))

    def _blend_colors(self, color1, color2, factor):
        """Blend two colors based on a factor (0-1)."""
        r1, g1, b1 = self._hex_to_rgb(color1)
        r2, g2, b2 = self._hex_to_rgb(color2)
        r = int(r1 + (r2 - r1) * factor)
        g = int(g1 + (g2 - g1) * factor)
        b = int(b1 + (b2 - b1) * factor)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _hex_to_rgb(self, hex_color):
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def _darken_color(self, hex_color, amount):
        """Darken a hex color by a given amount (0-1)."""
        r, g, b = self._hex_to_rgb(hex_color)
        r = max(0, int(r * (1 - amount)))
        g = max(0, int(g * (1 - amount)))
        b = max(0, int(b * (1 - amount)))
        return f"#{r:02x}{g:02x}{b:02x}"

class HistoryTab(tk.Frame):
    """Onglet moderne pour afficher l'historique des parties."""

    def __init__(self, parent, user_profile: UserProfile, profile_manager, game_analyzer: GameAnalyzer, show_analysis_callback, **kwargs):
        super().__init__(parent, **kwargs)
        self.user_profile = user_profile
        self.profile_manager = profile_manager  # Store profile manager
        self.game_analyzer = game_analyzer  # Store GameAnalyzer instance
        self.show_analysis_callback = show_analysis_callback  # Store the callback function

        self.configure(padx=20, pady=20)
        header_frame = tk.Frame(self, bg=config.COLORS["profile_background"])
        header_frame.pack(fill="x", pady=(0, 15))
        
        filter_label = tk.Label(header_frame, text="Filtrer par:",
                              bg=config.COLORS["profile_background"],
                              fg=config.COLORS["profile_text"],
                              font=tkFont.Font(**config.FONTS["profile_stat_label"]))
        filter_label.pack(side="left", padx=(0, 10))
        
        player_var = tk.StringVar(value="Tous les joueurs")
        player_combo = ttk.Combobox(header_frame, textvariable=player_var, width=20,
                                   state="readonly")
        
        all_players = set()
        for game in self.user_profile.game_analyses.values():
            all_players.add(game.white_player)
            all_players.add(game.black_player)
        player_combo['values'] = ["Tous les joueurs"] + sorted(list(all_players))
        player_combo.pack(side="left", padx=5)
        player_combo.bind("<<ComboboxSelected>>", lambda e: self.apply_filters())
        
        color_var = tk.StringVar(value="Toutes les couleurs")
        color_combo = ttk.Combobox(header_frame, textvariable=color_var, width=17,
                                  state="readonly")
        color_combo['values'] = ["Toutes les couleurs", "Blancs", "Noirs"]
        color_combo.pack(side="left", padx=5)
        color_combo.bind("<<ComboboxSelected>>", lambda e: self.apply_filters())
        
        date_var = tk.StringVar(value="Tous les temps")
        date_combo = ttk.Combobox(header_frame, textvariable=date_var, width=15,
                                 state="readonly")
        date_combo['values'] = ["Tous les temps", "Semaine dernière", "Mois dernier", "Année"]
        date_combo.pack(side="left", padx=5)
        date_combo.bind("<<ComboboxSelected>>", lambda e: self.apply_filters())
        
        button_font = tkFont.Font(**config.FONTS["profile_button"])
        reset_button = tk.Button(header_frame, text="Réinitialiser",
                               command=self.reset_filters,
                               font=button_font,
                               bg=config.COLORS["profile_background"],
                               fg=config.COLORS["profile_text"],
                               activebackground=config.COLORS["profile_border"],
                               padx=12, pady=6,
                               borderwidth=1, relief="solid")
        reset_button.pack(side="right")
        
        self.filters = {
            "player": player_var,
            "color": color_var,
            "date": date_var
        }
        
        self.combos = {
            "player": player_combo,
            "color": color_combo,
            "date": date_combo
        }
        
        self.canvas = tk.Canvas(self, bg=config.COLORS["profile_background"],
                              highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        
        self.content_frame = tk.Frame(self.canvas, bg=config.COLORS["profile_background"])
        self.content_frame.bind("<Configure>", 
                              lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        
        self.content_window = self.canvas.create_window((0, 0), window=self.content_frame, anchor="nw")
        self.canvas.bind("<Configure>", self.resize_frame)
        
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)
        
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.populate_history()

    def resize_frame(self, event):
        """Ajuste la largeur du frame de contenu quand la fenêtre est redimensionnée."""
        self.canvas.itemconfig(self.content_window, width=event.width)
    
    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling on the canvas."""
        if event.num == 5 or event.delta < 0:
            delta = 1
        elif event.num == 4 or event.delta > 0:
            delta = -1
        else:
            delta = 0
        self.canvas.yview_scroll(delta, "units")
    
    def apply_filters(self):
        """Applique les filtres sélectionnés et met à jour l'affichage."""
        self.populate_history()
    
    def reset_filters(self):
        """Réinitialise tous les filtres."""
        for key, var in self.filters.items():
            default_value = self.combos[key]['values'][0]
            if var.get() != default_value:
                var.set(default_value)
        self.populate_history()

    def populate_history(self):
        """Remplit l'historique avec les parties filtrées et un style moderne."""
        # Mise à jour de la liste des joueurs dans le filtre déroulant
        self.update_player_list()
        
        # Vider le contenu actuel
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        filtered_games = self.filter_games()
        
        if not filtered_games:
            no_games_frame = tk.Frame(self.content_frame, bg=config.COLORS["profile_background"],
                                    padx=20, pady=40)
            no_games_frame.pack(fill="x")
            
            no_games_label = tk.Label(no_games_frame, text="Aucune partie ne correspond aux filtres sélectionnés",
                                    font=tkFont.Font(**config.FONTS["profile_stat_value"]),
                                    bg=config.COLORS["profile_background"],
                                    fg=config.COLORS["profile_secondary_text"])
            no_games_label.pack()
            return
        
        for game_analysis in filtered_games:
            game_card = GameCard(self.content_frame, 
                                 game_analysis, 
                                 self.user_profile, 
                                 self.profile_manager, 
                                 on_select=self.on_game_select, 
                                 on_delete=self.populate_history)
            game_card.pack(pady=(0, 10), padx=5, fill="x")

    def filter_games(self):
        """Filtre les parties selon les critères sélectionnés."""
        games = list(self.user_profile.game_analyses.values())
        
        games.sort(key=lambda g: g.game_date, reverse=True)
        
        player_filter = self.filters["player"].get()
        if player_filter != "Tous les joueurs":
            games = [g for g in games if g.white_player == player_filter or g.black_player == player_filter]
        
        color_filter = self.filters["color"].get()
        username_lower = self.user_profile.username.lower()
        if color_filter == "Blancs":
            games = [g for g in games if g.white_player.lower() == username_lower]
        elif color_filter == "Noirs":
            games = [g for g in games if g.black_player.lower() == username_lower]
        # Si "Toutes les couleurs" est sélectionné, on affiche toutes les parties où l'utilisateur apparaît
        # (soit en tant que Blanc, soit en tant que Noir)
        else:
            games = [g for g in games if g.white_player.lower() == username_lower or 
                                       g.black_player.lower() == username_lower]
        
        date_filter = self.filters["date"].get()
        if date_filter != "Tous les temps":
            today = datetime.date.today()
            
            if date_filter == "Semaine dernière":
                cutoff = today - datetime.timedelta(days=7)
            elif date_filter == "Mois dernier":
                cutoff = today - datetime.timedelta(days=30)
            elif date_filter == "Année":
                cutoff = today - datetime.timedelta(days=365)
            games = [g for g in games if g.game_date >= cutoff]
        
        return games

    def on_game_select(self, game_analysis):
        """Gère la sélection d'une partie."""
        print(f"Partie sélectionnée: {game_analysis.game_id}")

        if game_analysis.move_evaluations:
            if self.show_analysis_callback:
                # Call the callback with only the game_analysis argument
                self.show_analysis_callback(game_analysis)
            else:
                messagebox.showerror("Erreur", "Impossible d'ouvrir la vue d'analyse.", parent=self)
        else:
            messagebox.showinfo("Analyse Non Disponible",
                                "Cette partie n'a pas encore été analysée. Utilisez le bouton 'Analyser Tout' ou importez à nouveau le PGN.",
                                parent=self)

    def update_player_list(self):
        """Met à jour la liste des joueurs dans le filtre déroulant."""
        # Sauvegarder la sélection actuelle
        current_selection = self.filters["player"].get()
        
        # Récupérer tous les noms de joueurs dans les parties
        all_players = set()
        for game in self.user_profile.game_analyses.values():
            all_players.add(game.white_player)
            all_players.add(game.black_player)
            
        # Mettre à jour la liste des valeurs avec la sélection par défaut + les joueurs triés
        new_values = ["Tous les joueurs"] + sorted(list(all_players))
        self.combos["player"]["values"] = new_values
        
        # Restaurer la sélection si elle existe toujours dans la nouvelle liste
        if current_selection in new_values:
            self.filters["player"].set(current_selection)
        else:
            # Sinon, revenir à la sélection par défaut
            self.filters["player"].set("Tous les joueurs")