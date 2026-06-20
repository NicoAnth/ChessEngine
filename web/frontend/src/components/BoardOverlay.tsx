/**
 * Board overlay rendered on top of the chessboard.
 * Shows:
 *   1. Classification icon badge on the destination square of the last played move
 *   2. Best-move arrow if the played move wasn't the engine's top choice
 *
 * Fully non-interactive (pointer-events: none) so the board keeps working normally.
 */

import { useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import type { MoveInsight } from '../lib/types';
import { getClassificationColor } from '../lib/utils';
import ClassificationIcon from './ClassificationIcon';

type BoardOverlayProps = {
  /** Size of the board in px (assumed square) */
  boardSize: number;
  /** 'white' | 'black' */
  boardOrientation: 'white' | 'black';
  /** The insight for the currently displayed move (ply-indexed) */
  insight: MoveInsight | null;
};

/* ─── Helpers ─── */

/** Parse a square string like "e4" into { file: 0-7, rank: 0-7 } (a1 = 0,0) */
function parseSquare(sq: string): { file: number; rank: number } | null {
  if (!sq || sq.length < 2) return null;
  const file = sq.charCodeAt(0) - 97; // 'a' = 0
  const rank = parseInt(sq[1], 10) - 1; // '1' = 0
  if (file < 0 || file > 7 || rank < 0 || rank > 7) return null;
  return { file, rank };
}

/** Convert file/rank to pixel position (top-left of square) relative to board. */
function squareToPixel(
  file: number,
  rank: number,
  boardSize: number,
  flipped: boolean,
): { x: number; y: number } {
  const sq = boardSize / 8;
  const col = flipped ? 7 - file : file;
  const row = flipped ? rank : 7 - rank;
  return { x: col * sq, y: row * sq };
}

/** Centre of a square */
function squareCenter(
  file: number,
  rank: number,
  boardSize: number,
  flipped: boolean,
): { cx: number; cy: number } {
  const { x, y } = squareToPixel(file, rank, boardSize, flipped);
  const half = boardSize / 16;
  return { cx: x + half, cy: y + half };
}

/* ─── Arrow component ─── */

function BestMoveArrow({
  fromSq,
  toSq,
  boardSize,
  flipped,
  color,
}: {
  fromSq: string;
  toSq: string;
  boardSize: number;
  flipped: boolean;
  color: string;
}) {
  const from = parseSquare(fromSq);
  const to = parseSquare(toSq);
  if (!from || !to) return null;

  const { cx: x1, cy: y1 } = squareCenter(from.file, from.rank, boardSize, flipped);
  const { cx: x2, cy: y2 } = squareCenter(to.file, to.rank, boardSize, flipped);

  const dx = x2 - x1;
  const dy = y2 - y1;
  const len = Math.sqrt(dx * dx + dy * dy);
  if (len < 1) return null;

  // Unit vectors — along and perpendicular to the arrow direction
  const ux = dx / len;
  const uy = dy / len;
  const px = -uy; // perpendicular
  const py = ux;

  const sqSize = boardSize / 8;
  const bodyHalf = sqSize * 0.12;   // half-width of shaft
  const headLen = sqSize * 0.45;    // length of arrowhead triangle
  const headHalf = sqSize * 0.28;   // half-width of arrowhead base

  // Shaft runs from start centre to where the head begins
  const shaftEndX = x2 - ux * headLen;
  const shaftEndY = y2 - uy * headLen;

  // 7-point polygon: shaft (4 corners) + head (3 corners)
  const points = [
    // Shaft start (left / right of centre)
    `${x1 + px * bodyHalf},${y1 + py * bodyHalf}`,
    // Shaft end left
    `${shaftEndX + px * bodyHalf},${shaftEndY + py * bodyHalf}`,
    // Head base left (wider)
    `${shaftEndX + px * headHalf},${shaftEndY + py * headHalf}`,
    // Tip
    `${x2},${y2}`,
    // Head base right
    `${shaftEndX - px * headHalf},${shaftEndY - py * headHalf}`,
    // Shaft end right
    `${shaftEndX - px * bodyHalf},${shaftEndY - py * bodyHalf}`,
    // Shaft start right
    `${x1 - px * bodyHalf},${y1 - py * bodyHalf}`,
  ].join(' ');

  return (
    <motion.svg
      className="absolute inset-0"
      width={boardSize}
      height={boardSize}
      viewBox={`0 0 ${boardSize} ${boardSize}`}
      initial={{ opacity: 0 }}
      animate={{ opacity: 0.82 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.25 }}
      style={{ pointerEvents: 'none' }}
    >
      <defs>
        <filter id="arrow-shadow" x="-20%" y="-20%" width="140%" height="140%">
          <feDropShadow dx="0" dy="1" stdDeviation="2" floodColor="#000" floodOpacity="0.35" />
        </filter>
      </defs>
      <polygon
        points={points}
        fill={color}
        filter="url(#arrow-shadow)"
      />
    </motion.svg>
  );
}

/* ─── Classification badge ─── */

function ClassificationBadge({
  classification,
  square,
  boardSize,
  flipped,
}: {
  classification: string;
  square: string;
  boardSize: number;
  flipped: boolean;
}) {
  const parsed = parseSquare(square);
  if (!parsed) return null;

  const { x, y } = squareToPixel(parsed.file, parsed.rank, boardSize, flipped);
  const sqSize = boardSize / 8;
  const badgeSize = Math.round(sqSize * 0.42);
  const color = getClassificationColor(classification);

  // Position at bottom-right corner of the square
  const left = x + sqSize - badgeSize * 0.55;
  const top = y - badgeSize * 0.35;

  return (
    <motion.div
      className="absolute flex items-center justify-center rounded-full"
      style={{
        width: badgeSize,
        height: badgeSize,
        left,
        top,
        background: 'var(--bg-deep)',
        border: `2px solid ${color}`,
        boxShadow: `0 0 8px ${color}40, 0 2px 6px rgba(0,0,0,0.4)`,
        zIndex: 20,
        pointerEvents: 'none',
      }}
      initial={{ scale: 0, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      exit={{ scale: 0, opacity: 0 }}
      transition={{ type: 'spring', stiffness: 500, damping: 25 }}
    >
      <ClassificationIcon
        classification={classification}
        size={Math.round(badgeSize * 0.6)}
        style={{ color }}
      />
    </motion.div>
  );
}

/* ─── Public overlay ─── */

export function BoardOverlay({
  boardSize,
  boardOrientation,
  insight,
}: BoardOverlayProps) {
  const flipped = boardOrientation === 'black';

  const { destSquare, bestFromSq, bestToSq, classification } = useMemo(() => {
    if (!insight) return { destSquare: null, bestFromSq: null, bestToSq: null, classification: null };

    // Destination square of the played move (last 2 chars of uci, e.g. "e2e4" → "e4")
    const uci = insight.uci ?? '';
    const dest = uci.length >= 4 ? uci.slice(2, 4) : null;

    // Best move arrow (only if played wasn't best)
    let bFrom: string | null = null;
    let bTo: string | null = null;
    const bestUci = insight.best_move_uci ?? '';
    if (bestUci.length >= 4) {
      bFrom = bestUci.slice(0, 2);
      bTo = bestUci.slice(2, 4);
    }

    // Arrow colour based on classification severity
    const cls = insight.classification;

    return {
      destSquare: dest,
      bestFromSq: bFrom,
      bestToSq: bTo,
      classification: cls,
    };
  }, [insight]);

  // Choose arrow colour: green-ish for "Meilleur coup" context, otherwise use a contrasting
  // accent to indicate the suggested improvement
  const arrowColor = useMemo(() => {
    if (!insight?.best_move_uci) return '';
    // Use a muted teal for the best-move suggestion arrow
    return '#3BD97B';
  }, [insight?.best_move_uci]);

  return (
    <div
      className="absolute inset-0"
      style={{ width: boardSize, height: boardSize, pointerEvents: 'none', zIndex: 10 }}
    >
      <AnimatePresence mode="wait">
        {/* Best-move arrow */}
        {bestFromSq && bestToSq && (
          <BestMoveArrow
            key={`arrow-${bestFromSq}-${bestToSq}`}
            fromSq={bestFromSq}
            toSq={bestToSq}
            boardSize={boardSize}
            flipped={flipped}
            color={arrowColor}
          />
        )}
      </AnimatePresence>

      <AnimatePresence mode="wait">
        {/* Classification badge */}
        {destSquare && classification && (
          <ClassificationBadge
            key={`badge-${destSquare}-${classification}`}
            classification={classification}
            square={destSquare}
            boardSize={boardSize}
            flipped={flipped}
          />
        )}
      </AnimatePresence>
    </div>
  );
}
