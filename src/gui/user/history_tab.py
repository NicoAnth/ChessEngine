"""
Onglet affichant l'historique des parties analysées de l'utilisateur avec une interface moderne et élégante.
"""

import tkinter as tk
from tkinter import ttk, font as tkFont
from src.user import UserProfile, GameAnalysis
from src.utils import config, resource_loader
import datetime
from PIL import Image, ImageTk, ImageDraw

class GameCard(tk.Frame):
    """Carte représentant une partie d'échecs avec style moderne."""
    
    def __init__(self, parent, game_analysis, user_profile, on_select=None, **kwargs):
        super().__init__(parent, bg=config.COLORS["profile_card_bg"], padx=15, pady=15, bd=0, **kwargs)
        self.game_analysis = game_analysis
        self.user_profile = user_profile  # Store user_profile
        self.on_select = on_select
        
        # Shadow effect with a second frame
        self.shadow = tk.Frame(parent, bg=config.COLORS["profile_card_shadow"], padx=15, pady=15, bd=0)
        
        # Configure style and interaction
        self.configure(cursor="hand2")  # Hand cursor indicates clickable
        self.bind("<Button-1>", self._on_click)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        
        # Game header (players, date)
        header_frame = tk.Frame(self, bg=config.COLORS["profile_card_bg"])
        header_frame.pack(fill="x", expand=True)
        
        # White player side
        white_frame = tk.Frame(header_frame, bg=config.COLORS["profile_card_bg"])
        white_frame.pack(side="left", fill="y")
        
        white_label = tk.Label(white_frame, text=game_analysis.white_player,
                             font=tkFont.Font(**config.FONTS["profile_stat_value"]),
                             bg=config.COLORS["profile_card_bg"],
                             fg=config.COLORS["profile_text"],
                             anchor="w")
        white_label.pack(side="left")
        
        # Result in center
        result = game_analysis.result
        result_label = tk.Label(header_frame, text=result,
                              font=tkFont.Font(**config.FONTS["profile_stat_value"]),
                              bg=config.COLORS["profile_card_bg"],
                              fg=config.COLORS["profile_accent"],
                              anchor="center",
                              width=5)
        result_label.pack(side="left", expand=True)
        
        # Black player side
        black_frame = tk.Frame(header_frame, bg=config.COLORS["profile_card_bg"])
        black_frame.pack(side="right", fill="y")
        
        black_label = tk.Label(black_frame, text=game_analysis.black_player,
                             font=tkFont.Font(**config.FONTS["profile_stat_value"]),
                             bg=config.COLORS["profile_card_bg"],
                             fg=config.COLORS["profile_text"],
                             anchor="e")
        black_label.pack(side="right")
        
        # Separator
        separator = ttk.Separator(self, orient="horizontal")
        separator.pack(fill="x", pady=10)
        
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
    
    def grid(self, **kwargs):
        """Positionne à la fois l'ombre et la carte principale."""
        self.shadow.grid(kwargs)
        super().grid(kwargs)
    
    def pack(self, **kwargs):
        """Positionne à la fois l'ombre et la carte principale."""
        padding = kwargs.pop("pady", 5)
        if isinstance(padding, tuple):
            shadow_padding = (padding[0], padding[1] + 3)
        else:
            shadow_padding = (padding, padding + 3)
        
        self.shadow.pack(pady=shadow_padding, fill="x", **kwargs)
        super().pack(pady=padding, fill="x", **kwargs)
        self.shadow.lower(self)  # Ensure shadow stays behind
    
    def _on_click(self, event):
        """Appelle la fonction de rappel avec l'analyse de partie."""
        if self.on_select:
            self.on_select(self.game_analysis)
    
    def _on_enter(self, event):
        """Effet de survol."""
        self.configure(bg=config.COLORS["profile_border"])
        for child in self.winfo_children():
            if child.winfo_class() == 'Frame':
                child.configure(bg=config.COLORS["profile_border"])
                for subchild in child.winfo_children():
                    if subchild.winfo_class() in ('Label', 'Frame'):
                        subchild.configure(bg=config.COLORS["profile_border"])
                        for subsubchild in subchild.winfo_children():
                            if subsubchild.winfo_class() in ('Label', 'Frame'):
                                subsubchild.configure(bg=config.COLORS["profile_border"])
    
    def _on_leave(self, event):
        """Annule l'effet de survol."""
        self.configure(bg=config.COLORS["profile_card_bg"])
        for child in self.winfo_children():
            if child.winfo_class() == 'Frame':
                child.configure(bg=config.COLORS["profile_card_bg"])
                for subchild in child.winfo_children():
                    if subchild.winfo_class() in ('Label', 'Frame'):
                        subchild.configure(bg=config.COLORS["profile_card_bg"])
                        for subsubchild in subchild.winfo_children():
                            if subsubchild.winfo_class() in ('Label', 'Frame'):
                                subsubchild.configure(bg=config.COLORS["profile_card_bg"])

