import { useRef, type ChangeEvent } from 'react';
import { motion } from 'framer-motion';
import {
  Cpu,
  RotateCcw,
  Zap,
  Sun,
  Moon,
  Upload,
  BarChart3,
  UserRound,
} from 'lucide-react';
import type { EngineStatus } from '../lib/types';
import { useTheme } from '../hooks/useTheme';

type TopBarProps = {
  engineStatus: EngineStatus;
  isBusy: boolean;
  onNewGame: () => void;
  onPlayEngine: () => void;
  onImportGame: (pgnText: string) => void | Promise<void | boolean>;
  onOpenReport: () => void;
  onOpenProfiles: () => void;
  hasInsights: boolean;
  activeProfileUsername: string | null;
};

export function TopBar({
  engineStatus,
  isBusy,
  onNewGame,
  onPlayEngine,
  onImportGame,
  onOpenReport,
  onOpenProfiles,
  hasInsights,
  activeProfileUsername,
}: TopBarProps) {
  const { toggleTheme, isDark } = useTheme();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleImportClick = () => {
    if (isBusy) return;
    fileInputRef.current?.click();
  };

  const handleFileChange = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    const text = await file.text();
    await Promise.resolve(onImportGame(text));
    event.target.value = '';
  };

  return (
    <motion.header
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.4, ease: 'easeOut' }}
      className="w-full px-6 py-3 flex items-center justify-between z-20 relative"
      style={{
        borderBottom: '1px solid var(--border-subtle)',
        background: 'var(--topbar-bg)',
        backdropFilter: 'blur(12px)',
      }}
    >
      {/* Logo – Caissa branding */}
      <div className="flex items-center gap-3">
        <motion.div
          className="relative w-10 h-10 flex items-center justify-center"
          whileHover={{ scale: 1.06 }}
          transition={{ type: 'spring', stiffness: 400, damping: 15 }}
        >
          <img
            src={isDark ? '/Caissa.png' : '/CaissaNoire.png'}
            alt="Caissa"
            className="w-10 h-10 object-contain"
            style={{ filter: isDark ? 'drop-shadow(0 0 8px rgba(232, 168, 76, 0.15))' : 'none' }}
          />
        </motion.div>
        <div className="flex flex-col">
          <span className="text-base font-bold tracking-tight leading-none gradient-text">
            Caissa
          </span>
          <span
            className="text-[10px] font-medium tracking-widest uppercase leading-none mt-0.5"
            style={{ color: 'var(--text-muted)' }}
          >
            Chess Analysis
          </span>
        </div>
      </div>

      {/* Center: Engine status chip */}
      <div className="flex items-center gap-2">
        <div
          className="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium"
          style={{
            background: 'var(--bg-elevated)',
            border: '1px solid var(--border-subtle)',
            color: 'var(--text-secondary)',
          }}
        >
          <span
            className="status-dot w-2 h-2 rounded-full inline-block"
            style={{
              backgroundColor:
                engineStatus === 'ready'
                  ? 'var(--success)'
                  : engineStatus === 'checking'
                    ? 'var(--warning)'
                    : 'var(--danger)',
            }}
          />
          <Cpu size={12} />
          Stockfish {engineStatus === 'ready' ? 'Ready' : engineStatus === 'checking' ? '...' : 'Off'}
        </div>
      </div>

      {/* Right: Actions */}
      <div className="flex items-center gap-2">
        <input
          ref={fileInputRef}
          type="file"
          accept=".pgn,text/plain"
          className="hidden"
          onChange={handleFileChange}
        />

        {/* Theme toggle */}
        <button
          onClick={toggleTheme}
          className="w-9 h-9 rounded-lg flex items-center justify-center cursor-pointer transition-colors"
          style={{
            background: 'var(--bg-elevated)',
            border: '1px solid var(--border-subtle)',
            color: 'var(--text-secondary)',
          }}
          title={isDark ? 'Light mode' : 'Dark mode'}
        >
          <motion.div
            key={isDark ? 'moon' : 'sun'}
            initial={{ rotate: -90, opacity: 0 }}
            animate={{ rotate: 0, opacity: 1 }}
            exit={{ rotate: 90, opacity: 0 }}
            transition={{ duration: 0.3 }}
          >
            {isDark ? <Sun size={16} /> : <Moon size={16} />}
          </motion.div>
        </button>

        {/* Report button */}
        <button
          onClick={onOpenReport}
          disabled={!hasInsights}
          className="btn-glow flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
          style={{
            background: 'var(--bg-elevated)',
            border: '1px solid var(--border-default)',
            color: hasInsights ? 'var(--accent)' : 'var(--text-muted)',
          }}
          title="Game report"
        >
          <BarChart3 size={14} />
          Report
        </button>

        <button
          onClick={onOpenProfiles}
          className="btn-glow flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium cursor-pointer"
          style={{
            background: activeProfileUsername ? 'var(--accent-soft)' : 'var(--bg-elevated)',
            border: `1px solid ${activeProfileUsername ? 'var(--accent)' : 'var(--border-default)'}`,
            color: activeProfileUsername ? 'var(--accent)' : 'var(--text-secondary)',
          }}
          title="Profils utilisateur"
        >
          <UserRound size={14} />
          {activeProfileUsername ?? 'Profile'}
        </button>

        <button
          onClick={handleImportClick}
          disabled={isBusy}
          className="btn-glow flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
          style={{
            background: 'var(--bg-elevated)',
            border: '1px solid var(--border-default)',
            color: 'var(--text-secondary)',
          }}
          title="Importer une partie PGN"
        >
          <Upload size={14} />
          Import PGN
        </button>

        <button
          onClick={onPlayEngine}
          disabled={isBusy}
          className="btn-glow flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
          style={{
            background: 'var(--bg-elevated)',
            border: '1px solid var(--border-default)',
            color: 'var(--accent)',
          }}
        >
          <Zap size={14} />
          Engine Move
        </button>
        <button
          onClick={onNewGame}
          disabled={isBusy}
          className="btn-glow flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
          style={{
            background: 'var(--topbar-btn-primary-bg)',
            border: 'none',
            color: 'var(--topbar-btn-primary-text)',
            boxShadow: '0 2px 12px rgba(232, 168, 76, 0.2)',
          }}
        >
          <RotateCcw size={14} />
          New Game
        </button>
      </div>
    </motion.header>
  );
}
