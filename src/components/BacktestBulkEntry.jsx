import { useState, useRef } from 'react';
import { downloadCSVTemplate, parseCSV, createTradeRecord } from '../utils/tradeLogger.js';

const SL_OPTIONS = ['0.5', '1.0', '1.5', '2.0', '2.5', '3.0'];
const LEV_OPTIONS = ['1', '2', '3', '5', '10', '20', '25', '50', '100'];

let nextId = 1;
function emptyRow() {
  return { id: nextId++, direction: 'LONG', entryPrice: '', atr: '', slMultiple: '1.0', tpPrice: '', leverage: '1', outcome: 'WIN' };
}

export default function BacktestBulkEntry({ startingCapital, onRunBacktest }) {
  const [rows, setRows] = useState([emptyRow()]);
  const fileRef = useRef();

  function addRow() {
    setRows(prev => [...prev, emptyRow()]);
  }

  function deleteRow(id) {
    setRows(prev => prev.length > 1 ? prev.filter(r => r.id !== id) : prev);
  }

  function updateRow(id, field, val) {
    setRows(prev => prev.map(r => r.id === id ? { ...r, [field]: val } : r));
  }

  function clearAll() {
    nextId = 1;
    setRows([emptyRow()]);
  }

  function handleCSV(e) {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = ev => {
      const parsed = parseCSV(ev.target.result);
      if (parsed.length > 0) {
        nextId = parsed.length + 1;
        setRows(parsed);
      }
    };
    reader.readAsText(file);
    e.target.value = '';
  }

  function runBacktest() {
    const validRows = rows.filter(r => r.entryPrice && r.atr && r.tpPrice &&
      parseFloat(r.entryPrice) > 0 && parseFloat(r.atr) > 0 && parseFloat(r.tpPrice) > 0);
    if (validRows.length === 0) return;

    let capital = parseFloat(startingCapital) || 10000;
    const trades = validRows.map((r, i) => {
      const trade = createTradeRecord({
        tradeNum: i + 1,
        direction: r.direction,
        entryPrice: r.entryPrice,
        atr: r.atr,
        slMultiple: r.slMultiple,
        tpPrice: r.tpPrice,
        leverage: r.leverage,
        capital,
        outcome: r.outcome,
      });
      capital = trade.capitalAfter;
      return trade;
    });
    onRunBacktest(trades);
  }

  const validCount = rows.filter(r =>
    r.entryPrice && r.atr && r.tpPrice &&
    parseFloat(r.entryPrice) > 0 && parseFloat(r.atr) > 0 && parseFloat(r.tpPrice) > 0
  ).length;

  const th = {
    padding: '0.5rem 0.625rem',
    color: '#444444',
    fontFamily: 'Helvetica, Arial, sans-serif',
    textTransform: 'uppercase',
    letterSpacing: '0.08em',
    fontSize: '0.75rem',
    textAlign: 'left',
    whiteSpace: 'nowrap',
    background: '#0d0d0d',
    borderBottom: '1px solid #2a2a2a',
  };

  return (
    <div className="terminal-panel">
      <div className="panel-header">
        <span style={{ display: 'inline-block', width: 8, height: 8, background: '#FF6600' }} />
        BACKTEST BULK ENTRY
        <span style={{ marginLeft: 'auto', color: '#888888', fontFamily: 'Helvetica, Arial, sans-serif', fontSize: '0.875rem' }}>
          {rows.length} ROWS · {validCount} VALID
        </span>
      </div>

      {/* Action bar */}
      <div style={{ padding: '0.75rem 1rem', borderBottom: '1px solid #2a2a2a', display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
        <ActionBtn onClick={addRow}>+ ADD ROW</ActionBtn>
        <ActionBtn onClick={downloadCSVTemplate}>↓ CSV TEMPLATE</ActionBtn>
        <label style={actionBtnStyle}>
          ↑ IMPORT CSV
          <input type="file" accept=".csv" ref={fileRef} onChange={handleCSV} style={{ display: 'none' }} />
        </label>
        <ActionBtn onClick={clearAll} danger>CLEAR ALL</ActionBtn>
      </div>

      {/* Table */}
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: '820px', fontFamily: 'Helvetica, Arial, sans-serif', fontSize: '0.875rem' }}>
          <thead>
            <tr>
              <th style={th}>#</th>
              <th style={th}>DIRECTION</th>
              <th style={th}>ENTRY PRICE</th>
              <th style={th}>ATR (14)</th>
              <th style={th}>SL MULT</th>
              <th style={th}>TP PRICE</th>
              <th style={th}>LEVERAGE</th>
              <th style={th}>OUTCOME</th>
              <th style={th}></th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row, idx) => (
              <tr
                key={row.id}
                style={{ borderBottom: '1px solid #1a1a1a' }}
                onMouseEnter={e => e.currentTarget.style.background = '#131313'}
                onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
              >
                <td style={{ padding: '0.375rem 0.625rem', color: '#444444', fontSize: '0.875rem' }}>{idx + 1}</td>

                {/* Direction — wider so full word fits */}
                <td style={{ padding: '0.375rem 0.375rem' }}>
                  <select
                    value={row.direction}
                    onChange={e => updateRow(row.id, 'direction', e.target.value)}
                    style={{
                      background: '#0a0a0a',
                      border: '1px solid #2a2a2a',
                      color: row.direction === 'LONG' ? '#00E676' : '#FF1744',
                      fontFamily: 'Helvetica, Arial, sans-serif',
                      fontSize: '0.875rem',
                      fontWeight: 600,
                      padding: '0.3rem 0.5rem',
                      outline: 'none',
                      width: '110px',
                      cursor: 'pointer',
                    }}
                  >
                    <option value="LONG">▲ LONG</option>
                    <option value="SHORT">▼ SHORT</option>
                  </select>
                </td>

                <td style={{ padding: '0.375rem 0.375rem' }}>
                  <input type="number" value={row.entryPrice} onChange={e => updateRow(row.id, 'entryPrice', e.target.value)}
                    style={cellInput} placeholder="0.0000" step="0.0001" />
                </td>
                <td style={{ padding: '0.375rem 0.375rem' }}>
                  <input type="number" value={row.atr} onChange={e => updateRow(row.id, 'atr', e.target.value)}
                    style={cellInput} placeholder="0.0000" step="0.0001" />
                </td>
                <td style={{ padding: '0.375rem 0.375rem' }}>
                  <select value={row.slMultiple} onChange={e => updateRow(row.id, 'slMultiple', e.target.value)} style={cellSelect}>
                    {SL_OPTIONS.map(o => <option key={o} value={o}>{o}x</option>)}
                  </select>
                </td>

                {/* TP Price — direct number input */}
                <td style={{ padding: '0.375rem 0.375rem' }}>
                  <input type="number" value={row.tpPrice} onChange={e => updateRow(row.id, 'tpPrice', e.target.value)}
                    style={{ ...cellInput, borderColor: row.tpPrice ? '#2a2a2a' : '#331a00' }} placeholder="0.0000" step="0.0001" />
                </td>

                <td style={{ padding: '0.375rem 0.375rem' }}>
                  <select value={row.leverage} onChange={e => updateRow(row.id, 'leverage', e.target.value)} style={cellSelect}>
                    {LEV_OPTIONS.map(o => <option key={o} value={o}>{o}x</option>)}
                  </select>
                </td>
                <td style={{ padding: '0.375rem 0.375rem' }}>
                  <select value={row.outcome} onChange={e => updateRow(row.id, 'outcome', e.target.value)}
                    style={{ ...cellSelect, color: row.outcome === 'WIN' ? '#00E676' : '#FF1744' }}>
                    <option value="WIN">WIN</option>
                    <option value="LOSS">LOSS</option>
                  </select>
                </td>
                <td style={{ padding: '0.375rem 0.375rem' }}>
                  <button
                    onClick={() => deleteRow(row.id)}
                    style={{ color: '#444444', background: 'none', border: 'none', cursor: 'pointer', width: '28px', height: '28px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1rem' }}
                    onMouseEnter={e => e.currentTarget.style.color = '#FF1744'}
                    onMouseLeave={e => e.currentTarget.style.color = '#444444'}
                  >✕</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Run button */}
      <div style={{ padding: '1rem', borderTop: '1px solid #2a2a2a' }}>
        <button
          className="btn-amber"
          style={{ width: '100%', padding: '0.875rem', fontSize: '1rem', opacity: validCount === 0 ? 0.3 : 1, cursor: validCount === 0 ? 'not-allowed' : 'pointer' }}
          onClick={runBacktest}
          disabled={validCount === 0}
        >
          ▶ RUN BACKTEST ({validCount} TRADES)
        </button>
      </div>
    </div>
  );
}

