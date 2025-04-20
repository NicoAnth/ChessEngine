import tkinter as tk
from tkinter import filedialog, messagebox, font as tkFont
from src.user import UserProfile, UserProfileManager, GameAnalysis
from src.utils import config, resource_loader
from .stats_tab import StatsTab
from .history_tab import HistoryTab
from src.gui.moderntabs import ModernTabs
import chess.pgn
from src.core.chess_game import ChessGame
from src.analysis.game_analyzer import GameAnalyzer
import datetime
from PIL import Image, ImageTk, ImageDraw, ImageFont

class UserProfileWindow(tk.Toplevel):
    """Fenêtre moderne et élégante pour afficher et gérer le profil utilisateur."""

    def __init__(self, parent, user_profile: UserProfile, profile_manager: UserProfileManager, game_analyzer: GameAnalyzer, **kwargs):
        super().__init__(parent, **kwargs)
        self.user_profile = user_profile
        self.profile_manager = profile_manager
        self.game_analyzer = game_analyzer
        self.parent = parent

        self.title(f"Profil de {self.user_profile.username}")
        self.geometry("900x700")
        self.configure(bg=config.COLORS["profile_background"])
        self.transient(parent)
        self.grab_set()

        # --- Main Frame ---
        main_frame = tk.Frame(self, bg=config.COLORS["profile_background"])
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Create Header Panel with Gradient Effect ---
        header_height = 150
        header_canvas = tk.Canvas(main_frame, height=header_height, 
                                  bg=config.COLORS["profile_header_bg"],
                                  highlightthickness=0)
        header_canvas.pack(fill=tk.X, pady=(0, 20))
        
        # Create gradient header effect
        for i in range(header_height):
            r1, g1, b1 = int(config.COLORS["profile_header_bg"][1:3], 16), int(config.COLORS["profile_header_bg"][3:5], 16), int(config.COLORS["profile_header_bg"][5:7], 16)
            r2, g2, b2 = int(config.COLORS["profile_header_gradient"][1:3], 16), int(config.COLORS["profile_header_gradient"][3:5], 16), int(config.COLORS["profile_header_gradient"][5:7], 16)
            
            ratio = i / header_height
            r = int(r1 * (1 - ratio) + r2 * ratio)
            g = int(g1 * (1 - ratio) + g2 * ratio)
            b = int(b1 * (1 - ratio) + b2 * ratio)
            
            color = f'#{r:02x}{g:02x}{b:02x}'
            header_canvas.create_line(0, i, 2000, i, fill=color)
        
        # --- Create and add avatar circle ---
        try:
            profile_image = resource_loader.load_image("profile_button.png", (80, 80))
            if profile_image:
                self.profile_image = profile_image
                header_canvas.create_oval(40-40, 75-40, 40+40, 75+40, fill=config.COLORS["profile_card_bg"], outline="")
                header_canvas.create_image(40, 75, image=profile_image)
            else:
                self._create_fallback_avatar(header_canvas, self.user_profile.username)
        except Exception:
            self._create_fallback_avatar(header_canvas, self.user_profile.username)
        
        # Add username and member since info
        header_canvas.create_text(100, 65, text=self.user_profile.username,
                                  anchor=tk.W, font=tkFont.Font(**config.FONTS["profile_username"]),
                                  fill=config.COLORS["profile_header_text"])
        
        member_since = f"Membre depuis {self.user_profile.creation_date.strftime('%d %B %Y')}"
        header_canvas.create_text(100, 95, text=member_since,
                                  anchor=tk.W, font=tkFont.Font(**config.FONTS["profile_header_info"]),
                                  fill=config.COLORS["profile_secondary_text"])
        
        # --- Import/Actions Button Frame ---
        button_frame_on_canvas = tk.Frame(header_canvas, bg=config.COLORS["profile_header_gradient"])
        header_canvas.create_window(880, 75, window=button_frame_on_canvas, anchor="e")

        button_font = tkFont.Font(**config.FONTS["profile_button"])
        button_kwargs = {
            "font": button_font,
            "bg": config.COLORS["profile_accent"],
            "fg": "white",
            "activebackground": config.COLORS["profile_accent_hover"],
            "activeforeground": "white",
            "padx": 12,
            "pady": 6,
            "borderwidth": 0,
            "relief": tk.FLAT,
            "cursor": "hand2"
        }

        import_button = tk.Button(button_frame_on_canvas, text=" Importer PGN", 
                                  command=self.import_pgn_files, 
                                  width=15, **button_kwargs)
        import_button.pack(side=tk.LEFT, padx=(0, 10))
        
        close_button = tk.Button(button_frame_on_canvas, text=" Fermer", 
                                 command=self.destroy, 
                                 width=10, **button_kwargs)
        close_button.pack(side=tk.LEFT)

        # --- Content Frame ---
        content_frame = tk.Frame(main_frame, bg=config.COLORS["profile_background"], padx=20, pady=20)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # --- Summary Stats Panel ---
        stats_summary = tk.Frame(content_frame, bg=config.COLORS["profile_background"])
        stats_summary.pack(fill=tk.X, pady=(0, 15))
        
        for i, (stat_title, stat_value) in enumerate([
            ("Parties Analysées", self.user_profile.aggregated_stats.get('game_count', 0)),
            ("Précision Moyenne", f"{self.user_profile.aggregated_stats.get('overall', {}).get('accuracy', 'N/A')}%"),
            ("Dernière Activité", self.user_profile.last_login.strftime('%d/%m/%Y'))
        ]):
            stat_card = tk.Frame(stats_summary, bg=config.COLORS["profile_card_bg"],
                                 padx=15, pady=15, bd=0)
            stat_card.grid(row=0, column=i, padx=5, sticky="nsew")
            
            shadow_frame = tk.Frame(stats_summary, bg=config.COLORS["profile_card_shadow"],
                                    padx=15, pady=15, bd=0)
            shadow_frame.grid(row=0, column=i, padx=5, sticky="nsew", pady=(3, 0))
            shadow_frame.lower(stat_card)
            
            value_font = tkFont.Font(**config.FONTS["profile_stat_value"])
            value_font.configure(size=16)
            
            value_label = tk.Label(stat_card, text=stat_value,
                                   font=value_font, bg=config.COLORS["profile_card_bg"],
                                   fg=config.COLORS["profile_text"])
            value_label.pack(anchor="w")
            
            title_label = tk.Label(stat_card, text=stat_title,
                                   font=tkFont.Font(**config.FONTS["profile_stat_label"]),
                                   bg=config.COLORS["profile_card_bg"],
                                   fg=config.COLORS["profile_secondary_text"])
            title_label.pack(anchor="w", pady=(5, 0))
        
        stats_summary.grid_columnconfigure(0, weight=1)
        stats_summary.grid_columnconfigure(1, weight=1)
        stats_summary.grid_columnconfigure(2, weight=1)

        # --- Modern Tabs Implementation ---
        self.tabs = ModernTabs(content_frame)
        self.tabs.pack(fill=tk.BOTH, expand=True)

        self.stats_tab = StatsTab(self.tabs.content_frame, self.user_profile, bg=config.COLORS["profile_background"])
        self.history_tab = HistoryTab(self.tabs.content_frame, self.user_profile, bg=config.COLORS["profile_background"])

        self.tabs.add_tab("Statistiques", self.stats_tab)
        self.tabs.add_tab("Historique", self.history_tab)
        
        self._apply_tab_styling()

    def import_pgn_files(self):
        file_paths = filedialog.askopenfilenames(
            title="Sélectionner des fichiers PGN à importer",
            filetypes=[("Fichiers PGN", "*.pgn"), ("Tous les fichiers", "*.*")],
            parent=self
        )

        if not file_paths:
            return

        imported_count = 0
        failed_count = 0
        skipped_count = 0

        progress_win = tk.Toplevel(self)
        progress_win.title("Importation...")
        progress_win.geometry("350x120")
        progress_win.configure(bg=config.COLORS["profile_background"])
        progress_win.transient(self)
        progress_win.grab_set()
        progress_label = tk.Label(progress_win, text="Importation en cours...",
                                  bg=config.COLORS["profile_background"],
                                  fg=config.COLORS["profile_text"],
                                  font=tkFont.Font(**config.FONTS["label"]))
        progress_label.pack(pady=(20, 10))
        progress_bar = tk.Canvas(progress_win, width=300, height=20, bg=config.COLORS["profile_border"])
        progress_bar.pack(fill=tk.X, padx=20, pady=(0, 20))
        self.update_idletasks()

        for file_path in file_paths:
            try:
                import io
                with open(file_path, 'r', encoding='utf-8') as pgn_file:
                    while True:
                        game_node = chess.pgn.read_game(pgn_file)
                        if game_node is None:
                            break

                        headers = game_node.headers
                        game_id_from_headers = f"{headers.get('White', 'NA')}_{headers.get('Black', 'NA')}_{headers.get('Date', 'NA')}_{headers.get('Event', 'NA')}"
                        if game_id_from_headers in self.user_profile.game_analyses:
                            skipped_count += 1
                            continue

                        temp_game = ChessGame()
                        temp_game.load_from_pgn(game_node)

                        analysis_results = self.game_analyzer.analyze_game(
                            list(temp_game.board.move_stack),
                            lambda p: None
                        )

                        date_str = headers.get("Date", "????.??.??")
                        try:
                            year, month, day = map(int, date_str.split('.'))
                            game_date = datetime.date(year, month, day)
                        except ValueError:
                            game_date = datetime.date.today()

                        exporter = chess.pgn.StringExporter(headers=True, variations=True, comments=True)
                        pgn_text = game_node.accept(exporter)

                        game_analysis = GameAnalysis(
                            game_date=game_date,
                            white_player=headers.get("White", "Unknown"),
                            black_player=headers.get("Black", "Unknown"),
                            result=headers.get("Result", "*"),
                            event=headers.get("Event"),
                            site=headers.get("Site"),
                            round=headers.get("Round"),
                            eco=headers.get("ECO"),
                            pgn_text=pgn_text,
                            move_evaluations=analysis_results.get("move_evaluations", []),
                            position_history=analysis_results.get("position_history", []),
                            white_stats=analysis_results.get("white_stats", {}),
                            black_stats=analysis_results.get("black_stats", {}),
                            white_phase_stats=analysis_results.get("white_phase_stats", {}),
                            black_phase_stats=analysis_results.get("black_phase_stats", {}),
                            critical_moments=analysis_results.get("critical_moments", []),
                            game_difficulty=analysis_results.get("game_difficulty", {}),
                            game_id=game_id_from_headers
                        )

                        self.user_profile.game_analyses[game_analysis.game_id] = game_analysis
                        self.user_profile._update_aggregated_stats()

                        imported_count += 1
                        progress_label.config(text=f"Importé: {imported_count}, Échec: {failed_count}, Ignoré: {skipped_count}")
                        self.update_idletasks()

            except Exception as e:
                failed_count += 1
                progress_label.config(text=f"Importé: {imported_count}, Échec: {failed_count}, Ignoré: {skipped_count}")
                self.update_idletasks()

        progress_win.destroy()

        self.profile_manager.save_profile(self.user_profile)
        self.history_tab.populate_history()

        messagebox.showinfo(
            "Importation Terminée",
            f"Importation terminée.\n\n"
            f"Parties importées et analysées : {imported_count}\n"
            f"Parties déjà existantes (ignorées) : {skipped_count}\n"
            f"Échecs d'importation/analyse : {failed_count}",
            parent=self
        )

    def _create_fallback_avatar(self, parent_frame, username):
        avatar_canvas = tk.Canvas(parent_frame, width=80, height=80, 
                                  bg=config.COLORS["profile_accent"], 
                                  highlightthickness=0)
        avatar_canvas.pack(side="left", padx=(30, 15))
        
        initial = username[0].upper() if username else "?"
        
        try:
            font = ImageFont.truetype("arial.ttf", 36) 
        except IOError:
            print("Arial font not found, using default Tkinter font for avatar.")
            font = tkFont.Font(family="Segoe UI", size=24, weight="bold")
            avatar_canvas.create_text(40, 40, text=initial, 
                                      font=font, 
                                      fill="white")
            return

        img = Image.new('RGB', (80, 80), color=config.COLORS["profile_accent"])
        draw = ImageDraw.Draw(img)
        
        try:
            bbox = draw.textbbox((0, 0), initial, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        except AttributeError:
            text_width, text_height = draw.textsize(initial, font=font)
             
        x = (80 - text_width) / 2
        y = (80 - text_height) / 2 - 5
        
        draw.text((x, y), initial, font=font, fill="white")
        
        self.fallback_avatar_image = ImageTk.PhotoImage(img)
        avatar_canvas.create_image(0, 0, anchor="nw", image=self.fallback_avatar_image)

    def _apply_tab_styling(self):
        for tab_title, tab_data in self.tabs.tabs.items():
            button = tab_data["button"]
            underline = tab_data["underline"]
            
            button.configure(
                font=("Segoe UI", 11),
                padx=15, 
                pady=8,
                bg=config.COLORS["profile_background"],
                activebackground=config.COLORS["profile_accent"],
                fg=config.COLORS["profile_text"],
                activeforeground="white",
                relief=tk.FLAT,
                borderwidth=0,
                highlightthickness=0
            )
            
            underline.configure(
                bg=config.COLORS["profile_accent"] if tab_title == self.tabs.current_tab else config.COLORS["profile_background"],
                height=3
            )
            
        self.tabs.content_frame.configure(
            bg=config.COLORS["profile_background"],
            padx=5,
            pady=10
        )
