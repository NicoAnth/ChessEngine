import { useState, useMemo } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import {
  UserRound, Plus, X, Clock3, BookOpen, Trophy,
  Download, Check, RefreshCw, Swords, Target,
  Crown, Trash2,
} from 'lucide-react';
import type { ProfileDetails, ProfileSummary, ExternalGame } from '../lib/types';
import { useTheme } from '../hooks/useTheme';

/* ─── Types ─── */

type UserProfileModalProps = {
  isOpen: boolean;
  onClose: () => void;
  profiles: ProfileSummary[];
  activeProfileUsername: string | null;
  activeProfileDetails: ProfileDetails | null;
  onCreateProfile: (username: string) => Promise<boolean>;
  onDeleteProfile: (username: string) => Promise<boolean>;
  onSelectProfile: (username: string | null) => Promise<void>;
  onLinkChessCom: (username: string, chesscomUsername: string) => Promise<void>;
  onFetchChessComGames: (username: string) => Promise<ExternalGame[]>;
  onLinkLichess: (username: string, lichessUsername: string) => Promise<void>;
  onFetchLichessGames: (username: string) => Promise<ExternalGame[]>;
  onImportGame: (pgn: string) => void;
};

type ExternalPlatform = 'chesscom' | 'lichess';
type TabId = 'overview' | 'chesscom' | 'lichess';

const TABS: { id: TabId; label: string; icon: React.ReactNode; color?: string }[] = [
  { id: 'overview', label: 'Vue d\'ensemble', icon: <Target size={14} /> },
  { id: 'chesscom', label: 'Chess.com', icon: <ChesscomIcon size={14} />, color: '#7FA650' },
  { id: 'lichess', label: 'Lichess', icon: <LichessIcon size={14} /> },
];


/* ─── Icons ─── */

function ChesscomIcon({ size = 16, className, style }: { size?: number; className?: string; style?: React.CSSProperties }) {
  return (
    <svg
      role="img"
      viewBox="0 0 24 24"
      width={size}
      height={size}
      className={className}
      style={style}
      fill="currentColor"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path d="M12 0a3.85 3.85 0 0 0-3.875 3.846A3.84 3.84 0 0 0 9.73 6.969l-2.79 1.85c0 .622.144 1.114.434 1.649H9.83c-.014.245-.014.549-.014.925 0 .025.003.048.006.071-.064 1.353-.507 3.472-3.62 5.842-.816.625-1.423 1.495-1.806 2.533a.33.33 0 0 0-.045.084 8.124 8.124 0 0 0-.39 2.516c0 .1.216 1.561 8.038 1.561s8.038-1.46 8.038-1.561c0-2.227-.824-4.048-2.24-5.133-4.034-3.08-3.586-5.74-3.644-6.838h2.458c.29-.535.434-1.027.434-1.649l-2.79-1.836a3.86 3.86 0 0 0 1.604-3.123A3.873 3.873 0 0 0 13.445.275c-.004-.002-.01.004-.015.004A3.76 3.76 0 0 0 12 0Z" />
    </svg>
  );
}

function LichessIcon({ size = 16, className, style }: { size?: number; className?: string; style?: React.CSSProperties }) {
  return (
    <svg
      role="img"
      viewBox="0 0 24 24"
      width={size}
      height={size}
      className={className}
      style={style}
      fill="currentColor"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path d="M10.457 6.161a.237.237 0 0 0-.296.165c-.8 2.785 2.819 5.579 5.214 7.428.653.504 1.216.939 1.591 1.292 1.745 1.642 2.564 2.851 2.733 3.178a.24.24 0 0 0 .275.122c.047-.013 4.726-1.3 3.934-4.574a.257.257 0 0 0-.023-.06L18.204 3.407 18.93.295a.24.24 0 0 0-.262-.293c-1.7.201-3.115.435-4.5 1.425-4.844-.323-8.718.9-11.213 3.539C.334 7.737-.246 11.515.085 14.128c.763 5.655 5.191 8.631 9.081 9.532.993.229 1.974.34 2.923.34 3.344 0 6.297-1.381 7.946-3.85a.24.24 0 0 0-.372-.3c-3.411 3.527-9.002 4.134-13.296 1.444-4.485-2.81-6.202-8.41-3.91-12.749C4.741 4.221 8.801 2.362 13.888 3.31c.056.01.115 0 .165-.029l.335-.197c.926-.546 1.961-1.157 2.873-1.279l-.694 1.993a.243.243 0 0 0 .02.202l6.082 10.192c-.193 2.028-1.706 2.506-2.226 2.611-.287-.645-.814-1.364-2.306-2.803-.422-.407-1.21-.941-2.124-1.56-2.364-1.601-5.937-4.02-5.391-5.984a.239.239 0 0 0-.165-.295z" />
    </svg>
  );
}

