import { useState, useRef } from 'react';
import { downloadCSVTemplate, parseCSV, createTradeRecord } from '../utils/tradeLogger.js';

const SL_OPTIONS = ['0.5', '1.0', '1.5', '2.0', '2.5', '3.0'];
const LEV_OPTIONS = ['1', '2', '3', '5', '10', '20', '25', '50', '100'];
const F = 'Helvetica, Arial, sans-serif';

function todayStr() {
  return new Date().toISOString().slice(0, 10);
}

let nextId = 1;
function emptyRow() {
  return { id: nextId++, date: todayStr(), direction: 'LONG', entryPrice: '', atr: '', slMultiple: '1.0', tpPrice: '', leverage: '1', outcome: 'WIN' };
}

export default function BacktestBulkEntry({ startingCapital, onRunBacktest }) {
  const [rows, setRows] = useState([emptyRow()]);
  const fileRef = useRef();

  function addRow() { setRows(prev => [...prev, emptyRow()]); }
  function deleteRow(id) { setRows(prev => prev.length > 1 ? prev.filter(r => r.id !== id) : prev); }
  function updateRow(id, field, val) { setRows(prev => prev.map(r => r.id === id ? { ...r, [field]: val } : r)); }
  function clearAll() { nextId = 1; setRows([emptyRow()]); }

  function handleCSV(e) {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = ev => {
      const parsed = parseCSV(ev.target.result);
      if (parsed.length > 0) { nextId = parsed.length + 1; setRows(parsed); }
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
      const trade = createTradeRecord({ tradeNum: i + 1, date: r.date, direction: r.direction, entryPrice: r.entryPrice, atr: r.atr, slMultiple: r.slMultiple, tpPrice: r.tpPrice, leverage: r.leverage, capital, outcome: r.outcome });
      capital = trade.capitalAfter;
      return trade;
    });
    onRunBacktest(trades);
  }

  const validCount = rows.filter(r =>
    r.entryPrice && r.atr && r.tpPrice &&
    parseFloat(r.entryPrice) > 0 && parseFloat(r.atr) > 0 && parseFloat(r.tpPrice) > 0
  ).length;

  const th = { padding: '0.5rem 0.625rem', color: '#444444', fontFamily: F, textTransform: 'uppercase', letterSpacing: '0.08em', fontSize: '0.75rem', textAlign: 'left', whiteSpace: 'nowrap', background: '#0d0d0d', borderBottom: '1px solid #2a2a2a' };

  return (
    <div className="terminal-panel">
      <div className="panel-header">
        <span style={{ display: 'inline-block', width: 8, height: 8, background: '#FF6600' }} />
        BACKTEST BULK ENTRY
        <span style={{ marginLeft: 'auto', color: '#888888', fontFamily: F, fontSize: '0.875rem' }}>
          {rows.length} ROWS{validCount > 0 ? ` · ${validCount} VALID` : ''}
        </span>
      </div>

      {/* Action bar — 2×2 grid on mobile, flex row on desktop */}
      <div className="bulk-action-bar">
        <ActionBtn onClick={addRow}>+ ADD ROW</ActionBtn>
        <ActionBtn onClick={downloadCSVTemplate}>↓ CSV TEMPLATE</ActionBtn>
        <label style={actionBtnStyle} className="bulk-action-btn">
          ↑ IMPORT CSV
          <input type="file" accept=".csv" ref={fileRef} onChange={handleCSV} style={{ display: 'none' }} />
        </label>
        <ActionBtn onClick={clearAll} danger>CLEAR ALL</ActionBtn>
      </div>

      {/* ── DESKTOP TABLE (hidden on mobile) ── */}
      <div className="bulk-table-view">
        <div style={{ overflowX: 'auto', WebkitOverflowScrolling: 'touch' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: '820px', fontFamily: F, fontSize: '0.875rem' }}>
            <thead>
              <tr>
                <th style={th}>#</th>
                <th style={th}>DATE</th>
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
                <tr key={row.id} style={{ borderBottom: '1px solid #1a1a1a' }}
                  onMouseEnter={e => e.currentTarget.style.background = '#131313'}
                  onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
                  <td style={{ padding: '0.375rem 0.625rem', color: '#444444', fontSize: '0.875rem' }}>{idx + 1}</td>
                  <td style={{ padding: '0.375rem 0.375rem' }}>
                    <input type="date" value={row.date} onChange={e => updateRow(row.id, 'date', e.target.value)} style={{ ...cellInput, width: '130px', colorScheme: 'dark' }} />
                  </td>
                  <td style={{ padding: '0.375rem 0.375rem' }}>
                    <select value={row.direction} onChange={e => updateRow(row.id, 'direction', e.target.value)}
                      style={{ background: '#0a0a0a', border: '1px solid #2a2a2a', color: row.direction === 'LONG' ? '#00E676' : '#FF1744', fontFamily: F, fontSize: '0.875rem', fontWeight: 600, padding: '0.3rem 0.5rem', outline: 'none', width: '110px', cursor: 'pointer' }}>
                      <option value="LONG">▲ LONG</option>
                      <option value="SHORT">▼ SHORT</option>
                    </select>
                  </td>
                  <td style={{ padding: '0.375rem 0.375rem' }}><input type="number" value={row.entryPrice} onChange={e => updateRow(row.id, 'entryPrice', e.target.value)} style={cellInput} placeholder="0.0000" step="0.0001" /></td>
                  <td style={{ padding: '0.375rem 0.375rem' }}><input type="number" value={row.atr} onChange={e => updateRow(row.id, 'atr', e.target.value)} style={cellInput} placeholder="0.0000" step="0.0001" /></td>
                  <td style={{ padding: '0.375rem 0.375rem' }}><select value={row.slMultiple} onChange={e => updateRow(row.id, 'slMultiple', e.target.value)} style={cellSelect}>{SL_OPTIONS.map(o => <option key={o} value={o}>{o}x</option>)}</select></td>
                  <td style={{ padding: '0.375rem 0.375rem' }}><input type="number" value={row.tpPrice} onChange={e => updateRow(row.id, 'tpPrice', e.target.value)} style={{ ...cellInput, borderColor: row.tpPrice ? '#2a2a2a' : '#331a00' }} placeholder="0.0000" step="0.0001" /></td>
                  <td style={{ padding: '0.375rem 0.375rem' }}><select value={row.leverage} onChange={e => updateRow(row.id, 'leverage', e.target.value)} style={cellSelect}>{LEV_OPTIONS.map(o => <option key={o} value={o}>{o}x</option>)}</select></td>
                  <td style={{ padding: '0.375rem 0.375rem' }}><select value={row.outcome} onChange={e => updateRow(row.id, 'outcome', e.target.value)} style={{ ...cellSelect, color: row.outcome === 'WIN' ? '#00E676' : '#FF1744' }}><option value="WIN">WIN</option><option value="LOSS">LOSS</option></select></td>
                  <td style={{ padding: '0.375rem 0.375rem' }}>
                    <button onClick={() => deleteRow(row.id)} style={{ color: '#444444', background: 'none', border: 'none', cursor: 'pointer', width: '28px', height: '28px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1rem' }}
                      onMouseEnter={e => e.currentTarget.style.color = '#FF1744'} onMouseLeave={e => e.currentTarget.style.color = '#444444'}>✕</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── MOBILE CARDS (hidden on desktop) ── */}
      <div className="bulk-card-view">
        {rows.map((row, idx) => (
          <TradeCard key={row.id} row={row} idx={idx} onUpdate={updateRow} onDelete={deleteRow} canDelete={rows.length > 1} />
        ))}
      </div>

      {/* Run button */}
      <div style={{ padding: '1rem', borderTop: '1px solid #2a2a2a' }}>
        <button className="btn-amber"
          style={{ width: '100%', padding: '0.875rem', fontSize: '1rem', opacity: validCount === 0 ? 0.3 : 1, cursor: validCount === 0 ? 'not-allowed' : 'pointer' }}
          onClick={runBacktest} disabled={validCount === 0}>
          ▶ RUN BACKTEST ({validCount} TRADES)
        </button>
      </div>
    </div>
  );
}

