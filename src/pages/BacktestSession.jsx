import { useNavigate } from 'react-router-dom';
import BacktestBulkEntry from '../components/BacktestBulkEntry.jsx';

export default function BacktestSession({ session, setTrades }) {
  const navigate = useNavigate();

  function handleRunBacktest(trades) {
    setTrades(trades);
    navigate('/report');
  }

  return (
    <div className="min-h-screen bg-[#0a0a0a] p-4">
      <div className="flex items-center justify-between mb-4 px-1">
        <div>
          <div className="text-[#FF6600] font-mono font-bold text-base">{session.name || 'BACKTEST MODE'}</div>
          <div className="text-[#444444] font-mono text-xs">
            Starting Capital: ${session.startingCapital?.toLocaleString()} {session.currency}
          </div>
        </div>
      </div>
      <BacktestBulkEntry
        startingCapital={session.startingCapital}
        onRunBacktest={handleRunBacktest}
      />
    </div>
  );
}
