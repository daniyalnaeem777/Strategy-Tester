import { useState } from 'react';
import { fmtDollar, fmtTimestamp, fmtPrice } from '../utils/formatters.js';

const COLS = [
  { key: 'tradeNum', label: '#' },
  { key: 'timestamp', label: 'TIME' },
  { key: 'direction', label: 'DIR' },
  { key: 'entryPrice', label: 'ENTRY' },
  { key: 'rr', label: 'R:R' },
  { key: 'outcome', label: 'OUTCOME' },
  { key: 'pnl', label: 'P&L' },
  { key: 'capitalAfter', label: 'CAPITAL' },
];

export default function TradeLogTable({ trades, maxRows = 5, showAll = false }) {
  const [sortKey, setSortKey] = useState('tradeNum');
  const [sortDir, setSortDir] = useState('desc');

  if (!trades || trades.length === 0) {
    return (
      <div className="terminal-panel">
        <div className="panel-header">
          <span style={{ display: 'inline-block', width: 8, height: 8, background: '#FF6600' }}></span>
          TRADE LOG
          <span style={{ marginLeft: 'auto', color: '#444444' }}>NO TRADES</span>
        </div>
        <div style={{ padding: '1.5rem', textAlign: 'center', color: '#444444', fontFamily: "'Roboto Mono', monospace", fontSize: '0.875rem' }}>
          No trades logged yet.
        </div>
      </div>
    );
  }

  function toggleSort(key) {
    if (sortKey === key) setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    else { setSortKey(key); setSortDir('desc'); }
  }

  let sorted = [...trades];
  if (showAll) {
    sorted.sort((a, b) => {
      const av = a[sortKey], bv = b[sortKey];
      if (sortDir === 'asc') return av > bv ? 1 : -1;
      return av < bv ? 1 : -1;
    });
  } else {
    sorted = sorted.slice(-maxRows).reverse();
  }

  return (
    <div className="terminal-panel">
      <div className="panel-header">
        <span style={{ display: 'inline-block', width: 8, height: 8, background: '#FF6600' }}></span>
        TRADE LOG
        {showAll && <span style={{ marginLeft: '0.5rem', color: '#444444', fontSize: '0.625rem' }}>CLICK HEADERS TO SORT</span>}
        <span style={{ marginLeft: 'auto', color: '#888888', fontFamily: "'Roboto Mono', monospace", fontSize: '0.75rem' }}>{trades.length} TOTAL</span>
      </div>
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', fontFamily: "'Roboto Mono', monospace", fontSize: '0.75rem', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid #2a2a2a' }}>
              {COLS.map(col => (
                <th
                  key={col.key}
                  onClick={() => showAll && toggleSort(col.key)}
                  style={{
                    padding: '0.5rem 0.75rem',
                    color: sortKey === col.key && showAll ? '#FF6600' : '#444444',
                    textTransform: 'uppercase',
                    letterSpacing: '0.1em',
                    fontSize: '0.625rem',
                    textAlign: col.key === 'pnl' || col.key === 'capitalAfter' ? 'right' : 'left',
                    cursor: showAll ? 'pointer' : 'default',
                    userSelect: 'none',
                    whiteSpace: 'nowrap',
                  }}
                >
                  {col.label}{showAll && sortKey === col.key ? (sortDir === 'asc' ? ' ▲' : ' ▼') : ''}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sorted.map(t => (
              <tr
                key={t.tradeNum}
                style={{
                  borderBottom: '1px solid #1a1a1a',
                  background: t.outcome === 'WIN' ? 'rgba(0,230,118,0.03)' : 'rgba(255,23,68,0.03)',
                }}
              >
                <td style={{ padding: '0.5rem 0.75rem', color: '#444444' }}>{t.tradeNum}</td>
                <td style={{ padding: '0.5rem 0.75rem', color: '#888888', whiteSpace: 'nowrap' }}>{fmtTimestamp(t.timestamp)}</td>
                <td style={{ padding: '0.5rem 0.75rem', color: t.direction === 'LONG' ? '#00E676' : '#FF1744' }}>
                  {t.direction === 'LONG' ? '▲' : '▼'} {t.direction}
                </td>
                <td style={{ padding: '0.5rem 0.75rem', color: '#E0E0E0', fontVariantNumeric: 'tabular-nums' }}>{t.entryPrice?.toFixed(4)}</td>
                <td style={{ padding: '0.5rem 0.75rem', color: '#FFB300', fontVariantNumeric: 'tabular-nums' }}>1:{t.rr?.toFixed(2)}</td>
                <td style={{ padding: '0.5rem 0.75rem' }}>
                  <span style={{
                    padding: '0.125rem 0.5rem',
                    fontSize: '0.625rem',
                    textTransform: 'uppercase',
                    background: t.outcome === 'WIN' ? 'rgba(0,230,118,0.1)' : 'rgba(255,23,68,0.1)',
                    color: t.outcome === 'WIN' ? '#00E676' : '#FF1744',
                    border: `1px solid ${t.outcome === 'WIN' ? 'rgba(0,230,118,0.3)' : 'rgba(255,23,68,0.3)'}`,
                  }}>
                    {t.outcome}
                  </span>
                </td>
                <td style={{ padding: '0.5rem 0.75rem', textAlign: 'right', fontVariantNumeric: 'tabular-nums', fontWeight: 500, color: t.pnl >= 0 ? '#00E676' : '#FF1744' }}>
                  {t.pnl >= 0 ? '+' : ''}{fmtDollar(t.pnl)}
                </td>
                <td style={{ padding: '0.5rem 0.75rem', textAlign: 'right', color: '#E0E0E0', fontVariantNumeric: 'tabular-nums' }}>
                  {fmtDollar(t.capitalAfter)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
