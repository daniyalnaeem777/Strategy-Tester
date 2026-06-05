import { useState } from 'react';

export default function SessionInit({ onInit }) {
  const [name, setName] = useState('');
  const [capital, setCapital] = useState('10000');
  const [currency, setCurrency] = useState('USD');
  const [error, setError] = useState('');

  const currencySymbol = { USD: '$', CAD: 'C$', GBP: '£', EUR: '€' }[currency] || '$';

  function handleMode(mode) {
    if (!capital || parseFloat(capital) <= 0) {
      setError('Please enter a valid starting capital.');
      return;
    }
    setError('');
    onInit({ name, startingCapital: capital, currency, mode });
  }

  return (
    <div style={{ minHeight: '100vh', background: '#0a0a0a', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem' }}>
      <div style={{ width: '100%', maxWidth: '480px' }}>

        {/* Logo block */}
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
            <div style={{ width: '2rem', height: '1px', background: '#FF6600' }}></div>
            <span style={{ color: '#FF6600', fontFamily: "Helvetica, Arial, sans-serif", fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.3em' }}>Fynalyse</span>
            <div style={{ width: '2rem', height: '1px', background: '#FF6600' }}></div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
            <span style={{ color: '#E0E0E0', fontFamily: "Helvetica, Arial, sans-serif", fontWeight: 700, fontSize: '2rem', letterSpacing: '0.15em' }}>TP/SL</span>
            <span style={{ background: '#FF6600', color: '#000000', fontFamily: "Helvetica, Arial, sans-serif", fontWeight: 700, fontSize: '1.0625rem', padding: '0.125rem 0.5rem', letterSpacing: '0.1em' }}>PRO</span>
          </div>
          <p style={{ color: '#888888', fontFamily: "Helvetica, Arial, sans-serif", fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.2em' }}>
            Bloomberg-Grade Strategy Tester
          </p>
        </div>

        {/* Panel */}
        <div className="terminal-panel">
          <div className="panel-header">
            <span style={{ display: 'inline-block', width: 8, height: 8, background: '#FF6600' }}></span>
            SESSION INITIALISATION
          </div>

          <div style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>

            {/* Capital */}
            <div>
              <label className="terminal-label" style={{ display: 'block', marginBottom: '0.375rem' }}>
                Starting Capital
              </label>
              <div style={{ display: 'flex' }}>
                <div style={{ background: '#1a1a1a', border: '1px solid #2a2a2a', borderRight: 'none', padding: '0 0.75rem', display: 'flex', alignItems: 'center', color: '#888888', fontFamily: "Helvetica, Arial, sans-serif", fontSize: '1.0625rem', flexShrink: 0 }}>
                  {currencySymbol}
                </div>
                <input
                  type="number"
                  value={capital}
                  onChange={e => { setCapital(e.target.value); setError(''); }}
                  className="terminal-input"
                  placeholder="10000"
                  min="1"
                  style={{ flex: 1 }}
                />
              </div>
              {error && <div style={{ color: '#FF1744', fontFamily: "Helvetica, Arial, sans-serif", fontSize: '0.8rem', marginTop: '0.25rem' }}>{error}</div>}
            </div>

            {/* Currency */}
            <div>
              <label className="terminal-label" style={{ display: 'block', marginBottom: '0.375rem' }}>Account Currency</label>
              <div style={{ position: 'relative' }}>
                <select value={currency} onChange={e => setCurrency(e.target.value)} className="terminal-select">
                  <option value="USD">USD — US Dollar</option>
                  <option value="CAD">CAD — Canadian Dollar</option>
                  <option value="GBP">GBP — British Pound</option>
                  <option value="EUR">EUR — Euro</option>
                </select>
                <div style={{ position: 'absolute', right: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: '#FF6600', fontSize: '0.8rem', pointerEvents: 'none' }}>▼</div>
              </div>
            </div>

            {/* Session name */}
            <div>
              <label className="terminal-label" style={{ display: 'block', marginBottom: '0.375rem' }}>
                Session Name <span style={{ color: '#444444' }}>(optional)</span>
              </label>
              <input
                type="text"
                value={name}
                onChange={e => setName(e.target.value)}
                className="terminal-input"
                placeholder="e.g. Gold 4H Strategy June 2026"
              />
            </div>

            {/* Mode selection */}
            <div style={{ borderTop: '1px solid #2a2a2a', paddingTop: '1.25rem' }}>
              <label className="terminal-label" style={{ display: 'block', marginBottom: '0.75rem' }}>Select Mode</label>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                <ModeButton
                  label="LIVE SESSION"
                  sublabel="Trade-by-trade entry"
                  icon="⬡"
                  primary
                  onClick={() => handleMode('LIVE')}
                />
                <ModeButton
                  label="BULK BACKTEST"
                  sublabel="Import historical trades"
                  icon="◈"
                  primary={false}
                  onClick={() => handleMode('BACKTEST')}
                />
              </div>
            </div>

          </div>
        </div>

        <p style={{ textAlign: 'center', color: '#2a2a2a', fontFamily: "Helvetica, Arial, sans-serif", fontSize: '0.8rem', marginTop: '1rem' }}>
          Session data stored locally in browser · No server required
        </p>
      </div>
    </div>
  );
}

function ModeButton({ label, sublabel, icon, primary, onClick }) {
  const [hovered, setHovered] = useState(false);
  const active = hovered || primary;

  return (
    <button
      onClick={onClick}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        border: `2px solid ${primary ? '#FF6600' : hovered ? '#FF6600' : '#2a2a2a'}`,
        background: primary && hovered ? '#FF6600' : hovered && !primary ? 'rgba(255,102,0,0.05)' : 'transparent',
        color: primary ? (hovered ? '#000000' : '#FF6600') : (hovered ? '#FF6600' : '#888888'),
        padding: '1rem',
        textAlign: 'left',
        cursor: 'pointer',
        transition: 'all 0.15s',
      }}
    >
      <div style={{ fontFamily: "Helvetica, Arial, sans-serif", fontSize: '1.25rem', marginBottom: '0.25rem' }}>{icon}</div>
      <div style={{ fontFamily: "Helvetica, Arial, sans-serif", fontWeight: 700, fontSize: '1.0625rem', textTransform: 'uppercase', letterSpacing: '0.1em' }}>{label}</div>
      <div style={{ fontFamily: "Helvetica, Arial, sans-serif", fontSize: '0.675rem', marginTop: '0.125rem', opacity: 0.7 }}>{sublabel}</div>
    </button>
  );
}
