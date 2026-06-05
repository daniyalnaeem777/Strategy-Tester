import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, ResponsiveContainer,
} from 'recharts';
import { fmtDollar } from '../utils/formatters.js';

function CustomDot(props) {
  const { cx, cy, payload } = props;
  if (!payload.outcome) return null;
  const color = payload.outcome === 'WIN' ? '#00E676' : '#FF1744';
  return <circle cx={cx} cy={cy} r={4} fill={color} stroke="#0a0a0a" strokeWidth={1.5} />;
}

function CustomTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div style={{ background: '#0a0a0a', border: '1px solid #FF6600', padding: '0.625rem 0.875rem', fontFamily: "'Roboto Mono', monospace" }}>
      <div style={{ color: '#FF6600', fontSize: '0.7rem', marginBottom: '0.25rem' }}>TRADE {d.trade}</div>
      <div style={{ color: '#E0E0E0', fontSize: '0.75rem' }}>Capital: {fmtDollar(d.capital)}</div>
      {d.outcome && (
        <>
          <div style={{ color: d.direction === 'LONG' ? '#00E676' : '#FF1744', fontSize: '0.7rem' }}>
            {d.direction === 'LONG' ? '▲' : '▼'} {d.direction} — {d.outcome}
          </div>
          <div style={{ color: d.pnl >= 0 ? '#00E676' : '#FF1744', fontSize: '0.75rem', fontWeight: 500 }}>
            {d.pnl >= 0 ? '+' : ''}{fmtDollar(d.pnl)}
          </div>
        </>
      )}
    </div>
  );
}

export default function EquityCurve({ trades, startingCapital, id = 'equity-curve' }) {
  const data = [
    { trade: 0, capital: startingCapital, outcome: null },
    ...trades.map((t, i) => ({
      trade: i + 1,
      capital: t.capitalAfter,
      outcome: t.outcome,
      pnl: t.pnl,
      direction: t.direction,
    })),
  ];

  const finalCapital = trades.length > 0 ? trades[trades.length - 1].capitalAfter : startingCapital;
  const isPositive = finalCapital >= startingCapital;
  const lineColor = isPositive ? '#00E676' : '#FF1744';

  const allCapitals = data.map(d => d.capital);
  const minVal = Math.min(...allCapitals) * 0.994;
  const maxVal = Math.max(...allCapitals) * 1.006;

  const pnlDiff = finalCapital - startingCapital;
  const pnlPct = startingCapital > 0 ? (pnlDiff / startingCapital * 100).toFixed(2) : '0.00';

  return (
    <div className="terminal-panel" id={id}>
      <div className="panel-header">
        <span style={{ display: 'inline-block', width: 8, height: 8, background: '#FF6600' }}></span>
        EQUITY CURVE
        <span style={{ marginLeft: 'auto', fontFamily: "'Roboto Mono', monospace", fontSize: '0.75rem', color: lineColor }}>
          {isPositive ? '▲' : '▼'} {(pnlDiff >= 0 ? '+' : '') + fmtDollar(pnlDiff)} ({isPositive ? '+' : ''}{pnlPct}%)
        </span>
      </div>
      <div style={{ padding: '1rem' }}>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 16 }}>
            <CartesianGrid strokeDasharray="2 5" stroke="#1a1a1a" />
            <XAxis
              dataKey="trade"
              tick={{ fill: '#888888', fontFamily: "'Roboto Mono', monospace", fontSize: 10 }}
              axisLine={{ stroke: '#2a2a2a' }}
              tickLine={false}
              label={{ value: 'TRADE #', position: 'insideBottom', offset: -8, fill: '#444444', fontSize: 9, fontFamily: "'Roboto Mono', monospace" }}
            />
            <YAxis
              domain={[minVal, maxVal]}
              tick={{ fill: '#888888', fontFamily: "'Roboto Mono', monospace", fontSize: 10 }}
              axisLine={{ stroke: '#2a2a2a' }}
              tickLine={false}
              tickFormatter={v => {
                if (v >= 1000000) return `$${(v / 1000000).toFixed(1)}M`;
                if (v >= 1000) return `$${(v / 1000).toFixed(1)}k`;
                return `$${v.toFixed(0)}`;
              }}
              width={58}
            />
            <Tooltip content={<CustomTooltip />} />
            <ReferenceLine
              y={startingCapital}
              stroke="#FF6600"
              strokeDasharray="5 4"
              strokeOpacity={0.5}
              label={{ value: 'START', fill: '#FF6600', fontSize: 8, fontFamily: "'Roboto Mono', monospace", position: 'insideTopRight' }}
            />
            <Line
              type="monotone"
              dataKey="capital"
              stroke={lineColor}
              strokeWidth={2}
              dot={<CustomDot />}
              activeDot={{ r: 6, fill: '#FF6600', stroke: '#0a0a0a', strokeWidth: 2 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