class HistoryTab(tk.Frame):
    """Onglet moderne pour afficher l'historique des parties."""

    def __init__(self, parent, user_profile: UserProfile, **kwargs):
        super().__init__(parent, **kwargs)
        self.user_profile = user_profile

        # Configure direct styling instead of ttk style
        self.configure(padx=20, pady=20)  # Use direct padding instead of ttk padding

        # Create a header frame using tk.Frame instead of ttk.Frame
        header_frame = tk.Frame(self, bg=config.COLORS["profile_background"])
        header_frame.pack(fill="x", pady=(0, 15))
        
        # Change ttk.Label to tk.Label with direct styling
        filter_label = tk.Label(header_frame, text="Filtrer par:",
                              bg=config.COLORS["profile_background"],
                              fg=config.COLORS["profile_text"],
                              font=tkFont.Font(**config.FONTS["profile_stat_label"]))
        filter_label.pack(side="left", padx=(0, 10))
        
        # Keep ttk.Combobox since they're hard to replace
        player_var = tk.StringVar(value="Tous les joueurs")
        player_combo = ttk.Combobox(header_frame, textvariable=player_var, width=20,
                                   state="readonly")
        
        # Get unique players
        all_players = set()
        for game in self.user_profile.game_analyses.values():
            all_players.add(game.white_player)
            all_players.add(game.black_player)
        player_combo['values'] = ["Tous les joueurs"] + sorted(list(all_players))
        player_combo.pack(side="left", padx=5)
        player_combo.bind("<<ComboboxSelected>>", lambda e: self.apply_filters())
        
        # Keep ttk.Combobox for color filter
        color_var = tk.StringVar(value="Toutes les couleurs")
        color_combo = ttk.Combobox(header_frame, textvariable=color_var, width=17,
                                  state="readonly")
        color_combo['values'] = ["Toutes les couleurs", "Blancs", "Noirs"]
        color_combo.pack(side="left", padx=5)
        color_combo.bind("<<ComboboxSelected>>", lambda e: self.apply_filters())
        
        # Keep ttk.Combobox for date filter
        date_var = tk.StringVar(value="Tous les temps")
        date_combo = ttk.Combobox(header_frame, textvariable=date_var, width=15,
                                 state="readonly")
        date_combo['values'] = ["Tous les temps", "Semaine dernière", "Mois dernier", "Année"]
        date_combo.pack(side="left", padx=5)
        date_combo.bind("<<ComboboxSelected>>", lambda e: self.apply_filters())
        
        # Replace ttk.Button with tk.Button using direct styling
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
        
        # Store filter variables and comboboxes for later use
        self.filters = {
            "player": player_var,
            "color": color_var,
            "date": date_var
        }
        
        # Store comboboxes for accessing their values
        self.combos = {
            "player": player_combo,
            "color": color_combo,
            "date": date_combo
        }
        
        # --- Main Content Area ---
        # Use Canvas with scrollbar for scrollable content, with direct styling
        self.canvas = tk.Canvas(self, bg=config.COLORS["profile_background"],
                              highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        
        # Replace ttk.Frame with tk.Frame
        self.content_frame = tk.Frame(self.canvas, bg=config.COLORS["profile_background"])
        self.content_frame.bind("<Configure>", 
                              lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        
        # Make content_frame expand to full width of canvas
        self.content_window = self.canvas.create_window((0, 0), window=self.content_frame, anchor="nw", width=self.winfo_width())
        self.canvas.bind("<Configure>", self.resize_frame)
        
        # Configure scrolling
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Populate history with filtered games
        self.populate_history()
    
    def resize_frame(self, event):
        """Ajuste la largeur du frame de contenu quand la fenêtre est redimensionnée."""
        self.canvas.itemconfig(self.content_window, width=event.width)
    
    def apply_filters(self):
        """Applique les filtres sélectionnés et met à jour l'affichage."""
        self.populate_history()
    
    def reset_filters(self):
        """Réinitialise tous les filtres."""
        for key, var in self.filters.items():
            # Get the first value (usually "All") from the corresponding combobox
            default_value = self.combos[key]['values'][0]
            if var.get() != default_value:
                var.set(default_value)
        self.populate_history()

    def populate_history(self):
        """Remplit l'historique avec les parties filtrées et un style moderne."""
        # Clear existing content
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Get filtered games
        filtered_games = self.filter_games()
        
        if not filtered_games:
            # Display message if no games match filters
            no_games_frame = tk.Frame(self.content_frame, bg=config.COLORS["profile_background"],
                                    padx=20, pady=40)
            no_games_frame.pack(fill="x")
            
            no_games_label = tk.Label(no_games_frame, text="Aucune partie ne correspond aux filtres sélectionnés",
                                    font=tkFont.Font(**config.FONTS["profile_stat_value"]),
                                    bg=config.COLORS["profile_background"],
                                    fg=config.COLORS["profile_secondary_text"])
            no_games_label.pack()
            return
        
        # Display each game as a card
        for game_analysis in filtered_games:
            game_card = GameCard(self.content_frame, game_analysis, self.user_profile, on_select=self.on_game_select)
            game_card.pack(pady=(0, 10), padx=5)
    
    def filter_games(self):
        """Filtre les parties selon les critères sélectionnés."""
        games = list(self.user_profile.game_analyses.values())
        
        # Sort by date (most recent first)
        games.sort(key=lambda g: g.game_date, reverse=True)
        
        # Apply player filter
        player_filter = self.filters["player"].get()
        if player_filter != "Tous les joueurs":
            games = [g for g in games if g.white_player == player_filter or g.black_player == player_filter]
        
        # Apply color filter
        color_filter = self.filters["color"].get()
        if color_filter == "Blancs":
            games = [g for g in games if g.white_player.lower() == self.user_profile.username.lower()]
        elif color_filter == "Noirs":
            games = [g for g in games if g.black_player.lower() == self.user_profile.username.lower()]
        
        # Apply date filter
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
        
        # This method could be expanded to:
        # 1. Open a detailed view of the game
        # 2. Load the game in the main chess board view
        # 3. Show a popup with game details
        
        # For now, we'll just print details to the console
        # TODO: Implement game viewing functionality