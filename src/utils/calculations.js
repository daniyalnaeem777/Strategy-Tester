export function calcTrade({ direction, entryPrice, atr, slMultiple, tpMultiple, leverage, capital }) {
  const entry = parseFloat(entryPrice) || 0;
  const atrVal = parseFloat(atr) || 0;
  const slMult = parseFloat(slMultiple) || 1;
  const tpMult = parseFloat(tpMultiple) || 2;
  const lev = parseFloat(leverage) || 1;
  const cap = parseFloat(capital) || 10000;

  const slDist = atrVal * slMult;
  const tpDist = atrVal * tpMult;

  const slPrice = direction === 'LONG' ? entry - slDist : entry + slDist;
  const tpPrice = direction === 'LONG' ? entry + tpDist : entry - tpDist;

  const slPct = entry > 0 ? (slDist / entry) * 100 : 0;
  const tpPct = entry > 0 ? (tpDist / entry) * 100 : 0;

  const rr = slDist > 0 ? tpDist / slDist : 0;

  const positionSize = cap * lev;
  const maxLoss = entry > 0 ? positionSize * (slDist / entry) : 0;
  const maxGain = entry > 0 ? positionSize * (tpDist / entry) : 0;

  const maxLossPct = cap > 0 ? (maxLoss / cap) * 100 : 0;
  const maxGainPct = cap > 0 ? (maxGain / cap) * 100 : 0;

  return {
    slPrice,
    tpPrice,
    slDist,
    tpDist,
    slPct,
    tpPct,
    rr,
    positionSize,
    maxLoss,
    maxGain,
    maxLossPct,
    maxGainPct,
    capitalAtRisk: maxLoss,
  };
}

export function applyTradeOutcome({ capital, outcome, maxGain, maxLoss }) {
  if (outcome === 'WIN') return capital + maxGain;
  if (outcome === 'LOSS') return capital - maxLoss;
  return capital;
}

export function calcBacktestStats(trades, startingCapital) {
  if (!trades || trades.length === 0) return null;

  const wins = trades.filter(t => t.outcome === 'WIN');
  const losses = trades.filter(t => t.outcome === 'LOSS');

  const totalPnL = trades.reduce((sum, t) => sum + t.pnl, 0);
  const totalPnLPct = startingCapital > 0 ? (totalPnL / startingCapital) * 100 : 0;

  const winRate = trades.length > 0 ? (wins.length / trades.length) * 100 : 0;

  const avgWin = wins.length > 0 ? wins.reduce((s, t) => s + t.pnl, 0) / wins.length : 0;
  const avgLoss = losses.length > 0 ? Math.abs(losses.reduce((s, t) => s + t.pnl, 0) / losses.length) : 0;

  const largestWin = wins.length > 0 ? Math.max(...wins.map(t => t.pnl)) : 0;
  const largestLoss = losses.length > 0 ? Math.abs(Math.min(...losses.map(t => t.pnl))) : 0;

  // Max drawdown
  let peak = startingCapital;
  let maxDD = 0;
  let maxDDStart = 0;
  let maxDDEnd = 0;
  let ddStart = 0;
  let capitals = [startingCapital, ...trades.map(t => t.capitalAfter)];

  for (let i = 0; i < capitals.length; i++) {
    if (capitals[i] > peak) {
      peak = capitals[i];
      ddStart = i;
    }
    const dd = peak - capitals[i];
    if (dd > maxDD) {
      maxDD = dd;
      maxDDStart = ddStart;
      maxDDEnd = i;
    }
  }

  const maxDDPct = peak > 0 ? (maxDD / peak) * 100 : 0;

  // Sharpe ratio (simplified, assuming daily returns)
  const pnls = trades.map(t => t.pnl);
  const mean = pnls.reduce((s, v) => s + v, 0) / pnls.length;
  const variance = pnls.reduce((s, v) => s + Math.pow(v - mean, 2), 0) / pnls.length;
  const stdDev = Math.sqrt(variance);
  const sharpe = stdDev > 0 ? mean / stdDev : 0;

  // Profit factor
  const grossWins = wins.reduce((s, t) => s + t.pnl, 0);
  const grossLosses = Math.abs(losses.reduce((s, t) => s + t.pnl, 0));
  const profitFactor = grossLosses > 0 ? grossWins / grossLosses : grossWins > 0 ? Infinity : 0;

  const expectancy = trades.length > 0 ? totalPnL / trades.length : 0;

  const avgRR = trades.length > 0 ? trades.reduce((s, t) => s + (t.rr || 0), 0) / trades.length : 0;

  // Best multiples
  const slGroups = groupBy(trades, 'slMultiple');
  const tpGroups = groupBy(trades, 'tpMultiple');
  const levGroups = groupBy(trades, 'leverage');

  const bestSL = bestGroup(slGroups);
  const bestTP = bestGroup(tpGroups);
  const bestLev = bestGroup(levGroups);

  return {
    totalTrades: trades.length,
    wins: wins.length,
    losses: losses.length,
    winRate,
    totalPnL,
    totalPnLPct,
    avgWin,
    avgLoss,
    largestWin,
    largestLoss,
    maxDD,
    maxDDPct,
    maxDDStart,
    maxDDEnd,
    sharpe,
    profitFactor,
    expectancy,
    avgRR,
    bestSL,
    bestTP,
    bestLev,
    capitals,
  };
}

function groupBy(arr, key) {
  return arr.reduce((acc, item) => {
    const k = item[key];
    if (!acc[k]) acc[k] = [];
    acc[k].push(item);
    return acc;
  }, {});
}

function bestGroup(groups) {
  let best = null;
  let bestPnL = -Infinity;
  for (const [key, trades] of Object.entries(groups)) {
    const total = trades.reduce((s, t) => s + t.pnl, 0);
    if (total > bestPnL) {
      bestPnL = total;
      best = key;
    }
  }
  return best;
}
