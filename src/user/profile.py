"""
Module de gestion des profils utilisateurs pour l'application ChessEngine.
Permet le stockage, la persistance et l'accès aux données des utilisateurs.
"""

import os
import json
import pickle
import datetime
import shutil
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Union, Any
import chess.pgn
from src.analysis.player_stats import PlayerStats


@dataclass
class GameAnalysis:
    """Représente l'analyse complète d'une partie d'échecs."""
    
    # Métadonnées de la partie
    game_date: datetime.date
    white_player: str
    black_player: str
    result: str
    event: Optional[str] = None
    site: Optional[str] = None
    round: Optional[str] = None
    eco: Optional[str] = None  # Code ECO de l'ouverture
    time_control: Optional[str] = None  # Cadence de la partie
    end_time: Optional[str] = None  # Heure de fin de partie au format "HH:MM:SS"
    
    # PGN original
    pgn_text: str = ""
    
    # Données d'analyse
    move_evaluations: List[Dict[str, Any]] = field(default_factory=list)
    position_history: List[str] = field(default_factory=list)  # Liste des positions FEN
    
    # Statistiques des joueurs
    white_stats: Dict[str, Any] = field(default_factory=dict)
    black_stats: Dict[str, Any] = field(default_factory=dict)
    white_phase_stats: Dict[str, Any] = field(default_factory=dict)
    black_phase_stats: Dict[str, Any] = field(default_factory=dict)
    
    # Détails supplémentaires d'analyse
    critical_moments: List[int] = field(default_factory=list)
    game_difficulty: Dict[str, Any] = field(default_factory=dict)
    
    # Identifiant unique de la partie
    game_id: str = field(default="")
    
    # Date d'analyse
    analysis_date: datetime.datetime = field(default_factory=datetime.datetime.now)
    
    def __post_init__(self):
        if not self.game_id:
            # Créer un identifiant basé sur les joueurs, la date et un timestamp
            self.game_id = f"{self.white_player}_vs_{self.black_player}_{self.game_date.strftime('%Y%m%d')}_{int(datetime.datetime.now().timestamp())}"
    
    def get_datetime(self) -> datetime.datetime:
        """Retourne un objet datetime complet combinant la date et l'heure de fin.
        
        Si l'heure de fin n'est pas disponible, utilise minuit comme heure par défaut.
        
        Returns:
            Un objet datetime complet pour le tri chronologique
        """
        try:
            if self.end_time:
                # Parser l'heure de fin, qui peut contenir des informations de fuseau horaire
                time_parts = self.end_time.split()
                time_str = time_parts[0]  # Partie HH:MM:SS
                
                # Séparer les heures, minutes et secondes
                hours, minutes, seconds = time_str.split(":")
                
                # Créer un datetime combinant la date et l'heure
                return datetime.datetime(
                    year=self.game_date.year,
                    month=self.game_date.month,
                    day=self.game_date.day,
                    hour=int(hours),
                    minute=int(minutes),
                    second=int(seconds)
                )
        except Exception:
            # En cas d'erreur de parsing, revenir à l'heure par défaut
            pass
            
        # Heure par défaut si end_time n'est pas disponible ou invalide
        return datetime.datetime(
            year=self.game_date.year,
            month=self.game_date.month,
            day=self.game_date.day
        )


