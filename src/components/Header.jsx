import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { fmtDollar } from '../utils/formatters.js';

export default function Header({ session, onExit }) {
  const navigate = useNavigate();
  const location = useLocation();

  const sessionPnL = session ? session.currentCapital - session.startingCapital : 0;
  const pnlColor = sessionPnL >= 0 ? '#00E676' : '#FF1744';

  const navItems = [];
  if (session?.mode === 'LIVE') navItems.push({ label: 'LIVE SESSION', path: '/live' });
  if (session?.mode === 'BACKTEST') navItems.push({ label: 'BACKTEST', path: '/backtest' });
  if (session?.trades?.length > 0) navItems.push({ label: 'REPORT', path: '/report' });

  const F = 'Helvetica, Arial, sans-serif';

  return (
    <header style={{
      background: '#0a0a0a',
      borderBottom: '1px solid #2a2a2a',
      padding: '0 1rem',
      height: '48px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      position: 'sticky',
      top: 0,
      zIndex: 50,
      gap: '0.75rem',
    }}>

      {/* Logo */}
      <button
        onClick={() => navigate(session?.mode === 'LIVE' ? '/live' : '/backtest')}
        style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'none', border: 'none', cursor: 'pointer', padding: 0, flexShrink: 0 }}
      >
        <span style={{ color: '#FF6600', fontFamily: F, fontWeight: 700, fontSize: '1.15rem', letterSpacing: '0.1em' }}>TP/SL</span>
        <span style={{ background: '#FF6600', color: '#000', fontFamily: F, fontWeight: 700, fontSize: '0.8rem', padding: '0.1rem 0.4rem' }}>PRO</span>
      </button>

      {/* Nav tabs */}
      {navItems.length > 0 && (
        <nav style={{ display: 'flex', border: '1px solid #2a2a2a', flexShrink: 0 }}>
          {navItems.map(item => (
            <button
              key={item.path}
              onClick={() => navigate(item.path)}
              style={{
                padding: '0.3rem 0.875rem',
                fontFamily: F,
                fontSize: '0.8rem',
                fontWeight: 600,
                textTransform: 'uppercase',
                letterSpacing: '0.08em',
                border: 'none',
                cursor: 'pointer',
                transition: 'all 0.15s',
                background: location.pathname === item.path ? '#FF6600' : 'transparent',
                color: location.pathname === item.path ? '#000' : '#888888',
              }}
            >
              {item.label}
            </button>
          ))}
        </nav>
      )}

      {/* Right: stats + exit + clock */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem', marginLeft: 'auto' }}>

        {/* Session stats */}
        {session?.mode && session?.trades?.length > 0 && (
          <div className="header-stats" style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
            <Stat label="TRADES" value={String(session.trades.length)} />
            <Stat label="CAPITAL" value={fmtDollar(session.currentCapital)} color="#FF6600" />
            <Stat label="P&L" value={(sessionPnL >= 0 ? '+' : '') + fmtDollar(sessionPnL)} color={pnlColor} />
          </div>
        )}

        {/* EXIT SESSION button */}
        <ExitButton onExit={onExit} navigate={navigate} />
      </div>
    </header>
  );
}

function ExitButton({ onExit, navigate }) {
  const [confirm, setConfirm] = useState(false);
  const F = 'Helvetica, Arial, sans-serif';

  if (confirm) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
        <span style={{ color: '#888888', fontFamily: F, fontSize: '0.8rem' }}>Exit session?</span>
        <button
          onClick={() => { onExit(); navigate('/'); }}
          style={{ background: '#FF1744', color: '#fff', border: 'none', fontFamily: F, fontSize: '0.8rem', fontWeight: 700, padding: '0.25rem 0.625rem', cursor: 'pointer', textTransform: 'uppercase' }}
        >YES</button>
        <button
          onClick={() => setConfirm(false)}
          style={{ background: 'transparent', color: '#888888', border: '1px solid #2a2a2a', fontFamily: F, fontSize: '0.8rem', padding: '0.25rem 0.625rem', cursor: 'pointer', textTransform: 'uppercase' }}
        >NO</button>
      </div>
    );
  }

  return (
    <button
      onClick={() => setConfirm(true)}
      style={{
        background: 'transparent',
        color: '#888888',
        border: '1px solid #2a2a2a',
        fontFamily: F,
        fontSize: '0.8rem',
        fontWeight: 600,
        padding: '0.3rem 0.75rem',
        cursor: 'pointer',
        textTransform: 'uppercase',
        letterSpacing: '0.08em',
        transition: 'all 0.15s',
        flexShrink: 0,
      }}
      onMouseEnter={e => { e.currentTarget.style.borderColor = '#FF1744'; e.currentTarget.style.color = '#FF1744'; }}
      onMouseLeave={e => { e.currentTarget.style.borderColor = '#2a2a2a'; e.currentTarget.style.color = '#888888'; }}
    >
      ✕ EXIT
    </button>
  );
}

function Stat({ label, value, color = '#E0E0E0' }) {
  const F = 'Helvetica, Arial, sans-serif';
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
      <span style={{ color: '#444444', fontFamily: F, fontSize: '0.6rem', textTransform: 'uppercase', letterSpacing: '0.12em' }}>{label}</span>
      <span style={{ color, fontFamily: F, fontSize: '0.9rem', fontWeight: 600, fontVariantNumeric: 'tabular-nums' }}>{value}</span>
    </div>
  );
}
