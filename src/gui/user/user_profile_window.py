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
import os
import shutil
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
        self.history_tab = HistoryTab(self.tabs.content_frame, self.user_profile, self.profile_manager, bg=config.COLORS["profile_background"])

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
                import io # Keep import local if only used here
                import chess.pgn # Keep import local if only used here
                import datetime # Keep import local if only used here
                from src.core.chess_game import ChessGame # Keep import local
                from src.analysis.game_analyzer import GameAnalysis # Keep import local

                with open(file_path, 'r', encoding='utf-8', errors='ignore') as pgn_file: # Added errors='ignore'
                    while True:
                        # Use try-except around read_game for robustness
                        try:
                            game_node = chess.pgn.read_game(pgn_file)
                        except Exception as read_err:
                            print(f"Error reading game from PGN {file_path}: {read_err}")
                            failed_count += 1 # Count as failed if a game within the file fails to parse
                            continue # Try next game in the file

                        if game_node is None:
                            break # End of file or no more games

                        headers = game_node.headers
                        # Create a more robust game ID
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

                        # Check if game already exists using the generated ID
                        if game_id_from_headers in self.user_profile.game_analyses:
                            skipped_count += 1
                            continue

                        # --- Game Analysis ---
                        temp_game = ChessGame()
                        temp_game.load_from_pgn(game_node)

                        # Ensure game_analyzer is available
                        if not self.game_analyzer:
                             print("Game Analyzer not available. Skipping analysis.")
                             analysis_results = {} # Provide empty results
                        else:
                            # Provide a simple progress update for analysis if possible
                            analysis_results = self.game_analyzer.analyze_game(
                                list(temp_game.board.move_stack),
                                lambda p: None # No detailed progress update here
                            )

                        # --- Date Parsing ---
                        date_str = headers.get("Date", "????.??.??")
                        try:
                            # Handle different date formats if necessary
                            cleaned_date_str = date_str.replace('.', '-').split(' ')[0] # Clean format
                            game_date = datetime.datetime.strptime(cleaned_date_str, '%Y-%m-%d').date()
                        except ValueError:
                            try:
                                # Try another common format
                                game_date = datetime.datetime.strptime(cleaned_date_str, '%d-%m-%Y').date()
                            except ValueError:
                                game_date = datetime.date.today() # Fallback

                        # --- PGN Export ---
                        exporter = chess.pgn.StringExporter(headers=True, variations=True, comments=True)
                        pgn_text = game_node.accept(exporter)

                        # --- Create GameAnalysis Object ---
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
                            game_id=game_id_from_headers # Use the generated ID
                        )

                        # --- Add to Profile and Update Stats ---
                        self.user_profile.game_analyses[game_analysis.game_id] = game_analysis
                        # Check if _update_aggregated_stats exists before calling
                        if hasattr(self.user_profile, '_update_aggregated_stats'):
                            self.user_profile._update_aggregated_stats()
                        else:
                            print("Warning: UserProfile._update_aggregated_stats method not found.")


                        imported_count += 1
                        # Update progress label less frequently or remove if too slow
                        # progress_label.config(text=f"Importé: {imported_count}, Échec: {failed_count}, Ignoré: {skipped_count}")
                        # self.update_idletasks()

            except Exception as e:
                failed_count += 1
                print(f"Erreur lors du traitement du fichier {file_path}: {e}") # Log the error
                # Update progress label less frequently or remove if too slow
                # progress_label.config(text=f"Importé: {imported_count}, Échec: {failed_count}, Ignoré: {skipped_count}")
                # self.update_idletasks()

        progress_win.destroy()

        # Save profile only once after all files are processed
        self.profile_manager.save_profile(self.user_profile)

        # Refresh tabs after saving and closing progress window
        if hasattr(self, 'history_tab') and self.history_tab:
             self.history_tab.populate_history() # Refresh history view
        if hasattr(self, 'stats_tab') and self.stats_tab:
             if hasattr(self.stats_tab, 'update_stats'):
                 self.stats_tab.update_stats() # Refresh stats view if method exists
             else:
                 # Fallback: Recreate stats tab or relevant parts if no update method
                 print("StatsTab does not have an update_stats method. Manual refresh might be needed.")


        messagebox.showinfo(
            "Importation Terminée",
            f"Importation terminée.\n\n"
            f"Parties importées et analysées : {imported_count}\n"
            f"Parties déjà existantes (ignorées) : {skipped_count}\n"
            f"Échecs d'importation/analyse : {failed_count}",
            parent=self
        )

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
