import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import ReportSummary from '../components/ReportSummary.jsx';
import EquityCurve from '../components/EquityCurve.jsx';
import DistributionCharts from '../components/DistributionCharts.jsx';
import TradeLogTable from '../components/TradeLogTable.jsx';
import AIAnalysisPanel from '../components/AIAnalysisPanel.jsx';
import { calcBacktestStats } from '../utils/calculations.js';
import { exportCSV, shareSummary } from '../utils/tradeLogger.js';
import { generatePDF } from '../utils/pdfReport.js';

const PROGRESS_STEPS = [
  'Capturing charts...',
  'Compiling trade data...',
  'Rendering AI analysis...',
  'Building PDF...',
  'Download ready.',
];

export default function Report({ session, setAiAnalysis, newSession }) {
  const navigate = useNavigate();
  const [pdfStep, setPdfStep] = useState(-1);
  const [pdfDone, setPdfDone] = useState(null);
  const [pdfError, setPdfError] = useState(null);
  const [copied, setCopied] = useState(false);
  const aiTriggerRef = useRef(null);

  const trades = session?.trades || [];
  const stats = calcBacktestStats(trades, session?.startingCapital);

  const isGenerating = pdfStep >= 0 && pdfStep < PROGRESS_STEPS.length - 1;
  const currentStepLabel = pdfStep >= 0 ? PROGRESS_STEPS[Math.min(pdfStep, PROGRESS_STEPS.length - 1)] : null;

  async function waitForAI() {
    // If AI analysis already exists, return it immediately
    if (session?.aiAnalysis) return session.aiAnalysis;
    // Otherwise trigger via the AI panel's exposed callback
    return new Promise((resolve) => {
      if (aiTriggerRef.current) {
        aiTriggerRef.current(resolve);
      } else {
        resolve(null);
      }
    });
  }

  async function handleGeneratePDF() {
    setPdfDone(null);
    setPdfError(null);
    setPdfStep(0);

    let aiAnalysis = session?.aiAnalysis;

    // Auto-trigger AI if not yet generated
    if (!aiAnalysis) {
      setPdfStep(-2); // special state for "generating AI"
      aiAnalysis = await waitForAI();
    }

    try {
      setPdfStep(0);
      const filename = await generatePDF({
        trades,
        stats,
        session: { ...session, aiAnalysis },
        aiAnalysis,
        equityCurveId: 'equity-curve',
        chartsId: 'distribution-charts',
        onProgress: (msg) => {
          const idx = PROGRESS_STEPS.indexOf(msg);
          if (idx >= 0) setPdfStep(idx);
        },
      });
      setPdfStep(PROGRESS_STEPS.length - 1);
      setPdfDone(`Report downloaded: ${filename}`);
    } catch (err) {
      setPdfError(`PDF generation failed: ${err.message}`);
      setPdfStep(-1);
    }
    setTimeout(() => { setPdfStep(-1); setPdfDone(null); setPdfError(null); }, 6000);
  }

  function handleExportCSV() {
    exportCSV(trades, session?.name);
  }

  function handleShareSummary() {
    shareSummary(stats, session?.name, session?.currency);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  }

  function handleNewSession() {
    newSession();
    navigate('/');
  }

  if (trades.length === 0) {
    return (
      <div style={{ minHeight: '100vh', background: '#0a0a0a', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ color: '#444444', fontFamily: "Helvetica, Arial, sans-serif", fontSize: '3rem', marginBottom: '1rem' }}>◫</div>
          <div style={{ color: '#888888', fontFamily: "Helvetica, Arial, sans-serif", fontSize: '1.0625rem', marginBottom: '1rem' }}>No trades to report</div>
          <button className="btn-amber" style={{ padding: '0.5rem 1.5rem' }} onClick={() => navigate(session?.mode === 'LIVE' ? '/live' : '/backtest')}>
            ← BACK TO SESSION
          </button>
        </div>
      </div>
    );
  }

  const generatingAI = pdfStep === -2;

  return (
    <div style={{ minHeight: '100vh', background: '#0a0a0a', padding: '1rem' }}>

      {/* Top action bar */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.5rem' }}>
        <div>
          <div style={{ color: '#FF6600', fontFamily: "Helvetica, Arial, sans-serif", fontWeight: 700, fontSize: '1.0625rem' }}>
            {session?.name || 'BACKTEST REPORT'}
          </div>
          <div style={{ color: '#444444', fontFamily: "Helvetica, Arial, sans-serif", fontSize: '1.0625rem' }}>
            {trades.length} trades · {session?.currency} · Starting capital: ${session?.startingCapital?.toLocaleString()}
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
          <button
            className="btn-amber"
            style={{ padding: '0.5rem 1rem', fontSize: '1.0625rem', opacity: isGenerating || generatingAI ? 0.6 : 1, cursor: isGenerating || generatingAI ? 'not-allowed' : 'pointer' }}
            onClick={handleGeneratePDF}
            disabled={isGenerating || generatingAI}
          >
            {generatingAI
              ? '◌ GENERATING AI...'
              : isGenerating
              ? `◌ ${currentStepLabel}`
              : '↓ GENERATE REPORT'}
          </button>

          <button className="btn-ghost" style={{ padding: '0.5rem 0.75rem', fontSize: '1.0625rem' }} onClick={handleExportCSV}>
            ↓ EXPORT CSV
          </button>

          <button className="btn-ghost" style={{ padding: '0.5rem 0.75rem', fontSize: '1.0625rem' }} onClick={handleShareSummary}>
            {copied ? '✓ COPIED' : '⎘ SHARE'}
          </button>

          <button
            onClick={handleNewSession}
            style={{
              border: '1px solid #FF1744',
              color: '#FF1744',
              background: 'transparent',
              fontFamily: "Helvetica, Arial, sans-serif",
              fontSize: '1.0625rem',
              padding: '0.5rem 0.75rem',
              textTransform: 'uppercase',
              letterSpacing: '0.1em',
              cursor: 'pointer',
            }}
          >
            ✕ NEW SESSION
          </button>
        </div>
      </div>

      {/* Progress bar */}
      {(isGenerating || generatingAI) && (
        <div style={{ marginBottom: '1rem', padding: '0.75rem 1rem', background: '#111111', border: '1px solid #FF6600', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{ display: 'flex', gap: '3px' }}>
            {[0,1,2,3,4].map(i => (
              <div key={i} style={{
                width: '5px', height: '18px', background: '#FF6600',
                opacity: 0.2 + (i * 0.18),
                animation: `pulse 1s ease-in-out ${i * 0.12}s infinite alternate`,
              }} />
            ))}
          </div>
          <span style={{ color: '#FF6600', fontFamily: "Helvetica, Arial, sans-serif", fontSize: '1.0625rem', textTransform: 'uppercase', letterSpacing: '0.1em' }}>
            {generatingAI ? 'Generating AI analysis before building report...' : currentStepLabel}
          </span>
          <div style={{ marginLeft: 'auto', display: 'flex', gap: '4px' }}>
            {PROGRESS_STEPS.slice(0, -1).map((_, i) => (
              <div key={i} style={{
                width: '24px', height: '3px',
                background: pdfStep > i ? '#FF6600' : pdfStep === i ? '#FFB300' : '#2a2a2a',
              }} />
            ))}
          </div>
        </div>
      )}

      {/* Success / error banners */}
      {pdfDone && (
        <div style={{ marginBottom: '1rem', padding: '0.75rem 1rem', border: '1px solid #00E676', background: 'rgba(0,230,118,0.05)', color: '#00E676', fontFamily: "Helvetica, Arial, sans-serif", fontSize: '1.0625rem' }}>
          ✓ {pdfDone}
        </div>
      )}
      {pdfError && (
        <div style={{ marginBottom: '1rem', padding: '0.75rem 1rem', border: '1px solid #FF1744', background: 'rgba(255,23,68,0.05)', color: '#FF1744', fontFamily: "Helvetica, Arial, sans-serif", fontSize: '1.0625rem' }}>
          ✗ {pdfError}
        </div>
      )}

      {/* Main grid: Summary + Equity Curve */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1rem', marginBottom: '1rem' }}>
        <div style={{ minWidth: 0 }}>
          <ReportSummary stats={stats} startingCapital={session?.startingCapital} />
        </div>
        <div style={{ minWidth: 0 }}>
          <EquityCurve
            trades={trades}
            startingCapital={session?.startingCapital}
            maxDDStart={stats?.maxDDStart}
            maxDDEnd={stats?.maxDDEnd}
            id="equity-curve"
          />
        </div>
      </div>

      {/* Distribution charts */}
      <div style={{ marginBottom: '1rem' }}>
        <DistributionCharts trades={trades} id="distribution-charts" />
      </div>

      {/* Full trade log */}
      <div style={{ marginBottom: '1rem' }}>
        <TradeLogTable trades={trades} showAll />
      </div>

      {/* AI Analysis */}
      <AIAnalysisPanel
        trades={trades}
        stats={stats}
        sessionName={session?.name}
        aiAnalysis={session?.aiAnalysis}
        onAnalysisComplete={setAiAnalysis}
        triggerRef={aiTriggerRef}
      />

      <style>{`
        @keyframes pulse {
          from { opacity: 0.3; transform: scaleY(0.8); }
          to { opacity: 1; transform: scaleY(1.2); }
        }
      `}</style>
    </div>
  );
}
