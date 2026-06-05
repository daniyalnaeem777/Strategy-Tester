import { useLocalStorage } from './useLocalStorage.js';
import { createTradeRecord } from '../utils/tradeLogger.js';

const DEFAULT_SESSION = {
  name: '',
  startingCapital: 10000,
  currency: 'USD',
  mode: null,
  currentCapital: 10000,
  trades: [],
  aiAnalysis: null,
  createdAt: null,
};

export function useSession() {
  const [session, setSession, clearSession] = useLocalStorage('tpsl_session', DEFAULT_SESSION);

  function initSession({ name, startingCapital, currency, mode }) {
    setSession({
      name,
      startingCapital: parseFloat(startingCapital),
      currency,
      mode,
      currentCapital: parseFloat(startingCapital),
      trades: [],
      aiAnalysis: null,
      createdAt: Date.now(),
    });
  }

  function logTrade({ direction, entryPrice, atr, slMultiple, tpMultiple, leverage, outcome }) {
    setSession(prev => {
      const tradeNum = (prev.trades?.length || 0) + 1;
      const trade = createTradeRecord({
        tradeNum,
        direction,
        entryPrice,
        atr,
        slMultiple,
        tpMultiple,
        leverage,
        capital: prev.currentCapital,
        outcome,
      });
      return {
        ...prev,
        currentCapital: trade.capitalAfter,
        trades: [...(prev.trades || []), trade],
      };
    });
  }

  function setTrades(trades) {
    setSession(prev => {
      const finalCapital = trades.length > 0 ? trades[trades.length - 1].capitalAfter : prev.startingCapital;
      return { ...prev, trades, currentCapital: finalCapital };
    });
  }

  function setAiAnalysis(analysis) {
    setSession(prev => ({ ...prev, aiAnalysis: analysis }));
  }

  function newSession() {
    clearSession();
  }

  return {
    session,
    initSession,
    logTrade,
    setTrades,
    setAiAnalysis,
    newSession,
  };
}
