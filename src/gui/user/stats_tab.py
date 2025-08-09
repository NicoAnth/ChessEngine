"""
Onglet affichant les statistiques agrégées de l'utilisateur avec une interface moderne et élégante.
"""

import tkinter as tk
from tkinter import ttk, font as tkFont
from src.user import UserProfile
from src.utils import config
import math
import statistics

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
        super().__init__(parent, bd=0, **kwargs)
        self.configure(bg="#FFFFFF")  # Explicit background

        # Shadow (uses place so it doesn't influence requested size)
        self.shadow = tk.Frame(self, bg=config.COLORS["profile_card_shadow"], bd=0)
        self.shadow.place(x=3, y=3, relwidth=1.0, relheight=1.0)

        # Content frame (uses pack so geometry propagates)
        self._content_frame = tk.Frame(self, bg=config.COLORS["profile_card_bg"], bd=0, padx=20, pady=20)
        self._content_frame.pack(fill="both", expand=True)

        if title:
            self.title_label = tk.Label(
                self._content_frame,
                text=title,
                font=tkFont.Font(**config.FONTS["profile_section_title"]),
                bg=config.COLORS["profile_card_bg"],
                fg=config.COLORS["profile_header_text"]
            )
            self.title_label.pack(anchor="w", pady=(0, 15))

    def get_content_frame(self):
        return self._content_frame

