export const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

export type OpeningInfo = {
  eco?: string;
  name?: string;
};

export type MoveInsight = {
  move_num: number;
  side: 'White' | 'Black';
  san: string;
  uci: string;
  classification: string;
  move_quality: number;
  score_before: number;
  score_after: number;
  score_change: number;
  best_move: string | null;
  best_move_uci?: string;
  opening?: OpeningInfo | null;
};

export type LastOpeningInfo = {
  eco?: string;
  name?: string;
  move_index?: number;
};

export type SideStats = {
  accuracy?: number;
  precision?: number;
  acpl?: number;
  consistency?: number;
  best_move_percentage?: number;
  avg_expected_points_loss?: number;
  critical_accuracy?: number;
  t1_accuracy?: number;
  t2_accuracy?: number;
  total_moves?: number;
  counts?: Record<string, number>;
};

export type EvalPoint = {
  ply: number;
  score: number;
};

export type DifficultyInfo = {
  overall: number;
  white: number;
  black: number;
};

export type GameInfo = {
  white?: string;
  black?: string;
  whiteElo?: string;
  blackElo?: string;
  event?: string;
  site?: string;
  date?: string;
  round?: string;
  result?: string;
  timeControl?: string;
  eco?: string;
  [key: string]: string | undefined;
};

export type EngineStatus = 'checking' | 'ready' | 'offline';

export type GameState = {
  sessionId: string | null;
  fen: string;
  analysisScore: string;
  analysisDepth: number;
  analysisBestMove: string;
  analysisError: string;
  engineStatus: EngineStatus;
  isBusy: boolean;
  boardOrientation: 'white' | 'black';
  currentOpening: OpeningInfo | null;
  moveInsights: MoveInsight[];
  whiteStats: SideStats;
  blackStats: SideStats;
};

export type ProfileSummary = {
  username: string;
  chesscom_username?: string;
  lichess_username?: string;
  created_at?: string;
  updated_at?: string;
  total_games: number;
};

export type ProfileTimeControlStat = {
  time_control: string;
  games: number;
  accuracy: number;
};

export type ProfileOpeningStat = {
  eco: string;
  name: string;
  games: number;
};

export type ProfileHistoryItem = {
  id: string;
  imported_at: string;
  event?: string;
  site?: string;
  date?: string;
  round?: string;
  result?: string;
  time_control?: string;
  eco?: string;
  opening_name?: string;
  white?: string;
  black?: string;
  white_elo?: string;
  black_elo?: string;
  moves?: number;
  user_side?: 'White' | 'Black' | 'Unknown';
  user_accuracy?: number;
  user_precision?: number;
  user_best_move_percentage?: number;
};

export type ExternalGame = {
    uuid: string;
    source: 'chesscom' | 'lichess';
    url?: string;
    pgn?: string;
    time_control?: string;
    end_time: number;
    rated: boolean;
    fen?: string;
    user_color: string;
    user_result: string;
    opponent_username: string;
    opponent_rating?: number;
};

// Alias for backward compat (or refactor later)
export type ChessComGame = ExternalGame;

export type ProfileDetails = {
  profile: {
    username: string;
    chesscom_username?: string;
    lichess_username?: string;
    created_at?: string;
    updated_at?: string;
    total_games: number;
  };
  stats: {
    overall_accuracy: number;
    accuracy_white: number;
    accuracy_black: number;
    games_as_white: number;
    games_as_black: number;
    by_time_control: ProfileTimeControlStat[];
    top_openings: ProfileOpeningStat[];
  };
  history: ProfileHistoryItem[];
};
