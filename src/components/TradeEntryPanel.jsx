import { useEffect } from 'react';
import { useLocalStorage } from '../hooks/useLocalStorage.js';

const SL_OPTIONS = ['0.5', '1.0', '1.5', '2.0', '2.5', '3.0'];
const TP_OPTIONS = ['0.5', '1.0', '1.5', '2.0', '2.5', '3.0'];
const LEV_OPTIONS = ['1', '2', '3', '5', '10', '20', '25', '50', '100'];

export default function TradeEntryPanel({ values, onChange }) {
  const [savedSL, setSavedSL] = useLocalStorage('tpsl_sl_mult', '1.0');
  const [savedTP, setSavedTP] = useLocalStorage('tpsl_tp_mult', '2.0');
  const [savedLev, setSavedLev] = useLocalStorage('tpsl_leverage', '1');

  useEffect(() => {
    if (!values.slMultiple) onChange('slMultiple', savedSL);
    if (!values.tpMultiple) onChange('tpMultiple', savedTP);
    if (!values.leverage) onChange('leverage', savedLev);
  }, []);

  function handleChange(field, val) {
    onChange(field, val);
    if (field === 'slMultiple') setSavedSL(val);
    if (field === 'tpMultiple') setSavedTP(val);
    if (field === 'leverage') setSavedLev(val);
  }

  function step(field, delta, decimals = 4) {
    const cur = parseFloat(values[field]) || 0;
    const next = Math.max(0, cur + delta);
    onChange(field, next.toFixed(decimals));
  }

  const longActive = values.direction === 'LONG';
  const shortActive = values.direction === 'SHORT';

  return (
    <div className="terminal-panel h-full">
      <div className="panel-header">
        <span style={{ display: 'inline-block', width: '8px', height: '8px', background: '#FF6600' }}></span>
        TRADE ENTRY
      </div>

      <div style={{ padding: '1rem' }}>

        {/* Direction */}
        <div style={{ marginBottom: '1rem' }}>
          <label className="terminal-label" style={{ display: 'block', marginBottom: '0.5rem' }}>Direction</label>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
            <button
              onClick={() => onChange('direction', 'LONG')}
              style={{
                border: `2px solid ${longActive ? '#00E676' : '#2a2a2a'}`,
                background: longActive ? '#00E676' : 'transparent',
                color: longActive ? '#000000' : '#888888',
                fontFamily: "Helvetica, Arial, sans-serif",
                fontWeight: 700,
                fontSize: '1.0625rem',
                padding: '0.75rem',
                textTransform: 'uppercase',
                letterSpacing: '0.1em',
                cursor: 'pointer',
                transition: 'all 0.15s',
              }}
            >
              ▲ LONG
            </button>
            <button
              onClick={() => onChange('direction', 'SHORT')}
              style={{
                border: `2px solid ${shortActive ? '#FF1744' : '#2a2a2a'}`,
                background: shortActive ? '#FF1744' : 'transparent',
                color: shortActive ? '#ffffff' : '#888888',
                fontFamily: "Helvetica, Arial, sans-serif",
                fontWeight: 700,
                fontSize: '1.0625rem',
                padding: '0.75rem',
                textTransform: 'uppercase',
                letterSpacing: '0.1em',
                cursor: 'pointer',
                transition: 'all 0.15s',
              }}
            >
              ▼ SHORT
            </button>
          </div>
        </div>

        {/* Entry Price */}
        <StepperField
          label="Entry Price"
          value={values.entryPrice || ''}
          onChange={v => onChange('entryPrice', v)}
          onStep={d => step('entryPrice', d, 4)}
          stepSize={0.0001}
          placeholder="0.0000"
        />

        {/* ATR */}
        <StepperField
          label="ATR (14)"
          value={values.atr || ''}
          onChange={v => onChange('atr', v)}
          onStep={d => step('atr', d, 4)}
          stepSize={0.0001}
          placeholder="0.0000"
        />

        {/* SL Multiple */}
        <div style={{ marginBottom: '1rem' }}>
          <label className="terminal-label" style={{ display: 'block', marginBottom: '0.375rem' }}>SL Multiple</label>
          <div style={{ position: 'relative' }}>
            <select
              value={values.slMultiple || savedSL}
              onChange={e => handleChange('slMultiple', e.target.value)}
              className="terminal-select"
            >
              {SL_OPTIONS.map(o => (
                <option key={o} value={o}>{o}x ATR</option>
              ))}
            </select>
            <div style={{ position: 'absolute', right: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: '#FF6600', fontSize: '1.0625rem', pointerEvents: 'none' }}>▼</div>
          </div>
        </div>

        {/* TP Multiple */}
        <div style={{ marginBottom: '1rem' }}>
          <label className="terminal-label" style={{ display: 'block', marginBottom: '0.375rem' }}>TP Multiple</label>
          <div style={{ position: 'relative' }}>
            <select
              value={values.tpMultiple || savedTP}
              onChange={e => handleChange('tpMultiple', e.target.value)}
              className="terminal-select"
            >
              {TP_OPTIONS.map(o => (
                <option key={o} value={o}>{o}x ATR</option>
              ))}
            </select>
            <div style={{ position: 'absolute', right: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: '#FF6600', fontSize: '1.0625rem', pointerEvents: 'none' }}>▼</div>
          </div>
        </div>

        {/* Leverage */}
        <div style={{ marginBottom: '0.5rem' }}>
          <label className="terminal-label" style={{ display: 'block', marginBottom: '0.375rem' }}>Leverage</label>
          <div style={{ position: 'relative' }}>
            <select
              value={values.leverage || savedLev}
              onChange={e => handleChange('leverage', e.target.value)}
              className="terminal-select"
            >
              {LEV_OPTIONS.map(o => (
                <option key={o} value={o}>{o}x</option>
              ))}
            </select>
            <div style={{ position: 'absolute', right: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: '#FF6600', fontSize: '1.0625rem', pointerEvents: 'none' }}>▼</div>
          </div>
        </div>

      </div>
    </div>
  );
}

function StepperField({ label, value, onChange, onStep, stepSize, placeholder }) {
  return (
    <div style={{ marginBottom: '1rem' }}>
      <label className="terminal-label" style={{ display: 'block', marginBottom: '0.375rem' }}>{label}</label>
      <div style={{ display: 'flex' }}>
        <button className="stepper-btn" onClick={() => onStep(-stepSize)}>−</button>
        <input
          type="number"
          value={value}
          onChange={e => onChange(e.target.value)}
          className="terminal-input"
          style={{ textAlign: 'center' }}
          placeholder={placeholder}
          step={stepSize}
        />
        <button className="stepper-btn" onClick={() => onStep(stepSize)}>+</button>
      </div>
    </div>
  );
}
