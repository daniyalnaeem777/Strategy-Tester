export function fmtPrice(val, decimals = 4) {
  if (val === null || val === undefined || isNaN(val)) return '—';
  return Number(val).toFixed(decimals);
}

export function fmtDollar(val, decimals = 2) {
  if (val === null || val === undefined || isNaN(val)) return '—';
  const abs = Math.abs(val);
  const prefix = val < 0 ? '-$' : '$';
  return `${prefix}${abs.toLocaleString('en-US', { minimumFractionDigits: decimals, maximumFractionDigits: decimals })}`;
}

export function fmtPct(val, decimals = 2) {
  if (val === null || val === undefined || isNaN(val)) return '—';
  return `${Number(val).toFixed(decimals)}%`;
}

export function fmtRR(val) {
  if (!val || isNaN(val)) return '—';
  return `1 : ${Number(val).toFixed(2)}`;
}

export function fmtMultiple(val) {
  if (!val) return '—';
  return `${val}x`;
}

export function fmtTimestamp(ts) {
  if (!ts) return '—';
  const d = new Date(ts);
  return d.toLocaleString('en-US', { month: 'short', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
}

export function fmtCurrency(amount, currency = 'USD') {
  const symbols = { USD: '$', CAD: 'C$', GBP: '£', EUR: '€' };
  const sym = symbols[currency] || '$';
  const abs = Math.abs(amount);
  const prefix = amount < 0 ? `-${sym}` : sym;
  return `${prefix}${abs.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

export function pnlColor(val) {
  if (val > 0) return '#00E676';
  if (val < 0) return '#FF1744';
  return '#888888';
}

export function pnlClass(val) {
  if (val > 0) return 'text-[#00E676]';
  if (val < 0) return 'text-[#FF1744]';
  return 'text-[#888888]';
}
