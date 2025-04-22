import tkinter as tk
from tkinter import filedialog, messagebox, font as tkFont
from src.user.profile import UserProfile, UserProfileManager, GameAnalysis
from src.utils import config, resource_loader
from .stats_tab import StatsTab
from .history_tab import HistoryTab
from src.gui.moderntabs import ModernTabs
import chess.pgn
from src.core.chess_game import ChessGame
from src.analysis.game_analyzer import GameAnalyzer
from src.gui.analysis_view import GameAnalysisView
import datetime
import os
import shutil
from PIL import Image, ImageTk, ImageDraw, ImageFont
import io
import concurrent.futures
import threading
import queue

class UserProfileWindow(tk.Toplevel):
    """Fenêtre moderne et élégante pour afficher et gérer le profil utilisateur."""

    def __init__(self, parent, user_profile: UserProfile, profile_manager: UserProfileManager, game_analyzer: GameAnalyzer, piece_images, **kwargs):
        super().__init__(parent, **kwargs)
        self.user_profile = user_profile
        self.profile_manager = profile_manager
        self.game_analyzer = game_analyzer
        self.parent = parent
        self.piece_images = piece_images

        self.title(f"Profil de {self.user_profile.username}")
        # Augmentation de la taille par défaut
        self.geometry("1000x800") 
        self.configure(bg=config.COLORS["profile_background"])
        self.transient(parent)
        self.grab_set()

        # --- Main Frame ---
        main_frame = tk.Frame(self, bg=config.COLORS["profile_background"])
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Create Header Panel ---
        header_height = 150
        self.header_canvas = tk.Canvas(main_frame, height=header_height,
                                       bg=config.COLORS["profile_header_bg"],
                                       highlightthickness=0)
        self.header_canvas.pack(fill=tk.X, pady=(0, 20))

        self._create_gradient_header()

        # --- Avatar Properties ---
        self.avatar_center_x = 60
        self.avatar_center_y = 75
        self.avatar_radius = 40
        self.avatar_size = (80, 80)

        # --- Draw Avatar ---
        self._draw_avatar()

        # --- Bind Click Event to Header ---
        self.header_canvas.bind("<Button-1>", self._handle_header_click)
        self.header_canvas.bind("<Motion>", self._handle_header_motion)
        self.header_canvas.bind("<Leave>", lambda e: self.header_canvas.config(cursor=""))

        # --- Add username and member since info ---
        self._draw_user_info()

        # --- Add Buttons ---
        self._create_header_buttons()

        # --- Content Frame ---
        content_frame = tk.Frame(main_frame, bg=config.COLORS["profile_background"], padx=20, pady=20)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # --- Summary Stats Panel ---
        self._create_stats_summary(content_frame)

        # --- Modern Tabs Implementation ---
        self._create_tabs(content_frame)

    def _create_gradient_header(self):
        header_height = int(self.header_canvas.cget("height"))
        r1, g1, b1 = self.winfo_rgb(config.COLORS["profile_header_bg"])
        r2, g2, b2 = self.winfo_rgb(config.COLORS["profile_header_gradient"])
        r1, g1, b1 = r1 // 256, g1 // 256, b1 // 256
        r2, g2, b2 = r2 // 256, g2 // 256, b2 // 256

        for i in range(header_height):
            ratio = i / header_height
            r = int(r1 * (1 - ratio) + r2 * ratio)
            g = int(g1 * (1 - ratio) + g2 * ratio)
            b = int(b1 * (1 - ratio) + b2 * ratio)
            color = f'#{r:02x}{g:02x}{b:02x}'
            self.header_canvas.create_line(0, i, self.winfo_width(), i, fill=color, tags="gradient")
        self.header_canvas.tag_lower("gradient")

    def _draw_avatar(self):
        """Draws the user avatar (custom, default, or fallback) on the header canvas."""
        # Clear previous avatar items
        self.header_canvas.delete("avatar")

        loaded_image = None
        image_type = None  # To track what was loaded: 'custom', 'default', 'fallback'

        # 1. Try loading custom avatar
        full_avatar_path = self.profile_manager.get_avatar_full_path(self.user_profile)
        if full_avatar_path:
            try:
                img = Image.open(full_avatar_path).convert("RGBA")
                mask = Image.new('L', self.avatar_size, 0)
                draw = ImageDraw.Draw(mask)
                draw.ellipse((0, 0) + self.avatar_size, fill=255)
                img = img.resize(self.avatar_size, Image.Resampling.LANCZOS)
                img.putalpha(mask)
                self.custom_avatar_image = ImageTk.PhotoImage(img)
                loaded_image = self.custom_avatar_image
                image_type = 'custom'
                print(f"Loaded custom avatar: {full_avatar_path}")
            except Exception as e:
                print(f"Error loading or processing custom avatar {full_avatar_path}: {e}")

        # 2. Try loading default avatar if custom failed or not set
        if not loaded_image:
            try:
                # Try loading with PIL first for masking
                default_img_pil = resource_loader.load_image_pil("profile_button.png")
                if default_img_pil:
                    default_img_pil = default_img_pil.convert("RGBA")
                    mask = Image.new('L', self.avatar_size, 0)
                    draw = ImageDraw.Draw(mask)
                    draw.ellipse((0, 0) + self.avatar_size, fill=255)
                    default_img_pil = default_img_pil.resize(self.avatar_size, Image.Resampling.LANCZOS)
                    default_img_pil.putalpha(mask)
                    self.default_profile_image = ImageTk.PhotoImage(default_img_pil)
                    loaded_image = self.default_profile_image
                    image_type = 'default'
                    print("Loaded and masked default avatar.")
                else:
                    # Fallback to non-masked default if PIL loading failed
                    default_image_tk = resource_loader.load_image("profile_button.png", self.avatar_size)
                    if default_image_tk:
                        self.default_profile_image = default_image_tk
                        loaded_image = self.default_profile_image
                        image_type = 'default'
                        print("Loaded default avatar (no mask).")
                    else:
                        print("Default avatar 'profile_button.png' not found.")
            except AttributeError:
                # Fallback if load_image_pil doesn't exist
                try:
                    default_image_tk = resource_loader.load_image("profile_button.png", self.avatar_size)
                    if default_image_tk:
                        self.default_profile_image = default_image_tk
                        loaded_image = self.default_profile_image
                        image_type = 'default'
                        print("Loaded default avatar (no mask, load_image_pil missing).")
                    else:
                        print("Default avatar 'profile_button.png' not found.")
                except Exception as e:
                    print(f"Error loading default avatar (tk): {e}")
            except Exception as e:
                print(f"Error loading or processing default avatar: {e}")

        # 3. Use fallback if both custom and default failed
        if not loaded_image:
            print("Using fallback avatar.")
            image_type = 'fallback'
            # Draw the circle background ONLY for the fallback avatar
            self.header_canvas.create_oval(
                self.avatar_center_x - self.avatar_radius,
                self.avatar_center_y - self.avatar_radius,
                self.avatar_center_x + self.avatar_radius,
                self.avatar_center_y + self.avatar_radius,
                fill=config.COLORS["profile_accent"],  # Use accent color for fallback background
                outline="", tags="avatar"
            )
            # Create the fallback initial text/image
            self._create_fallback_avatar(self.header_canvas, self.user_profile.username, self.avatar_center_x, self.avatar_center_y, tags="avatar")
        else:
            # Draw the loaded custom or default image
            self.header_canvas.create_image(self.avatar_center_x, self.avatar_center_y, image=loaded_image, tags="avatar")

        # Ensure avatar is above gradient
        self.header_canvas.tag_raise("avatar", "gradient")

    def _create_fallback_avatar(self, parent_canvas, username, center_x, center_y, tags=None):
        """Crée l'initiale pour l'avatar de secours (le cercle est dessiné dans _draw_avatar)."""
        avatar_size = self.avatar_size[0]
        initial = username[0].upper() if username else "?"

        # Tente d'utiliser une police spécifique, sinon utilise une police par défaut
        try:
            # Utilise Pillow pour un meilleur rendu de texte si possible
            font = ImageFont.truetype("arial.ttf", 36)
            # Create a smaller transparent image just for the text
            img = Image.new('RGBA', (avatar_size, avatar_size), (255, 255, 255, 0))
            draw = ImageDraw.Draw(img)

            # Use textbbox for better centering
            try:
                bbox = draw.textbbox((0, 0), initial, font=font, anchor="lt")  # Pillow 9.2.0+
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                x = (avatar_size - text_width) / 2 - bbox[0]
                y = (avatar_size - text_height) / 2 - bbox[1]
            except TypeError:  # Older Pillow or different anchor behavior
                try:
                    # Pillow >= 8.0
                    bbox = draw.textbbox((0, 0), initial, font=font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                    x = (avatar_size - text_width) / 2
                    y = (avatar_size - text_height) / 2
                except AttributeError:  # Very old Pillow
                    text_width, text_height = draw.textsize(initial, font=font)
                    x = (avatar_size - text_width) / 2
                    y = (avatar_size - text_height) / 2

            draw.text((x, y), initial, font=font, fill="white")

            # Convertit l'image Pillow en PhotoImage Tkinter et la stocke
            self.fallback_avatar_render = ImageTk.PhotoImage(img)
            # Place l'image (texte) sur le canvas parent aux coordonnées spécifiées
            parent_canvas.create_image(center_x, center_y, image=self.fallback_avatar_render, tags=tags)

        except (IOError, NameError, FileNotFoundError):  # Added FileNotFoundError for font
            print("Arial font or Pillow not found, using default Tkinter font for fallback avatar.")
            tk_font = tkFont.Font(family="Segoe UI", size=24, weight="bold")
            # Draw text directly on the canvas
            parent_canvas.create_text(center_x, center_y, text=initial,
                                      font=tk_font,
                                      fill="white", tags=tags)

    def _draw_user_info(self):
        self.header_canvas.delete("userinfo")
        username_x = self.avatar_center_x + self.avatar_radius + 20
        self.header_canvas.create_text(username_x, self.avatar_center_y - 10, text=self.user_profile.username,
                                       anchor=tk.W, font=tkFont.Font(**config.FONTS["profile_username"]),
                                       fill=config.COLORS["profile_header_text"], tags="userinfo")

        member_since = f"Membre depuis {self.user_profile.creation_date.strftime('%d %B %Y')}"
        self.header_canvas.create_text(username_x, self.avatar_center_y + 20, text=member_since,
                                       anchor=tk.W, font=tkFont.Font(**config.FONTS["profile_header_info"]),
                                       fill=config.COLORS["profile_secondary_text"], tags="userinfo")
        self.header_canvas.tag_raise("userinfo")

    def _create_header_buttons(self):
        button_frame = tk.Frame(self.header_canvas, bg=config.COLORS["profile_header_gradient"])
        self.header_canvas.create_window(self.winfo_width() - 20, self.avatar_center_y,
                                         window=button_frame, anchor="e", tags="buttons")

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

        analyze_button = tk.Button(button_frame, text=" Analyser Tout",
                                   command=self.analyze_all_unalyzed_games,
                                   width=15, **button_kwargs)
        analyze_button.pack(side=tk.LEFT, padx=(0, 10))

        import_button = tk.Button(button_frame, text=" Importer PGN",
                                  command=self.import_pgn_files,
                                  width=15, **button_kwargs)
        import_button.pack(side=tk.LEFT, padx=(0, 10))

        close_button = tk.Button(button_frame, text=" Fermer",
                                 command=self.destroy,
                                 width=10, **button_kwargs)
        close_button.pack(side=tk.LEFT)
        self.header_canvas.tag_raise("buttons")

        self.header_canvas.bind("<Configure>", self._on_header_resize)

    def _on_header_resize(self, event):
        self.header_canvas.delete("gradient")
        self._create_gradient_header()
        self.header_canvas.coords("buttons", event.width - 20, self.avatar_center_y)
        self.header_canvas.tag_raise("avatar")
        self.header_canvas.tag_raise("userinfo")
        self.header_canvas.tag_raise("buttons")

    def _create_stats_summary(self, parent_frame):
        stats_summary = tk.Frame(parent_frame, bg=config.COLORS["profile_background"])
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

    def _create_tabs(self, parent_frame):
        self.tabs = ModernTabs(parent_frame)
        self.tabs.pack(fill=tk.BOTH, expand=True)

        self.stats_tab = StatsTab(self.tabs.content_frame, self.user_profile, bg=config.COLORS["profile_background"])
        # Pass game_analyzer and the new callback method to HistoryTab
        self.history_tab = HistoryTab(self.tabs.content_frame,
                                      self.user_profile,
                                      self.profile_manager,
                                      self.game_analyzer, # Pass the analyzer instance
                                      self.show_game_analysis, # Pass the callback method
                                      bg=config.COLORS["profile_background"])

        self.tabs.add_tab("Statistiques", self.stats_tab)
        self.tabs.add_tab("Historique", self.history_tab)

        self._apply_tab_styling()

    def _is_click_on_avatar(self, x, y):
        distance_sq = (x - self.avatar_center_x)**2 + (y - self.avatar_center_y)**2
        return distance_sq <= self.avatar_radius**2

    def _handle_header_motion(self, event):
        if self._is_click_on_avatar(event.x, event.y):
            self.header_canvas.config(cursor="hand2")
        else:
            self.header_canvas.config(cursor="")

    def _handle_header_click(self, event):
        if self._is_click_on_avatar(event.x, event.y):
            self._change_avatar()

    def _change_avatar(self):
        file_path = filedialog.askopenfilename(
            title="Sélectionner une image pour l'avatar",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.gif *.bmp"), ("Tous les fichiers", "*.*")],
            parent=self
        )

        if not file_path:
            return

        try:
            with Image.open(file_path) as img:
                img.verify()

            new_avatar_path = self.profile_manager.set_avatar(self.user_profile.username, file_path)

            if new_avatar_path:
                self.user_profile.avatar_path = new_avatar_path
                self._draw_avatar()
                messagebox.showinfo("Avatar Mis à Jour", "Votre nouvel avatar a été défini avec succès.", parent=self)
            else:
                messagebox.showerror("Erreur Avatar", "Impossible de définir le nouvel avatar.", parent=self)

        except FileNotFoundError:
            messagebox.showerror("Erreur Fichier", f"Le fichier sélectionné n'a pas été trouvé:\n{file_path}", parent=self)
        except (IOError, SyntaxError, Image.UnidentifiedImageError):
            messagebox.showerror("Erreur Image", f"Le fichier sélectionné n'est pas une image valide:\n{file_path}", parent=self)
        except Exception as e:
            messagebox.showerror("Erreur Inconnue", f"Une erreur est survenue : {e}")
            print(f"Unexpected error changing avatar: {e}")

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
        # Simple progress indicator (could be replaced with ttk.Progressbar if ttk is used)
        progress_info_label = tk.Label(progress_win, text="0/0",
                                       bg=config.COLORS["profile_background"],
                                       fg=config.COLORS["profile_text"])
        progress_info_label.pack(pady=5)
        self.update_idletasks()

        total_files = len(file_paths)
        for idx, file_path in enumerate(file_paths):
            progress_info_label.config(text=f"{idx+1}/{total_files}")
            progress_label.config(text=f"Traitement: {os.path.basename(file_path)}")
            self.update_idletasks()
            try:
                import io
                import chess.pgn
                import datetime
                from src.core.chess_game import ChessGame
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as pgn_file:
                    while True:
                        try:
                            game_node = chess.pgn.read_game(pgn_file)
                        except Exception as read_err:
                            print(f"Error reading game from PGN {file_path}: {read_err}")
                            failed_count += 1
                            continue

                        if game_node is None:
                            break

                        headers = game_node.headers
                        game_id_parts = [
                            headers.get('Event', 'UnknownEvent'),
                            headers.get('Site', 'UnknownSite'),
                            headers.get('Date', '????.??.??').replace('.', '-'),
                            headers.get('Round', '?'),
                            headers.get('White', 'UnknownWhite'),
                            headers.get('Black', 'UnknownBlack'),
                            headers.get('Result', '*')
                        ]
                        game_id_from_headers = "_".join(part.replace(' ', '_') for part in game_id_parts)

                        if game_id_from_headers in self.user_profile.game_analyses:
                            skipped_count += 1
                            continue

                        temp_game = ChessGame()
                        temp_game.load_from_pgn(game_node)

                        if not self.game_analyzer:
                             print("Game Analyzer not available. Skipping analysis.")
                             analysis_results = {}
                        else:
                            analysis_results = self.game_analyzer.analyze_game(
                                list(temp_game.board.move_stack),
                                lambda p: None
                            )

                        date_str = headers.get("Date", "????.??.??")
                        try:
                            cleaned_date_str = date_str.replace('.', '-').split(' ')[0]
                            game_date = datetime.datetime.strptime(cleaned_date_str, '%Y-%m-%d').date()
                        except ValueError:
                            try:
                                game_date = datetime.datetime.strptime(cleaned_date_str, '%d-%m-%Y').date()
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
                            time_control=headers.get("TimeControl"), # Extraire la cadence
                            pgn_text=pgn_text,
                            move_evaluations=analysis_results.get("move_evaluations", []),
                            position_history=analysis_results.get("position_history", []),
                            white_stats=analysis_results.get("white_stats", {}),
                            black_stats=analysis_results.get("black_stats", {}),
                            white_phase_stats=analysis_results.get("white_phase_stats", {}),
                            black_phase_stats=analysis_results.get("black_phase_stats", {}),
                            critical_moments=analysis_results.get("critical_moments", []),
                            game_difficulty=analysis_results.get("difficulty_metrics", {}),
                            game_id=game_id_from_headers,
                            analysis_date=datetime.datetime.now()
                        )

                        self.user_profile.game_analyses[game_analysis.game_id] = game_analysis
                        if hasattr(self.user_profile, '_update_aggregated_stats'):
                            self.user_profile._update_aggregated_stats()
                        else:
                            print("Warning: UserProfile._update_aggregated_stats method not found.")

                        imported_count += 1

            except Exception as e:
                failed_count += 1
                print(f"Erreur lors du traitement du fichier {file_path}: {e}")

        progress_win.destroy()

        self.profile_manager.save_profile(self.user_profile)

        if hasattr(self, 'history_tab') and self.history_tab:
             self.history_tab.populate_history()
        if hasattr(self, 'stats_tab') and self.stats_tab:
             if hasattr(self.stats_tab, 'update_stats'):
                 self.stats_tab.update_stats()
             else:
                 print("StatsTab does not have an update_stats method. Manual refresh might be needed.")

        messagebox.showinfo(
            "Importation Terminée",
            f"Importation terminée.\n\n"
            f"Parties importées et analysées : {imported_count}\n"
            f"Parties déjà existantes (ignorées) : {skipped_count}\n"
            f"Échecs d'importation/analyse : {failed_count}",
            parent=self
        )

    def analyze_all_unalyzed_games(self):
        """Analyzes all games in the profile that haven't been analyzed yet in a background thread."""
        games_to_analyze = []
        for game_id, analysis in self.user_profile.game_analyses.items():
            # Check if analysis data is missing or incomplete
            if not analysis.move_evaluations or not analysis.white_stats or not analysis.black_stats:
                games_to_analyze.append(analysis)

        if not games_to_analyze:
            messagebox.showinfo("Analyse", "Toutes les parties dans le profil sont déjà analysées.", parent=self)
            return

        if not self.game_analyzer:
            messagebox.showerror("Erreur", "Le moteur d'analyse n'est pas disponible.", parent=self)
            return

        # --- Threading Setup ---
        self.analysis_queue = queue.Queue()
        self.analysis_thread = threading.Thread(
            target=self._run_analysis_thread,
            args=(games_to_analyze,),
            daemon=True # Allows the app to exit even if this thread is running
        )
        # --- End Threading Setup ---

        # --- Progress Window Setup ---
        self.progress_win = tk.Toplevel(self)
        self.progress_win.title("Analyse en cours...")
        self.progress_win.geometry("400x170") # Slightly taller for status
        self.progress_win.configure(bg=config.COLORS["profile_background"])
        self.progress_win.transient(self)
        self.progress_win.grab_set()
        self.progress_win.protocol("WM_DELETE_WINDOW", self._cancel_analysis) # Handle window close

        self.progress_label = tk.Label(self.progress_win, text="Préparation de l'analyse...",
                                  bg=config.COLORS["profile_background"],
                                  fg=config.COLORS["profile_text"],
                                  font=tkFont.Font(**config.FONTS["label"]))
        self.progress_label.pack(pady=(20, 5))

        self.progress_info_label = tk.Label(self.progress_win, text=f"0/{len(games_to_analyze)}",
                                       bg=config.COLORS["profile_background"],
                                       fg=config.COLORS["profile_text"])
        self.progress_info_label.pack(pady=5)

        self.current_game_label = tk.Label(self.progress_win, text="", wraplength=380,
                                      bg=config.COLORS["profile_background"],
                                      fg=config.COLORS["profile_secondary_text"])
        self.current_game_label.pack(pady=5)

        self.status_label = tk.Label(self.progress_win, text="", wraplength=380,
                                     bg=config.COLORS["profile_background"],
                                     fg=config.COLORS["profile_secondary_text"])
        self.status_label.pack(pady=5)

        # Add a cancel button
        cancel_button = tk.Button(self.progress_win, text="Annuler", command=self._cancel_analysis,
                                  font=tkFont.Font(**config.FONTS["profile_button"]),
                                  bg=config.COLORS["profile_background"],
                                  fg=config.COLORS["profile_text"],
                                  activebackground=config.COLORS["profile_border"],
                                  activeforeground=config.COLORS["profile_text"],
                                  relief=tk.SOLID,
                                  borderwidth=1,
                                  padx=10, pady=5)
        cancel_button.pack(pady=(10, 10))
        # --- End Progress Window Setup ---

        # Disable analysis button while running
        # Assuming the button is stored or can be accessed, e.g., self.analyze_button
        # self.analyze_button.config(state=tk.DISABLED)

        self.analysis_cancelled = False
        self.analysis_thread.start()
        self.after(100, self._check_analysis_queue) # Start checking the queue

    def _run_analysis_thread(self, games_to_analyze):
        """The actual analysis loop running in the background thread."""
        analyzed_count = 0
        failed_count = 0
        total_games = len(games_to_analyze)

        for idx, game_analysis in enumerate(games_to_analyze):
            if self.analysis_cancelled:
                self.analysis_queue.put(("status", "Analyse annulée."))
                break

            # Send progress update to the main thread via queue
            progress_update = {
                "current": idx + 1,
                "total": total_games,
                "game_info": f"{game_analysis.white_player} vs {game_analysis.black_player} ({game_analysis.game_date})"
            }
            self.analysis_queue.put(("progress", progress_update))

            try:
                pgn_stream = io.StringIO(game_analysis.pgn_text)
                game_node = chess.pgn.read_game(pgn_stream)
                if not game_node:
                    self.analysis_queue.put(("log", f"Skipping game {game_analysis.game_id}: Could not parse PGN."))
                    failed_count += 1
                    continue

                headers = game_node.headers
                game_analysis.time_control = headers.get("TimeControl", game_analysis.time_control)

                board = game_node.board()
                moves = list(game_node.mainline_moves())

                # --- Call analyze_game --- 
                # This call itself might take time, but it's now in a background thread
                self.analysis_queue.put(("status", f"Analyse du moteur pour {game_analysis.game_id}..."))
                analysis_results = self.game_analyzer.analyze_game(moves, analysis_board=board)
                # --- Analysis finished for this game --- 

                # Update GameAnalysis object (still in background thread - generally safe for data objects)
                game_analysis.move_evaluations = analysis_results.get("move_evaluations", [])
                game_analysis.position_history = analysis_results.get("position_history", [])
                game_analysis.white_stats = analysis_results.get("white_stats", {})
                game_analysis.black_stats = analysis_results.get("black_stats", {})
                game_analysis.white_phase_stats = analysis_results.get("white_phase_stats", {})
                game_analysis.black_phase_stats = analysis_results.get("black_phase_stats", {})
                game_analysis.critical_moments = analysis_results.get("critical_moments", [])
                game_analysis.game_difficulty = analysis_results.get("difficulty_metrics", {})
                game_analysis.analysis_date = datetime.datetime.now()

                analyzed_count += 1

            except Exception as e:
                failed_count += 1
                self.analysis_queue.put(("log", f"Erreur lors de l'analyse de la partie {game_analysis.game_id}: {e}"))

        # Signal completion
        completion_data = {
            "analyzed": analyzed_count,
            "failed": failed_count,
            "cancelled": self.analysis_cancelled
        }
        self.analysis_queue.put(("done", completion_data))

    def _check_analysis_queue(self):
        """Checks the queue for updates from the analysis thread and updates the UI."""
        try:
            while True: # Process all messages currently in the queue
                message_type, data = self.analysis_queue.get_nowait()

                if message_type == "progress":
                    self.progress_label.config(text="Analyse en cours...")
                    self.progress_info_label.config(text=f"{data['current']}/{data['total']}")
                    self.current_game_label.config(text=data['game_info'])
                elif message_type == "status":
                    self.status_label.config(text=data)
                elif message_type == "log":
                    print(data) # Log errors or info to console
                elif message_type == "done":
                    self._finalize_analysis(data)
                    return # Stop checking queue

        except queue.Empty:
            # If the queue is empty, schedule the next check only if the thread is still alive
            if self.analysis_thread.is_alive():
                self.after(100, self._check_analysis_queue)
            else:
                # Thread finished unexpectedly or completed without sending 'done'
                # Check if progress_win still exists before trying to destroy
                if self.progress_win and self.progress_win.winfo_exists():
                     messagebox.showerror("Erreur", "Le thread d'analyse s'est terminé de manière inattendue.", parent=self)
                     self.progress_win.destroy()
                # Re-enable button if needed
                # if hasattr(self, 'analyze_button'): self.analyze_button.config(state=tk.NORMAL)

        except Exception as e:
            print(f"Error processing analysis queue: {e}")
            # Consider showing an error message box
            if self.progress_win and self.progress_win.winfo_exists():
                self.progress_win.destroy()
            # Re-enable button if needed
            # if hasattr(self, 'analyze_button'): self.analyze_button.config(state=tk.NORMAL)

    def _finalize_analysis(self, results):
        """Called on the main thread when analysis is complete."""
        # Destroy progress window if it exists
        if self.progress_win and self.progress_win.winfo_exists():
            self.progress_win.destroy()

        # Re-enable button if needed
        # if hasattr(self, 'analyze_button'): self.analyze_button.config(state=tk.NORMAL)

        analyzed_count = results["analyzed"]
        failed_count = results["failed"]
        cancelled = results["cancelled"]

        if cancelled:
            messagebox.showwarning("Analyse Annulée", "L'analyse des parties a été annulée.", parent=self)
        else:
            if analyzed_count > 0 or failed_count > 0:
                print(f"Sauvegarde du profil {self.user_profile.username} après analyse.")
                try:
                    self.profile_manager.save_profile(self.user_profile)
                except Exception as e:
                     messagebox.showerror("Erreur Sauvegarde", f"Erreur lors de la sauvegarde du profil après analyse: {e}", parent=self)
                     print(f"Error saving profile after analysis: {e}")
                     # Decide if you want to proceed with UI updates even if save failed

            # Refresh UI elements (safely, as this is the main thread)
            try:
                if hasattr(self, 'history_tab') and self.history_tab and self.history_tab.winfo_exists():
                    print("Rafraîchissement de l'historique...")
                    self.history_tab.populate_history()
            except Exception as e:
                print(f"Error refreshing history tab: {e}")

            try:
                if hasattr(self, 'stats_tab') and self.stats_tab and self.stats_tab.winfo_exists():
                    if hasattr(self.stats_tab, 'update_stats'):
                        print("Rafraîchissement des statistiques...")
                        self.stats_tab.update_stats()
            except Exception as e:
                print(f"Error refreshing stats tab: {e}")

            messagebox.showinfo(
                "Analyse Terminée",
                f"Analyse des parties terminée.\n\n"
                f"Parties analysées avec succès : {analyzed_count}\n"
                f"Échecs d'analyse : {failed_count}",
                parent=self
            )

    def _cancel_analysis(self):
        """Sets the cancellation flag and handles progress window closure."""
        if self.analysis_thread and self.analysis_thread.is_alive():
            print("Annulation de l'analyse demandée...")
            self.analysis_cancelled = True
            # Optionally, you could try to interrupt the engine if possible,
            # but simply setting the flag is often sufficient.
        # Ensure progress window is closed if it exists
        if self.progress_win and self.progress_win.winfo_exists():
            self.progress_win.destroy()

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

    def show_game_analysis(self, game_analysis: GameAnalysis):
        """Callback function to open the GameAnalysisView for a selected game."""
        print(f"Opening analysis view for game: {game_analysis.game_id}")
        if not self.piece_images:
             print("Error: piece_images not available in UserProfileWindow.")
             messagebox.showerror("Erreur", "Les images des pièces ne sont pas chargées.", parent=self)
             return
        try:
            # 1. Créer l'instance du gestionnaire de vue
            view_manager = GameAnalysisView(self, self.game_analyzer, self.piece_images)

            # 2. Appeler show_analysis pour créer et afficher la fenêtre
            analysis_window = view_manager.show_analysis(game_analysis)

            # 3. Vérifier si la fenêtre a été créée et la rendre modale
            if analysis_window and isinstance(analysis_window, tk.Toplevel):
                analysis_window.grab_set() # Appeler sur la fenêtre Toplevel retournée
                analysis_window.focus_set()
            elif analysis_window:
                 print(f"Warning: show_analysis returned something other than a Toplevel window: {type(analysis_window)}")
            else:
                 print("Error: show_analysis did not return a window.")
                 messagebox.showerror("Erreur d'Affichage", "Impossible de créer la fenêtre d'analyse.", parent=self)

        except Exception as e:
            messagebox.showerror("Erreur d'Analyse", f"Impossible d'ouvrir la vue d'analyse : {e}", parent=self)
            print(f"Error opening GameAnalysisView: {e}")
            import traceback
            traceback.print_exc()
