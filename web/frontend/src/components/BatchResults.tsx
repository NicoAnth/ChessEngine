import { motion, AnimatePresence } from 'framer-motion';
import { X, Eye, Layers, AlertTriangle } from 'lucide-react';
import type { BatchGameSummary } from '../lib/types';

type BatchResultsProps = {
  isOpen: boolean;
  games: BatchGameSummary[];
  onReview: (game: BatchGameSummary) => void;
  onClose: () => void;
};

function resultBadge(result: string) {
  const map: Record<string, { label: string; color: string }> = {
    '1-0': { label: '1–0', color: 'var(--success)' },
    '0-1': { label: '0–1', color: 'var(--danger)' },
    '1/2-1/2': { label: '½–½', color: 'var(--text-muted)' },
  };
  return map[result] ?? { label: result || '*', color: 'var(--text-muted)' };
}

function acc(v?: number | null) {
  return typeof v === 'number' ? `${v.toFixed(1)}%` : '—';
}

/* Results of a batch analysis: one row per analysed game. Clicking a row opens
   that game in the normal review UI (each game is its own session). */
export function BatchResults({ isOpen, games, onReview, onClose }: BatchResultsProps) {
  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          className="fixed inset-0 z-40 flex items-center justify-center p-6"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.25 }}
        >
          <div className="absolute inset-0" style={{ background: 'rgba(0,0,0,0.55)', backdropFilter: 'blur(10px)' }} onClick={onClose} />

          <motion.div
            className="relative z-10 flex flex-col rounded-2xl overflow-hidden"
            style={{
              background: 'var(--bg-surface)',
              border: '1px solid var(--border-default)',
              boxShadow: 'var(--shadow-lg)',
              width: 'min(820px, 100%)',
              maxHeight: '85vh',
            }}
            initial={{ scale: 0.95, opacity: 0, y: 20 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.96, opacity: 0, y: 12 }}
            transition={{ type: 'spring', bounce: 0.15, duration: 0.45 }}
          >
            {/* Header */}
            <div
              className="flex items-center justify-between px-6 py-4"
              style={{ borderBottom: '1px solid var(--border-subtle)' }}
            >
              <div className="flex items-center gap-2.5">
                <Layers size={18} style={{ color: 'var(--accent)' }} />
                <div className="flex flex-col">
                  <span className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>
                    {games.length} partie{games.length > 1 ? 's' : ''} analysée{games.length > 1 ? 's' : ''}
                  </span>
                  <span className="text-[11px]" style={{ color: 'var(--text-muted)' }}>
                    Cliquez une partie pour la revoir en détail
                  </span>
                </div>
              </div>
              <button
                onClick={onClose}
                className="w-8 h-8 rounded-lg flex items-center justify-center cursor-pointer"
                style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)', color: 'var(--text-secondary)' }}
                title="Fermer"
              >
                <X size={16} />
              </button>
            </div>

            {/* Table */}
            <div className="overflow-y-auto px-3 py-3" style={{ minHeight: 0 }}>
              {/* Column headers */}
              <div
                className="grid items-center px-3 py-2 text-[10px] font-semibold uppercase tracking-wider"
                style={{ gridTemplateColumns: '1.6fr 0.5fr 1.3fr 0.7fr 0.6fr 0.7fr', color: 'var(--text-muted)' }}
              >
                <span>Joueurs</span>
                <span className="text-center">Rés.</span>
                <span>Ouverture</span>
                <span className="text-center">Préc. ♔/♚</span>
                <span className="text-center">Coups</span>
                <span></span>
              </div>

              {games.map((g) => {
                const rb = resultBadge(g.result);
                return (
                  <motion.div
                    key={g.session_id}
                    initial={{ opacity: 0, y: 6 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="grid items-center px-3 py-2.5 rounded-lg group hover:bg-[var(--bg-hover)] transition-colors"
                    style={{ gridTemplateColumns: '1.6fr 0.5fr 1.3fr 0.7fr 0.6fr 0.7fr' }}
                  >
                    {/* Players */}
                    <div className="flex flex-col min-w-0">
                      <span className="text-xs font-medium truncate" style={{ color: 'var(--text-primary)' }}>
                        {g.white}
                      </span>
                      <span className="text-xs truncate" style={{ color: 'var(--text-secondary)' }}>
                        {g.black}
                      </span>
                    </div>

                    {/* Result */}
                    <span className="text-center text-xs font-bold font-mono" style={{ color: rb.color }}>
                      {rb.label}
                    </span>

                    {/* Opening */}
                    <span className="text-[11px] truncate" style={{ color: 'var(--text-secondary)' }} title={g.opening}>
                      {g.error ? (
                        <span className="flex items-center gap-1" style={{ color: 'var(--danger)' }}>
                          <AlertTriangle size={11} /> Échec
                        </span>
                      ) : (
                        <>
                          {g.eco ? <span style={{ color: 'var(--text-muted)' }}>{g.eco} </span> : null}
                          {g.opening || '—'}
                        </>
                      )}
                    </span>

                    {/* Accuracy white/black */}
                    <span className="text-center text-[11px] font-mono tabular-nums" style={{ color: 'var(--text-secondary)' }}>
                      {acc(g.white_accuracy)} / {acc(g.black_accuracy)}
                    </span>

                    {/* Moves */}
                    <span className="text-center text-[11px] font-mono tabular-nums" style={{ color: 'var(--text-muted)' }}>
                      {g.moves}
                    </span>

                    {/* Review action */}
                    <div className="flex justify-end">
                      <button
                        onClick={() => onReview(g)}
                        disabled={!!g.error}
                        className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-[11px] font-medium cursor-pointer disabled:opacity-30 disabled:cursor-not-allowed"
                        style={{ background: 'var(--accent-soft)', color: 'var(--accent)', border: '1px solid var(--accent-soft)' }}
                        title="Revoir cette partie"
                      >
                        <Eye size={12} /> Revoir
                      </button>
                    </div>
                  </motion.div>
                );
              })}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
