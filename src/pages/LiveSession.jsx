import { useState } from 'react';
import TradeEntryPanel from '../components/TradeEntryPanel.jsx';
import LiveCalculationsPanel from '../components/LiveCalculationsPanel.jsx';

const DEFAULT_VALUES = {
  direction: 'LONG',
  entryPrice: '',
  atr: '',
  slMultiple: '1.0',
  tpPrice: '',
  leverage: '1',
};

export default function LiveSession({ session }) {
  const [values, setValues] = useState(DEFAULT_VALUES);

  function handleChange(field, val) {
    setValues(prev => ({ ...prev, [field]: val }));
  }

  return (
    <div style={{ minHeight: '100vh', background: '#0a0a0a', padding: '1rem' }}>

      {/* Session banner */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
        <div>
          <div style={{ color: '#FF6600', fontFamily: "Helvetica, Arial, sans-serif", fontWeight: 700, fontSize: '0.9375rem' }}>
            {session.name || 'LIVE SESSION'}
          </div>
          <div style={{ color: '#444444', fontFamily: "Helvetica, Arial, sans-serif", fontSize: '0.8rem' }}>
            {session.currency} · Capital: ${session.currentCapital?.toLocaleString()}
          </div>
        </div>
      </div>

      {/* Two-column entry grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1rem' }}>
        <div>
          <TradeEntryPanel values={values} onChange={handleChange} />
        </div>
        <div>
          <LiveCalculationsPanel
            tradeValues={values}
            capital={session.currentCapital}
          />
        </div>
      </div>
    </div>
  );
}