function TradeCard({ row, idx, onUpdate, onDelete, canDelete }) {
  const isValid = row.entryPrice && row.atr && row.tpPrice &&
    parseFloat(row.entryPrice) > 0 && parseFloat(row.atr) > 0 && parseFloat(row.tpPrice) > 0;

  const cardInput = { background: '#0a0a0a', border: '1px solid #2a2a2a', color: '#E0E0E0', fontFamily: F, fontSize: '1rem', padding: '0.5rem 0.75rem', width: '100%', outline: 'none', minHeight: '44px', boxSizing: 'border-box' };
  const cardSelect = { ...cardInput, cursor: 'pointer', appearance: 'none' };
  const label = { color: '#888888', fontFamily: F, fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: '0.1em', display: 'block', marginBottom: '0.25rem' };

  return (
    <div style={{ borderBottom: '2px solid #2a2a2a', padding: '0.875rem' }}>
      {/* Card header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{ color: '#FF6600', fontFamily: F, fontWeight: 700, fontSize: '0.875rem' }}>TRADE #{idx + 1}</span>
          {isValid && <span style={{ color: '#00E676', fontFamily: F, fontSize: '0.65rem', border: '1px solid #00E676', padding: '0.1rem 0.375rem' }}>VALID</span>}
        </div>
        {canDelete && (
          <button onClick={() => onDelete(row.id)} style={{ color: '#444444', background: 'none', border: '1px solid #2a2a2a', cursor: 'pointer', padding: '0.25rem 0.625rem', fontFamily: F, fontSize: '0.8rem' }}
            onMouseEnter={e => { e.currentTarget.style.borderColor = '#FF1744'; e.currentTarget.style.color = '#FF1744'; }}
            onMouseLeave={e => { e.currentTarget.style.borderColor = '#2a2a2a'; e.currentTarget.style.color = '#444444'; }}>
            ✕ REMOVE
          </button>
        )}
      </div>

      {/* Row 1: Date + Direction */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.625rem', marginBottom: '0.625rem' }}>
        <div>
          <span style={label}>Date</span>
          <input type="date" value={row.date} onChange={e => onUpdate(row.id, 'date', e.target.value)} style={{ ...cardInput, colorScheme: 'dark' }} />
        </div>
        <div>
          <span style={label}>Direction</span>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.375rem' }}>
            <button onClick={() => onUpdate(row.id, 'direction', 'LONG')}
              style={{ border: `2px solid ${row.direction === 'LONG' ? '#00E676' : '#2a2a2a'}`, background: row.direction === 'LONG' ? '#00E676' : 'transparent', color: row.direction === 'LONG' ? '#000' : '#888888', fontFamily: F, fontWeight: 700, fontSize: '0.8rem', padding: '0.5rem 0', cursor: 'pointer', minHeight: '44px' }}>
              ▲ LONG
            </button>
            <button onClick={() => onUpdate(row.id, 'direction', 'SHORT')}
              style={{ border: `2px solid ${row.direction === 'SHORT' ? '#FF1744' : '#2a2a2a'}`, background: row.direction === 'SHORT' ? '#FF1744' : 'transparent', color: row.direction === 'SHORT' ? '#fff' : '#888888', fontFamily: F, fontWeight: 700, fontSize: '0.8rem', padding: '0.5rem 0', cursor: 'pointer', minHeight: '44px' }}>
              ▼ SHORT
            </button>
          </div>
        </div>
      </div>

      {/* Row 2: Entry Price + ATR */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.625rem', marginBottom: '0.625rem' }}>
        <div>
          <span style={label}>Entry Price</span>
          <input type="number" value={row.entryPrice} onChange={e => onUpdate(row.id, 'entryPrice', e.target.value)} style={cardInput} placeholder="0.0000" step="0.0001" />
        </div>
        <div>
          <span style={label}>ATR (14)</span>
          <input type="number" value={row.atr} onChange={e => onUpdate(row.id, 'atr', e.target.value)} style={cardInput} placeholder="0.0000" step="0.0001" />
        </div>
      </div>

      {/* Row 3: TP Price + SL Mult */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.625rem', marginBottom: '0.625rem' }}>
        <div>
          <span style={label}>TP Price</span>
          <input type="number" value={row.tpPrice} onChange={e => onUpdate(row.id, 'tpPrice', e.target.value)} style={{ ...cardInput, borderColor: row.tpPrice ? '#2a2a2a' : '#331a00' }} placeholder="0.0000" step="0.0001" />
        </div>
        <div>
          <span style={label}>SL Multiple</span>
          <div style={{ position: 'relative' }}>
            <select value={row.slMultiple} onChange={e => onUpdate(row.id, 'slMultiple', e.target.value)} style={cardSelect}>
              {SL_OPTIONS.map(o => <option key={o} value={o}>{o}x ATR</option>)}
            </select>
            <span style={{ position: 'absolute', right: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: '#FF6600', fontSize: '0.75rem', pointerEvents: 'none' }}>▼</span>
          </div>
        </div>
      </div>

      {/* Row 4: Leverage + Outcome */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.625rem' }}>
        <div>
          <span style={label}>Leverage</span>
          <div style={{ position: 'relative' }}>
            <select value={row.leverage} onChange={e => onUpdate(row.id, 'leverage', e.target.value)} style={cardSelect}>
              {LEV_OPTIONS.map(o => <option key={o} value={o}>{o}x</option>)}
            </select>
            <span style={{ position: 'absolute', right: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: '#FF6600', fontSize: '0.75rem', pointerEvents: 'none' }}>▼</span>
          </div>
        </div>
        <div>
          <span style={label}>Outcome</span>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.375rem' }}>
            <button onClick={() => onUpdate(row.id, 'outcome', 'WIN')}
              style={{ border: `2px solid ${row.outcome === 'WIN' ? '#00E676' : '#2a2a2a'}`, background: row.outcome === 'WIN' ? '#00E676' : 'transparent', color: row.outcome === 'WIN' ? '#000' : '#888888', fontFamily: F, fontWeight: 700, fontSize: '0.875rem', padding: '0.5rem 0', cursor: 'pointer', minHeight: '44px' }}>
              WIN
            </button>
            <button onClick={() => onUpdate(row.id, 'outcome', 'LOSS')}
              style={{ border: `2px solid ${row.outcome === 'LOSS' ? '#FF1744' : '#2a2a2a'}`, background: row.outcome === 'LOSS' ? '#FF1744' : 'transparent', color: row.outcome === 'LOSS' ? '#fff' : '#888888', fontFamily: F, fontWeight: 700, fontSize: '0.875rem', padding: '0.5rem 0', cursor: 'pointer', minHeight: '44px' }}>
              LOSS
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

const cellInput = { background: '#0a0a0a', border: '1px solid #2a2a2a', color: '#E0E0E0', fontFamily: F, fontSize: '0.875rem', padding: '0.3rem 0.5rem', outline: 'none', width: '108px' };
const cellSelect = { background: '#0a0a0a', border: '1px solid #2a2a2a', color: '#E0E0E0', fontFamily: F, fontSize: '0.875rem', padding: '0.3rem 0.5rem', outline: 'none', width: '80px', cursor: 'pointer' };
const actionBtnStyle = { background: 'transparent', color: '#FF6600', fontFamily: F, fontWeight: 600, fontSize: '0.875rem', padding: '0.4rem 0.875rem', border: '1px solid #FF6600', textTransform: 'uppercase', letterSpacing: '0.08em', cursor: 'pointer', display: 'inline-flex', alignItems: 'center', justifyContent: 'center' };

function ActionBtn({ onClick, danger, children }) {
  return (
    <button onClick={onClick}
      style={{ ...actionBtnStyle, borderColor: danger ? '#FF1744' : '#FF6600', color: danger ? '#FF1744' : '#FF6600' }}
      onMouseEnter={e => { e.currentTarget.style.background = danger ? '#FF1744' : '#FF6600'; e.currentTarget.style.color = danger ? '#fff' : '#000'; }}
      onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = danger ? '#FF1744' : '#FF6600'; }}>
      {children}
    </button>
  );
}
