import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import TradeEntryPanel from '../components/TradeEntryPanel.jsx';
import LiveCalculationsPanel from '../components/LiveCalculationsPanel.jsx';
import TradeLogTable from '../components/TradeLogTable.jsx';

const DEFAULT_VALUES = {
  direction: 'LONG',
  entryPrice: '',
  atr: '',
  slMultiple: '1.0',
  tpMultiple: '2.0',
  leverage: '1',
};

export default function LiveSession({ session, logTrade }) {
  const [values, setValues] = useState(DEFAULT_VALUES);
  const [flash, setFlash] = useState(null); // 'WIN' | 'LOSS' | null
  const navigate = useNavigate();

  function handleChange(field, val) {
    setValues(prev => ({ ...prev, [field]: val }));
  }

  function handleLog(outcome) {
    logTrade({ ...values, outcome });
    setFlash(outcome);
    setTimeout(() => setFlash(null), 2000);
  }

  const sessionPnL = (session.currentCapital || 0) - (session.startingCapital || 0);

  return (
    <div style={{ minHeight: '100vh', background: '#0a0a0a', padding: '1rem' }}>

      {/* Session banner */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
        <div>
          <div style={{ color: '#FF6600', fontFamily: "Helvetica, Arial, sans-serif", fontWeight: 700, fontSize: '0.9375rem' }}>
            {session.name || 'LIVE SESSION'}
          </div>
          <div style={{ color: '#444444', fontFamily: "Helvetica, Arial, sans-serif", fontSize: '0.8rem' }}>
            {session.currency} · Capital: ${session.currentCapital?.toLocaleString()} · {session.trades?.length || 0} trades
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          {flash && (
            <div style={{
              fontFamily: "Helvetica, Arial, sans-serif",
              fontSize: '1.0625rem',
              fontWeight: 700,
              padding: '0.25rem 0.75rem',
              border: `1px solid ${flash === 'WIN' ? '#00E676' : '#FF1744'}`,
              color: flash === 'WIN' ? '#00E676' : '#FF1744',
              background: flash === 'WIN' ? 'rgba(0,230,118,0.1)' : 'rgba(255,23,68,0.1)',
              animation: 'fadeIn 0.2s ease',
            }}>
              {flash} LOGGED
            </div>
          )}
          {(session.trades?.length || 0) > 0 && (
            <button
              className="btn-amber"
              style={{ fontSize: '1.0625rem', padding: '0.375rem 0.75rem' }}
              onClick={() => navigate('/report')}
            >
              VIEW REPORT →
            </button>
          )}
        </div>
      </div>

      {/* Two-column entry grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1rem', marginBottom: '1rem' }}>
        <div>
          <TradeEntryPanel values={values} onChange={handleChange} />
        </div>
        <div>
          <LiveCalculationsPanel
            tradeValues={values}
            capital={session.currentCapital}
            onLogWin={() => handleLog('WIN')}
            onLogLoss={() => handleLog('LOSS')}
          />
        </div>
      </div>

      {/* Running trade log */}
      <TradeLogTable trades={session.trades || []} maxRows={5} />

      <style>{`
        @keyframes fadeIn { from { opacity: 0; transform: scale(0.95); } to { opacity: 1; transform: scale(1); } }
      `}</style>
    </div>
  );
}
