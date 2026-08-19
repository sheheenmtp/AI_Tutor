import { useState, useRef, useEffect } from 'react';
import { Sun, Moon, Code2, Zap, ChevronDown, User, Activity, Settings, LogOut, LayoutList } from 'lucide-react';

export default function Header({
  user,
  progress,
  theme,
  onThemeToggle,
  onLogout,
  questionBankOpen = false,
  onToggleQuestionBank,
  onOpenProfile
}) {
  const levelRaw = user?.current_level ? user.current_level : 'beginner';
  const levelKey = levelRaw.toLowerCase().replace(/\s+/g, '_');
  const levelLabel = levelKey
    .split('_')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');

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
              <button
                className="question-bank-toggle"
                onClick={onToggleQuestionBank}
              >
                <LayoutList size={14} />
                {questionBankOpen ? "Workspace" : "Questions"}
              </button>

              <div className="hd" />

              <div className={`level-pill ${levelKey}`}>
                <Zap size={10} fill="currentColor" strokeWidth={0} />
                {levelLabel}
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
                    <div className="dd-user-email">
                      {progress?.next_problem?.title
                        ? `Next: ${progress.next_problem.title}`
                        : ''}
                    </div>
                  </div>
                </div>

                <div
                  className="dd-item"
                  onClick={() => {
                    onOpenProfile?.();
                    setDropOpen(false);
                  }}
                >
                  <User size={15} />
                  Profile
                </div>
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
    </header>
  );
}
