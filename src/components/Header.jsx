import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { fmtDollar } from '../utils/formatters.js';

export default function Header({ session }) {
  const [time, setTime] = useState(new Date());
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  const sessionPnL = session ? session.currentCapital - session.startingCapital : 0;
  const pnlColor = sessionPnL >= 0 ? '#00E676' : '#FF1744';

  const navItems = [];
  if (session?.mode === 'LIVE') navItems.push({ label: 'LIVE SESSION', path: '/live' });
  if (session?.mode === 'BACKTEST') navItems.push({ label: 'BACKTEST', path: '/backtest' });
  if (session?.trades?.length > 0) navItems.push({ label: 'REPORT', path: '/report' });

  return (
    <header style={{
      background: '#0a0a0a',
      borderBottom: '1px solid #2a2a2a',
      padding: '0 1rem',
      height: '44px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      position: 'sticky',
      top: 0,
      zIndex: 50,
    }}>
      {/* Logo */}
      <button
        onClick={() => navigate('/')}
        style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
      >
        <span style={{ color: '#FF6600', fontFamily: "'Roboto Mono', monospace", fontWeight: 700, fontSize: '1.1rem', letterSpacing: '0.15em' }}>TP/SL</span>
        <span style={{ background: '#FF6600', color: '#000000', fontFamily: "'Roboto Mono', monospace", fontWeight: 700, fontSize: '0.7rem', padding: '0.125rem 0.4rem', letterSpacing: '0.05em' }}>PRO</span>
        <span style={{ color: '#2a2a2a', fontFamily: "'Roboto Mono', monospace", marginLeft: '0.25rem', display: 'none' }}>|</span>
      </button>

      {/* Nav */}
      {navItems.length > 0 && (
        <nav style={{ display: 'flex', border: '1px solid #2a2a2a' }}>
          {navItems.map(item => (
            <button
              key={item.path}
              onClick={() => navigate(item.path)}
              style={{
                padding: '0.25rem 0.75rem',
                fontFamily: "'Roboto Mono', monospace",
                fontSize: '0.7rem',
                textTransform: 'uppercase',
                letterSpacing: '0.1em',
                border: 'none',
                cursor: 'pointer',
                transition: 'all 0.15s',
                background: location.pathname === item.path ? '#FF6600' : 'transparent',
                color: location.pathname === item.path ? '#000000' : '#888888',
              }}
            >
              {item.label}
            </button>
          ))}
        </nav>
      )}

      {/* Right side stats + clock */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
        {session?.mode && session?.trades?.length > 0 && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
            <Stat label="TRADES" value={String(session.trades.length)} />
            <Stat label="CAPITAL" value={fmtDollar(session.currentCapital)} color="#FF6600" />
            <Stat label="P&L" value={(sessionPnL >= 0 ? '+' : '') + fmtDollar(sessionPnL)} color={pnlColor} />
          </div>
        )}
        <div style={{ color: '#FF6600', fontFamily: "'Roboto Mono', monospace", fontSize: '0.75rem', fontVariantNumeric: 'tabular-nums', minWidth: '70px', textAlign: 'right' }}>
          {time.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })}
        </div>
      </div>
    </header>
  );
}

function Stat({ label, value, color = '#E0E0E0' }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
      <span style={{ color: '#444444', fontFamily: "'Roboto Mono', monospace", fontSize: '0.55rem', textTransform: 'uppercase', letterSpacing: '0.15em' }}>{label}</span>
      <span style={{ color, fontFamily: "'Roboto Mono', monospace", fontSize: '0.75rem', fontWeight: 500, fontVariantNumeric: 'tabular-nums' }}>{value}</span>
    </div>
  );
}
