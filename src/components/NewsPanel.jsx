import { useState, useEffect } from 'react';

const RSS_FEEDS = [
  { label: 'Markets', url: 'https://feeds.bbci.co.uk/news/business/rss.xml' },
  { label: 'Crypto', url: 'https://finance.yahoo.com/news/rssindex' },
  { label: 'Forex', url: 'https://feeds.reuters.com/reuters/businessNews' },
];

const RSS2JSON = 'https://api.rss2json.com/v1/api.json?rss_url=';

function timeAgo(dateStr) {
  const diff = Date.now() - new Date(dateStr).getTime();
  const m = Math.floor(diff / 60000);
  if (m < 1) return 'just now';
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

export default function NewsPanel() {
  const [activeTab, setActiveTab] = useState(0);
  const [retryCount, setRetryCount] = useState(0);
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const F = 'Helvetica, Arial, sans-serif';

  useEffect(() => {
    setLoading(true);
    setError(null);
    setArticles([]);
    const url = `${RSS2JSON}${encodeURIComponent(RSS_FEEDS[activeTab].url)}&count=20`;
    fetch(url)
      .then(r => r.json())
      .then(data => {
        if (data.status === 'ok' && data.items?.length > 0) {
          setArticles(data.items);
        } else {
          setError(`Feed unavailable (${data.message || data.status || 'no items'})`);
        }
        setLoading(false);
      })
      .catch(e => { setError(`Network error: ${e.message}`); setLoading(false); });
  }, [activeTab, retryCount]);

  return (
    <div className="terminal-panel" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div className="panel-header">
        <span style={{ display: 'inline-block', width: 8, height: 8, background: '#FF6600' }} />
        MARKET NEWS
        <span style={{ marginLeft: 'auto', color: '#00E676', fontFamily: F, fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
          <span style={{ display: 'inline-block', width: 6, height: 6, borderRadius: '50%', background: '#00E676' }} />
          LIVE
        </span>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', borderBottom: '1px solid #2a2a2a' }}>
        {RSS_FEEDS.map((f, i) => (
          <button
            key={i}
            onClick={() => setActiveTab(i)}
            style={{
              padding: '0.4rem 0.875rem',
              fontFamily: F,
              fontSize: '0.75rem',
              fontWeight: 600,
              textTransform: 'uppercase',
              letterSpacing: '0.08em',
              border: 'none',
              borderBottom: i === activeTab ? '2px solid #FF6600' : '2px solid transparent',
              cursor: 'pointer',
              background: 'transparent',
              color: i === activeTab ? '#FF6600' : '#444444',
              transition: 'color 0.15s',
            }}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* Feed */}
      <div style={{ flex: 1, overflowY: 'auto' }}>
        {loading && (
          <div style={{ padding: '1rem', color: '#444444', fontFamily: F, fontSize: '0.8rem', textAlign: 'center' }}>
            LOADING FEED...
          </div>
        )}
        {error && (
          <div style={{ padding: '1rem', textAlign: 'center' }}>
            <div style={{ color: '#FF1744', fontFamily: F, fontSize: '0.75rem', marginBottom: '0.5rem' }}>{error}</div>
            <button
              onClick={() => setRetryCount(c => c + 1)}
              style={{ background: 'transparent', border: '1px solid #FF6600', color: '#FF6600', fontFamily: F, fontSize: '0.7rem', padding: '0.25rem 0.625rem', cursor: 'pointer', textTransform: 'uppercase', letterSpacing: '0.08em' }}
            >↺ RETRY</button>
          </div>
        )}
        {!loading && !error && articles.map((item, i) => (
          <a
            key={i}
            href={item.link}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              display: 'block',
              padding: '0.625rem 0.875rem',
              borderBottom: '1px solid #1a1a1a',
              textDecoration: 'none',
              transition: 'background 0.15s',
            }}
            onMouseEnter={e => e.currentTarget.style.background = '#111111'}
            onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
          >
            <div style={{ color: '#E0E0E0', fontFamily: F, fontSize: '0.8rem', lineHeight: 1.4, marginBottom: '0.25rem' }}>
              {item.title}
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span style={{ color: '#444444', fontFamily: F, fontSize: '0.675rem', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                {timeAgo(item.pubDate)}
              </span>
              {item.author && (
                <>
                  <span style={{ color: '#2a2a2a' }}>·</span>
                  <span style={{ color: '#444444', fontFamily: F, fontSize: '0.675rem' }}>{item.author}</span>
                </>
              )}
            </div>
          </a>
        ))}
      </div>

      <div style={{ padding: '0.5rem 0.875rem', borderTop: '1px solid #1a1a1a', color: '#2a2a2a', fontFamily: F, fontSize: '0.65rem', textTransform: 'uppercase', letterSpacing: '0.1em' }}>
        Via RSS · Auto-refreshes on tab switch
      </div>
    </div>
  );
}
