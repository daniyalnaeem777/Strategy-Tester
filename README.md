# TP/SL Pro — Bloomberg-Grade Trading Strategy Tester

A professional trading strategy backtesting and live session calculator with a Bloomberg Terminal aesthetic.

## Features

- **Live Session Mode** — Log trades in real-time as you replay on TradingView
- **Backtest Bulk Entry** — Import or manually enter historical trades for analysis
- **Full Report** — Equity curve, distribution charts, and performance metrics
- **AI Analysis** — Claude-powered institutional-grade strategy analysis
- **PDF Export** — Full formatted report with charts and trade log
- **PWA** — Installable on mobile for on-the-go live session use

## Setup

### 1. Install dependencies

```bash
npm install
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and add your Anthropic API key:

```
VITE_ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### 3. Start development server

```bash
npm run dev
```

## Deploy to Vercel (3 commands)

```bash
npm install -g vercel
vercel login
vercel --prod
```

When prompted, set the environment variable `VITE_ANTHROPIC_API_KEY` in the Vercel dashboard under **Project Settings → Environment Variables**.

## Project Structure

```
src/
  components/
    Header.jsx              # Top nav bar with session stats + live clock
    TradeEntryPanel.jsx     # Direction, entry, ATR, SL/TP/leverage inputs
    LiveCalculationsPanel.jsx  # Real-time calculations + log buttons
    TradeLogTable.jsx       # Running trade history table
    ReportSummary.jsx       # Performance metrics panel
    EquityCurve.jsx         # Recharts equity curve with win/loss dots
    DistributionCharts.jsx  # Win/Loss pie, P&L by direction/SL/TP/leverage
    AIAnalysisPanel.jsx     # Claude API integration for strategy analysis
    SessionInit.jsx         # Session setup screen
    BacktestBulkEntry.jsx   # Bulk trade entry table with CSV import/export
  pages/
    LiveSession.jsx         # Live session page
    BacktestSession.jsx     # Backtest entry page
    Report.jsx              # Full report page with PDF/CSV export
  utils/
    calculations.js         # Trade math, backtest stats, drawdown, Sharpe
    formatters.js           # Number/currency/date formatting helpers
    tradeLogger.js          # Trade record creation, CSV export, share
    pdfReport.js            # jsPDF + html2canvas PDF generation
  hooks/
    useSession.js           # Session state management + localStorage
    useLocalStorage.js      # Generic localStorage hook
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `VITE_ANTHROPIC_API_KEY` | For AI features | Your Anthropic API key from console.anthropic.com |

## Tech Stack

- **React** + **Vite**
- **Tailwind CSS** (Bloomberg terminal design system)
- **Recharts** (equity curve + distribution charts)
- **Anthropic SDK** (Claude AI strategy analysis)
- **jsPDF** + **html2canvas** + **jspdf-autotable** (client-side PDF)
- **React Router** (SPA routing)
- **localStorage** (full session persistence)
