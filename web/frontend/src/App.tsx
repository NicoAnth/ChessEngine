import { useState, useMemo } from 'react';
import { Chessboard } from 'react-chessboard';
import { useChessGame } from './hooks/useChessGame';
import { TopBar } from './components/TopBar';
import { EvalBar } from './components/EvalBar';
import { PlayerBanner } from './components/PlayerBanner';
import { AnalysisPanel } from './components/AnalysisPanel';
import { MoveHistory } from './components/MoveHistory';
import { GameControls } from './components/GameControls';
import { GameInfoBanner } from './components/GameInfoBanner';
import { GameReport } from './components/GameReport';
import { UserProfileModal } from './components/UserProfileModal';
import { AnalysisOverlay } from './components/AnalysisOverlay';
import { BatchOverlay } from './components/BatchOverlay';
import { BatchResults } from './components/BatchResults';
import { BoardOverlay } from './components/BoardOverlay';
import { OpeningBanner } from './components/OpeningBanner';

function App() {
  const {
    fen,
    displayedAnalysisScore,
    displayedAnalysisDepth,
    displayedAnalysisBestMove,
    analysisError,
    engineStatus,
    isBusy,
    analysisProgress,
    batchActive,
    batchProgress,
    batchResults,
    boardOrientation,
    lastOpening,
    moveInsights,
    currentPly,
    maxPly,
    isReviewMode,
    gameInfo,
    whiteStats,
    blackStats,
    turn,
    moveCount,
    makeMove,
    playComputerMove,
    importPgn,
    importGames,
    loadBatchGame,
    closeBatchResults,
    startNewGame,
    undoMove,
    flipBoard,
    goToPly,
    goToPreviousMove,
    goToNextMove,
    clearGameInfo,
    evalChart,
    difficulty,
    profiles,
    activeProfileUsername,
    activeProfileDetails,
    createProfile,
    deleteProfile,
    selectProfile,
    linkChessComProfile,
    fetchChessComGames,
    linkLichessProfile,
    fetchLichessGames,
  } = useChessGame();

  const [showReport, setShowReport] = useState(false);
  const [showProfiles, setShowProfiles] = useState(false);
  const isFlipped = boardOrientation === 'black';
  const topPlayer = isFlipped ? 'white' : 'black';
  const bottomPlayer = isFlipped ? 'black' : 'white';

  // Current move insight for board overlay (ply 0 = initial, insight[0] = after ply 1)
  const currentInsight = useMemo(() => {
    if (currentPly <= 0 || moveInsights.length === 0) return null;
    // currentPly is 1-indexed for moves: insight at index ply-1
    return moveInsights[currentPly - 1] ?? null;
  }, [currentPly, moveInsights]);

  return (
    <div
      className="min-h-screen flex flex-col relative"
      style={{ background: 'var(--bg-deep)', color: 'var(--text-primary)' }}
    >
      {/* Ambient glow effects */}
      <div className="ambient-glow" style={{ top: '-200px', left: '20%' }} />
      <div className="ambient-glow" style={{ bottom: '-200px', right: '10%' }} />

      {/* Top Bar */}
      <TopBar
        engineStatus={engineStatus}
        isBusy={isBusy}
        onNewGame={startNewGame}
        onPlayEngine={playComputerMove}
        onImportGame={importGames}
        onOpenReport={() => setShowReport(true)}
        onOpenProfiles={() => setShowProfiles(true)}
        hasInsights={moveInsights.length > 0}
        activeProfileUsername={activeProfileUsername}
      />

      {/* Main Layout */}
      <main
        className="flex-1 flex justify-center items-start gap-6 px-6 py-6 relative z-10"
        style={{ maxWidth: 1280, margin: '0 auto', width: '100%' }}
      >
        {/* Left Column: Board Area */}
        <div className="flex flex-col gap-2" style={{ width: 'fit-content' }}>
          {/* Game info banner (imported game metadata) */}
          {gameInfo && (
            <GameInfoBanner info={gameInfo} onDismiss={clearGameInfo} />
          )}

          {/* Top player banner */}
          <PlayerBanner
            color={topPlayer}
            stats={topPlayer === 'white' ? whiteStats : blackStats}
            isActive={
              (topPlayer === 'white' && turn === 'White') ||
              (topPlayer === 'black' && turn === 'Black')
            }
            playerName={topPlayer === 'white' ? gameInfo?.white : gameInfo?.black}
            playerElo={topPlayer === 'white' ? gameInfo?.whiteElo : gameInfo?.blackElo}
          />

          {/* Opening banner */}
          <OpeningBanner
            insights={moveInsights}
            currentPly={currentPly}
            lastOpening={lastOpening}
          />

          {/* Board + Eval bar row */}
          <div className="flex gap-2 items-stretch">
            {/* Eval Bar */}
            <EvalBar score={displayedAnalysisScore} flipped={isFlipped} />

            {/* Chessboard */}
            <div className="board-container relative" style={{ width: 560, height: 560 }}>
              <Chessboard
                options={{
                  position: fen,
                  boardOrientation,
                  onPieceDrop: ({
                    sourceSquare,
                    targetSquare,
                  }: {
                    sourceSquare: string | null;
                    targetSquare: string | null;
                  }) => {
                    if (isReviewMode) return false;
                    if (!sourceSquare || !targetSquare) return false;
                    return makeMove(sourceSquare, targetSquare);
                  },
                  darkSquareStyle: { backgroundColor: 'var(--board-dark)' },
                  lightSquareStyle: { backgroundColor: 'var(--board-light)' },
                }}
              />
              <BoardOverlay
                boardSize={560}
                boardOrientation={boardOrientation}
                insight={currentInsight}
              />
            </div>
          </div>

          {/* Bottom player banner */}
          <PlayerBanner
            color={bottomPlayer}
            stats={bottomPlayer === 'white' ? whiteStats : blackStats}
            isActive={
              (bottomPlayer === 'white' && turn === 'White') ||
              (bottomPlayer === 'black' && turn === 'Black')
            }
            playerName={bottomPlayer === 'white' ? gameInfo?.white : gameInfo?.black}
            playerElo={bottomPlayer === 'white' ? gameInfo?.whiteElo : gameInfo?.blackElo}
          />

          {/* Controls under board */}
          <div className="flex justify-center mt-1">
            <GameControls
              onUndo={undoMove}
              onFlip={flipBoard}
              onPrevMove={goToPreviousMove}
              onNextMove={goToNextMove}
              canGoPrev={currentPly > 0}
              canGoNext={currentPly < maxPly}
              boardOrientation={boardOrientation}
            />
          </div>
        </div>

        {/* Right Column: Sidebar */}
        <div
          className="flex flex-col gap-4"
          style={{ width: 320, minHeight: 0, maxHeight: 'calc(100vh - 100px)' }}
        >
          {/* Analysis Panel */}
          <AnalysisPanel
            score={displayedAnalysisScore}
            depth={displayedAnalysisDepth}
            bestMove={displayedAnalysisBestMove}
            whiteStats={whiteStats}
            blackStats={blackStats}
            turn={turn}
            moveCount={moveCount}
            error={analysisError}
          />

          {/* Move History */}
          <div className="flex-1 flex flex-col min-h-0">
            <MoveHistory
              insights={moveInsights}
              activePly={currentPly}
              onSelectPly={goToPly}
            />
          </div>
        </div>
      </main>

      {/* Game Report Modal */}
      <GameReport
        isOpen={showReport}
        onClose={() => setShowReport(false)}
        whiteStats={whiteStats}
        blackStats={blackStats}
        evalChart={evalChart}
        difficulty={difficulty}
        gameInfo={gameInfo}
        insights={moveInsights}
        onSelectPly={goToPly}
      />

      <UserProfileModal
        isOpen={showProfiles}
        onClose={() => setShowProfiles(false)}
        profiles={profiles}
        activeProfileUsername={activeProfileUsername}
        activeProfileDetails={activeProfileDetails}
        onCreateProfile={createProfile}
        onDeleteProfile={deleteProfile}
        onSelectProfile={selectProfile}
        onLinkChessCom={linkChessComProfile}
        onFetchChessComGames={fetchChessComGames}
        onLinkLichess={linkLichessProfile}
        onFetchLichessGames={fetchLichessGames}
        onImportGame={importPgn}
      />

      {/* Analysis Progress Overlay (single game) */}
      <AnalysisOverlay
        isOpen={isBusy && analysisProgress !== null}
        progress={analysisProgress}
      />

      {/* Batch analysis progress overlay (multi-game import) */}
      <BatchOverlay
        isOpen={batchActive}
        progress={batchProgress}
        doneCount={batchResults?.length ?? 0}
      />

      {/* Batch results list (after a batch completes) */}
      <BatchResults
        isOpen={!batchActive && (batchResults?.length ?? 0) > 0}
        games={batchResults ?? []}
        onReview={loadBatchGame}
        onClose={closeBatchResults}
      />
    </div>
  );
}

export default App;
