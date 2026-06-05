import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import BacktestBulkEntry from '../components/BacktestBulkEntry.jsx';

function formatElapsed(seconds) {
  const h = Math.floor(seconds / 3600).toString().padStart(2, '0');
  const m = Math.floor((seconds % 3600) / 60).toString().padStart(2, '0');
  const s = (seconds % 60).toString().padStart(2, '0');
  return `${h}:${m}:${s}`;
}

export default function BacktestSession({ session, setTrades }) {
  const navigate = useNavigate();
  const [elapsed, setElapsed] = useState(0);
  const F = 'Helvetica, Arial, sans-serif';

  useEffect(() => {
    setElapsed(0);
    const t = setInterval(() => setElapsed(s => s + 1), 1000);
    return () => clearInterval(t);
  }, []);

  function handleRunBacktest(trades) {
    setTrades(trades);
    navigate('/report');
  }

  return (
    <div style={{ minHeight: '100vh', background: '#0a0a0a', padding: '1rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
        <div>
          <div style={{ color: '#FF6600', fontFamily: F, fontWeight: 700, fontSize: '0.9375rem' }}>
            {session.name || 'BACKTEST MODE'}
          </div>
          <div style={{ color: '#444444', fontFamily: F, fontSize: '0.8rem' }}>
            Starting Capital: ${session.startingCapital?.toLocaleString()} {session.currency}
          </div>
        </div>
        <div style={{ color: '#FF6600', fontFamily: F, fontSize: '1.1rem', fontWeight: 700, fontVariantNumeric: 'tabular-nums', letterSpacing: '0.05em' }}>
          {formatElapsed(elapsed)}
        </div>
      </div>
      <BacktestBulkEntry
        startingCapital={session.startingCapital}
        onRunBacktest={handleRunBacktest}
      />
    </div>
  );
}
