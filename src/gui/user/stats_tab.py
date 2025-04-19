"""
Onglet affichant les statistiques agrégées de l'utilisateur avec une interface moderne et élégante.
"""

import tkinter as tk
from tkinter import ttk, font as tkFont
from src.user import UserProfile
from src.utils import config
import math

class CircularProgress(tk.Canvas):
    """Widget de progression circulaire pour afficher des statistiques de façon visuelle."""
    
    def __init__(self, parent, size=100, progress=0, fg_color="#4361EE", bg_color="#E9ECEF",
                 text_color="#344767", value="0%", **kwargs):
        super().__init__(parent, width=size, height=size, bg=parent["bg"], highlightthickness=0, **kwargs)
        self.size = size
        self.fg_color = fg_color
        self.bg_color = bg_color
        self.text_color = text_color
        
        # Dessiner l'arrière-plan du cercle
        self.create_circle(size/2, size/2, size/2 - 5, fill=bg_color)
        
        # Dessiner l'arc de progression
        self.arc = self.create_arc(5, 5, size-5, size-5, start=90, extent=0, fill=fg_color, outline="")
        
        # Dessiner le texte au centre
        text_font = tkFont.Font(family="Segoe UI", size=int(size/6), weight="bold")
        self.value_text = self.create_text(size/2, size/2, text=value, fill=text_color, font=text_font)
        
        # Animer la progression
        self.set_progress(progress)
        
    def create_circle(self, x, y, r, **kwargs):
        return self.create_oval(x-r, y-r, x+r, y+r, **kwargs)
    
    def set_progress(self, progress):
        """Anime la progression de 0 à la valeur finale."""
        # Limiter la progression entre 0 et 100
        progress = min(100, max(0, progress))
        
        # Animer la progression en 20 étapes
        steps = 20
        step_size = progress / steps
        
        def animate(step):
            if step <= steps:
                current_progress = step * step_size
                extent = -3.6 * current_progress  # 3.6 = 360 / 100
                self.itemconfig(self.arc, extent=extent)
                self.after(20, animate, step + 1)
        
        animate(0)
        
        # Mettre à jour le texte avec la valeur finale
        self.itemconfig(self.value_text, text=f"{int(progress)}%")

class StatCard(tk.Frame):
    """Carte stylisée pour afficher une statistique clé."""
    
    def __init__(self, parent, title="", value="", icon=None, **kwargs):
        # Remove bg=parent.cget("bg") as ttk parent might not support it
        super().__init__(parent, bd=0, **kwargs) 
        self.configure(bg="#FFFFFF") # Set a default background explicitly if needed

        # Shadow Frame (slightly larger, placed first, covers the container)
        self.shadow = tk.Frame(self, bg=config.COLORS["profile_card_shadow"], bd=0)
        # Place shadow slightly offset down and right
        self.shadow.place(x=3, y=3, relwidth=1.0, relheight=1.0)

        # Content Frame (on top of shadow, slightly smaller than container)
        self._content_frame = tk.Frame(self, bg=config.COLORS["profile_card_bg"], bd=0, padx=20, pady=20)
        self._content_frame.place(x=0, y=0, relwidth=1.0, relheight=1.0) # Position at top-left

        # Titre de la carte (inside content frame)
        if title:
            self.title_label = tk.Label(self._content_frame, text=title,
                                      font=tkFont.Font(**config.FONTS["profile_section_title"]),
                                      bg=config.COLORS["profile_card_bg"],
                                      fg=config.COLORS["profile_header_text"])
            self.title_label.pack(anchor="w", pady=(0, 15))

    def get_content_frame(self):
        """Retourne le frame interne où les widgets de contenu doivent être ajoutés."""
        return self._content_frame