@dataclass
class UserProfile:
    """Profil utilisateur avec historique des parties et statistiques."""
    
    username: str
    creation_date: datetime.datetime = field(default_factory=datetime.datetime.now)
    last_login: datetime.datetime = field(default_factory=datetime.datetime.now)
    avatar_path: Optional[str] = None  # Chemin RELATIF vers l'avatar personnalisé (depuis data_directory)
    
    # Dictionnaire des analyses de parties, indexées par game_id
    game_analyses: Dict[str, GameAnalysis] = field(default_factory=dict)
    
    # Statistiques agrégées
    aggregated_stats: Dict[str, Any] = field(default_factory=dict)
    
    # Préférences utilisateur
    preferences: Dict[str, Any] = field(default_factory=dict)
    
    def add_game_from_pgn(self, pgn_file_path: str, game_analyzer) -> Optional[str]:
        """
        Ajoute une partie d'échecs à partir d'un fichier PGN et l'analyse.
        
        Args:
            pgn_file_path: Chemin du fichier PGN
            game_analyzer: Instance de GameAnalyzer pour l'analyse
            
        Returns:
            ID de la partie ajoutée ou None en cas d'échec
        """
        try:
            with open(pgn_file_path, "r") as f:
                game = chess.pgn.read_game(f)
                
            if not game:
                return None
                
            # Extraire les métadonnées
            headers = game.headers
            white_player = headers.get("White", "Unknown")
            black_player = headers.get("Black", "Unknown")
            result = headers.get("Result", "*")
            date_str = headers.get("Date", "????.??.??")
            
            # Convertir la date
            try:
                year, month, day = date_str.split(".")
                game_date = datetime.date(int(year), int(month), int(day))
            except ValueError:
                game_date = datetime.date.today()
            
            # Extraire l'heure de fin si elle est disponible
            end_time = headers.get("EndTime")
            
            # Convertir le PGN en texte pour stockage
            pgn_text = str(game)
            
            # Créer un nouvel objet GameAnalysis
            game_analysis = GameAnalysis(
                game_date=game_date,
                white_player=white_player,
                black_player=black_player,
                result=result,
                event=headers.get("Event"),
                site=headers.get("Site"),
                round=headers.get("Round"),
                eco=headers.get("ECO"),
                time_control=headers.get("TimeControl"),
                end_time=end_time,
                pgn_text=pgn_text
            )
            
            # Extraction des coups pour l'analyse
            board = game.board()
            moves = [move for move in game.mainline_moves()]
            
            # Analyse de la partie
            analysis_results = game_analyzer.analyze_game(moves, analysis_board=board)
            
            # Stockage des résultats d'analyse
            game_analysis.move_evaluations = analysis_results["move_evaluations"]
            game_analysis.position_history = analysis_results["position_history"]
            game_analysis.white_stats = analysis_results["white_stats"]
            game_analysis.black_stats = analysis_results["black_stats"]
            game_analysis.white_phase_stats = analysis_results["white_phase_stats"]
            game_analysis.black_phase_stats = analysis_results["black_phase_stats"]
            game_analysis.critical_moments = analysis_results["critical_moments"]
            
            # Ajouter l'analyse de difficulté si disponible
            if "game_difficulty" in analysis_results:
                game_analysis.game_difficulty = analysis_results["game_difficulty"]
            
            # Ajouter l'analyse à la collection
            self.game_analyses[game_analysis.game_id] = game_analysis
            
            # Mettre à jour les statistiques agrégées
            self._update_aggregated_stats()
            
            return game_analysis.game_id
            
        except Exception as e:
            print(f"Erreur lors de l'analyse de la partie PGN: {e}")
            return None
    
    def _update_aggregated_stats(self):
        """Calcule et met à jour les statistiques agrégées de l'utilisateur."""
        player_stats = PlayerStats()
        
        # Collecter toutes les évaluations où l'utilisateur est blanc ou noir
        white_evals = []
        black_evals = []
        
        for game_id, analysis in self.game_analyses.items():
            # Déterminer si l'utilisateur joue avec les blancs ou les noirs
            is_white = analysis.white_player.strip().lower() == self.username.strip().lower()
            is_black = analysis.black_player.strip().lower() == self.username.strip().lower()
            
            if is_white:
                white_evals.extend(analysis.move_evaluations)
            elif is_black:
                black_evals.extend(analysis.move_evaluations)
        
        # Filtrer les évaluations de l'utilisateur
        user_white_evals = [eval for eval in white_evals if eval["side"] == "White"]
        user_black_evals = [eval for eval in black_evals if eval["side"] == "Black"]
        
        # Calculer les statistiques
        user_white_stats = player_stats.calculate_player_stats(user_white_evals)
        user_black_stats = player_stats.calculate_player_stats(user_black_evals)
        user_all_evals = user_white_evals + user_black_evals
        user_overall_stats = player_stats.calculate_player_stats(user_all_evals)

        # Comptage des parties selon la couleur où l'utilisateur a effectivement joué
        white_game_ids = set()
        black_game_ids = set()
        for game_id, analysis in self.game_analyses.items():
            if analysis.white_player.strip().lower() == self.username.strip().lower():
                white_game_ids.add(game_id)
            elif analysis.black_player.strip().lower() == self.username.strip().lower():
                black_game_ids.add(game_id)
        user_white_game_count = len(white_game_ids)
        user_black_game_count = len(black_game_ids)
        user_total_game_count = user_white_game_count + user_black_game_count
        # Inject game_count into per-color stats for affichage direct
        user_white_stats["game_count"] = user_white_game_count
        user_black_stats["game_count"] = user_black_game_count
        user_overall_stats["game_count"] = user_total_game_count
        
        # Statistiques par phase
        user_white_phase_stats = player_stats.calculate_phase_stats(user_white_evals)
        user_black_phase_stats = player_stats.calculate_phase_stats(user_black_evals)
        user_overall_phase_stats = player_stats.calculate_phase_stats(user_all_evals)
        
        # Stocker les statistiques agrégées
        openings_stats = {}
        # Agrégation par ECO
        for game_id, analysis in self.game_analyses.items():
            # On veut l'ouverture finale atteinte (dernier coup encore dans le livre/opening)
            eco_code = None
            opening_name = None
            try:
                for mv in analysis.move_evaluations:
                    op = mv.get("opening")
                    if op and op.get("eco"):
                        # écrase jusqu'au dernier rencontré
                        eco_code = op.get("eco")
                        opening_name = op.get("name") or op.get("full_name") or opening_name
            except Exception:
                pass
            # fallback sur meta ECO si rien trouvé
            if not eco_code:
                eco_code = analysis.eco
            if not eco_code:
                continue  # ignorer parties sans ECO finale

            # Initialiser structure
            o = openings_stats.setdefault(eco_code, {
                "games": 0,
                "wins": 0.0,  # demi-points
                "user_color_games": {"white": 0, "black": 0},
                "user_opening_evals": [],  # move_quality des coups d'ouverture utilisateur
                "blunders": 0,
                "total_user_opening_moves": 0,
                "book_depths": [],
                "post_book_scores": [],
                "lines": [],  # séquences SAN jusqu'à sortie de théorie
                "name": None
            })
            # Enregistrer nom final si absent
            if o.get("name") is None and opening_name:
                o["name"] = opening_name

            # Déterminer couleur utilisateur dans cette partie
            is_white = analysis.white_player.strip().lower() == self.username.strip().lower()
            is_black = analysis.black_player.strip().lower() == self.username.strip().lower()
            if not (is_white or is_black):
                continue
            color = "white" if is_white else "black"
            o["user_color_games"][color] += 1
            o["games"] += 1

            # Résultat demi-points
            res = analysis.result.strip()
            if res == "1-0":
                o["wins"] += 1.0 if is_white else 0.0
            elif res == "0-1":
                o["wins"] += 1.0 if is_black else 0.0
            elif res in ("1/2-1/2", "1/2-1/2 "):
                o["wins"] += 0.5

            # Identifier profondeur de livre: dernier index où un mv contient 'opening'
            book_last_index = -1
            san_sequence = []
            try:
                for idx, mv in enumerate(analysis.move_evaluations):
                    if mv.get("opening"):
                        book_last_index = idx
                    # construire séquence SAN utilisateur uniquement jusqu'à sortie de théorie
                # Two passes: build sequence up to and including book_last_index
                if book_last_index >= 0:
                    for mv in analysis.move_evaluations[:book_last_index+1]:
                        san_sequence.append(mv.get("san", "?"))
            except Exception:
                pass
            # Profondeur (en demi-coups) convertie en coups entiers
            if book_last_index >= 0:
                book_depth_moves = analysis.move_evaluations[book_last_index].get("move_num", book_last_index//2 + 1)
                o["book_depths"].append(book_depth_moves)

            # Score post-livre: score_after du premier coup sans 'opening' après book
            try:
                if book_last_index >= 0 and book_last_index + 1 < len(analysis.move_evaluations):
                    post_mv = analysis.move_evaluations[book_last_index + 1]
                    score_after = post_mv.get("score_after")
                    if isinstance(score_after, (int, float)):
                        # Ajuster perspective utilisateur (score est côté trait? stocké white perspective?)
                        # Dans move_analyzer, scores sont déjà perspective joueur actif; simplifions: si utilisateur est noir, inverser
                        if is_black:
                            score_after = -score_after
                        o["post_book_scores"].append(score_after)
            except Exception:
                pass

            # Collecte des évaluations d'ouverture pour précision/blunders (limité aux coups d'ouverture)
            try:
                for mv in analysis.move_evaluations[:book_last_index+1 if book_last_index >=0 else 0]:
                    if mv.get("side") == ("White" if is_white else "Black"):
                        q = mv.get("move_quality")
                        if isinstance(q, (int,float)):
                            o["user_opening_evals"].append(q)
                        cls = mv.get("classification")
                        if cls == "Grosse erreur":
                            o["blunders"] += 1
                        o["total_user_opening_moves"] += 1
            except Exception:
                pass

            if san_sequence:
                o["lines"].append(san_sequence)

        # Calcul métriques finales pour chaque ouverture (uniquement si l'utilisateur a joué au moins 1 partie)
        openings_summary = {}
        for eco, data in openings_stats.items():
            if data["games"] == 0:
                # Ignore les ouvertures présentes uniquement parce que l'analyse contenait une ECO
                # mais où l'utilisateur n'a pas participé.
                continue
            games = data["games"]  # nombre réel de parties utilisateur pour cette ouverture
            total_moves = data["total_user_opening_moves"] if data["total_user_opening_moves"] > 0 else 1
            denom_games = games if games > 0 else 1  # sécurité division
            score_pct = (data["wins"] / denom_games) * 100
            precision = (sum(data["user_opening_evals"]) / len(data["user_opening_evals"]) * 100) if data["user_opening_evals"] else 0.0
            blunders_per_100 = data["blunders"] / total_moves * 100
            avg_depth = sum(data["book_depths"]) / len(data["book_depths"]) if data["book_depths"] else 0.0
            avg_post_score = sum(data["post_book_scores"]) / len(data["post_book_scores"]) if data["post_book_scores"] else 0.0
            # Performance heuristic: 1500 + (precision-50)*10 + (score_pct-50)*5
            perf = int(1500 + (precision - 50)*10 + (score_pct - 50)*5)
            # Stabilité: proportion de coups conformes à la ligne majoritaire sur profondeur minimale commune
            stability = 0.0
            if data["lines"]:
                min_len = min(len(l) for l in data["lines"])
                if min_len > 0:
                    matches = 0
                    total_positions = min_len * len(data["lines"])
                    for ply in range(min_len):
                        freq = {}
                        for line in data["lines"]:
                            move = line[ply]
                            freq[move] = freq.get(move, 0) + 1
                        matches += max(freq.values())
                    stability = (matches / total_positions) * 100
            openings_summary[eco] = {
                "games": games,
                "score_pct": round(score_pct, 1),
                "precision": round(precision, 1),
                "perf": perf,
                "blunders_per_100": round(blunders_per_100, 2),
                "avg_depth": round(avg_depth, 1),
                "avg_post_score": round(avg_post_score, 2),
                "stability": round(stability, 1),
                "name": data.get("name")
            }

        # Baseline blunders for problematic lines detection
        blunder_values = [o["blunders_per_100"] for o in openings_summary.values()]
        if blunder_values:
            mean_bl = sum(blunder_values)/len(blunder_values)
            # simple std dev
            variance = sum((v-mean_bl)**2 for v in blunder_values)/len(blunder_values)
            std_bl = variance ** 0.5
        else:
            mean_bl = 0.0
            std_bl = 0.0
        # Marquer ouvertures problématiques
        for eco, o in openings_summary.items():
            o["problematic"] = o["blunders_per_100"] > mean_bl + std_bl and o["score_pct"] < 50

        # Couverture des ouvertures reconnues (seulement les parties avec une ECO finale trouvée)
        recognized_opening_games = sum(o["games"] for o in openings_summary.values()) if openings_summary else 0

        total_analyses = len(self.game_analyses)
        self.aggregated_stats = {
            "overall": user_overall_stats,
            "white": user_white_stats,
            "black": user_black_stats,
            "phase_stats": {
                "overall": user_overall_phase_stats,
                "white": user_white_phase_stats,
                "black": user_black_phase_stats
            },
            "openings": openings_summary,
            # game_count désormais = parties où l'utilisateur a joué (cohérent avec affichages)
            "game_count": user_total_game_count,
            # Nombre total d'analyses stockées (peut inclure des parties où l'utilisateur n'est pas joueur)
            "analysis_count": total_analyses,
            "recognized_opening_games": recognized_opening_games,
            "missing_opening_games": max(user_total_game_count - recognized_opening_games, 0),
            "last_updated": datetime.datetime.now()
        }

    def delete_game_analysis(self, game_id: str) -> bool:
        """
        Supprime une analyse de partie du profil.

        Args:
            game_id: L'ID de la partie à supprimer.

        Returns:
            True si la suppression a réussi, False sinon.
        """
        if game_id in self.game_analyses:
            try:
                del self.game_analyses[game_id]
                self._update_aggregated_stats()  # Recalculer les stats après suppression
                print(f"Analyse de partie {game_id} supprimée.")
                return True
            except Exception as e:
                print(f"Erreur lors de la suppression de l'analyse {game_id}: {e}")
                return False
        else:
            print(f"Analyse de partie {game_id} non trouvée pour suppression.")
            return False


class UserProfileManager:
    """Gestionnaire de profils utilisateurs."""
    
    def __init__(self, data_directory: str = "user_profiles"):
        """
        Initialise le gestionnaire de profils.
        
        Args:
            data_directory: Répertoire de stockage des profils
        """
        self.data_directory = data_directory
        self.profiles = {}
        # Chemin absolu vers le dossier des avatars
        self.avatars_directory = os.path.abspath(os.path.join(self.data_directory, "avatars"))

        # Créer les répertoires de données s'ils n'existent pas
        Path(self.data_directory).mkdir(parents=True, exist_ok=True)
        Path(self.avatars_directory).mkdir(parents=True, exist_ok=True)  # Créer le dossier avatars

        # Charger les profils existants
        self._load_profiles()
    
    def _get_profile_path(self, username: str) -> str:
        """Obtenir le chemin du fichier de profil pour un utilisateur."""
        return os.path.join(self.data_directory, f"{username.lower()}.json")
    
    def _load_profiles(self):
        """Charger tous les profils disponibles."""
        for file_path in Path(self.data_directory).glob("*.json"):
            try:
                username = file_path.stem
                self._load_profile(username)
            except Exception as e:
                print(f"Erreur lors du chargement du profil {file_path}: {e}")
    
    def _load_profile(self, username: str) -> Optional[UserProfile]:
        """Charger un profil spécifique depuis le disque."""
        file_path = self._get_profile_path(username)
        
        try:
            if not os.path.exists(file_path):
                return None
                
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            profile = UserProfile(
                username=data["username"],
                creation_date=datetime.datetime.fromisoformat(data["creation_date"]),
                last_login=datetime.datetime.fromisoformat(data["last_login"]),
                avatar_path=data.get("avatar_path"),  # Charger le chemin relatif de l'avatar
                aggregated_stats=data["aggregated_stats"],
                preferences=data["preferences"]
            )
            
            # Charger les analyses de parties
            for game_id, game_data in data["game_analyses"].items():
                analysis = GameAnalysis(
                    game_date=datetime.date.fromisoformat(game_data["game_date"]),
                    white_player=game_data["white_player"],
                    black_player=game_data["black_player"],
                    result=game_data["result"],
                    event=game_data.get("event"),
                    site=game_data.get("site"),
                    round=game_data.get("round"),
                    eco=game_data.get("eco"),
                    time_control=game_data.get("time_control"),  # Charger la cadence
                    end_time=game_data.get("end_time"),  # Charger l'heure de fin
                    pgn_text=game_data["pgn_text"],
                    game_id=game_id,
                    analysis_date=datetime.datetime.fromisoformat(game_data["analysis_date"])
                )
                
                # Ajouter les détails d'analyse
                analysis.move_evaluations = game_data["move_evaluations"]
                analysis.position_history = game_data["position_history"]
                analysis.white_stats = game_data["white_stats"]
                analysis.black_stats = game_data["black_stats"]
                analysis.white_phase_stats = game_data["white_phase_stats"]
                analysis.black_phase_stats = game_data["black_phase_stats"]
                analysis.critical_moments = game_data["critical_moments"]
                analysis.game_difficulty = game_data.get("game_difficulty", {})
                
                profile.game_analyses[game_id] = analysis

            # Recalculer les stats si la nouvelle section 'openings' n'existe pas (compatibilité ascendante)
            try:
                need_recompute = False
                agg = profile.aggregated_stats or {}
                if "openings" not in agg:
                    need_recompute = True
                else:
                    openings_dict = agg.get("openings", {}) or {}
                    for eco_code, odata in openings_dict.items():
                        if not isinstance(odata, dict) or not odata.get("name"):
                            need_recompute = True
                            break
                # Vérifier présence des nouveaux compteurs cohérents
                if agg.get("analysis_count") is None or agg.get("recognized_opening_games") is None:
                    need_recompute = True
                # Vérifier game_count cohérent avec white/black game_count (migration)
                w_gc = agg.get("white", {}).get("game_count")
                b_gc = agg.get("black", {}).get("game_count")
                if (w_gc is None or b_gc is None) and profile.game_analyses:
                    need_recompute = True
                if agg.get("game_count") and w_gc is not None and b_gc is not None:
                    if agg.get("game_count") != (w_gc + b_gc):
                        need_recompute = True
                if need_recompute:
                    profile._update_aggregated_stats()
            except Exception as e:
                print(f"Warning: impossible de recalculer les statistiques d'ouvertures pour {username}: {e}")
            
            self.profiles[username.lower()] = profile
            return profile
            
        except Exception as e:
            print(f"Erreur lors du chargement du profil {username}: {e}")
            return None
    
    def save_profile(self, profile: UserProfile):
        """Sauvegarder un profil sur le disque."""
        file_path = self._get_profile_path(profile.username)
        
        try:
            # Convertir en dictionnaire pour la sérialisation JSON
            data = {
                "username": profile.username,
                "creation_date": profile.creation_date.isoformat(),
                "last_login": profile.last_login.isoformat(),
                "avatar_path": profile.avatar_path,  # Sauvegarder le chemin relatif de l'avatar
                "aggregated_stats": profile.aggregated_stats,
                "preferences": profile.preferences,
                "game_analyses": {}
            }
            
            # --- Correction: Convertir datetime dans aggregated_stats ---
            if "last_updated" in data["aggregated_stats"] and isinstance(data["aggregated_stats"]["last_updated"], datetime.datetime):
                data["aggregated_stats"]["last_updated"] = data["aggregated_stats"]["last_updated"].isoformat()
            # --- Fin Correction ---
            
            # Convertir chaque analyse de partie
            for game_id, analysis in profile.game_analyses.items():
                game_data = {
                    "game_date": analysis.game_date.isoformat(),
                    "white_player": analysis.white_player,
                    "black_player": analysis.black_player,
                    "result": analysis.result,
                    "event": analysis.event,
                    "site": analysis.site,
                    "round": analysis.round,
                    "eco": analysis.eco,
                    "time_control": analysis.time_control,  # Sauvegarder la cadence
                    "end_time": analysis.end_time,  # Sauvegarder l'heure de fin
                    "pgn_text": analysis.pgn_text,
                    "move_evaluations": analysis.move_evaluations,
                    "position_history": analysis.position_history,
                    "white_stats": analysis.white_stats,
                    "black_stats": analysis.black_stats,
                    "white_phase_stats": analysis.white_phase_stats,
                    "black_phase_stats": analysis.black_phase_stats,
                    "critical_moments": analysis.critical_moments,
                    "game_difficulty": analysis.game_difficulty,
                    "analysis_date": analysis.analysis_date.isoformat()
                }
                data["game_analyses"][game_id] = game_data
            
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"Erreur lors de la sauvegarde du profil {profile.username}: {e}")
    
    def get_profile(self, username: str) -> Optional[UserProfile]:
        """
        Récupérer le profil d'un utilisateur.
        
        Args:
            username: Nom d'utilisateur
            
        Returns:
            Profil utilisateur ou None s'il n'existe pas
        """
        username_lower = username.lower()
        
        # Vérifier si le profil est en mémoire
        if username_lower in self.profiles:
            return self.profiles[username_lower]
        
        # Essayer de le charger depuis le disque
        return self._load_profile(username)
    
    def create_profile(self, username: str) -> UserProfile:
        """
        Créer un nouveau profil utilisateur.
        
        Args:
            username: Nom d'utilisateur
            
        Returns:
            Nouveau profil utilisateur
        
        Raises:
            ValueError: Si le profil existe déjà
        """
        username_lower = username.lower()
        
        if username_lower in self.profiles or os.path.exists(self._get_profile_path(username)):
            raise ValueError(f"Le profil utilisateur '{username}' existe déjà")
        
        profile = UserProfile(username=username)
        self.profiles[username_lower] = profile
        self.save_profile(profile)
        
        return profile
    
    def export_profile(self, username: str, export_path: str):
        """
        Exporter le profil d'un utilisateur au format pickle (pour une sauvegarde complète).
        
        Args:
            username: Nom d'utilisateur
            export_path: Chemin d'exportation
            
        Returns:
            True si l'exportation est réussie, False sinon
        """
        profile = self.get_profile(username)
        if not profile:
            return False
        
        try:
            with open(export_path, "wb") as f:
                pickle.dump(profile, f)
            return True
        except Exception as e:
            print(f"Erreur lors de l'exportation du profil {username}: {e}")
            return False
    
    def import_profile(self, import_path: str) -> Optional[UserProfile]:
        """
        Importer un profil depuis un fichier pickle.
        
        Args:
            import_path: Chemin du fichier à importer
            
        Returns:
            Profil importé ou None en cas d'échec
        """
        try:
            with open(import_path, "rb") as f:
                profile = pickle.load(f)
            
            if not isinstance(profile, UserProfile):
                print("Le fichier importé ne contient pas un profil utilisateur valide")
                return None
            
            # Mettre à jour la date de dernière connexion
            profile.last_login = datetime.datetime.now()
            
            # Ajouter au gestionnaire et sauvegarder
            username_lower = profile.username.lower()
            self.profiles[username_lower] = profile
            self.save_profile(profile)
            
            return profile
        except Exception as e:
            print(f"Erreur lors de l'importation du profil: {e}")
            return None
    
    def set_avatar(self, username: str, source_image_path: str) -> Optional[str]:
        """
        Définit un nouvel avatar pour l'utilisateur en copiant l'image source.

        Args:
            username: Nom d'utilisateur.
            source_image_path: Chemin de l'image source à copier.

        Returns:
            Le nouveau chemin relatif de l'avatar copié (depuis data_directory) ou None en cas d'erreur.
        """
        profile = self.get_profile(username)
        if not profile:
            print(f"Profil {username} non trouvé pour définir l'avatar.")
            return None

        try:
            source_path = Path(source_image_path)
            if not source_path.is_file():
                print(f"Fichier source de l'avatar non trouvé: {source_image_path}")
                return None

            # Créer un nom de fichier basé sur le nom d'utilisateur et l'extension originale
            file_extension = source_path.suffix
            # Utiliser un nom de fichier prévisible pour faciliter la gestion
            avatar_filename = f"{username.lower()}{file_extension}"
            # Chemin absolu de destination
            destination_path = Path(self.avatars_directory) / avatar_filename

            # Copier le fichier (écrase s'il existe déjà)
            shutil.copy2(source_image_path, destination_path)

            # Stocker le chemin relatif par rapport à data_directory
            relative_avatar_path = os.path.join("avatars", avatar_filename)
            profile.avatar_path = relative_avatar_path
            self.save_profile(profile)

            print(f"Avatar pour {username} mis à jour et copié vers {destination_path}")
            return relative_avatar_path

        except Exception as e:
            print(f"Erreur lors de la définition de l'avatar pour {username}: {e}")
            return None

    def get_avatar_full_path(self, profile: UserProfile) -> Optional[str]:
        """
        Retourne le chemin absolu de l'avatar de l'utilisateur, s'il est défini.

        Args:
            profile: L'objet UserProfile.

        Returns:
            Le chemin absolu de l'avatar ou None.
        """
        if profile.avatar_path:
            # Construit le chemin absolu à partir de data_directory et du chemin relatif stocké
            full_path = os.path.abspath(os.path.join(self.data_directory, profile.avatar_path))
            if os.path.exists(full_path):
                return full_path
            else:
                # Si le fichier n'existe pas, invalider le chemin dans le profil
                print(f"Fichier avatar introuvable: {full_path}. Suppression de la référence.")
                profile.avatar_path = None
                self.save_profile(profile)  # Sauvegarder le profil avec le chemin invalidé
                return None
        return None