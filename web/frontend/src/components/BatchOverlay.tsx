import { motion, AnimatePresence } from 'framer-motion';
import { Layers } from 'lucide-react';
import type { BatchProgress } from '../lib/types';

type BatchOverlayProps = {
  isOpen: boolean;
  progress: BatchProgress | null;
  doneCount: number;
};

/* Progress overlay for a multi-game batch analysis: overall game count + the
   current game's position progress. Mirrors AnalysisOverlay's visual language. */
export function BatchOverlay({ isOpen, progress, doneCount }: BatchOverlayProps) {
  const movePct = progress && progress.moveTotal
    ? Math.round((progress.moveCurrent / progress.moveTotal) * 100)
    : 0;
  const gamePct = progress && progress.gameTotal
    ? Math.round((doneCount / progress.gameTotal) * 100)
    : 0;

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          className="fixed inset-0 z-50 flex items-center justify-center"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.35 }}
        >
          <div
            className="absolute inset-0"
            style={{
              background: 'rgba(0, 0, 0, 0.55)',
              backdropFilter: 'blur(16px) saturate(120%)',
              WebkitBackdropFilter: 'blur(16px) saturate(120%)',
            }}
          />

          <motion.div
            className="relative z-10 flex flex-col items-center gap-6 px-12 py-10 rounded-2xl"
            style={{
              background: 'var(--glass-bg)',
              backdropFilter: 'blur(24px) saturate(160%)',
              WebkitBackdropFilter: 'blur(24px) saturate(160%)',
              border: '1px solid var(--border-default)',
              boxShadow:
                '0 0 0 1px var(--border-subtle), var(--shadow-lg), 0 0 80px rgba(232, 168, 76, 0.08)',
              minWidth: 420,
              maxWidth: 500,
            }}
            initial={{ scale: 0.92, opacity: 0, y: 24 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.95, opacity: 0, y: 12 }}
            transition={{ type: 'spring', bounce: 0.15, duration: 0.5 }}
          >
            {/* Icon */}
            <div
              className="relative z-10 w-16 h-16 rounded-2xl flex items-center justify-center"
              style={{
                background: 'linear-gradient(135deg, var(--accent-soft), rgba(232,168,76,0.03))',
                border: '1px solid var(--accent-soft)',
              }}
            >
              <motion.div
                animate={{ rotate: [0, 6, -6, 0] }}
                transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
              >
                <Layers size={26} style={{ color: 'var(--accent)' }} />
              </motion.div>
            </div>

            {/* Title */}
            <div className="text-center">
              <h2 className="text-base font-semibold tracking-tight" style={{ color: 'var(--text-primary)' }}>
                Analyse du lot
              </h2>
              <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>
                Partie {progress?.gameCurrent ?? 0} / {progress?.gameTotal ?? 0}
                {progress?.gameLabel ? ` · ${progress.gameLabel}` : ''}
              </p>
            </div>

            {/* Overall games progress */}
            <div className="w-full flex flex-col gap-2">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-medium" style={{ color: 'var(--text-secondary)' }}>
                  Parties terminées : {doneCount} / {progress?.gameTotal ?? 0}
                </span>
                <span className="text-[11px] font-bold font-mono tabular-nums" style={{ color: 'var(--accent)' }}>
                  {gamePct}%
                </span>
              </div>
              <div className="relative w-full h-2 rounded-full overflow-hidden" style={{ background: 'var(--bg-hover)' }}>
                <motion.div
                  className="absolute inset-y-0 left-0 rounded-full"
                  style={{ background: 'linear-gradient(90deg, var(--accent), #f0b860)', boxShadow: '0 0 12px var(--accent-glow)' }}
                  initial={{ width: '0%' }}
                  animate={{ width: `${gamePct}%` }}
                  transition={{ duration: 0.4, ease: 'easeOut' }}
                />
              </div>
            </div>

            {/* Current game position progress */}
            <div className="w-full flex flex-col gap-2">
              <div className="flex items-center justify-between">
                <span className="text-[11px]" style={{ color: 'var(--text-muted)' }}>
                  Position {progress?.moveCurrent ?? 0} / {progress?.moveTotal ?? 0}
                </span>
                <span className="text-[11px] font-mono tabular-nums" style={{ color: 'var(--text-muted)' }}>
                  {movePct}%
                </span>
              </div>
              <div className="relative w-full h-1.5 rounded-full overflow-hidden" style={{ background: 'var(--bg-hover)' }}>
                <motion.div
                  className="absolute inset-y-0 left-0 rounded-full"
                  style={{ background: 'var(--accent-soft)' }}
                  animate={{ width: `${movePct}%` }}
                  transition={{ duration: 0.2, ease: 'easeOut' }}
                />
              </div>
            </div>

            <p className="text-[10px] italic" style={{ color: 'var(--text-muted)', opacity: 0.6 }}>
              Le moteur creuse vos parties…
            </p>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