class StatsTab(tk.Frame):
    """Onglet moderne pour afficher les statistiques de l'utilisateur."""

    def __init__(self, parent, user_profile: UserProfile, **kwargs):
        super().__init__(parent, **kwargs)
        self.user_profile = user_profile
        self.configure(padx=20, pady=20)

        # Scrollable canvas + vertical scrollbar
        self._canvas = tk.Canvas(self, bg=config.COLORS["profile_background"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self._canvas.yview)
        self._content_frame = tk.Frame(self._canvas, bg=config.COLORS["profile_background"])
        self._content_frame.bind(
            "<Configure>", lambda e: self._canvas.configure(scrollregion=self._canvas.bbox("all"))
        )
        window_id = self._canvas.create_window((0, 0), window=self._content_frame, anchor="nw")
        self._canvas.bind(
            "<Configure>", lambda e: self._canvas.itemconfig(window_id, width=e.width)
        )
        self._canvas.configure(yscrollcommand=scrollbar.set)
        self._canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Schedule bindings and section building
        self.after(10, self._bind_global_wheel)
        self.after(20, self._initialize_sections)

    def _bind_global_wheel(self):
        """Attach wheel events so scrolling works regardless of hovered child."""
        canvas = self._canvas

        def wheel(event):
            delta = 0
            if hasattr(event, "delta") and event.delta:
                delta = int(-1 * (event.delta / 120))  # Windows/Mac
            elif getattr(event, "num", None) == 4:
                delta = -3  # Linux up
            elif getattr(event, "num", None) == 5:
                delta = 3   # Linux down
            if delta:
                canvas.yview_scroll(delta, "units")
            return "break"

        # Prevent duplicate bindings
        for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            self.unbind_all(seq)
        self.bind_all("<MouseWheel>", wheel)
        self.bind_all("<Button-4>", wheel)
        self.bind_all("<Button-5>", wheel)

    def _initialize_sections(self):
        """Build all statistics sections (KPI, performance, openings)."""
        self._build_kpi_dashboard(self._content_frame)
        tk.Frame(self._content_frame, height=8, bg=config.COLORS["profile_background"]).pack(fill="x")
        self._build_performance_sections()
        self._build_openings_section(self._content_frame)

    def _build_performance_sections(self):
        """Build performance, counts distribution, phase and color sections."""
        overall_stats = self.user_profile.aggregated_stats.get("overall", {})

        # Container for performance & counts side by side
        performance_frame = tk.Frame(self._content_frame, bg=config.COLORS["profile_background"])
        performance_frame.pack(fill="x", pady=(0, 20))
        performance_frame.columnconfigure(0, weight=2)
        performance_frame.columnconfigure(1, weight=3)

        # --- Performance globale ---
        perf_card = StatCard(performance_frame, title="Performance Globale")
        perf_card.grid(row=0, column=0, sticky="nsew", padx=5, pady=3)
        perf_content = perf_card.get_content_frame()

        accuracy = overall_stats.get("accuracy", 0)
        if not isinstance(accuracy, (int, float)):
            accuracy = 0

        circular_frame = tk.Frame(perf_content, bg=config.COLORS["profile_card_bg"])
        circular_frame.pack(fill="x", pady=10)
        progress = CircularProgress(circular_frame, size=120, progress=accuracy,
                                    fg_color=config.COLORS["profile_accent"])
        progress.pack(side="left", padx=(10, 30))

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

        # --- Répartition des coups ---
        counts_card = StatCard(performance_frame, title="Qualité des Coups")
        counts_card.grid(row=0, column=1, sticky="nsew", padx=5, pady=3)
        counts_content = counts_card.get_content_frame()
        counts = overall_stats.get("counts", {})
        total_moves = overall_stats.get("total_moves", 0) or 1
        quality_order = ["Coup brillant", "Super coup", "Meilleur coup", "Excellent", "Bon coup",
                         "Théorie", "Imprécision", "Erreur", "Grosse erreur"]
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
        bars_frame = tk.Frame(counts_content, bg=config.COLORS["profile_card_bg"])
        bars_frame.pack(fill="x", pady=10)
        max_bar_width = 300
        for i, quality in enumerate(quality_order):
            count = counts.get(quality, 0)
            if count == 0 and quality not in ["Erreur", "Grosse erreur"]:
                continue
            percentage = count / total_moves * 100
            bar_width = int(max_bar_width * (percentage / 100))
            line_frame = tk.Frame(bars_frame, bg=config.COLORS["profile_card_bg"])
            line_frame.pack(fill="x", pady=2)
            tk.Label(line_frame, text=f"{quality}",
                     font=tkFont.Font(**config.FONTS["profile_stat_label"]),
                     bg=config.COLORS["profile_card_bg"],
                     fg=config.COLORS["profile_secondary_text"],
                     width=12, anchor="w").pack(side="left")
            bar_container = tk.Frame(line_frame, bg=config.COLORS["profile_background"], height=20)
            bar_container.pack(side="left", fill="x", expand=True, padx=(0, 10))
            bar = tk.Frame(bar_container, bg=quality_colors.get(quality, "#CCCCCC"), width=bar_width, height=18)
            bar.pack(side="left", anchor="w")
            tk.Label(line_frame, text=f"{count} ({percentage:.1f}%)",
                     font=tkFont.Font(**config.FONTS["profile_stat_value"]),
                     bg=config.COLORS["profile_card_bg"],
                     fg=config.COLORS["profile_text"]).pack(side="right")
            bar.config(width=1)
            def animate_bar(b, target_width, step=0):
                if step < 20:
                    current_width = int(target_width * (step / 20))
                    b.config(width=current_width)
                    self.after(20, animate_bar, b, target_width, step + 1)
                else:
                    b.config(width=target_width)
            self.after(100 + i * 50, animate_bar, bar, bar_width)

        # --- Performance par phase ---
        phase_card = StatCard(self._content_frame, title="Performance par Phase de Jeu")
        phase_card.pack(fill="x", pady=(0, 20))
        phase_content = phase_card.get_content_frame()
        phase_frame = tk.Frame(phase_content, bg=config.COLORS["profile_card_bg"])
        phase_frame.pack(fill="x")
        phase_stats = self.user_profile.aggregated_stats.get("phase_stats", {}).get("overall", {})
        phases = ["opening", "middlegame", "endgame"]
        phase_names = {"opening": "Ouverture", "middlegame": "Milieu de partie", "endgame": "Finale"}
        for i, phase in enumerate(phases):
            phase_data = phase_stats.get(phase, {})
            p_acc = phase_data.get("accuracy", 0)
            if not isinstance(p_acc, (int, float)):
                p_acc = 0
            phase_item = tk.Frame(phase_frame, bg=config.COLORS["profile_card_bg"])
            phase_item.grid(row=0, column=i, padx=10, sticky="nsew")
            phase_progress = CircularProgress(phase_item, size=100, progress=p_acc,
                                              fg_color=config.COLORS["profile_chart_colors"][i],
                                              text_color=config.COLORS["profile_text"])
            phase_progress.pack(pady=10)
            tk.Label(phase_item, text=phase_names.get(phase, phase.capitalize()),
                     font=tkFont.Font(**config.FONTS["profile_stat_value"]),
                     bg=config.COLORS["profile_card_bg"],
                     fg=config.COLORS["profile_text"]).pack(pady=(5, 0))
            tk.Label(phase_item, text=f"{phase_data.get('total_moves', 0)} coups",
                     font=tkFont.Font(**config.FONTS["profile_stat_label"]),
                     bg=config.COLORS["profile_card_bg"],
                     fg=config.COLORS["profile_secondary_text"]).pack()
        for i in range(3):
            phase_frame.columnconfigure(i, weight=1)

        # --- Performance par couleur ---
        colors_card = StatCard(self._content_frame, title="Performance par Couleur")
        colors_card.pack(fill="x")
        colors_content = colors_card.get_content_frame()
        colors_frame = tk.Frame(colors_content, bg=config.COLORS["profile_card_bg"])
        colors_frame.pack(fill="x")
        white_stats = self.user_profile.aggregated_stats.get("white", {}).copy()
        black_stats = self.user_profile.aggregated_stats.get("black", {}).copy()
        if (white_stats.get("game_count", 0) == 0 or not isinstance(white_stats.get("game_count", 0), int)) and self.user_profile.game_analyses:
            username_l = self.user_profile.username.lower()
            white_games = sum(1 for ga in self.user_profile.game_analyses.values() if ga.white_player.lower() == username_l)
            if white_games:
                white_stats["game_count"] = white_games
        if (black_stats.get("game_count", 0) == 0 or not isinstance(black_stats.get("game_count", 0), int)) and self.user_profile.game_analyses:
            username_l = self.user_profile.username.lower()
            black_games = sum(1 for ga in self.user_profile.game_analyses.values() if ga.black_player.lower() == username_l)
            if black_games:
                black_stats["game_count"] = black_games
        for i, (color, stats, label, bg_color, text_color) in enumerate([
            ("white", white_stats, "Blancs", "#FFFFFF", config.COLORS["profile_text"]),
            ("black", black_stats, "Noirs", "#333333", "#FFFFFF")
        ]):
            color_frame = tk.Frame(colors_frame, bg=config.COLORS["profile_card_bg"])
            color_frame.grid(row=0, column=i, padx=10, sticky="nsew")
            header = tk.Frame(color_frame, bg=bg_color, padx=10, pady=8)
            header.pack(fill="x")
            tk.Label(header, text=label,
                     font=tkFont.Font(**config.FONTS["profile_stat_value"]),
                     bg=bg_color, fg=text_color).pack()
            content = tk.Frame(color_frame, bg=config.COLORS["profile_card_bg"], padx=10, pady=10)
            content.pack(fill="x")
            c_acc = stats.get("accuracy", 0)
            if not isinstance(c_acc, (int, float)):
                c_acc = 0
            for j, (stat_label, stat_value) in enumerate([
                ("Précision", f"{c_acc:.1f}%"),
                ("Parties", str(stats.get("game_count", 0))),
                ("Coups", str(stats.get("total_moves", 0)))
            ]):
                row_frame = tk.Frame(content, bg=config.COLORS["profile_card_bg"])
                row_frame.pack(fill="x", pady=2)
                tk.Label(row_frame, text=stat_label,
                         font=tkFont.Font(**config.FONTS["profile_stat_label"]),
                         bg=config.COLORS["profile_card_bg"],
                         fg=config.COLORS["profile_secondary_text"]).pack(side="left")
                tk.Label(row_frame, text=stat_value,
                         font=tkFont.Font(**config.FONTS["profile_stat_value"]),
                         bg=config.COLORS["profile_card_bg"],
                         fg=config.COLORS["profile_text"]).pack(side="right")
        colors_frame.columnconfigure(0, weight=1)
        colors_frame.columnconfigure(1, weight=1)

    def _build_kpi_dashboard(self, parent):
        """Crée un tableau de bord de KPIs principaux en haut de l'onglet."""
        overall = self.user_profile.aggregated_stats.get("overall", {})
        counts = overall.get("counts", {})
        total_moves = overall.get("total_moves", 0) or 1
        game_count = self.user_profile.aggregated_stats.get("game_count", 0)  # parties réellement jouées par l'utilisateur
        analysis_count = self.user_profile.aggregated_stats.get("analysis_count", game_count)
        white_gc = self.user_profile.aggregated_stats.get("white", {}).get("game_count", 0)
        black_gc = self.user_profile.aggregated_stats.get("black", {}).get("game_count", 0)
        recognized_openings = self.user_profile.aggregated_stats.get("recognized_opening_games", 0)
        missing_openings = self.user_profile.aggregated_stats.get("missing_opening_games", 0)

        # Récupération des move_evaluations utilisateur pour stats avancées
        # (on reconstruit la liste depuis les analyses pour médiane/écart-type)
        move_qualities = []
        results = []  # Stocke 1 pour victoire, 0.5 pour nulles, 0 pour défaites
        for ga in self.user_profile.game_analyses.values():
            # Déterminer côté utilisateur
            is_white = ga.white_player.lower() == self.user_profile.username.lower()
            is_black = ga.black_player.lower() == self.user_profile.username.lower()
            if not (is_white or is_black):
                continue
            # Résultat
            res = ga.result.strip()
            if res == "1-0":
                results.append(1 if is_white else 0)
            elif res == "0-1":
                results.append(1 if is_black else 0)
            elif res == "1/2-1/2":
                results.append(0.5)
            # Move qualities
            for mv in ga.move_evaluations:
                if is_white and mv.get("side") == "White":
                    mq = mv.get("move_quality")
                    if isinstance(mq, (int, float)):
                        move_qualities.append(mq)
                elif is_black and mv.get("side") == "Black":
                    mq = mv.get("move_quality")
                    if isinstance(mq, (int, float)):
                        move_qualities.append(mq)

        # Score %
        score_percent = (sum(results) / len(results) * 100) if results else 0.0

        # Performance rating (simplifiée) : perf = opp_avg + (400 * (score - 0.5)) / max(0.01, score*(1-score))
        # Ici on n'a pas encore les Elos adverses => placeholder basé sur accuracy ~ elo delta
        # On propose une estimation: base 1500 + (accuracy - 50)*15
        accuracy = overall.get("accuracy", 0.0) or 0.0
        perf_rating = int(1500 + (accuracy - 50) * 15)
        perf_rating = max(600, perf_rating)

        # Précision moyenne (déjà accuracy / precision dans stats). Utilisons accuracy pour 'moyenne'.
        precision_linear = overall.get("precision", 0.0) or 0.0

        # Médiane et écart-type des move_qualities (convertis en %)
        if move_qualities:
            qualities_pct = [mq * 100 for mq in move_qualities]
            try:
                median_precision = statistics.median(qualities_pct)
            except statistics.StatisticsError:
                median_precision = 0.0
            if len(qualities_pct) > 1:
                try:
                    stdev_precision = statistics.pstdev(qualities_pct)
                except statistics.StatisticsError:
                    stdev_precision = 0.0
            else:
                stdev_precision = 0.0
        else:
            median_precision = 0.0
            stdev_precision = 0.0

        # Taux d'imprécisions / erreurs / gaffes (per 100 moves)
        imprecisions_per_100 = counts.get("Imprécision", 0) / total_moves * 100
        errors_per_100 = counts.get("Erreur", 0) / total_moves * 100
        blunders_per_100 = counts.get("Grosse erreur", 0) / total_moves * 100

        # Carte KPI
        kpi_card = StatCard(parent, title="Tableau de Bord")
        kpi_card.pack(fill="x", pady=(0, 20))
        card_body = kpi_card.get_content_frame()

        # Grille responsive
        grid = tk.Frame(card_body, bg=config.COLORS["profile_card_bg"])
        grid.pack(fill="x")
        for i in range(6):
            grid.columnconfigure(i, weight=1, uniform="kpi")

        # Fabrique de KPI
        def add_kpi(col, label, primary, secondary=None, accent="#4361EE"):
            wrapper = tk.Frame(grid, bg=config.COLORS["profile_card_bg"], padx=10, pady=5)
            wrapper.grid(row=0, column=col, sticky="nsew", padx=4)
            title_lbl = tk.Label(wrapper, text=label.upper(),
                                 font=tkFont.Font(family="Segoe UI", size=8, weight="bold"),
                                 fg=config.COLORS["profile_secondary_text"],
                                 bg=config.COLORS["profile_card_bg"])
            title_lbl.pack(anchor="w")
            val_lbl = tk.Label(wrapper, text=primary,
                               font=tkFont.Font(family="Segoe UI", size=18, weight="bold"),
                               fg=accent, bg=config.COLORS["profile_card_bg"])
            val_lbl.pack(anchor="w", pady=(2, 0))
            if secondary:
                sec_lbl = tk.Label(wrapper, text=secondary,
                                   font=tkFont.Font(family="Segoe UI", size=10),
                                   fg=config.COLORS["profile_text"],
                                   bg=config.COLORS["profile_card_bg"])
                sec_lbl.pack(anchor="w", pady=(2, 0))

        # Instanciations des KPI
        add_kpi(0, "Score %", f"{score_percent:.1f}%", f"{game_count} parties")
        add_kpi(1, "Perf Rating", str(perf_rating), "Estimation")
        add_kpi(2, "Précision", f"{accuracy:.1f}%", f"Lin: {precision_linear:.1f}%")
        add_kpi(3, "Median ±σ", f"{median_precision:.1f}%", f"±{stdev_precision:.1f}")
        add_kpi(4, "Erreurs/100", f"{errors_per_100:.2f}", f"Imp: {imprecisions_per_100:.2f}")
        add_kpi(5, "Blunders/100", f"{blunders_per_100:.2f}")

        # Ligne de cohérence des données
        info = tk.Frame(card_body, bg=config.COLORS["profile_card_bg"])
        info.pack(fill="x", pady=(10,0))
        note = (f"Analyses: {analysis_count}  |  Parties utilisateur: {game_count} (Blancs {white_gc} / Noirs {black_gc})  |  "
            f"Ouvertures reconnues: {recognized_openings}" + (f" (+{missing_openings} sans ECO)" if missing_openings else ""))
        tk.Label(info, text=note, font=tkFont.Font(family="Segoe UI", size=9),
             bg=config.COLORS["profile_card_bg"], fg=config.COLORS["profile_secondary_text"], anchor="w").pack(anchor="w")

    def _build_openings_section(self, parent):
        openings = self.user_profile.aggregated_stats.get("openings", {})
        if not openings:
            return

        # Trier par nombre de parties
        top = sorted(openings.items(), key=lambda x: x[1].get("games",0), reverse=True)[:10]

        card = StatCard(parent, title="Ouvertures - Top 10")
        card.pack(fill="x", pady=(20, 10))
        body = card.get_content_frame()

        headers = ["Ouverture", "Parties", "Score%", "Précision", "Perf", "Bl/100"]
        table = tk.Frame(body, bg=config.COLORS["profile_card_bg"])
        table.pack(fill="x")
        col_weights = [4,1,1,1,1,1]  # ouverture plus large
        for i,w in enumerate(col_weights):
            table.grid_columnconfigure(i, weight=w)
        # header
        for i,h in enumerate(headers):
            sticky = "w" if i == 0 else "e"
            tk.Label(table, text=h, font=tkFont.Font(family="Segoe UI", size=10, weight="bold"),
                     bg=config.COLORS["profile_card_bg"], fg=config.COLORS["profile_secondary_text"]).grid(row=0, column=i, padx=5, pady=2, sticky=sticky)
        # rows
        for r,(eco,data) in enumerate(top, start=1):
            name = data.get("name") or eco
            vals = [name, data.get("games",0), data.get("score_pct",0.0), data.get("precision",0.0), data.get("perf",0), data.get("blunders_per_100",0.0)]
            for c,val in enumerate(vals):
                anchor = "w" if c==0 else "e"
                tk.Label(table, text=str(val), font=tkFont.Font(family="Segoe UI", size=10),
                         bg=config.COLORS["profile_card_bg"], fg=config.COLORS["profile_text"]).grid(row=r, column=c, padx=5, pady=2, sticky=anchor)

        # Sortie de théorie
        theory_card = StatCard(parent, title="Sortie de Théorie")
        theory_card.pack(fill="x", pady=(0,10))
        t_body = theory_card.get_content_frame()
        avg_depth = sum(d.get("avg_depth",0) for _, d in top)/len(top) if top else 0
        avg_post = sum(d.get("avg_post_score",0) for _, d in top)/len(top) if top else 0
        for label, value in [
            ("Profondeur moyenne", f"{avg_depth:.1f} coups"),
            ("Évaluation moyenne post-livre", f"{avg_post:+.2f}")
        ]:
            f = tk.Frame(t_body, bg=config.COLORS["profile_card_bg"])
            f.pack(fill="x", pady=2)
            tk.Label(f, text=label, font=tkFont.Font(**config.FONTS["profile_stat_label"]),
                     bg=config.COLORS["profile_card_bg"], fg=config.COLORS["profile_secondary_text"]).pack(side="left")
            tk.Label(f, text=value, font=tkFont.Font(**config.FONTS["profile_stat_value"]),
                     bg=config.COLORS["profile_card_bg"], fg=config.COLORS["profile_text"]).pack(side="right")

        # Ouvertures problématiques
        problematic = [ (eco,d) for eco,d in openings.items() if d.get("problematic") ]
        if problematic:
            prob_card = StatCard(parent, title="Lignes Problématiques")
            prob_card.pack(fill="x", pady=(0,10))
            p_body = prob_card.get_content_frame()
            for eco, d in sorted(problematic, key=lambda x: x[1].get("blunders_per_100",0), reverse=True):
                f = tk.Frame(p_body, bg=config.COLORS["profile_card_bg"])
                f.pack(fill="x", pady=2)
                name = d.get("name") or eco
                desc = f"{name}  Bl/100: {d.get('blunders_per_100')}  Score%: {d.get('score_pct')}"
                tk.Label(f, text=desc, font=tkFont.Font(family="Segoe UI", size=10),
                         bg=config.COLORS["profile_card_bg"], fg=config.COLORS["profile_text"]).pack(anchor="w")

        # Stabilité répertoire
        stab_card = StatCard(parent, title="Stabilité des Ouvertures")
        stab_card.pack(fill="x", pady=(0,10))
        s_body = stab_card.get_content_frame()
        for eco, data in top:
            f = tk.Frame(s_body, bg=config.COLORS["profile_card_bg"])
            f.pack(fill="x", pady=1)
            name = data.get("name") or eco
            tk.Label(f, text=f"{name}", font=tkFont.Font(family="Segoe UI", size=10, weight="bold"),
                     bg=config.COLORS["profile_card_bg"], fg=config.COLORS["profile_secondary_text"]).pack(side="left")
            tk.Label(f, text=f"Stabilité: {data.get('stability',0)}%", font=tkFont.Font(family="Segoe UI", size=10),
                     bg=config.COLORS["profile_card_bg"], fg=config.COLORS["profile_text"]).pack(side="right")