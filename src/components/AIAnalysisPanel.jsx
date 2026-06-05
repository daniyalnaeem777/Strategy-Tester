import { useState, useEffect } from 'react';
import Anthropic from '@anthropic-ai/sdk';

const SECTIONS = [
  'STRATEGY OVERVIEW',
  'SL MULTIPLE ANALYSIS',
  'TP MULTIPLE ANALYSIS',
  'LEVERAGE ASSESSMENT',
  'DIRECTIONAL BIAS',
  'PATTERN OBSERVATIONS',
  'RISK MANAGEMENT SCORE',
  'THREE RECOMMENDATIONS',
  'VERDICT',
];

export default function AIAnalysisPanel({ trades, stats, sessionName, aiAnalysis, onAnalysisComplete, triggerRef }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Allow parent (Report page) to trigger analysis for PDF
  useEffect(() => {
    if (triggerRef) {
      triggerRef.current = (callback) => {
        runAnalysis(callback);
      };
    }
  }, [triggerRef, trades, stats]);

  async function runAnalysis(externalCallback) {
    setLoading(true);
    setError(null);

    const apiKey = import.meta.env.VITE_ANTHROPIC_API_KEY;
    if (!apiKey) {
      const msg = 'VITE_ANTHROPIC_API_KEY not configured. Add it to your .env file.';
      setError(msg);
      setLoading(false);
      if (externalCallback) externalCallback(null);
      return;
    }

    const client = new Anthropic({ apiKey, dangerouslyAllowBrowser: true });

    const tradeSummary = trades.slice(0, 50).map(t =>
      `T${t.tradeNum}: ${t.direction} | Entry:${t.entryPrice?.toFixed(4)} | ATR:${t.atr?.toFixed(4)} | SL:${t.slMultiple}x | TP:${t.tpMultiple}x | Lev:${t.leverage}x | ${t.outcome} | P&L:$${t.pnl?.toFixed(2)} | Capital:$${t.capitalAfter?.toFixed(2)}`
    ).join('\n');

    const metricsText = stats ? `
Total Trades: ${stats.totalTrades}
Win Rate: ${stats.winRate?.toFixed(1)}%
Total P&L: $${stats.totalPnL?.toFixed(2)} (${stats.totalPnLPct?.toFixed(2)}%)
Avg Win: $${stats.avgWin?.toFixed(2)} | Avg Loss: $${stats.avgLoss?.toFixed(2)}
Largest Win: $${stats.largestWin?.toFixed(2)} | Largest Loss: $${stats.largestLoss?.toFixed(2)}
Max Drawdown: $${stats.maxDD?.toFixed(2)} (${stats.maxDDPct?.toFixed(2)}%)
Sharpe Ratio: ${stats.sharpe?.toFixed(2)}
Profit Factor: ${isFinite(stats.profitFactor) ? stats.profitFactor?.toFixed(2) : '∞'}
Expectancy: $${stats.expectancy?.toFixed(2)}
Avg R:R: 1:${stats.avgRR?.toFixed(2)}
Best SL Multiple: ${stats.bestSL}x | Best TP Multiple: ${stats.bestTP}x | Best Leverage: ${stats.bestLev}x` : '';

    try {
      const msg = await client.messages.create({
        model: 'claude-sonnet-4-20250514',
        max_tokens: 2000,
        system: 'You are an expert quantitative trading analyst reviewing a backtesting session. Analyse the provided trade log and performance metrics with institutional-grade rigour. Be direct, specific, and actionable. Format your response in clearly labelled sections using exactly these headers in ALL CAPS followed by a colon.',
        messages: [{
          role: 'user',
          content: `Session: ${sessionName || 'Unnamed Session'}

PERFORMANCE METRICS:
${metricsText}

TRADE LOG (${trades.length} total, showing first 50):
${tradeSummary}

Please analyse this data in these exact sections:
STRATEGY OVERVIEW:
SL MULTIPLE ANALYSIS:
TP MULTIPLE ANALYSIS:
LEVERAGE ASSESSMENT:
DIRECTIONAL BIAS:
PATTERN OBSERVATIONS:
RISK MANAGEMENT SCORE:
THREE RECOMMENDATIONS:
VERDICT: (must be exactly one of: STRONG EDGE DETECTED / REFINE AND RETEST / NO EDGE — STOP TRADING THIS SETUP)`
        }],
      });

      const text = msg.content[0].text;
      onAnalysisComplete(text);
      if (externalCallback) externalCallback(text);
    } catch (err) {
      setError(`API Error: ${err.message}`);
      if (externalCallback) externalCallback(null);
    } finally {
      setLoading(false);
    }
  }

  function parseAnalysis(text) {
    if (!text) return [];
    const sections = [];
    const lines = text.split('\n');
    let current = null;

    for (const line of lines) {
      const match = SECTIONS.find(s =>
        line.toUpperCase().trimStart().startsWith(s + ':') ||
        line.toUpperCase().trim() === s + ':'
      );
      if (match) {
        if (current) sections.push(current);
        current = {
          title: match,
          content: line.replace(new RegExp(`^${match}:?\\s*`, 'i'), '').trim()
        };
      } else if (current) {
        current.content += (current.content ? '\n' : '') + line;
      }
    }
    if (current) sections.push(current);
    return sections;
  }

  const sections = aiAnalysis ? parseAnalysis(aiAnalysis) : [];
  const verdict = sections.find(s => s.title === 'VERDICT');
  const verdictText = verdict?.content?.trim() || '';
  const verdictColor = verdictText.includes('STRONG EDGE') ? '#00E676'
    : verdictText.includes('NO EDGE') ? '#FF1744'
    : '#FFD600';

  return (
    <div className="terminal-panel" style={{ marginTop: '1rem' }}>
      <div className="panel-header">
        <span style={{ display: 'inline-block', width: 8, height: 8, background: '#FF6600' }}></span>
        AI STRATEGY ANALYSIS
        <span style={{ color: '#333333', fontFamily: "Helvetica, Arial, sans-serif", fontSize: '1.0625rem', marginLeft: '0.5rem' }}>
          claude-sonnet-4-20250514
        </span>
        <div style={{ marginLeft: 'auto', display: 'flex', gap: '0.5rem' }}>
          {!aiAnalysis && !loading && (
            <button className="btn-amber" style={{ fontSize: '1.0625rem', padding: '0.25rem 0.75rem' }} onClick={() => runAnalysis()}>
              ▶ RUN ANALYSIS
            </button>
          )}
          {aiAnalysis && !loading && (
            <button className="btn-ghost" style={{ fontSize: '1.0625rem', padding: '0.25rem 0.75rem' }} onClick={() => runAnalysis()}>
              ↺ RE-ANALYSE
            </button>
          )}
        </div>
      </div>

      <div style={{ padding: '1rem' }}>
        {!aiAnalysis && !loading && !error && (
          <div style={{ textAlign: 'center', padding: '3rem 1rem' }}>
            <div style={{ color: '#333333', fontFamily: "Helvetica, Arial, sans-serif", fontSize: '2.5rem', marginBottom: '1rem' }}>◈</div>
            <div style={{ color: '#888888', fontFamily: "Helvetica, Arial, sans-serif", fontSize: '1.0625rem', marginBottom: '0.5rem' }}>
              AI analysis not yet generated
            </div>
            <div style={{ color: '#444444', fontFamily: "Helvetica, Arial, sans-serif", fontSize: '1.0625rem', marginBottom: '1.5rem' }}>
              Requires VITE_ANTHROPIC_API_KEY in .env
            </div>
            <button className="btn-amber" style={{ padding: '0.625rem 1.5rem' }} onClick={() => runAnalysis()}>
              ▶ GENERATE AI ANALYSIS
            </button>
          </div>
        )}

        {loading && (
          <div style={{ textAlign: 'center', padding: '3rem 1rem' }}>
            <div style={{ color: '#FF6600', fontFamily: "Helvetica, Arial, sans-serif", fontSize: '1.0625rem', textTransform: 'uppercase', letterSpacing: '0.2em', marginBottom: '1rem' }}>
              ANALYSING TRADE DATA...
            </div>
            <div style={{ display: 'flex', justifyContent: 'center', gap: '4px', marginBottom: '1rem' }}>
              {[0,1,2,3,4,5,6].map(i => (
                <div key={i} style={{
                  width: '5px', height: '24px', background: '#FF6600',
                  opacity: 0.15 + i * 0.12,
                  animation: `barPulse 0.9s ease-in-out ${i * 0.1}s infinite alternate`,
                }} />
              ))}
            </div>
            <div style={{ color: '#444444', fontFamily: "Helvetica, Arial, sans-serif", fontSize: '1.0625rem' }}>
              Sending {trades.length} trades to Claude API...
            </div>
            <style>{`
              @keyframes barPulse {
                from { transform: scaleY(0.4); opacity: 0.2; }
                to { transform: scaleY(1); opacity: 1; }
              }
            `}</style>
          </div>
        )}

        {error && !loading && (
          <div style={{ padding: '1rem', border: '1px solid #FF1744', background: 'rgba(255,23,68,0.05)', marginBottom: '1rem' }}>
            <div style={{ color: '#FF1744', fontFamily: "Helvetica, Arial, sans-serif", fontSize: '1.0625rem' }}>{error}</div>
            <button className="btn-ghost" style={{ marginTop: '0.75rem', fontSize: '1.0625rem', padding: '0.375rem 0.75rem', borderColor: '#FF1744', color: '#FF1744' }} onClick={() => runAnalysis()}>
              ↺ RETRY
            </button>
          </div>
        )}

        {aiAnalysis && !loading && sections.length > 0 && (
          <div>
            {/* Verdict banner */}
            {verdict && (
              <div style={{
                border: `2px solid ${verdictColor}`,
                background: `${verdictColor}15`,
                padding: '1rem',
                textAlign: 'center',
                marginBottom: '1.5rem',
              }}>
                <div style={{ color: '#888888', fontFamily: "Helvetica, Arial, sans-serif", fontSize: '1.0625rem', textTransform: 'uppercase', letterSpacing: '0.25em', marginBottom: '0.25rem' }}>
                  AI VERDICT
                </div>
                <div style={{ color: verdictColor, fontFamily: "Helvetica, Arial, sans-serif", fontWeight: 700, fontSize: '1.1rem', letterSpacing: '0.05em' }}>
                  {verdictText}
                </div>
              </div>
            )}

            {/* All sections */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              {sections.filter(s => s.title !== 'VERDICT').map(section => (
                <div key={section.title} style={{ borderLeft: '2px solid #FF6600', paddingLeft: '1rem' }}>
                  <div style={{
                    color: '#FF6600',
                    fontFamily: "Helvetica, Arial, sans-serif",
                    fontSize: '0.8rem',
                    textTransform: 'uppercase',
                    letterSpacing: '0.15em',
                    marginBottom: '0.5rem',
                  }}>
                    {section.title}
                  </div>
                  <div style={{
                    color: '#E0E0E0',
                    fontFamily: "Helvetica, Arial, sans-serif",
                    fontSize: '0.8125rem',
                    lineHeight: 1.7,
                    whiteSpace: 'pre-wrap',
                  }}>
                    {section.content.trim()}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