const cellInput = {
  background: '#0a0a0a',
  border: '1px solid #2a2a2a',
  color: '#E0E0E0',
  fontFamily: 'Helvetica, Arial, sans-serif',
  fontSize: '0.875rem',
  padding: '0.3rem 0.5rem',
  outline: 'none',
  width: '108px',
};

const cellSelect = {
  background: '#0a0a0a',
  border: '1px solid #2a2a2a',
  color: '#E0E0E0',
  fontFamily: 'Helvetica, Arial, sans-serif',
  fontSize: '0.875rem',
  padding: '0.3rem 0.5rem',
  outline: 'none',
  width: '80px',
  cursor: 'pointer',
};

const actionBtnStyle = {
  background: 'transparent',
  color: '#FF6600',
  fontFamily: 'Helvetica, Arial, sans-serif',
  fontWeight: 600,
  fontSize: '0.875rem',
  padding: '0.4rem 0.875rem',
  border: '1px solid #FF6600',
  textTransform: 'uppercase',
  letterSpacing: '0.08em',
  cursor: 'pointer',
  display: 'inline-flex',
  alignItems: 'center',
};

function ActionBtn({ onClick, danger, children }) {
  return (
    <button
      onClick={onClick}
      style={{ ...actionBtnStyle, borderColor: danger ? '#FF1744' : '#FF6600', color: danger ? '#FF1744' : '#FF6600' }}
      onMouseEnter={e => { e.currentTarget.style.background = danger ? '#FF1744' : '#FF6600'; e.currentTarget.style.color = danger ? '#fff' : '#000'; }}
      onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = danger ? '#FF1744' : '#FF6600'; }}
    >
      {children}
    </button>
  );
}