/* ─── Helpers ─── */


function getInitials(name: string): string {
  return name.slice(0, 2).toUpperCase();
}

function accuracyColor(acc?: number): string {
  if (!acc) return 'var(--text-muted)';
  if (acc >= 90) return 'var(--success)';
  if (acc >= 70) return 'var(--warning)';
  return 'var(--danger)';
}

function resultLabel(r?: string): { text: string; color: string } {
  if (r === 'win') return { text: 'Victoire', color: 'var(--success)' };
  if (r === 'loss') return { text: 'Défaite', color: 'var(--danger)' };
  return { text: 'Nulle', color: 'var(--text-muted)' };
}

/* ─── Micro-animation presets ─── */

const fadeUp = {
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: 12 },
  transition: { duration: 0.22 },
};

const staggerContainer = {
  animate: { transition: { staggerChildren: 0.04 } },
};

const staggerChild = {
  initial: { opacity: 0, y: 8 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.25 } },
};

/* ═══════════════════════════════════════════
   MAIN MODAL
   ═══════════════════════════════════════════ */

export function UserProfileModal({
  isOpen,
  onClose,
  profiles,
  activeProfileUsername,
  activeProfileDetails,
  onCreateProfile,
  onDeleteProfile,
  onSelectProfile,
  onLinkChessCom,
  onFetchChessComGames,
  onLinkLichess,
  onFetchLichessGames,
  onImportGame,
}: UserProfileModalProps) {
  const [newUsername, setNewUsername] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [activeTab, setActiveTab] = useState<TabId>('overview');

  const [platformInput, setPlatformInput] = useState('');
  const [isLinking, setIsLinking] = useState(false);
  const [fetchedGames, setFetchedGames] = useState<ExternalGame[]>([]);
  const [isFetchingGames, setIsFetchingGames] = useState(false);
  const [fetchError, setFetchError] = useState('');

  const sortedProfiles = useMemo(
    () => [...profiles].sort((a, b) => (b.updated_at ?? '').localeCompare(a.updated_at ?? '')),
    [profiles],
  );

  /* handlers */
  const handleCreate = async () => {
    const trimmed = newUsername.trim();
    if (!trimmed || isSubmitting) return;
    setIsSubmitting(true);
    const ok = await onCreateProfile(trimmed);
    setIsSubmitting(false);
    if (ok) setNewUsername('');
  };

  const handleLink = async (platform: ExternalPlatform) => {
    if (!activeProfileUsername || !platformInput.trim()) return;
    setIsLinking(true);
    try {
      if (platform === 'chesscom') {
        await onLinkChessCom(activeProfileUsername, platformInput.trim());
      } else {
        await onLinkLichess(activeProfileUsername, platformInput.trim());
      }
      setPlatformInput('');
    } catch {
      alert(`Erreur lors de la liaison du compte ${platform}`);
    } finally {
      setIsLinking(false);
    }
  };

  const handleFetchGames = async (platform: ExternalPlatform) => {
    if (!activeProfileUsername) return;
    setIsFetchingGames(true);
    setFetchedGames([]);
    setFetchError('');
    try {
      const games =
        platform === 'chesscom'
          ? await onFetchChessComGames(activeProfileUsername)
          : await onFetchLichessGames(activeProfileUsername);
      setFetchedGames(games);
    } catch {
      setFetchError('Erreur lors de la récupération des parties');
    } finally {
      setIsFetchingGames(false);
    }
  };

  const switchTab = (id: TabId) => {
    setActiveTab(id);
    setFetchedGames([]);
    setFetchError('');
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* ── Backdrop ── */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50"
            style={{ background: 'rgba(0, 0, 0, 0.65)', backdropFilter: 'blur(8px)' }}
            onClick={onClose}
          />

          {/* ── Modal ── */}
          <motion.div
            initial={{ opacity: 0, y: 18, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 18, scale: 0.96 }}
            transition={{ duration: 0.28, ease: [0.22, 1, 0.36, 1] }}
            className="fixed inset-0 z-50 flex items-center justify-center p-6 pointer-events-none"
          >
            <div
              className="glass-panel pointer-events-auto relative flex flex-col overflow-hidden"
              style={{ width: '100%', maxWidth: 1060, height: 'calc(100vh - 80px)' }}
              onClick={(e) => e.stopPropagation()}
            >
              {/* ▸ Ambient glow behind header */}
              <div
                className="absolute -top-24 left-1/2 -translate-x-1/2 w-[500px] h-[200px] pointer-events-none"
                style={{
                  background: 'radial-gradient(ellipse, var(--accent-glow) 0%, transparent 70%)',
                  opacity: 0.5,
                }}
              />

              {/* ─── Header ─── */}
              <div
                className="relative px-6 py-4 flex items-center justify-between shrink-0"
                style={{ borderBottom: '1px solid var(--border-subtle)' }}
              >
                <div className="flex items-center gap-3">
                  <div
                    className="w-10 h-10 rounded-xl flex items-center justify-center"
                    style={{
                      background: 'linear-gradient(135deg, var(--accent), #d4863a)',
                      color: 'var(--bg-deep)',
                      boxShadow: '0 4px 16px var(--accent-glow)',
                    }}
                  >
                    <Crown size={20} />
                  </div>
                  <div>
                    <h2 className="text-base font-bold tracking-tight" style={{ color: 'var(--text-primary)' }}>
                      Espace Joueur
                    </h2>
                    <p className="text-[11px] tracking-wide" style={{ color: 'var(--text-muted)' }}>
                      Profils · Statistiques · Intégrations
                    </p>
                  </div>
                </div>

                <button
                  onClick={onClose}
                  className="w-8 h-8 rounded-lg flex items-center justify-center cursor-pointer transition-all hover:rotate-90"
                  style={{
                    background: 'var(--bg-surface)',
                    border: '1px solid var(--border-subtle)',
                    color: 'var(--text-secondary)',
                  }}
                >
                  <X size={16} />
                </button>
              </div>

              {/* ─── Body: sidebar + main ─── */}
              <div className="flex flex-1 overflow-hidden">
                {/* ── Sidebar ── */}
                <aside
                  className="w-64 shrink-0 flex flex-col overflow-y-auto"
                  style={{
                    borderRight: '1px solid var(--border-subtle)',
                    background: 'var(--bg-base)',
                  }}
                >
                  {/* Create profile */}
                  <div className="p-3 flex flex-col gap-2" style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                    <span
                      className="text-[10px] font-semibold uppercase tracking-widest px-1"
                      style={{ color: 'var(--text-muted)' }}
                    >
                      Profils
                    </span>
                    <div className="flex gap-1.5">
                      <input
                        value={newUsername}
                        onChange={(e) => setNewUsername(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
                        placeholder="Nouveau profil…"
                        className="flex-1 px-3 py-2 rounded-lg text-xs outline-none placeholder:text-[var(--text-muted)]"
                        style={{
                          background: 'var(--bg-surface)',
                          border: '1px solid var(--border-subtle)',
                          color: 'var(--text-primary)',
                        }}
                      />
                      <button
                        onClick={handleCreate}
                        disabled={isSubmitting || !newUsername.trim()}
                        className="w-9 h-9 rounded-lg flex items-center justify-center cursor-pointer disabled:opacity-30 transition-opacity"
                        style={{
                          background: 'var(--topbar-btn-primary-bg)',
                          color: 'var(--topbar-btn-primary-text)',
                        }}
                      >
                        <Plus size={14} />
                      </button>
                    </div>
                  </div>

                  {/* Profile list */}
                  <div className="flex-1 p-2 flex flex-col gap-1">
                    {sortedProfiles.map((profile) => {
                      const active = profile.username === activeProfileUsername;
                      return (
                        <motion.div
                          key={profile.username}
                          className="relative group"
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          whileHover={{ x: 2 }} // We move the container
                        >
                          <button
                            onClick={() => onSelectProfile(profile.username)}
                            className="w-full text-left px-3 py-2.5 rounded-xl flex items-center gap-3 transition-all cursor-pointer"
                            style={{
                              background: active
                                ? 'linear-gradient(135deg, var(--accent-soft), rgba(232,168,76,0.06))'
                                : 'transparent',
                              border: `1px solid ${active ? 'rgba(232,168,76,0.2)' : 'transparent'}`,
                            }}
                          >
                            {/* Avatar circle */}
                            <div
                              className="w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold shrink-0"
                              style={{
                                background: active
                                  ? 'linear-gradient(135deg, var(--accent), #d4863a)'
                                  : 'var(--bg-elevated)',
                                color: active ? 'var(--bg-deep)' : 'var(--text-muted)',
                                border: active ? 'none' : '1px solid var(--border-subtle)',
                              }}
                            >
                              {getInitials(profile.username)}
                            </div>
                            <div className="flex-1 min-w-0">
                              <div
                                className="text-sm font-medium truncate"
                                style={{ color: active ? 'var(--accent)' : 'var(--text-secondary)' }}
                              >
                                {profile.username}
                              </div>
                              {/* Platform badges */}
                              <div className="flex items-center gap-1.5 mt-0.5">
                                {profile.chesscom_username && (
                                  <span
                                    className="text-[9px] px-1.5 py-0.5 rounded font-medium flex items-center gap-1"
                                  style={{ background: 'rgba(127,166,80,0.15)', color: '#7FA650' }}
                                >
                                  <ChesscomIcon size={9} />
                                  chess.com
                                </span>
                              )}
                              {profile.lichess_username && (
                                <span
                                  className="text-[9px] px-1.5 py-0.5 rounded font-medium flex items-center gap-1"
                                  style={{ background: 'rgba(49,46,43,0.08)', color: 'var(--text-secondary)' }}
                                >
                                  <LichessIcon size={9} />
                                  lichess
                                </span>
                              )}
                            </div>
                          </div>
                          </button>
                          
                          {/* Delete button (hover only) */}
                          <div className="absolute right-2 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-opacity">
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                if (window.confirm(`Voulez-vous vraiment supprimer le profil "${profile.username}" ?\nCette action est irréversible.`)) {
                                  onDeleteProfile(profile.username);
                                }
                              }}
                              className="w-7 h-7 flex items-center justify-center rounded-lg hover:bg-red-500/10 hover:text-red-500 transition-colors"
                              style={{ color: 'var(--text-muted)' }}
                              title="Supprimer le profil"
                            >
                              <Trash2 size={13} />
                            </button>
                          </div>
                        </motion.div>
                      );
                    })}

                    {sortedProfiles.length === 0 && (
                      <div className="flex-1 flex flex-col items-center justify-center gap-2 py-8">
                        <UserRound size={24} style={{ color: 'var(--text-muted)', opacity: 0.4 }} />
                        <span className="text-xs text-center" style={{ color: 'var(--text-muted)' }}>
                          Pas encore de profil
                        </span>
                      </div>
                    )}
                  </div>
                </aside>

                {/* ── Main content ── */}
                <main className="flex-1 flex flex-col overflow-hidden" style={{ background: 'var(--bg-deep)' }}>
                  {!activeProfileDetails ? (
                    <EmptyState />
                  ) : (
                    <>
                      {/* Tab bar */}
                      <nav
                        className="flex items-center gap-1 px-5 pt-3 pb-0 shrink-0"
                        style={{ borderBottom: '1px solid var(--border-subtle)' }}
                      >
                        {TABS.map((tab) => {
                          const active = activeTab === tab.id;
                          return (
                            <button
                              key={tab.id}
                              onClick={() => switchTab(tab.id)}
                              className="relative flex items-center gap-2 px-4 py-2.5 text-xs font-medium cursor-pointer transition-colors"
                              style={{ color: active ? (tab.color ?? 'var(--accent)') : 'var(--text-muted)' }}
                            >
                              {tab.icon}
                              {tab.label}
                              {active && (
                                <motion.div
                                  layoutId="profile-tab-indicator"
                                  className="absolute bottom-0 left-2 right-2 h-0.5 rounded-full"
                                  style={{ background: tab.color ?? 'var(--accent)' }}
                                  transition={{ type: 'spring', bounce: 0.18, duration: 0.45 }}
                                />
                              )}
                            </button>
                          );
                        })}
                      </nav>

                      {/* Tab content */}
                      <div className="flex-1 overflow-y-auto p-6">
                        <AnimatePresence mode="wait">
                          {activeTab === 'overview' && (
                            <motion.div key="overview" {...fadeUp}>
                              <OverviewTab details={activeProfileDetails} />
                            </motion.div>
                          )}
                          {activeTab === 'chesscom' && (
                            <motion.div key="chesscom" {...fadeUp}>
                              <IntegrationTab
                                platform="chesscom"
                                linkedUsername={activeProfileDetails.profile.chesscom_username}
                                platformInput={platformInput}
                                setPlatformInput={setPlatformInput}
                                isLinking={isLinking}
                                onLink={() => handleLink('chesscom')}
                                isFetching={isFetchingGames}
                                onFetch={() => handleFetchGames('chesscom')}
                                games={fetchedGames}
                                fetchError={fetchError}
                                onImport={(pgn) => { onImportGame(pgn); onClose(); }}
                              />
                            </motion.div>
                          )}
                          {activeTab === 'lichess' && (
                            <motion.div key="lichess" {...fadeUp}>
                              <IntegrationTab
                                platform="lichess"
                                linkedUsername={activeProfileDetails.profile.lichess_username}
                                platformInput={platformInput}
                                setPlatformInput={setPlatformInput}
                                isLinking={isLinking}
                                onLink={() => handleLink('lichess')}
                                isFetching={isFetchingGames}
                                onFetch={() => handleFetchGames('lichess')}
                                games={fetchedGames}
                                fetchError={fetchError}
                                onImport={(pgn) => { onImportGame(pgn); onClose(); }}
                              />
                            </motion.div>
                          )}
                        </AnimatePresence>
                      </div>
                    </>
                  )}
                </main>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

/* ═══════════════════════════════════════════
   EMPTY STATE
   ═══════════════════════════════════════════ */

function EmptyState() {
  const { isDark } = useTheme();
  return (
    <div className="flex-1 flex flex-col items-center justify-center gap-4 p-8">
      <div className="relative">
        <div
          className="absolute inset-0 rounded-full"
          style={{
            background: 'radial-gradient(circle, var(--accent-soft) 0%, transparent 70%)',
            transform: 'scale(3)',
            opacity: 0.5,
          }}
        />
        <img
          src={isDark ? '/Caissa.png' : '/CaissaNoire.png'}
          alt="Caissa"
          className="relative w-16 h-16 object-contain"
          style={{ opacity: 0.5, filter: 'drop-shadow(0 0 12px rgba(232, 168, 76, 0.15))' }}
        />
      </div>
      <p className="text-sm font-medium" style={{ color: 'var(--text-secondary)' }}>
        Sélectionnez ou créez un profil
      </p>
      <p className="text-xs max-w-xs text-center" style={{ color: 'var(--text-muted)' }}>
        Votre espace joueur vous permet de suivre vos progrès, analyser votre répertoire et importer vos parties.
      </p>
    </div>
  );
}

/* ═══════════════════════════════════════════
   OVERVIEW TAB
   ═══════════════════════════════════════════ */

function OverviewTab({ details }: { details: ProfileDetails }) {
  const { stats, history } = details;

  return (
    <motion.div className="flex flex-col gap-5" {...staggerContainer} initial="initial" animate="animate">
      {/* ── Hero stats ── */}
      <motion.div className="grid grid-cols-3 gap-3" variants={staggerChild}>
        <HeroStat
          label="Accuracy globale"
          value={`${Math.round(stats.overall_accuracy)}%`}
          icon={<Target size={16} />}
          accentGradient
        />
        <HeroStat
          label="Accuracy blanc"
          value={`${Math.round(stats.accuracy_white)}%`}
          icon={<span className="w-3 h-3 rounded-sm bg-white inline-block" />}
        />
        <HeroStat
          label="Accuracy noir"
          value={`${Math.round(stats.accuracy_black)}%`}
          icon={<span className="w-3 h-3 rounded-sm bg-zinc-800 border border-zinc-600 inline-block" />}
        />
      </motion.div>

      {/* ── Accuracy by time control + Top openings ── */}
      <motion.div className="grid grid-cols-2 gap-3" variants={staggerChild}>
        {/* Time controls */}
        <div
          className="rounded-xl p-4 flex flex-col"
          style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)' }}
        >
          <SectionHeader icon={<Clock3 size={13} />} label="Accuracy par cadence" />
          <div className="mt-3 flex flex-col gap-2">
            {stats.by_time_control.length === 0 && <NoData />}
            {stats.by_time_control.map((row) => (
              <div key={row.time_control} className="flex items-center gap-2 text-xs">
                <span className="flex-1 truncate" style={{ color: 'var(--text-secondary)' }}>
                  {row.time_control}
                </span>
                <span
                  className="font-mono font-semibold"
                  style={{ color: accuracyColor(row.accuracy) }}
                >
                  {Math.round(row.accuracy)}%
                </span>
                <span
                  className="text-[10px] px-1.5 py-0.5 rounded"
                  style={{ background: 'var(--bg-elevated)', color: 'var(--text-muted)' }}
                >
                  {row.games} {row.games > 1 ? 'parties' : 'partie'}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Top openings */}
        <div
          className="rounded-xl p-4 flex flex-col"
          style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)' }}
        >
          <SectionHeader icon={<BookOpen size={13} />} label="Top ouvertures" />
          <div className="mt-3 flex flex-col gap-2">
            {stats.top_openings.length === 0 && <NoData />}
            {stats.top_openings.map((op, i) => (
              <div key={op.name} className="flex items-center gap-2 text-xs">
                <span
                  className="w-5 h-5 rounded flex items-center justify-center text-[10px] font-bold shrink-0"
                  style={{
                    background: i === 0 ? 'var(--accent-soft)' : 'var(--bg-elevated)',
                    color: i === 0 ? 'var(--accent)' : 'var(--text-muted)',
                  }}
                >
                  {i + 1}
                </span>
                <span className="flex-1 truncate" style={{ color: 'var(--text-secondary)' }}>
                  {op.name}
                </span>
                <span className="font-mono" style={{ color: 'var(--text-primary)' }}>
                  {op.games}
                </span>
              </div>
            ))}
          </div>
        </div>
      </motion.div>

      {/* ── Game history ── */}
      <motion.div
        className="rounded-xl p-4"
        style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)' }}
        variants={staggerChild}
      >
        <SectionHeader icon={<Trophy size={13} />} label="Historique des imports" />
        <div className="mt-3 flex flex-col gap-1.5 max-h-72 overflow-y-auto pr-1">
          {history.length === 0 && <NoData />}
          {history.map((game, i) => (
            <div
              key={i}
              className="flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors"
              style={{ background: 'var(--bg-elevated)' }}
            >
              {/* Result indicator */}
              <div
                className="w-1 h-9 rounded-full shrink-0"
                style={{
                  background:
                    game.user_accuracy && game.user_accuracy >= 80
                      ? 'var(--success)'
                      : game.user_accuracy && game.user_accuracy >= 60
                        ? 'var(--warning)'
                        : 'var(--danger)',
                }}
              />
              <div className="flex-1 min-w-0">
                <div className="text-xs font-medium truncate" style={{ color: 'var(--text-primary)' }}>
                  {game.white} vs {game.black}
                </div>
                <div className="text-[11px] mt-0.5 flex items-center gap-1.5" style={{ color: 'var(--text-muted)' }}>
                  <span>{game.date}</span>
                  <span style={{ opacity: 0.4 }}>·</span>
                  <span>{game.time_control}</span>
                </div>
              </div>
              <div className="text-right shrink-0">
                <span
                  className="text-sm font-mono font-bold"
                  style={{ color: accuracyColor(game.user_accuracy) }}
                >
                  {game.user_accuracy ? `${Math.round(game.user_accuracy)}%` : '–'}
                </span>
              </div>
            </div>
          ))}
        </div>
      </motion.div>
    </motion.div>
  );
}

/* ═══════════════════════════════════════════
   INTEGRATION TAB  (Chess.com / Lichess)
   ═══════════════════════════════════════════ */

function IntegrationTab({
  platform,
  linkedUsername,
  platformInput,
  setPlatformInput,
  isLinking,
  onLink,
  isFetching,
  onFetch,
  games,
  fetchError,
  onImport,
}: {
  platform: ExternalPlatform;
  linkedUsername?: string;
  platformInput: string;
  setPlatformInput: (v: string) => void;
  isLinking: boolean;
  onLink: () => void;
  isFetching: boolean;
  onFetch: () => void;
  games: ExternalGame[];
  fetchError: string;
  onImport: (pgn: string) => void;
}) {
  const isChessCom = platform === 'chesscom';
  const accent = isChessCom ? '#7FA650' : '#312e2b';
  const accentSoft = isChessCom
    ? 'rgba(127,166,80,0.12)'
    : 'rgba(49,46,43,0.08)';
  const accentBorder = isChessCom
    ? 'rgba(127,166,80,0.25)'
    : 'rgba(49,46,43,0.15)';
  const platformName = isChessCom ? 'Chess.com' : 'Lichess';

  /* ── Not linked: onboarding state ── */
  if (!linkedUsername) {
    return (
      <div className="flex flex-col items-center justify-center h-80 gap-5 text-center">
        {/* Platform icon */}
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.1, type: 'spring', bounce: 0.3 }}
          className="w-20 h-20 rounded-2xl flex items-center justify-center"
          style={{
            background: `linear-gradient(135deg, ${accentSoft}, transparent)`,
            border: `1px solid ${accentSoft}`,
          }}
        >
          {isChessCom ? <ChesscomIcon size={32} style={{ color: accent }} /> : <LichessIcon size={32} style={{ color: accent }} />}
        </motion.div>

        <div>
          <h3 className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>
            Connecter {platformName}
          </h3>
          <p className="text-xs mt-1 max-w-sm" style={{ color: 'var(--text-muted)' }}>
            Liez votre compte pour importer automatiquement vos parties récentes et enrichir vos statistiques.
          </p>
        </div>

        <div className="flex gap-2 w-full max-w-xs">
          <input
            className="flex-1 px-3 py-2.5 rounded-lg text-sm outline-none placeholder:text-[var(--text-muted)]"
            style={{
              background: 'var(--bg-surface)',
              border: '1px solid var(--border-default)',
              color: 'var(--text-primary)',
            }}
            placeholder={`Pseudo ${platformName}`}
            value={platformInput}
            onChange={(e) => setPlatformInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && onLink()}
          />
          <button
            onClick={onLink}
            disabled={isLinking || !platformInput.trim()}
            className="px-5 py-2.5 rounded-lg text-sm font-semibold cursor-pointer disabled:opacity-40 transition-opacity flex items-center gap-2"
            style={{
              background: accent,
              color: '#fff',
            }}
          >
            {isLinking ? <RefreshCw size={14} className="animate-spin" /> : (isChessCom ? <ChesscomIcon size={14} /> : <LichessIcon size={14} />)}
            {isLinking ? '…' : 'Lier'}
          </button>
        </div>
      </div>
    );
  }

  /* ── Linked: account + games list ── */
  return (
    <div className="flex flex-col gap-4 h-full">
      {/* Linked account card */}
      <div
        className="flex items-center justify-between p-4 rounded-xl"
        style={{
          background: accentSoft,
          border: `1px solid ${accentBorder}`,
        }}
      >
        <div className="flex items-center gap-3">
          <div
            className="w-10 h-10 rounded-xl flex items-center justify-center"
            style={{ background: accent, color: '#fff' }}
          >
            {isChessCom ? <ChesscomIcon size={18} /> : <LichessIcon size={18} />}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>
                {linkedUsername}
              </span>
              <Check size={14} style={{ color: 'var(--success)' }} />
            </div>
            <span className="text-[11px]" style={{ color: 'var(--text-muted)' }}>
              {platformName} · Compte lié
            </span>
          </div>
        </div>

        <button
          onClick={onFetch}
          disabled={isFetching}
          className="btn-glow flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-medium cursor-pointer disabled:opacity-50 transition-all"
          style={{
            background: 'var(--bg-surface)',
            border: '1px solid var(--border-default)',
            color: 'var(--text-secondary)',
          }}
        >
          <RefreshCw size={13} className={isFetching ? 'animate-spin' : ''} />
          Récupérer les parties
        </button>
      </div>

      {/* Error */}
      {fetchError && (
        <div
          className="flex items-center gap-2 p-3 rounded-lg text-xs"
          style={{
            background: 'rgba(248,113,113,0.08)',
            border: '1px solid rgba(248,113,113,0.18)',
            color: 'var(--danger)',
          }}
        >
          <X size={14} />
          {fetchError}
        </div>
      )}

      {/* Loading skeleton */}
      {isFetching && (
        <div className="flex flex-col gap-2">
          {[...Array(3)].map((_, i) => (
            <div
              key={i}
              className="h-16 rounded-xl animate-pulse"
              style={{ background: 'var(--bg-surface)' }}
            />
          ))}
        </div>
      )}

      {/* Games list */}
      {games.length > 0 && (
        <div className="flex-1 overflow-y-auto pr-1">
          <div className="flex items-center justify-between mb-3">
            <span className="text-[11px] font-semibold uppercase tracking-widest" style={{ color: 'var(--text-muted)' }}>
              Parties récentes
            </span>
            <span
              className="text-[10px] px-2 py-0.5 rounded-full font-mono"
              style={{ background: 'var(--bg-elevated)', color: 'var(--text-secondary)' }}
            >
              {games.length}
            </span>
          </div>

          <motion.div
            className="flex flex-col gap-2"
            initial="initial"
            animate="animate"
            variants={staggerContainer}
          >
            {games.map((game) => {
              const res = resultLabel(game.user_result);
              return (
                <motion.div
                  key={game.uuid}
                  variants={staggerChild}
                  className="group flex items-center gap-3 p-3 rounded-xl transition-all cursor-default"
                  style={{
                    background: 'var(--bg-surface)',
                    border: '1px solid var(--border-subtle)',
                  }}
                  whileHover={{
                    borderColor: 'var(--border-default)',
                    background: 'var(--bg-elevated)',
                  }}
                >
                  {/* Result bar */}
                  <div
                    className="w-1 h-11 rounded-full shrink-0"
                    style={{ background: res.color }}
                  />

                  {/* Game info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <Swords size={12} style={{ color: 'var(--text-muted)' }} />
                      <span className="text-sm font-medium truncate" style={{ color: 'var(--text-primary)' }}>
                        vs {game.opponent_username}
                      </span>
                      {game.opponent_rating && (
                        <span
                          className="text-[10px] px-1.5 py-0.5 rounded font-mono"
                          style={{ background: 'var(--bg-elevated)', color: 'var(--text-muted)' }}
                        >
                          {game.opponent_rating}
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-2 mt-1 text-[11px]" style={{ color: 'var(--text-muted)' }}>
                      <span>{game.time_control}</span>
                      <span style={{ opacity: 0.35 }}>·</span>
                      <span>{new Date(game.end_time * 1000).toLocaleDateString()}</span>
                    </div>
                  </div>

                  {/* Result badge */}
                  <span
                    className="text-[10px] px-2 py-1 rounded-md font-semibold shrink-0"
                    style={{
                      background: `${res.color}15`,
                      color: res.color,
                    }}
                  >
                    {res.text}
                  </span>

                  {/* Import button */}
                  <button
                    onClick={() => game.pgn && onImport(game.pgn)}
                    disabled={!game.pgn}
                    className="btn-glow flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] font-medium cursor-pointer disabled:opacity-30 transition-all shrink-0"
                    style={{
                      background: 'var(--accent-soft)',
                      color: 'var(--accent)',
                      border: '1px solid transparent',
                    }}
                  >
                    <Download size={12} />
                    Importer
                  </button>
                </motion.div>
              );
            })}
          </motion.div>
        </div>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════
   SHARED UI ATOMS
   ═══════════════════════════════════════════ */

function HeroStat({
  label,
  value,
  icon,
  accentGradient,
}: {
  label: string;
  value: string;
  icon: React.ReactNode;
  accentGradient?: boolean;
}) {
  return (
    <div
      className="relative overflow-hidden rounded-xl p-4 flex flex-col gap-2"
      style={{
        background: accentGradient
          ? 'linear-gradient(135deg, rgba(232,168,76,0.10) 0%, var(--bg-surface) 100%)'
          : 'var(--bg-surface)',
        border: `1px solid ${accentGradient ? 'rgba(232,168,76,0.15)' : 'var(--border-subtle)'}`,
      }}
    >
      {accentGradient && (
        <div
          className="absolute -top-6 -right-6 w-20 h-20 rounded-full pointer-events-none"
          style={{ background: 'radial-gradient(circle, var(--accent-glow) 0%, transparent 70%)' }}
        />
      )}
      <div className="flex items-center gap-2">
        <span style={{ color: accentGradient ? 'var(--accent)' : 'var(--text-muted)' }}>{icon}</span>
        <span
          className="text-[10px] font-semibold uppercase tracking-widest"
          style={{ color: 'var(--text-muted)' }}
        >
          {label}
        </span>
      </div>
      <span
        className="text-2xl font-bold font-mono"
        style={{ color: accentGradient ? 'var(--accent)' : 'var(--text-primary)' }}
      >
        {value}
      </span>
    </div>
  );
}

function SectionHeader({ icon, label }: { icon: React.ReactNode; label: string }) {
  return (
    <div className="flex items-center gap-2">
      <span style={{ color: 'var(--text-muted)' }}>{icon}</span>
      <span
        className="text-[10px] font-semibold uppercase tracking-widest"
        style={{ color: 'var(--text-muted)' }}
      >
        {label}
      </span>
    </div>
  );
}

function NoData() {
  return (
    <span className="text-[11px] italic" style={{ color: 'var(--text-muted)', opacity: 0.6 }}>
      Pas de données disponibles.
    </span>
  );
}
