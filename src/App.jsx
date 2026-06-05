import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Header from './components/Header.jsx';
import SessionInit from './components/SessionInit.jsx';
import LiveSession from './pages/LiveSession.jsx';
import BacktestSession from './pages/BacktestSession.jsx';
import Report from './pages/Report.jsx';
import { useSession } from './hooks/useSession.js';

export default function App() {
  const { session, initSession, logTrade, setTrades, setAiAnalysis, newSession } = useSession();

  const hasSession = session?.mode !== null && session?.mode !== undefined;

  return (
    <BrowserRouter>
      <div className="min-h-screen bg-[#0a0a0a] font-sans">
        {hasSession && <Header session={session} onExit={newSession} />}
        <Routes>
          <Route
            path="/"
            element={
              hasSession
                ? <Navigate to={session.mode === 'LIVE' ? '/live' : '/backtest'} replace />
                : <SessionInit onInit={initSession} />
            }
          />
          <Route
            path="/live"
            element={
              !hasSession
                ? <Navigate to="/" replace />
                : session.mode !== 'LIVE'
                ? <Navigate to="/backtest" replace />
                : <LiveSession session={session} />
            }
          />
          <Route
            path="/backtest"
            element={
              !hasSession
                ? <Navigate to="/" replace />
                : session.mode !== 'BACKTEST'
                ? <Navigate to="/live" replace />
                : <BacktestSession session={session} setTrades={setTrades} />
            }
          />
          <Route
            path="/report"
            element={
              !hasSession
                ? <Navigate to="/" replace />
                : <Report session={session} setAiAnalysis={setAiAnalysis} newSession={newSession} />
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}
