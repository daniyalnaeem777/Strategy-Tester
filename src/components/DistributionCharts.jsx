import {
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';

const tooltipStyle = {
  contentStyle: {
    background: '#0a0a0a',
    border: '1px solid #FF6600',
    fontFamily: "Helvetica, Arial, sans-serif",
    fontSize: '11px',
    color: '#E0E0E0',
  },
  itemStyle: { color: '#E0E0E0' },
};

function axisProps() {
  return {
    tick: { fill: '#888888', fontFamily: "Helvetica, Arial, sans-serif", fontSize: 10 },
    axisLine: { stroke: '#2a2a2a' },
    tickLine: false,
  };
}

export default function DistributionCharts({ trades, id = 'distribution-charts' }) {
  const wins = trades.filter(t => t.outcome === 'WIN').length;
  const losses = trades.filter(t => t.outcome === 'LOSS').length;

  const pieData = [
    { name: 'WIN', value: wins, fill: '#00E676' },
    { name: 'LOSS', value: losses, fill: '#FF1744' },
  ];

  // Direction breakdown
  const dirData = [
    { name: 'L-WIN', value: trades.filter(t => t.direction === 'LONG' && t.outcome === 'WIN').reduce((s, t) => s + t.pnl, 0), fill: '#00E676' },
    { name: 'L-LOSS', value: trades.filter(t => t.direction === 'LONG' && t.outcome === 'LOSS').reduce((s, t) => s + t.pnl, 0), fill: '#FF1744' },
    { name: 'S-WIN', value: trades.filter(t => t.direction === 'SHORT' && t.outcome === 'WIN').reduce((s, t) => s + t.pnl, 0), fill: '#00A0FF' },
    { name: 'S-LOSS', value: trades.filter(t => t.direction === 'SHORT' && t.outcome === 'LOSS').reduce((s, t) => s + t.pnl, 0), fill: '#FF8800' },
  ].filter(d => d.value !== 0);

  const slData = groupNetPnL(trades, 'slMultiple');
  const tpData = groupNetPnL(trades, 'tpMultiple');
  const levData = groupNetPnL(trades, 'leverage');

  return (
    <div id={id} style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem' }}>

      <ChartPanel title="WIN / LOSS DISTRIBUTION">
        <ResponsiveContainer width="100%" height={210}>
          <PieChart>
            <Pie
              data={pieData}
              cx="50%" cy="50%"
              outerRadius={75}
              dataKey="value"
              label={({ name, percent, value }) => value > 0 ? `${name} ${(percent * 100).toFixed(0)}%` : ''}
              labelLine={false}
            >
              {pieData.map((entry, i) => <Cell key={i} fill={entry.fill} />)}
            </Pie>
            <Tooltip {...tooltipStyle} formatter={(v, n) => [v, n]} />
          </PieChart>
        </ResponsiveContainer>
      </ChartPanel>

      <ChartPanel title="P&L BY DIRECTION">
        <BarGroupChart data={dirData} suffix="" isDollar />
      </ChartPanel>

      <ChartPanel title="P&L BY SL MULTIPLE">
        <BarGroupChart data={slData} suffix="x" isDollar />
      </ChartPanel>

      <ChartPanel title="P&L BY TP MULTIPLE">
        <BarGroupChart data={tpData} suffix="x" isDollar />
      </ChartPanel>

      <ChartPanel title="P&L BY LEVERAGE" style={{ gridColumn: 'span 1' }}>
        <BarGroupChart data={levData} suffix="x" isDollar />
      </ChartPanel>

    </div>
  );
}

function ChartPanel({ title, children }) {
  return (
    <div className="terminal-panel">
      <div className="panel-header" style={{ fontSize: '0.65rem' }}>
        <span style={{ display: 'inline-block', width: 6, height: 6, background: '#FF6600' }}></span>
        {title}
      </div>
      <div style={{ padding: '0.75rem' }}>{children}</div>
    </div>
  );
}

function BarGroupChart({ data, suffix, isDollar }) {
  if (!data.length) {
    return <div style={{ height: 210, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#444444', fontFamily: "Helvetica, Arial, sans-serif", fontSize: '1.0625rem' }}>NO DATA</div>;
  }
  return (
    <ResponsiveContainer width="100%" height={210}>
      <BarChart data={data} margin={{ top: 5, right: 8, left: 0, bottom: 5 }}>
        <CartesianGrid strokeDasharray="2 4" stroke="#1a1a1a" />
        <XAxis
          dataKey="name"
          {...axisProps()}
          tickFormatter={v => `${v}${suffix}`}
        />
        <YAxis
          {...axisProps()}
          tickFormatter={v => isDollar ? (Math.abs(v) >= 1000 ? `$${(v/1000).toFixed(1)}k` : `$${v.toFixed(0)}`) : v}
          width={52}
        />
        <Tooltip
          {...tooltipStyle}
          formatter={v => [isDollar ? (v >= 0 ? '+$' + v.toFixed(2) : '-$' + Math.abs(v).toFixed(2)) : v, 'Net P&L']}
          labelFormatter={v => `${v}${suffix}`}
        />
        <Bar dataKey="value" radius={0}>
          {data.map((entry, i) => <Cell key={i} fill={entry.value >= 0 ? '#00E676' : '#FF1744'} fillOpacity={0.85} />)}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

function groupNetPnL(trades, key) {
  const groups = {};
  for (const t of trades) {
    const k = t[key];
    if (groups[k] === undefined) groups[k] = 0;
    groups[k] += t.pnl;
  }
  return Object.entries(groups)
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => parseFloat(a.name) - parseFloat(b.name));
}
