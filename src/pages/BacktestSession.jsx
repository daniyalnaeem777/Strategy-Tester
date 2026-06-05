import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import BacktestBulkEntry from '../components/BacktestBulkEntry.jsx';

export default function BacktestSession({ session, setTrades }) {
  const navigate = useNavigate();
  const [time, setTime] = useState(new Date());
  const F = 'Helvetica, Arial, sans-serif';

  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000);
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
          {time.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })}
        </div>
      </div>
      <BacktestBulkEntry
        startingCapital={session.startingCapital}
        onRunBacktest={handleRunBacktest}
      />
    </div>
  );
}
