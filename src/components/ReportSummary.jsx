import { fmtDollar, fmtPct } from '../utils/formatters.js';

export default function ReportSummary({ stats, startingCapital }) {
  if (!stats) return null;

  return (
    <div className="terminal-panel" style={{ height: '100%' }}>
      <div className="panel-header">
        <span style={{ display: 'inline-block', width: 8, height: 8, background: '#FF6600' }}></span>
        PERFORMANCE SUMMARY
      </div>

      <div style={{ padding: '1rem' }}>

        <Section label="TRADE STATS">
          <Row label="Total Trades" value={stats.totalTrades} />
          <Row label="Wins" value={stats.wins} color="#00E676" />
          <Row label="Losses" value={stats.losses} color="#FF1744" />
          <Row label="Win Rate" value={fmtPct(stats.winRate)} color={stats.winRate >= 50 ? '#00E676' : '#FF1744'} />
        </Section>

        <Section label="P&L">
          <Row
            label="Total P&L ($)"
            value={(stats.totalPnL >= 0 ? '+' : '') + fmtDollar(stats.totalPnL)}
            color={stats.totalPnL >= 0 ? '#00E676' : '#FF1744'}
          />
          <Row
            label="Total P&L (%)"
            value={(stats.totalPnLPct >= 0 ? '+' : '') + fmtPct(stats.totalPnLPct)}
            color={stats.totalPnLPct >= 0 ? '#00E676' : '#FF1744'}
          />
          <Row label="Average Win" value={fmtDollar(stats.avgWin)} color="#00E676" />
          <Row label="Average Loss" value={'-' + fmtDollar(stats.avgLoss)} color="#FF1744" />
          <Row label="Largest Win" value={fmtDollar(stats.largestWin)} color="#00E676" />
          <Row label="Largest Loss" value={'-' + fmtDollar(stats.largestLoss)} color="#FF1744" />
        </Section>

        <Section label="RISK METRICS">
          <Row label="Max Drawdown ($)" value={'-' + fmtDollar(stats.maxDD)} color="#FF1744" />
          <Row label="Max Drawdown (%)" value={'-' + fmtPct(stats.maxDDPct)} color="#FF1744" />
          <Row
            label="Sharpe Ratio"
            value={stats.sharpe?.toFixed(2)}
            color={stats.sharpe >= 1 ? '#00E676' : stats.sharpe >= 0 ? '#FFD600' : '#FF1744'}
          />
          <Row
            label="Profit Factor"
            value={isFinite(stats.profitFactor) ? stats.profitFactor?.toFixed(2) : '∞'}
            color={stats.profitFactor >= 1.5 ? '#00E676' : stats.profitFactor >= 1 ? '#FFD600' : '#FF1744'}
          />
          <Row
            label="Expectancy / Trade"
            value={(stats.expectancy >= 0 ? '+' : '') + fmtDollar(stats.expectancy)}
            color={stats.expectancy >= 0 ? '#00E676' : '#FF1744'}
          />
          <Row label="Average R:R" value={'1 : ' + stats.avgRR?.toFixed(2)} color="#FF6600" />
        </Section>

        <Section label="BEST PARAMETERS">
          <Row label="Best SL Multiple" value={stats.bestSL ? stats.bestSL + 'x ATR' : '—'} color="#FF6600" />
          <Row label="Best TP Multiple" value={stats.bestTP ? stats.bestTP + 'x ATR' : '—'} color="#FF6600" />
          <Row label="Best Leverage" value={stats.bestLev ? stats.bestLev + 'x' : '—'} color="#FF6600" />
        </Section>

      </div>
    </div>
  );
}

function Section({ label, children }) {
  return (
    <div style={{ marginBottom: '1rem' }}>
      <div style={{ color: '#444444', fontFamily: "'Roboto Mono', monospace", fontSize: '0.6rem', textTransform: 'uppercase', letterSpacing: '0.2em', marginBottom: '0.25rem', paddingLeft: '0.25rem' }}>
        {label}
      </div>
      <div style={{ background: '#0d0d0d', border: '1px solid #1a1a1a' }}>
        {children}
      </div>
    </div>
  );
}

function Row({ label, value, color = '#E0E0E0' }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.375rem 0.75rem', borderBottom: '1px solid #1a1a1a' }}>
      <span style={{ color: '#888888', fontFamily: "'Roboto Mono', monospace", fontSize: '0.75rem' }}>{label}</span>
      <span style={{ color, fontFamily: "'Roboto Mono', monospace", fontSize: '0.875rem', fontWeight: 500, fontVariantNumeric: 'tabular-nums' }}>{value}</span>
    </div>
  );
}
