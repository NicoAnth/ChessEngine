import { useState, useEffect, useCallback, useMemo } from 'react';
import { Chess } from 'chess.js';
import axios from 'axios';
import type { AnalysisProgress } from '../components/AnalysisOverlay';
import {
  API_URL,
  type OpeningInfo,
  type LastOpeningInfo,
  type MoveInsight,
  type SideStats,
  type EngineStatus,
  type GameInfo,
  type EvalPoint,
  type DifficultyInfo,
  type ProfileSummary,
  type ProfileDetails,
  type ExternalGame,
} from '../lib/types';

/**
 * Custom hook encapsulating all chess game state and API interactions.
 * Keeps the App component clean and purely presentational.
 */
export function useChessGame() {
  const [game, setGame] = useState(new Chess());
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [fen, setFen] = useState(game.fen());
  const [initialFen, setInitialFen] = useState(game.fen());
  const [reviewPly, setReviewPly] = useState<number | null>(null);
  const [timelineFens, setTimelineFens] = useState<string[]>([game.fen()]);

  // Analysis
  const [analysisScore, setAnalysisScore] = useState('0.00');
  const [analysisDepth, setAnalysisDepth] = useState(0);
  const [analysisBestMove, setAnalysisBestMove] = useState('');
  const [analysisError, setAnalysisError] = useState('');

  // Engine
  const [engineStatus, setEngineStatus] = useState<EngineStatus>('checking');
  const [isBusy, setIsBusy] = useState(false);
  const [analysisProgress, setAnalysisProgress] = useState<AnalysisProgress | null>(null);

  // Board
  const [boardOrientation, setBoardOrientation] = useState<'white' | 'black'>('white');

  // Insights
  const [currentOpening, setCurrentOpening] = useState<OpeningInfo | null>(null);
  const [lastOpening, setLastOpening] = useState<LastOpeningInfo | null>(null);
  const [moveInsights, setMoveInsights] = useState<MoveInsight[]>([]);
  const [whiteStats, setWhiteStats] = useState<SideStats>({});
  const [blackStats, setBlackStats] = useState<SideStats>({});
  const [gameInfo, setGameInfo] = useState<GameInfo | null>(null);
  const [evalChart, setEvalChart] = useState<EvalPoint[]>([]);
  const [difficulty, setDifficulty] = useState<DifficultyInfo | null>(null);

  // Profiles
  const [profiles, setProfiles] = useState<ProfileSummary[]>([]);
  const [activeProfileUsername, setActiveProfileUsername] = useState<string | null>(null);
  const [activeProfileDetails, setActiveProfileDetails] = useState<ProfileDetails | null>(null);

  // ── Helpers ──

  const cloneGameWithHistory = useCallback((source: Chess): Chess => {
    const cloned = new Chess();
    const pgn = source.pgn();
    if (pgn) cloned.loadPgn(pgn);
    return cloned;
  }, []);

  // ── API calls ──

  const checkEngineStatus = useCallback(async () => {
    try {
      const res = await axios.get(`${API_URL}/engine/status`);
      setEngineStatus(res.data.available ? 'ready' : 'offline');
      if (!res.data.available && res.data.error) {
        setAnalysisError(`Engine indisponible: ${res.data.error}`);
      }
    } catch {
      setEngineStatus('offline');
      setAnalysisError('Impossible de contacter le backend moteur.');
    }
  }, []);

  const fetchAnalysis = useCallback(async (sid: string) => {
    try {
      const res = await axios.post(`${API_URL}/game/analyze`, {
        session_id: sid,
        uci: '0000',
      });
      setAnalysisScore(res.data.score ?? '0.00');
      setAnalysisDepth(res.data.depth ?? 0);
      setAnalysisBestMove(res.data.best_move ?? '');
      setAnalysisError('');
    } catch (e) {
      console.error('Analysis failed', e);
      setAnalysisError('Analyse Stockfish indisponible pour cette position.');
    }
  }, []);

  const parseHeaders = useCallback((raw: Record<string, string> | undefined): GameInfo | null => {
    if (!raw || Object.keys(raw).length === 0) return null;
    return {
      white: raw.White,
      black: raw.Black,
      whiteElo: raw.WhiteElo,
      blackElo: raw.BlackElo,
      event: raw.Event,
      site: raw.Site,
      date: raw.Date || raw.UTCDate,
      round: raw.Round,
      result: raw.Result,
      timeControl: raw.TimeControl,
      eco: raw.ECO,
    };
  }, []);

  const fetchInsights = useCallback(async (sid: string) => {
    try {
      const res = await axios.get(`${API_URL}/game/${sid}/insights`);
      setInitialFen(res.data.initial_fen ?? new Chess().fen());
      setCurrentOpening(res.data.opening ?? null);
      setLastOpening(res.data.last_opening ?? null);
      setMoveInsights(res.data.moves ?? []);
      setWhiteStats(res.data.white_stats ?? {});
      setBlackStats(res.data.black_stats ?? {});
      const h = parseHeaders(res.data.headers);
      if (h) setGameInfo(h);
      setEvalChart(res.data.eval_chart ?? []);
      setDifficulty(res.data.difficulty ?? null);
    } catch (e) {
      console.error('Insights failed', e);
    }
  }, [parseHeaders]);

  const fetchProfiles = useCallback(async () => {
    try {
      const res = await axios.get(`${API_URL}/profiles`);
      setProfiles(res.data ?? []);
    } catch (e) {
      console.error('Failed to fetch profiles', e);
    }
  }, []);

  const fetchProfileDetails = useCallback(async (username: string) => {
    try {
      const res = await axios.get(`${API_URL}/profiles/${encodeURIComponent(username)}`);
      setActiveProfileDetails(res.data ?? null);
    } catch (e) {
      console.error('Failed to fetch profile details', e);
      setActiveProfileDetails(null);
    }
  }, []);

  const createProfile = useCallback(async (username: string) => {
    const trimmed = username.trim();
    if (!trimmed) return false;

    try {
      await axios.post(`${API_URL}/profiles`, { username: trimmed });
      setActiveProfileUsername(trimmed);
      await fetchProfiles();
      await fetchProfileDetails(trimmed);
      return true;
    } catch (e) {
      console.error('Failed to create profile', e);
      return false;
    }
  }, [fetchProfiles, fetchProfileDetails]);

  const deleteProfile = useCallback(async (username: string) => {
    try {
      if (!username) return false;
      await axios.delete(`${API_URL}/profiles/${encodeURIComponent(username)}`);

      if (activeProfileUsername === username) {
        setActiveProfileUsername(null);
        setActiveProfileDetails(null);
      }
      await fetchProfiles();
      return true;
    } catch (e) {
      console.error('Failed to delete profile', e);
      return false;
    }
  }, [activeProfileUsername, fetchProfiles]);

  const linkChessComProfile = useCallback(async (username: string, chesscom_username: string) => {
    try {
      if (!username) return;
      await axios.put(`${API_URL}/profiles/${username}/link/chesscom`, { chesscom_username });
      await fetchProfileDetails(username);
    } catch (e) {
      console.error(e);
      throw e;
    }
  }, [fetchProfileDetails]);

  const linkLichessProfile = useCallback(async (username: string, lichess_username: string) => {
    try {
      if (!username) return;
      await axios.put(`${API_URL}/profiles/${username}/link/lichess`, { lichess_username });
      await fetchProfileDetails(username);
    } catch (e) {
      console.error(e);
      throw e;
    }
  }, [fetchProfileDetails]);

  const fetchChessComGames = useCallback(async (username: string): Promise<ExternalGame[]> => {
    try {
      const response = await axios.get<ExternalGame[]>(`${API_URL}/profiles/${username}/chesscom/games`);
      return response.data;
    } catch (e) {
      console.error(e);
      throw e;
    }
  }, []);

  const fetchLichessGames = useCallback(async (username: string): Promise<ExternalGame[]> => {
    try {
      const response = await axios.get<ExternalGame[]>(`${API_URL}/profiles/${username}/lichess/games`);
      return response.data;
    } catch (e) {
      console.error(e);
      throw e;
    }
  }, []);

  const selectProfile = useCallback(async (username: string | null) => {
    setActiveProfileUsername(username);
    if (!username) {
      setActiveProfileDetails(null);
      return;
    }
    await fetchProfileDetails(username);
  }, [fetchProfileDetails]);

  // ── Actions ──

  const startNewGame = useCallback(async () => {
    try {
      setIsBusy(true);
      const res = await axios.post(`${API_URL}/game/new`);
      const data = res.data;
      setSessionId(data.session_id);
      const newGame = new Chess(data.fen);
      setGame(newGame);
      setInitialFen(data.fen);
      setReviewPly(null);
      setTimelineFens([data.fen]);
      setFen(newGame.fen());
      setAnalysisScore('0.00');
      setAnalysisDepth(0);
      setAnalysisBestMove('');
      setAnalysisError('');
      setCurrentOpening(null);
      setLastOpening(null);
      setMoveInsights([]);
      setWhiteStats({});
      setBlackStats({});
      setGameInfo(null);
      setEvalChart([]);
      setDifficulty(null);
      await fetchAnalysis(data.session_id);
      await fetchInsights(data.session_id);
    } catch (error) {
      console.error('Error starting new game:', error);
      setAnalysisError('Échec de création de partie côté backend.');
    } finally {
      setIsBusy(false);
    }
  }, [fetchAnalysis, fetchInsights]);

  const makeMove = useCallback(
    (sourceSquare: string, targetSquare: string): boolean => {
      if (reviewPly !== null) {
        setAnalysisError('Revenez au dernier coup pour jouer une nouvelle suite.');
        return false;
      }
      if (!sessionId || !sourceSquare || !targetSquare) return false;

      const sid = sessionId;
      const previousGame = cloneGameWithHistory(game);
      const tempGame = cloneGameWithHistory(game);
      const move = tempGame.move({
        from: sourceSquare,
        to: targetSquare,
        promotion: 'q',
      });

      if (!move) return false;

      setGame(tempGame);
      setFen(tempGame.fen());

      void axios
        .post(`${API_URL}/game/move`, {
          session_id: sid,
          uci: move.from + move.to + (move.promotion || ''),
        })
        .then(async (response) => {
          if (!response.data.success) {
            setGame(previousGame);
            setFen(previousGame.fen());
            setAnalysisError(response.data.message ?? 'Coup refusé par le serveur.');
            return;
          }
          setAnalysisError('');
          await fetchAnalysis(sid);
          await fetchInsights(sid);
        })
        .catch((e) => {
          console.error('Move error', e);
          setGame(previousGame);
          setFen(previousGame.fen());
          setAnalysisError('Erreur réseau pendant le coup.');
        });

      return true;
    },
    [reviewPly, sessionId, game, cloneGameWithHistory, fetchAnalysis, fetchInsights],
  );

  const playComputerMove = useCallback(async () => {
    if (!sessionId) return;
    try {
      setIsBusy(true);
      const previousGame = cloneGameWithHistory(game);
      const res = await axios.post(`${API_URL}/game/bestmove`, {
        session_id: sessionId,
        uci: '',
      });

      if (res.data.success) {
        const engineUci: string | undefined = res.data.played_uci;
        if (engineUci) {
          const next = cloneGameWithHistory(game);
          const engineMove = next.move({
            from: engineUci.slice(0, 2),
            to: engineUci.slice(2, 4),
            promotion: engineUci.length > 4 ? engineUci[4] : undefined,
          });
          if (engineMove) {
            setGame(next);
            setFen(next.fen());
          } else {
            const serverGame = new Chess(res.data.fen);
            setGame(serverGame);
            setFen(serverGame.fen());
          }
        } else {
          const serverGame = new Chess(res.data.fen);
          setGame(serverGame);
          setFen(serverGame.fen());
        }
        setReviewPly(null);
        setAnalysisError('');
        await fetchAnalysis(sessionId);
        await fetchInsights(sessionId);
      } else {
        setGame(previousGame);
        setFen(previousGame.fen());
        setAnalysisError(res.data.message ?? "Le moteur n'a pas pu jouer.");
      }
    } catch (e) {
      console.error('Engine move failed', e);
      setAnalysisError('Erreur moteur pendant le calcul du meilleur coup.');
    } finally {
      setIsBusy(false);
    }
  }, [sessionId, game, cloneGameWithHistory, fetchAnalysis, fetchInsights]);

  const importPgn = useCallback(
    async (pgnText: string) => {
      if (!pgnText.trim()) {
        setAnalysisError('Le fichier PGN est vide.');
        return false;
      }

      const createSession = async () => {
        const newGameRes = await axios.post(`${API_URL}/game/new`);
        return newGameRes.data.session_id as string;
      };

      try {
        setIsBusy(true);
        setAnalysisProgress(null);

        let sid = sessionId;
        if (!sid) {
          sid = await createSession();
        }

        // SSE streaming import with real-time progress
        const streamImport = (targetSid: string): Promise<{ success: boolean; fen?: string; headers?: Record<string, string> }> => {
          return new Promise((resolve, reject) => {
            const body = JSON.stringify({
              session_id: targetSid,
              pgn: pgnText,
              profile_username: activeProfileUsername,
            });

            fetch(`${API_URL}/game/import/stream`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body,
            })
              .then(async (response) => {
                if (!response.ok) {
                  const errBody = await response.json().catch(() => ({ detail: 'Import failed' }));
                  reject(new Error(errBody.detail ?? `HTTP ${response.status}`));
                  return;
                }

                const reader = response.body?.getReader();
                if (!reader) {
                  reject(new Error('No response body'));
                  return;
                }

                const decoder = new TextDecoder();
                let buffer = '';

                const processLines = (text: string) => {
                  buffer += text;
                  const lines = buffer.split('\n');
                  buffer = lines.pop() ?? '';

                  for (const line of lines) {
                    if (!line.startsWith('data: ')) continue;
                    try {
                      const data = JSON.parse(line.slice(6));

                      if (data.type === 'progress') {
                        setAnalysisProgress({
                          current: data.current,
                          total: data.total,
                          side: data.side,
                          san: data.san,
                          classification: data.classification ?? '',
                        });
                      } else if (data.type === 'done') {
                        resolve({
                          success: true,
                          fen: data.fen,
                          headers: data.headers,
                        });
                      } else if (data.type === 'error') {
                        reject(new Error(data.message));
                      }
                    } catch {
                      // skip malformed SSE lines
                    }
                  }
                };

                const pump = async (): Promise<void> => {
                  const { done, value } = await reader.read();
                  if (done) {
                    if (buffer.trim()) processLines('\n');
                    return;
                  }
                  processLines(decoder.decode(value, { stream: true }));
                  return pump();
                };

                pump().catch(reject);
              })
              .catch(reject);
          });
        };

        let result;
        try {
          result = await streamImport(sid);
        } catch (firstError) {
          if (firstError instanceof Error && firstError.message.includes('404')) {
            sid = await createSession();
            result = await streamImport(sid);
          } else {
            throw firstError;
          }
        }

        if (!result.success) {
          setAnalysisError('Import PGN impossible.');
          return false;
        }

        setSessionId(sid);
        const importedGame = new Chess(result.fen);
        setGame(importedGame);
        setReviewPly(null);
        setFen(importedGame.fen());
        setAnalysisError('');
        setGameInfo(parseHeaders(result.headers));

        await fetchAnalysis(sid);
        await fetchInsights(sid);
        if (activeProfileUsername) {
          await fetchProfileDetails(activeProfileUsername);
          await fetchProfiles();
        }
        return true;
      } catch (e) {
        console.error('PGN import failed', e);
        const message = e instanceof Error ? e.message : 'Erreur lors de l\u2019import PGN.';
        setAnalysisError(message);
        return false;
      } finally {
        setIsBusy(false);
        setAnalysisProgress(null);
      }
    },
    [sessionId, activeProfileUsername, fetchAnalysis, fetchInsights, fetchProfileDetails, fetchProfiles, parseHeaders],
  );

  const undoMove = useCallback(() => {
    if (reviewPly !== null) {
      setReviewPly(null);
      setFen(game.fen());
      return;
    }
    const undone = cloneGameWithHistory(game);
    undone.undo();
    setGame(undone);
    setFen(undone.fen());
  }, [reviewPly, game, cloneGameWithHistory]);

  const flipBoard = useCallback(() => {
    setBoardOrientation((c) => (c === 'white' ? 'black' : 'white'));
  }, []);

  const clearGameInfo = useCallback(() => {
    setGameInfo(null);
  }, []);

  const rebuildTimeline = useCallback((startFen: string, insights: MoveInsight[]): string[] => {
    const timeline: string[] = [startFen];
    const replay = new Chess(startFen);

    for (const insight of insights) {
      try {
        replay.move(insight.uci);
        timeline.push(replay.fen());
      } catch {
        break;
      }
    }

    return timeline;
  }, []);

  useEffect(() => {
    const nextTimeline = rebuildTimeline(initialFen, moveInsights);
    setTimelineFens(nextTimeline);

    if (reviewPly === null) {
      setFen(nextTimeline[nextTimeline.length - 1] ?? initialFen);
      return;
    }

    const clamped = Math.max(0, Math.min(reviewPly, nextTimeline.length - 1));
    if (clamped !== reviewPly) {
      setReviewPly(clamped === nextTimeline.length - 1 ? null : clamped);
    }
    setFen(nextTimeline[clamped] ?? initialFen);
  }, [initialFen, moveInsights, reviewPly, rebuildTimeline]);

  const currentPly = reviewPly ?? Math.max(0, timelineFens.length - 1);
  const maxPly = Math.max(0, timelineFens.length - 1);

  const goToPly = useCallback(
    (ply: number) => {
      if (!timelineFens.length) return;
      const clamped = Math.max(0, Math.min(ply, timelineFens.length - 1));
      setReviewPly(clamped === timelineFens.length - 1 ? null : clamped);
      setFen(timelineFens[clamped]);
    },
    [timelineFens],
  );

  const goToPreviousMove = useCallback(() => {
    if (currentPly <= 0) return;
    goToPly(currentPly - 1);
  }, [currentPly, goToPly]);

  const goToNextMove = useCallback(() => {
    if (currentPly >= maxPly) return;
    goToPly(currentPly + 1);
  }, [currentPly, maxPly, goToPly]);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null;
      const tagName = target?.tagName?.toLowerCase();
      if (tagName === 'input' || tagName === 'textarea' || target?.isContentEditable) {
        return;
      }

      if (event.key === 'ArrowLeft') {
        event.preventDefault();
        goToPreviousMove();
      } else if (event.key === 'ArrowRight') {
        event.preventDefault();
        goToNextMove();
      }
    };

    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [goToPreviousMove, goToNextMove]);

  const displayedGame = useMemo(() => {
    const parsed = new Chess();
    parsed.load(fen);
    return parsed;
  }, [fen]);

  const displayedAnalysis = useMemo(() => {
    const hasHistoricalPosition = currentPly < moveInsights.length;

    if (!hasHistoricalPosition) {
      return {
        score: analysisScore,
        depth: analysisDepth > 0 ? analysisDepth : null,
        bestMove: analysisBestMove,
      };
    }

    const insightForPosition = moveInsights[currentPly];
    const scoreBefore = Number(insightForPosition?.score_before ?? 0);
    const scoreFromWhitePerspective =
      insightForPosition?.side === 'Black' ? -scoreBefore : scoreBefore;

    return {
      score: scoreFromWhitePerspective.toFixed(2),
      depth: null,
      bestMove: insightForPosition?.best_move ?? '',
    };
  }, [currentPly, moveInsights, analysisScore, analysisDepth, analysisBestMove]);

  // ── Init ──

  useEffect(() => {
    void fetchProfiles();
    void checkEngineStatus();
    void startNewGame();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ── Public API ──

  return {
    // State
    fen,
    sessionId,
    analysisScore,
    analysisDepth,
    analysisBestMove,
    displayedAnalysisScore: displayedAnalysis.score,
    displayedAnalysisDepth: displayedAnalysis.depth,
    displayedAnalysisBestMove: displayedAnalysis.bestMove,
    profiles,
    activeProfileUsername,
    activeProfileDetails,
    analysisError,
    engineStatus,
    isBusy,
    analysisProgress,
    boardOrientation,
    currentOpening,
    lastOpening,
    moveInsights,
    reviewPly,
    currentPly,
    maxPly,
    isReviewMode: reviewPly !== null,
    gameInfo,
    evalChart,
    difficulty,
    whiteStats,
    blackStats,
    isGameOver: displayedGame.isGameOver(),
    turn: displayedGame.turn() === 'w' ? 'White' : 'Black',
    moveCount: displayedGame.moveNumber(),

    // Actions
    makeMove,
    playComputerMove,
    importPgn,
    startNewGame,
    undoMove,
    flipBoard,
    clearGameInfo,
    goToPly,
    goToPreviousMove,
    goToNextMove,
    createProfile,
    deleteProfile,
    selectProfile,
    fetchProfileDetails,
    fetchProfiles,
    linkChessComProfile,
    fetchChessComGames,
    linkLichessProfile,
    fetchLichessGames,
  };
}
