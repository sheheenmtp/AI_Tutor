import { useState, useRef, useEffect } from 'react';
import { Sun, Moon, Code2, Zap, ChevronDown, ChevronRight, User, Activity, Settings, LogOut } from 'lucide-react';

const LEVEL_CONFIG = {
  beginner:     { color: '#34d399', gradient: 'linear-gradient(90deg,#10b981,#34d399)' },
  intermediate: { color: '#fbbf24', gradient: 'linear-gradient(90deg,#f59e0b,#fbbf24)' },
  advanced:     { color: '#fb7185', gradient: 'linear-gradient(90deg,#e11d48,#fb7185)' },
};

export default function Header({ user, theme, onThemeToggle, onLogout }) {
  const level  = user?.current_level ?? 'beginner';
  const lvlCfg = LEVEL_CONFIG[level] ?? LEVEL_CONFIG.beginner;

  const [dropOpen, setDropOpen] = useState(false);
  const dropRef = useRef(null);

  // Close on outside click / Escape
  useEffect(() => {
    const handleClick = (e) => {
      if (dropRef.current && !dropRef.current.contains(e.target)) setDropOpen(false);
    };
    const handleKey = (e) => { if (e.key === 'Escape') setDropOpen(false); };
    document.addEventListener('mousedown', handleClick);
    document.addEventListener('keydown', handleKey);
    return () => {
      document.removeEventListener('mousedown', handleClick);
      document.removeEventListener('keydown', handleKey);
    };
  }, []);

  const initials = user?.username
    ? user.username.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase()
    : 'U';

  return (
    <header className="header">

      {/* ── Floating nav bar ─────────────────────────── */}
      <div className="header-container">

        {/* Logo */}
        <div className="logo">
          <div className="logo-icon">
            <Code2 size={15} color="#fff" strokeWidth={2.5} />
          </div>
          <span className="logo-text">Py<span>Tutor</span></span>
        </div>

        {/* Right cluster */}
        <div className="header-right">
          {user && (
            <>
              <div className={`level-pill ${level}`}>
                <Zap size={10} fill="currentColor" strokeWidth={0} />
                {level.charAt(0).toUpperCase() + level.slice(1)}
              </div>

              <div className="hd" />

              <div className="stat-card">
                <div className="stat-content">
                  <span className="stat-label">Solved</span>
                  <span className="stat-value" style={{ color: '#34d399' }}>{user.problems_solved}</span>
                </div>
              </div>

              <div className="stat-card">
                <div className="stat-content">
                  <span className="stat-label">Score</span>
                  <span className="stat-value" style={{ color: '#818cf8' }}>{user.total_score}</span>
                </div>
              </div>

              <div className="hd" />
            </>
          )}

          {/* Theme toggle */}
          <button className="theme-toggle" onClick={onThemeToggle} aria-label="Toggle theme">
            {theme === 'dark' ? <Sun size={15} /> : <Moon size={15} />}
          </button>

          {/* User dropdown */}
          {user && (
            <div className={`user-btn ${dropOpen ? 'open' : ''}`}
              ref={dropRef}
              onClick={() => setDropOpen(p => !p)}
              role="button"
              aria-haspopup="true"
              aria-expanded={dropOpen}
            >
              <div className="avatar">{initials}</div>
              <span className="user-name">{user.username?.split(' ')[0] ?? 'User'}</span>
              <ChevronDown size={13} className="chevron-icon" />

              {/* Dropdown panel */}
              <div className={`dropdown ${dropOpen ? 'open' : ''}`} onClick={e => e.stopPropagation()}>

                <div className="dd-user-info">
                  <div className="dd-avatar">{initials}</div>
                  <div>
                    <div className="dd-user-name">{user.username ?? 'User'}</div>
                    <div className="dd-user-email">{user.email ?? ''}</div>
                  </div>
                </div>

                <div className="dd-item"><User size={15} />Profile</div>
                <div className="dd-item"><Activity size={15} />My Progress</div>
                <div className="dd-item"><Settings size={15} />Settings</div>

                <div className="dd-separator" />

                <div className="dd-item danger" onClick={onLogout}>
                  <LogOut size={15} />Sign out
                </div>

              </div>
            </div>
          )}
        </div>
      </div>

      {/* ── Progress strip ──────────────────────────── */}
      {user && <ProgressStrip user={user} lvlCfg={lvlCfg} />}

    </header>
  );
}

function ProgressStrip({ user, lvlCfg }) {
  const levels = ['beginner', 'intermediate', 'advanced'];
  const labels = ['Beginner', 'Intermediate', 'Advanced'];
  const idx    = levels.indexOf(user.current_level);

  const thresholds = [0, 5, 15, 30];
  const start = thresholds[idx]     ?? 0;
  const end   = thresholds[idx + 1] ?? start + 15;
  const pct   = Math.min(100, Math.max(0,
    Math.round(((user.problems_solved - start) / (end - start)) * 100)
  ));

  return (
    <div className="progress-section">
      <div className="progress-breadcrumb">
        {labels.map((label, i) => (
          <span key={label} style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <span
              className={`progress-step${i < idx ? ' done' : ''}${i === idx ? ' current' : ''}`}
              style={i === idx ? { color: lvlCfg.color } : undefined}
            >
              {label}
            </span>
            {i < 2 && (
              <span className="progress-chevron">
                <ChevronRight size={10} />
              </span>
            )}
          </span>
        ))}
      </div>

      <div className="progress-track">
        <div className="progress-fill" style={{ width: `${pct}%`, background: lvlCfg.gradient }} />
      </div>

      <span className="progress-pct" style={{ color: lvlCfg.color }}>{pct}%</span>
    </div>
  );
} 