import { motion, AnimatePresence } from 'framer-motion';
import {
  Trophy,
  Calendar,
  MapPin,
  Clock,
  Swords,
  X,
} from 'lucide-react';
import type { GameInfo } from '../lib/types';

type GameInfoBannerProps = {
  info: GameInfo | null;
  onDismiss: () => void;
};

export function GameInfoBanner({ info, onDismiss }: GameInfoBannerProps) {
  if (!info) return null;

  const hasEvent = info.event && info.event !== '?';
  const hasSite = info.site && info.site !== '?';
  const hasDate = info.date && info.date !== '????.??.??';
  const hasResult = info.result && info.result !== '*';
  const hasTimeControl = info.timeControl;

  // Format date (PGN dates are YYYY.MM.DD)
  const formatDate = (raw: string) => {
    const parts = raw.split('.');
    if (parts.length === 3) {
      const [y, m, d] = parts;
      const months = [
        '', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
        'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
      ];
      const mi = parseInt(m, 10);
      return `${months[mi] || m} ${parseInt(d, 10)}, ${y}`;
    }
    return raw;
  };

  // Format result into a readable label + color
  const resultDisplay = (r: string) => {
    switch (r) {
      case '1-0':
        return { label: 'White wins', color: 'var(--success)' };
      case '0-1':
        return { label: 'Black wins', color: 'var(--danger)' };
      case '1/2-1/2':
        return { label: 'Draw', color: 'var(--text-muted)' };
      default:
        return { label: r, color: 'var(--text-muted)' };
    }
  };

  const result = hasResult ? resultDisplay(info.result!) : null;

  const tags: { icon: React.ReactNode; text: string; accent?: boolean; color?: string }[] = [];

  if (hasEvent) tags.push({ icon: <Trophy size={12} />, text: info.event! });
  if (hasSite) tags.push({ icon: <MapPin size={12} />, text: info.site! });
  if (hasDate) tags.push({ icon: <Calendar size={12} />, text: formatDate(info.date!) });
  if (hasTimeControl) tags.push({ icon: <Clock size={12} />, text: info.timeControl! });
  if (result) tags.push({ icon: <Swords size={12} />, text: result.label, accent: true, color: result.color });

  if (tags.length === 0) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: -12, height: 0 }}
        animate={{ opacity: 1, y: 0, height: 'auto' }}
        exit={{ opacity: 0, y: -12, height: 0 }}
        transition={{ duration: 0.3, ease: 'easeOut' }}
        className="glass-panel-sm px-4 py-2.5 flex items-center gap-3 overflow-hidden relative"
      >
        {/* Tags */}
        <div className="flex items-center gap-3 flex-wrap flex-1 min-w-0">
          {tags.map((tag, i) => (
            <div
              key={i}
              className="flex items-center gap-1.5 text-[11px] font-medium whitespace-nowrap"
              style={{ color: tag.color ?? 'var(--text-secondary)' }}
            >
              <span style={{ color: tag.accent ? tag.color : 'var(--text-muted)', opacity: 0.7 }}>
                {tag.icon}
              </span>
              <span
                className={tag.accent ? 'font-semibold' : ''}
              >
                {tag.text}
              </span>
              {i < tags.length - 1 && (
                <span
                  className="ml-1.5"
                  style={{
                    width: 3,
                    height: 3,
                    borderRadius: '50%',
                    background: 'var(--border-strong)',
                    display: 'inline-block',
                  }}
                />
              )}
            </div>
          ))}
        </div>

        {/* Dismiss */}
        <button
          onClick={onDismiss}
          className="flex-shrink-0 w-5 h-5 flex items-center justify-center rounded opacity-40 hover:opacity-100 transition-opacity cursor-pointer"
          style={{ color: 'var(--text-muted)' }}
          title="Dismiss"
        >
          <X size={12} />
        </button>
      </motion.div>
    </AnimatePresence>
  );
}
