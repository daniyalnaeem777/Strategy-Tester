import { fmtPrice, fmtDollar, fmtPct, fmtRR } from '../utils/formatters.js';
import { calcTrade } from '../utils/calculations.js';

export default function LiveCalculationsPanel({ tradeValues, capital, onLogWin, onLogLoss }) {
  const calc = calcTrade({
    direction: tradeValues.direction || 'LONG',
    entryPrice: tradeValues.entryPrice || 0,
    atr: tradeValues.atr || 0,
    slMultiple: tradeValues.slMultiple || 1,
    tpPrice: tradeValues.tpPrice || 0,
    leverage: tradeValues.leverage || 1,
    capital,
  });

  const ready = parseFloat(tradeValues.entryPrice) > 0 && parseFloat(tradeValues.atr) > 0 && parseFloat(tradeValues.tpPrice) > 0;

  return (
    <div className="terminal-panel" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div className="panel-header">
        <span style={{ display: 'inline-block', width: 8, height: 8, background: '#FF6600' }}></span>
        LIVE CALCULATIONS
        <span style={{ marginLeft: 'auto', fontFamily: "Helvetica, Arial, sans-serif", fontSize: '1.0625rem' }}>
          {ready
            ? <span style={{ color: '#00E676' }}>● LIVE</span>
            : <span style={{ color: '#333333' }}>○ ENTER VALUES</span>
          }
        </span>
      </div>

      <div style={{ flex: 1, padding: '1rem', overflowY: 'auto' }}>

        <MetricSection label="PRICES">
          <MetricRow label="Stop Loss Price" value={ready ? fmtPrice(calc.slPrice) : '—'} color="#FF1744" />
          <MetricRow label="Take Profit Price" value={ready ? fmtPrice(calc.tpPrice) : '—'} color="#00E676" />
        </MetricSection>

        <MetricSection label="DISTANCES">
          <MetricRow label="SL Distance" value={ready ? `${fmtPrice(calc.slDist)} (${fmtPct(calc.slPct)})` : '—'} color="#FF1744" />
          <MetricRow label="TP Distance" value={ready ? `${fmtPrice(calc.tpDist)} (${fmtPct(calc.tpPct)})` : '—'} color="#00E676" />
          <MetricRow label="Risk / Reward" value={ready ? fmtRR(calc.rr) : '—'} color="#FF6600" />
        </MetricSection>

        <MetricSection label="POSITION SIZE">
          <MetricRow label="Effective Size" value={ready ? fmtDollar(calc.positionSize) : '—'} />
          <MetricRow label="Capital at Risk" value={ready ? fmtDollar(calc.capitalAtRisk) : '—'} color="#FFD600" />
          <MetricRow label="Current Capital" value={fmtDollar(capital)} color="#FF6600" />
        </MetricSection>

        <MetricSection label="OUTCOME SCENARIOS">
          <MetricRow label="Max Loss (SL Hit)" value={ready ? `${fmtDollar(calc.maxLoss)} (${fmtPct(calc.maxLossPct)})` : '—'} color="#FF1744" />
          <MetricRow label="Max Gain (TP Hit)" value={ready ? `${fmtDollar(calc.maxGain)} (${fmtPct(calc.maxGainPct)})` : '—'} color="#00E676" />
        </MetricSection>

      </div>

      {/* Log buttons */}
      <div style={{ padding: '1rem', paddingTop: 0 }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
          <button
            className="btn-win"
            style={{ padding: '0.875rem', fontSize: '1.0625rem', opacity: ready ? 1 : 0.3, cursor: ready ? 'pointer' : 'not-allowed' }}
            onClick={onLogWin}
            disabled={!ready}
          >
            ✓ LOG WIN
          </button>
          <button
            className="btn-loss"
            style={{ padding: '0.875rem', fontSize: '1.0625rem', opacity: ready ? 1 : 0.3, cursor: ready ? 'pointer' : 'not-allowed' }}
            onClick={onLogLoss}
            disabled={!ready}
          >
            ✗ LOG LOSS
          </button>
        </div>
      </div>
    </div>
  );
}

function MetricSection({ label, children }) {
  return (
    <div style={{ marginBottom: '0.875rem' }}>
      <div style={{ color: '#444444', fontFamily: "Helvetica, Arial, sans-serif", fontSize: '0.6rem', textTransform: 'uppercase', letterSpacing: '0.2em', marginBottom: '0.25rem', paddingLeft: '0.25rem' }}>
        {label}
      </div>
      <div style={{ background: '#0d0d0d', border: '1px solid #1a1a1a' }}>
        {children}
      </div>
    </div>
  );
}

function MetricRow({ label, value, color = '#E0E0E0' }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.375rem 0.75rem', borderBottom: '1px solid #1a1a1a' }}>
      <span style={{ color: '#888888', fontFamily: "Helvetica, Arial, sans-serif", fontSize: '1.0625rem' }}>{label}</span>
      <span style={{ color, fontFamily: "Helvetica, Arial, sans-serif", fontSize: '1.0625rem', fontWeight: 500, fontVariantNumeric: 'tabular-nums' }}>{value}</span>
    </div>
  );
}