class StatsTab(ttk.Frame):
    """Onglet moderne pour afficher les statistiques de l'utilisateur."""

    def __init__(self, parent, user_profile: UserProfile, **kwargs):
        super().__init__(parent, **kwargs)
        self.user_profile = user_profile

        # Use style from parent window if available
        self.style = getattr(parent, 'style', ttk.Style())

        # Configure base style for this tab
        self.configure(padding=20, style="Profile.TFrame")

        # --- Main Content Frame ---
        # Utiliser un Canvas avec scrollbar pour les longs contenus
        canvas = tk.Canvas(self, bg=config.COLORS["profile_background"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        
        # Frame de contenu qui contiendra tous les widgets
        content_frame = ttk.Frame(canvas, style="Profile.TFrame")
        content_frame.bind("<Configure>", 
                          lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        # Ajouter le frame au canvas
        canvas_frame = canvas.create_window((0, 0), window=content_frame, anchor="nw")
        
        # Configurer le canvas pour qu'il s'étende horizontalement avec la fenêtre
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_frame, width=e.width))
        
        # Configurer la scrollbar
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Placement du canvas et de la scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # --- Contenu de l'onglet ---
        # Première rangée: Performance Globale avec graphique circulaire
        performance_frame = ttk.Frame(content_frame, style="Profile.TFrame")
        performance_frame.pack(fill="x", pady=(0, 20))
        performance_frame.columnconfigure(0, weight=2)
        performance_frame.columnconfigure(1, weight=3)
        
        # --- Carte de performance globale ---
        overall_stats = self.user_profile.aggregated_stats.get("overall", {})
        perf_card = StatCard(performance_frame, title="Performance Globale")
        perf_card.grid(row=0, column=0, sticky="nsew", padx=5, pady=3) # Apply grid here

        # Get the content frame to add widgets inside the card
        perf_content = perf_card.get_content_frame()

        # Progression circulaire pour l'accuracy
        accuracy = overall_stats.get("accuracy", 0)
        if not isinstance(accuracy, (int, float)):
            accuracy = 0

        circular_frame = tk.Frame(perf_content, bg=config.COLORS["profile_card_bg"]) # Parent is perf_content
        circular_frame.pack(fill="x", pady=10)

        progress = CircularProgress(circular_frame, size=120, progress=accuracy,
                                   fg_color=config.COLORS["profile_accent"])
        progress.pack(side="left", padx=(10, 30))

        # Stats textuelles
        stats_frame = tk.Frame(circular_frame, bg=config.COLORS["profile_card_bg"])
        stats_frame.pack(side="left", fill="both", expand=True)
        
        for i, (label, value) in enumerate([
            ("Précision moyenne", f"{accuracy:.1f}%" if isinstance(accuracy, (int, float)) else "N/A"),
            ("Parties analysées", str(self.user_profile.aggregated_stats.get("game_count", 0))),
            ("Total coups joués", str(overall_stats.get("total_moves", 0)))
        ]):
            tk.Label(stats_frame, text=label, 
                   font=tkFont.Font(**config.FONTS["profile_stat_label"]),
                   bg=config.COLORS["profile_card_bg"],
                   fg=config.COLORS["profile_secondary_text"]).grid(row=i, column=0, sticky="w", pady=3)
            
            tk.Label(stats_frame, text=value,
                   font=tkFont.Font(**config.FONTS["profile_stat_value"]),
                   bg=config.COLORS["profile_card_bg"],
                   fg=config.COLORS["profile_text"]).grid(row=i, column=1, sticky="e", pady=3, padx=(20, 0))

        # --- Carte de répartition des coups ---
        counts_card = StatCard(performance_frame, title="Qualité des Coups")
        counts_card.grid(row=0, column=1, sticky="nsew", padx=5, pady=3) # Apply grid here

        # Get the content frame
        counts_content = counts_card.get_content_frame()

        counts = overall_stats.get("counts", {})
        total_moves = overall_stats.get("total_moves", 0) or 1  # Éviter division par zéro
        
        # Ordre des qualités pour l'affichage
        quality_order = ["Coup brillant", "Super coup", "Meilleur coup", "Excellent", "Bon coup", 
                        "Théorie", "Imprécision", "Erreur", "Grosse erreur"]
        
        # Couleurs associées aux qualités (utiliser les couleurs de classification ou par défaut)
        quality_colors = {
            "Coup brillant": "#D500F9",
            "Super coup": "#00E5FF",
            "Meilleur coup": "#3BD97B",
            "Excellent": "#6BE29B",
            "Bon coup": "#8EF0B5",
            "Théorie": "#A78BFA",
            "Imprécision": "#F7C76E",
            "Erreur": "#FF6B6B",
            "Grosse erreur": "#F44336"
        }
        
        # Frame pour les barres (Parent is counts_content)
        bars_frame = tk.Frame(counts_content, bg=config.COLORS["profile_card_bg"])
        bars_frame.pack(fill="x", pady=10)
        
        # Largeur maximale de barre en pixels
        max_bar_width = 300
        
        # Créer une barre pour chaque qualité
        for i, quality in enumerate(quality_order):
            count = counts.get(quality, 0)
            if count == 0 and quality not in ["Erreur", "Grosse erreur"]:  # Toujours montrer les erreurs
                continue
                
            percentage = count / total_moves * 100
            bar_width = int(max_bar_width * (percentage / 100))
            
            # Frame pour chaque ligne (qualité + barre)
            line_frame = tk.Frame(bars_frame, bg=config.COLORS["profile_card_bg"])
            line_frame.pack(fill="x", pady=2)
            
            # Label de qualité
            quality_label = tk.Label(line_frame, text=f"{quality}",
                                   font=tkFont.Font(**config.FONTS["profile_stat_label"]),
                                   bg=config.COLORS["profile_card_bg"],
                                   fg=config.COLORS["profile_secondary_text"],
                                   width=12, anchor="w")
            quality_label.pack(side="left")
            
            # Frame pour la barre
            bar_container = tk.Frame(line_frame, bg=config.COLORS["profile_background"], height=20)
            bar_container.pack(side="left", fill="x", expand=True, padx=(0, 10))
            
            # Barre colorée
            bar = tk.Frame(bar_container, bg=quality_colors.get(quality, "#CCCCCC"), 
                         width=bar_width, height=18)
            bar.pack(side="left", anchor="w")
            
            # Pourcentage
            percentage_label = tk.Label(line_frame, text=f"{count} ({percentage:.1f}%)",
                                      font=tkFont.Font(**config.FONTS["profile_stat_value"]),
                                      bg=config.COLORS["profile_card_bg"],
                                      fg=config.COLORS["profile_text"])
            percentage_label.pack(side="right")
            
            # Animation de la barre (initialement 0, puis expansion)
            bar.config(width=1)
            
            def animate_bar(b, target_width, step=0):
                if step < 20:  # 20 steps animation
                    current_width = int(target_width * (step / 20))
                    b.config(width=current_width)
                    self.after(20, animate_bar, b, target_width, step + 1)
                else:
                    b.config(width=target_width)  # Final width
            
            # Démarrer l'animation après un court délai
            self.after(100 + i * 50, animate_bar, bar, bar_width)
        
        # --- Phase Performance Card ---
        # Analyse par phase (ouverture, milieu, finale)
        phase_card = StatCard(content_frame, title="Performance par Phase de Jeu")
        phase_card.pack(fill="x", pady=(0, 20)) # Apply pack here

        # Get the content frame
        phase_content = phase_card.get_content_frame()

        phase_frame = tk.Frame(phase_content, bg=config.COLORS["profile_card_bg"]) # Parent is phase_content
        phase_frame.pack(fill="x")
        
        # Récupérer les statistiques par phase
        phase_stats = self.user_profile.aggregated_stats.get("phase_stats", {}).get("overall", {})
        phases = ["opening", "middlegame", "endgame"]
        phase_names = {"opening": "Ouverture", "middlegame": "Milieu de partie", "endgame": "Finale"}
        
        for i, phase in enumerate(phases):
            phase_data = phase_stats.get(phase, {})
            accuracy = phase_data.get("accuracy", 0)
            if not isinstance(accuracy, (int, float)):
                accuracy = 0
                
            # Frame pour chaque phase (Parent is phase_frame)
            phase_item = tk.Frame(phase_frame, bg=config.COLORS["profile_card_bg"])
            phase_item.grid(row=0, column=i, padx=10, sticky="nsew")
            
            # Indicateur circulaire pour la phase
            phase_progress = CircularProgress(phase_item, size=100, progress=accuracy,
                                            fg_color=config.COLORS["profile_chart_colors"][i],
                                            text_color=config.COLORS["profile_text"])
            phase_progress.pack(pady=10)
            
            # Nom de la phase
            phase_label = tk.Label(phase_item, text=phase_names.get(phase, phase.capitalize()),
                                 font=tkFont.Font(**config.FONTS["profile_stat_value"]),
                                 bg=config.COLORS["profile_card_bg"],
                                 fg=config.COLORS["profile_text"])
            phase_label.pack(pady=(5, 0))
            
            # Nombre de coups
            moves_label = tk.Label(phase_item, text=f"{phase_data.get('total_moves', 0)} coups",
                                 font=tkFont.Font(**config.FONTS["profile_stat_label"]),
                                 bg=config.COLORS["profile_card_bg"],
                                 fg=config.COLORS["profile_secondary_text"])
            moves_label.pack()
        
        # Configure grid pour égaliser les colonnes
        phase_frame.columnconfigure(0, weight=1)
        phase_frame.columnconfigure(1, weight=1)
        phase_frame.columnconfigure(2, weight=1)
        
        # --- Other stats can be added below ---
        # For example, compare White vs Black performance
        colors_card = StatCard(content_frame, title="Performance par Couleur")
        colors_card.pack(fill="x") # Apply pack here

        # Get the content frame
        colors_content = colors_card.get_content_frame()

        colors_frame = tk.Frame(colors_content, bg=config.COLORS["profile_card_bg"]) # Parent is colors_content
        colors_frame.pack(fill="x")
        
        white_stats = self.user_profile.aggregated_stats.get("white", {})
        black_stats = self.user_profile.aggregated_stats.get("black", {})
        
        # Colonnes pour blanc et noir
        for i, (color, stats, label, bg_color, text_color) in enumerate([
            ("white", white_stats, "Blancs", "#FFFFFF", config.COLORS["profile_text"]),
            ("black", black_stats, "Noirs", "#333333", "#FFFFFF")
        ]):
            color_frame = tk.Frame(colors_frame, bg=config.COLORS["profile_card_bg"]) # Parent is colors_frame
            color_frame.grid(row=0, column=i, padx=10, sticky="nsew")
            
            # En-tête avec fond de couleur
            header = tk.Frame(color_frame, bg=bg_color, padx=10, pady=8)
            header.pack(fill="x")
            
            header_text = tk.Label(header, text=label,
                                 font=tkFont.Font(**config.FONTS["profile_stat_value"]),
                                 bg=bg_color,
                                 fg=text_color)
            header_text.pack()
            
            # Contenu
            content = tk.Frame(color_frame, bg=config.COLORS["profile_card_bg"], padx=10, pady=10)
            content.pack(fill="x")
            
            accuracy = stats.get("accuracy", 0)
            if not isinstance(accuracy, (int, float)):
                accuracy = 0
                
            # Afficher les statistiques
            for j, (stat_label, stat_value) in enumerate([
                ("Précision", f"{accuracy:.1f}%"),
                ("Parties", str(stats.get("game_count", 0))),
                ("Coups", str(stats.get("total_moves", 0)))
            ]):
                row_frame = tk.Frame(content, bg=config.COLORS["profile_card_bg"]) # Parent is content
                row_frame.pack(fill="x", pady=2)
                
                lab = tk.Label(row_frame, text=stat_label,
                             font=tkFont.Font(**config.FONTS["profile_stat_label"]),
                             bg=config.COLORS["profile_card_bg"],
                             fg=config.COLORS["profile_secondary_text"])
                lab.pack(side="left")
                
                val = tk.Label(row_frame, text=stat_value,
                             font=tkFont.Font(**config.FONTS["profile_stat_value"]),
                             bg=config.COLORS["profile_card_bg"],
                             fg=config.COLORS["profile_text"])
                val.pack(side="right")
        
        # Configure grid pour égaliser les colonnes
        colors_frame.columnconfigure(0, weight=1)
        colors_frame.columnconfigure(1, weight=1)