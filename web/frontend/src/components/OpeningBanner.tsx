import { useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { BookOpen, BookX, Sparkles } from 'lucide-react';
import type { MoveInsight, LastOpeningInfo } from '../lib/types';

type OpeningBannerProps = {
  insights: MoveInsight[];
  currentPly: number;
  lastOpening: LastOpeningInfo | null;
};

/**
 * Modern opening banner that shows the current opening information
 * based on the currently viewed ply. Animates between states:
 * - In theory: shows current ECO + opening name with book icon
 * - Out of theory: shows the game's final opening + "Sortie de la théorie"
 * - No opening: hidden
 */
export function OpeningBanner({ insights, currentPly, lastOpening }: OpeningBannerProps) {
  // Derive current opening from the move at current ply
  const { displayedOpening, isInTheory, theoryEndMove } = useMemo(() => {
    if (!lastOpening?.name) {
      return { displayedOpening: null, isInTheory: false, theoryEndMove: 0 };
    }

    // Calculate the move number where theory ends
    // move_index is 0-based ply count from detector
    const theoryEnd = lastOpening.move_index !== undefined ? lastOpening.move_index + 1 : 0;

    // Find the opening at the current ply
    if (currentPly <= 0) {
      return {
        displayedOpening: { eco: lastOpening.eco, name: lastOpening.name },
        isInTheory: true,
        theoryEndMove: theoryEnd,
      };
    }

    const insight = insights[currentPly - 1];
    if (!insight) {
      return {
        displayedOpening: { eco: lastOpening.eco, name: lastOpening.name },
        isInTheory: false,
        theoryEndMove: theoryEnd,
      };
    }

    // If the current move has an opening, we're still in theory
    if (insight.opening?.name) {
      return {
        displayedOpening: insight.opening,
        isInTheory: true,
        theoryEndMove: theoryEnd,
      };
    }

    // Past theory — show the game's final opening
    return {
      displayedOpening: { eco: lastOpening.eco, name: lastOpening.name },
      isInTheory: false,
      theoryEndMove: theoryEnd,
    };
  }, [insights, currentPly, lastOpening]);

  if (!displayedOpening) return null;

  // Calculate the move number for display (e.g. "coup 6" for ply 11 = move 6 White)
  const theoryEndMoveNum = Math.ceil(theoryEndMove / 2);

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={`${displayedOpening.eco}-${isInTheory}`}
        initial={{ opacity: 0, y: -6, scale: 0.97 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: 6, scale: 0.97 }}
        transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
        className="relative overflow-hidden rounded-xl"
        style={{
          background: isInTheory
            ? 'linear-gradient(135deg, rgba(167, 139, 250, 0.08) 0%, rgba(167, 139, 250, 0.03) 100%)'
            : 'linear-gradient(135deg, rgba(232, 168, 76, 0.08) 0%, rgba(232, 168, 76, 0.03) 100%)',
          border: `1px solid ${isInTheory ? 'rgba(167, 139, 250, 0.15)' : 'rgba(232, 168, 76, 0.15)'}`,
        }}
      >
        {/* Subtle shimmer effect */}
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            background: isInTheory
              ? 'radial-gradient(ellipse at 20% 50%, rgba(167, 139, 250, 0.06) 0%, transparent 70%)'
              : 'radial-gradient(ellipse at 20% 50%, rgba(232, 168, 76, 0.06) 0%, transparent 70%)',
          }}
        />

        <div className="relative flex items-center gap-3 px-4 py-2.5">
          {/* Icon */}
          <motion.div
            initial={{ rotate: -10, scale: 0.8 }}
            animate={{ rotate: 0, scale: 1 }}
            transition={{ duration: 0.4, ease: 'easeOut' }}
            className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0"
            style={{
              background: isInTheory
                ? 'rgba(167, 139, 250, 0.12)'
                : 'rgba(232, 168, 76, 0.12)',
              color: isInTheory ? 'var(--cls-theory)' : 'var(--accent)',
            }}
          >
            {isInTheory ? <BookOpen size={16} /> : <BookX size={16} />}
          </motion.div>

          {/* Text content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              {/* ECO badge */}
              {displayedOpening.eco && (
                <span
                  className="text-[10px] font-bold tracking-wider px-1.5 py-0.5 rounded"
                  style={{
                    background: isInTheory
                      ? 'rgba(167, 139, 250, 0.15)'
                      : 'rgba(232, 168, 76, 0.15)',
                    color: isInTheory ? 'var(--cls-theory)' : 'var(--accent)',
                  }}
                >
                  {displayedOpening.eco}
                </span>
              )}

              {/* Opening name */}
              <span
                className="text-sm font-semibold truncate"
                style={{ color: 'var(--text-primary)' }}
              >
                {displayedOpening.name}
              </span>
            </div>

            {/* Subtitle: theory status */}
            {!isInTheory && theoryEndMoveNum > 0 && (
              <motion.div
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.15, duration: 0.25 }}
                className="flex items-center gap-1.5 mt-0.5"
              >
                <Sparkles
                  size={10}
                  style={{ color: 'var(--accent)', opacity: 0.7 }}
                />
                <span
                  className="text-[10px] font-medium"
                  style={{ color: 'var(--text-muted)' }}
                >
                  Sortie de la théorie au coup {theoryEndMoveNum}
                </span>
              </motion.div>
            )}
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
