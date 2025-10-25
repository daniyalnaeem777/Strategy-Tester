# tp_sl_calculator.py — TP/SL (Live + Backtest) with PDF report (no CSV), polished UI
# - Table is HTML-rendered (no Streamlit toolbar), single "Serial Number" column
# - Only "Extract Report (PDF)" action under the table
# - Helvetica everywhere, compact single-border sections

from datetime import datetime
from io import BytesIO
from math import sqrt
from pathlib import Path
import json
import pandas as pd
import streamlit as st

# Optional libs (install in requirements.txt): pandas, matplotlib, reportlab
try:
    import matplotlib.pyplot as plt
except ModuleNotFoundError:
    plt = None

try:
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
    from reportlab.lib import colors
    REPORTLAB_OK = True
except Exception:
    REPORTLAB_OK = False

# ---------------- Page & Style ----------------
st.set_page_config(page_title="TP/SL Calculator", page_icon="📈", layout="wide")
st.markdown("""
<style>
  * { font-family: Helvetica, Arial, sans-serif !important; }
  h1,h2,h3,h4,strong,b { font-weight:700 !important; letter-spacing:.2px; }
  .subtitle { font-style: italic; margin-top:-6px; margin-bottom:14px; }
  [data-testid="stContainer"] > div[style*="border: 1px solid"] {
    border: 1px solid rgba(255,255,255,0.85) !important;
    border-radius: 14px !important;
    padding: 12px 16px !important;
    margin-bottom: 14px !important;
  }
  .chip {
    display:inline-block; padding:6px 10px; border-radius:999px;
    border:1px solid rgba(255,255,255,0.14); margin-right:8px;
  }
  .boldlabel label > div:first-child { font-weight:700 !important; }
  .stNumberInput > div > div > input { font-weight:700; }
  /* Safety net: hide any stray toolbar if a dataframe sneaks in */
  div[data-testid="stDataFrame"] [data-testid="stElementToolbar"] { display:none !important; }
</style>
""", unsafe_allow_html=True)

TP_MULT = 2.0
DEC = 4

# ---------------- State ----------------
if "bt" not in st.session_state:
    st.session_state.bt = {
        "recording": False,
        "session_name": "",
        "start_equity": None,
        "equity": None,
        "trades": [],
        "last_calc": None,
        "summary_ready": False,
        "stamp": None
    }

# ---------------- Persistence (optional local save of sessions) ----------------
SESS_DIR = Path.cwd() / "sessions"
SESS_DIR.mkdir(exist_ok=True)

def _safe_name(name: str) -> str:
    return "".join(ch for ch in (name or "Session").strip().replace(" ", "_")
                   if ch.isalnum() or ch in "._-")[:64]

def _equity_series(start_equity: float, trades: list[dict]) -> list[float]:
    eq = [float(start_equity or 0.0)]
    e = eq[0]
    for t in trades:
        e *= (1.0 + (t["pct_gain"]/100.0))
        eq.append(e)
    return eq

def _pct_tp_sl(entry, sl, tp, side):
    if side == "Long":
        sl_pct = abs((entry - sl) / entry) * 100.0
        tp_pct = abs((tp - entry) / entry) * 100.0
    else:
        sl_pct = abs((sl - entry) / entry) * 100.0
        tp_pct = abs((entry - tp) / entry) * 100.0
    return sl_pct, tp_pct

def _pct_from_exit(entry, exit_price, side):
    return ((exit_price - entry) / entry) * 100.0 if side == "Long" else ((entry - exit_price) / entry) * 100.0

def _compound(dec_pct):
    if st.session_state.bt["equity"] is None:
        st.warning("Start a backtesting session first."); return
    st.session_state.bt["equity"] *= (1.0 + dec_pct)

def _log_trade(result_label, side, entry, atr, sl_mult, sl, tp, rr, exit_price, pct_gain):
    st.session_state.bt["trades"].append({
        "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "result": result_label, "side": side, "entry": entry, "atr": atr,
        "sl_mult": sl_mult, "sl": sl, "tp": tp, "rr": rr,
        "exit_price": exit_price, "pct_gain": pct_gain,
    })

# ---------------- HTML Table (no toolbar) ----------------
def render_trades_table(df: pd.DataFrame):
    try:
        sty = (
            df.style
              .set_table_styles([
                  {"selector":"th","props":"text-align:center; font-weight:700;"},
                  {"selector":"td","props":"text-align:center;"},
              ])
              .hide(axis="index")
        )
    except Exception:
        sty = df.style.set_table_styles([
            {"selector":"th","props":"text-align:center; font-weight:700;"},
            {"selector":"td","props":"text-align:center;"},
        ])
        try: sty = sty.hide_index()
        except Exception: pass
    st.markdown(sty.to_html(), unsafe_allow_html=True)

# ---------------- PDF Builder ----------------
def build_and_offer_pdf(display_df: pd.DataFrame, trades_internal: pd.DataFrame):
    if not REPORTLAB_OK or plt is None:
        st.error("Please add `reportlab` and `matplotlib` to requirements.txt to export PDF.")
        return

    # Metrics
    wins = (trades_internal["pct_gain"] >= 0).sum()
    losses = (trades_internal["pct_gain"] < 0).sum()
    total_trades = len(trades_internal)
    win_pct = (wins / total_trades * 100.0) if total_trades else 0.0
    rets = [x/100.0 for x in trades_internal["pct_gain"].tolist()]
    sharpe = 0.0
    if rets:
        mu = sum(rets)/len(rets)
        var = sum((r-mu)**2 for r in rets) / max(len(rets)-1, 1)
        sd = var**0.5
        sharpe = (mu/sd * (len(rets)**0.5)) if sd > 0 else 0.0

    start_eq = float(st.session_state.bt["start_equity"] or 0.0)
    eq_vals = _equity_series(start_eq, st.session_state.bt["trades"])

    # Pie (white)
    fig_pie, axp = plt.subplots(figsize=(7,4))
    fig_pie.patch.set_facecolor("white"); axp.set_facecolor("white")
    wedges, _, _ = axp.pie([wins, losses], colors=["#00c853","#ff1744"],
                           autopct=lambda p:f"{p:.1f}%", startangle=90,
                           textprops={"color":"black","weight":"bold"})
    axp.axis("equal")
    axp.legend(wedges, ["Wins","Losses"], loc="center left", bbox_to_anchor=(1.02, 0.5))
    pie_buf = BytesIO(); fig_pie.savefig(pie_buf, format="png", bbox_inches="tight", dpi=200); plt.close(fig_pie); pie_buf.seek(0)

    # Equity (white)
    fig_eq, axe = plt.subplots(figsize=(10,3.5))
    fig_eq.patch.set_facecolor("white"); axe.set_facecolor("white")
    axe.plot(range(len(eq_vals)), eq_vals, marker='o')
    axe.set_xlabel("Number of Trades"); axe.set_ylabel("Account Size"); axe.grid(alpha=0.25)
    eq_buf = BytesIO(); fig_eq.savefig(eq_buf, format="png", bbox_inches="tight", dpi=200); plt.close(fig_eq); eq_buf.seek(0)

    # Rows (exactly as displayed)
    rows = [list(display_df.columns)]
    for _, r in display_df.iterrows():
        rows.append([r[c] for c in display_df.columns])

    # PDF
    pdf_buf = BytesIO()
    doc = SimpleDocTemplate(pdf_buf, leftMargin=18, rightMargin=18, topMargin=18, bottomMargin=18)
    styles = getSampleStyleSheet()
    body = ParagraphStyle("Body", parent=styles["Normal"], fontName="Helvetica",
                          fontSize=12, leading=15, alignment=TA_JUSTIFY)
    h_center = ParagraphStyle("HCenter", parent=styles["Heading1"], fontName="Helvetica-Bold",
                              fontSize=16, leading=18, alignment=TA_CENTER, spaceAfter=8)
    h_sub = ParagraphStyle("HSub", parent=styles["Heading2"], fontName="Helvetica-Bold",
                           fontSize=13, leading=16, alignment=TA_JUSTIFY, spaceBefore=6, spaceAfter=6)

    story = []
    story.append(Paragraph("Backtesting Performance Metrics", h_center))
    story.append(Spacer(0, 6))

    story.append(Paragraph("Trades", h_sub))
    tbl = Table(rows, repeatRows=1)
    tbl.setStyle(TableStyle([
        ("FONT", (0,0), (-1,-1), "Helvetica", 12),
        ("BACKGROUND", (0,0), (-1,0), colors.whitesmoke),
        ("TEXTCOLOR", (0,0), (-1,0), colors.black),
        ("ALIGN", (0,0), (-1,0), "CENTER"),
        ("ALIGN", (0,1), (-1,-1), "CENTER"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("INNERGRID", (0,0), (-1,-1), 0.25, colors.grey),
        ("BOX", (0,0), (-1,-1), 0.5, colors.grey),
    ]))
    story.append(tbl)
    story.append(Spacer(0, 10))

    end_eq = eq_vals[-1] if eq_vals else start_eq
    kpis = (
        f"Total Trades: <b>{total_trades}</b> • Wins: <b>{wins}</b> • Losses: <b>{losses}</b><br/>"
        f"Winning Percentage: <b>{win_pct:.1f}%</b> • Sharpe (per-trade): <b>{sharpe:.2f}</b><br/>"
        f"Start Equity: <b>{start_eq:.2f}</b> • End Equity: <b>{end_eq:.2f}</b>"
    )
    story.append(Paragraph("Summary", h_sub))
    story.append(Paragraph(kpis, body))
    story.append(Spacer(0, 8))

    story.append(Paragraph("Win / Loss Breakdown", h_sub))
    story.append(RLImage(pie_buf, width=450, height=250))
    story.append(Spacer(0, 6))
    story.append(Paragraph("Legend: Green = Wins, Red = Losses.", body))
    story.append(Spacer(0, 8))

    story.append(Paragraph("Equity Curve", h_sub))
    story.append(RLImage(eq_buf, width=500, height=170))
    story.append(Spacer(0, 6))

    doc.build(story); pdf_buf.seek(0)

    session_name = _safe_name(st.session_state.bt.get("session_name") or "Session")
    stamp = st.session_state.bt.get("stamp") or datetime.now().strftime("%Y%m%d_%H%M%S")

    st.download_button(
        "⬇️ Download Report (PDF)",
        data=pdf_buf,
        file_name=f"{session_name}__{stamp}_report.pdf",
        mime="application/pdf",
        use_container_width=True
    )

# ---------------- Header ----------------
st.markdown("# TP/SL Calculator")
st.markdown(
    "<div class='subtitle'>Live & Backtest • Realistic Compounding • Precision-Engineered Strategy Execution</div>",
    unsafe_allow_html=True
)

# ---------------- Mode ----------------
with st.container(border=True):
    mode = st.radio("Mode", ["Live", "Backtest"], horizontal=True)

# ---------------- LIVE ----------------
if mode == "Live":
    with st.container(border=True):
        st.markdown("### **Direction**")
        st.markdown("<div class='boldlabel'>", unsafe_allow_html=True)
        side_live = st.radio("Direction", ["Long", "Short"], horizontal=True, label_visibility="collapsed")
        st.markdown("</div>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("### **SL Multiple**")
        sl_choice_live = st.radio("SL × ATR", ["1.0", "1.5"], horizontal=True, label_visibility="collapsed")
        sl_mult_live = 1.0 if sl_choice_live == "1.0" else 1.5
        st.markdown(
            f"<span class='chip'>Current SL = {sl_mult_live} × ATR</span>"
            f"<span class='chip'>TP = {TP_MULT} × ATR</span>",
            unsafe_allow_html=True
        )

    with st.container(border=True):
        c1, c2 = st.columns(2)
        with c1:
            entry_live = st.number_input("Entry Price", min_value=0.0, format=f'%.{DEC}f')
        with c2:
            atr_live = st.number_input("ATR (14)", min_value=0.0, format=f'%.{DEC}f')

    with st.container(border=True):
        if st.button("Calculate"):
            if entry_live <= 0 or atr_live <= 0:
                st.error("Please enter positive numbers for Entry and ATR.")
            else:
                if side_live == "Long":
                    sl = entry_live - sl_mult_live * atr_live
                    tp = entry_live + TP_MULT * atr_live
                    rr = (tp - entry_live) / max(entry_live - sl, 1e-12)
                    dsl, dtp = entry_live - sl, tp - entry_live
                else:
                    sl = entry_live + sl_mult_live * atr_live
                    tp = entry_live - TP_MULT * atr_live
                    rr = (entry_live - tp) / max(sl - entry_live, 1e-12)
                    dsl, dtp = sl - entry_live, entry_live - tp
                sl_pct, tp_pct = _pct_tp_sl(entry_live, sl, tp, side_live)

                a, b, c = st.columns([1,1,1])
                with a:
                    st.markdown("**Stop Loss**"); st.error(f"**{sl:.{DEC}f}**")
                    st.caption(f"Δ {dsl:.{DEC}f} ({sl_pct:.2f}%)")
                with b:
                    st.markdown("**Take Profit**"); st.success(f"**{tp:.{DEC}f}**")
                    st.caption(f"Δ {dtp:.{DEC}f} ({tp_pct:.2f}%)")
                with c:
                    st.markdown("**Reward : Risk**"); st.info(f"**{rr:.2f} : 1**")

# ---------------- BACKTEST ----------------
if mode == "Backtest":
    # Controls
    with st.container(border=True):
        st.markdown("### **Backtesting Controls**")
        c1, c2 = st.columns([2,1])
        with c1:
            st.session_state.bt["session_name"] = st.text_input(
                "Session Name", value=st.session_state.bt.get("session_name",""),
                placeholder="e.g., BTC_1H_TrendPullback"
            )
        with c2:
            if not st.session_state.bt.get("stamp"):
                st.session_state.bt["stamp"] = datetime.now().strftime("%Y%m%d_%H%M%S")
        start_equity = st.number_input("Account Size (Starting Equity)", min_value=0.0,
                                       value=float(st.session_state.bt["start_equity"] or 0.0),
                                       step=100.0, format="%.2f")
        c3, c4 = st.columns([1,1])
        with c3:
            start_clicked = st.button("Start Session", use_container_width=True)
        with c4:
            end_clicked = st.button("End Session", use_container_width=True)

        if start_clicked:
            if start_equity <= 0:
                st.error("Please enter a positive account size.")
            else:
                st.session_state.bt.update({
                    "recording": True, "start_equity": start_equity, "equity": start_equity,
                    "trades": [], "summary_ready": False, "last_calc": None,
                    "stamp": datetime.now().strftime("%Y%m%d_%H%M%S")
                })
                st.success("Backtesting started.")

        if end_clicked:
            if st.session_state.bt["recording"]:
                st.session_state.bt["recording"] = False
                st.session_state.bt["summary_ready"] = True
                st.info("Backtesting ended. Summary below.")
            else:
                st.info("No active session to end.")

    # Calculator
    with st.container(border=True):
        st.markdown("**Direction**")
        st.markdown("<div class='boldlabel'>", unsafe_allow_html=True)
        side = st.radio("Direction", ["Long", "Short"], horizontal=True, label_visibility="collapsed")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("**SL Multiple**")
        sl_choice = st.radio("SL × ATR", ["1.0", "1.5"], horizontal=True, label_visibility="collapsed")
        sl_mult = 1.0 if sl_choice == "1.0" else 1.5
        st.markdown(
            f"<span class='chip'>Current SL = {sl_mult} × ATR</span>"
            f"<span class='chip'>TP = {TP_MULT} × ATR</span>",
            unsafe_allow_html=True
        )

        c1, c2 = st.columns(2)
        with c1:
            entry = st.number_input("Entry Price", min_value=0.0, format=f'%.{DEC}f')
        with c2:
            atr = st.number_input("ATR (14)", min_value=0.0, format=f'%.{DEC}f')

        if entry > 0 and atr > 0:
            if side == "Long":
                sl = entry - sl_mult * atr; tp = entry + TP_MULT * atr
                rr = (tp - entry) / max(entry - sl, 1e-12)
                dsl, dtp = entry - sl, tp - entry
            else:
                sl = entry + sl_mult * atr; tp = entry - TP_MULT * atr
                rr = (entry - tp) / max(sl - entry, 1e-12)
                dsl, dtp = sl - entry, entry - tp
            sl_pct, tp_pct = _pct_tp_sl(entry, sl, tp, side)

            a, b, c = st.columns([1,1,1])
            with a:
                st.markdown("**Stop Loss**"); st.error(f"**{sl:.{DEC}f}**")
                st.caption(f"Δ {dsl:.{DEC}f} ({sl_pct:.2f}%)")
            with b:
                st.markdown("**Take Profit**"); st.success(f"**{tp:.{DEC}f}**")
                st.caption(f"Δ {dtp:.{DEC}f} ({tp_pct:.2f}%)")
            with c:
                st.markdown("**Reward : Risk**"); st.info(f"**{rr:.2f} : 1**")

            st.session_state.bt["last_calc"] = {
                "side": side, "entry": entry, "atr": atr,
                "sl_mult": sl_mult, "sl": sl, "tp": tp, "rr": rr,
                "sl_pct": sl_pct, "tp_pct": tp_pct
            }

            st.markdown("---")
            st.markdown("**Record Trade**")
            exit_price = st.number_input("Exit Price (for Closed at 'Selected Price')",
                                         min_value=0.0, format=f'%.{DEC}f')

            r1, r2, r3 = st.columns(3)
            with r1:
                if st.button("Record Win ✅", use_container_width=True,
                             disabled=not st.session_state.bt["recording"]):
                    calc = st.session_state.bt["last_calc"]
                    _compound(calc["tp_pct"]/100.0)
                    _log_trade("WIN", calc["side"], calc["entry"], calc["atr"], calc["sl_mult"],
                               calc["sl"], calc["tp"], calc["rr"], None, calc["tp_pct"])
                    st.success("Recorded full TP win.")
            with r2:
                if st.button("Record Loss ❌", use_container_width=True,
                             disabled=not st.session_state.bt["recording"]):
                    calc = st.session_state.bt["last_calc"]
                    _compound(-(calc["sl_pct"]/100.0))
                    _log_trade("LOSS", calc["side"], calc["entry"], calc["sl_mult"],
                               calc["sl"], calc["tp"], calc["rr"], None, -calc["sl_pct"])
                    st.warning("Recorded full SL loss.")
            with r3:
                if st.button("Closed at 'Selected Price'", use_container_width=True,
                             disabled=not st.session_state.bt["recording"]):
                    if exit_price <= 0:
                        st.error("Enter a valid Exit Price.")
                    else:
                        calc = st.session_state.bt["last_calc"]
                        pct = _pct_from_exit(calc["entry"], exit_price, calc["side"])
                        _compound(pct/100.0)
                        _log_trade("CLOSED", calc["side"], calc["entry"], calc["atr"], calc["sl_mult"],
                                   calc["sl"], calc["tp"], calc["rr"], exit_price, pct)
                        st.info(f"Recorded CLOSED at {exit_price:.{DEC}f} ({'▲' if pct>=0 else '▼'}{abs(pct):.2f}%).")
        else:
            st.info("Enter **Entry** and **ATR** to see TP/SL and record trades.")

    # ------------- Summary (after End Session) -------------
    if st.session_state.bt["summary_ready"]:
        internal = pd.DataFrame(st.session_state.bt["trades"])
        if not internal.empty:
            # Build display table once with a single Serial Number column
            disp = internal.copy()
            disp.insert(0, "Serial Number", range(1, len(disp) + 1))
            disp = disp[[
                "Serial Number","ts","result","side","entry","atr",
                "sl_mult","sl","tp","rr","exit_price","pct_gain"
            ]].rename(columns={
                "ts":"Time","result":"Result","side":"Side","entry":"Entry","atr":"ATR",
                "sl_mult":"SL Multiple","sl":"Stop Loss","tp":"Take Profit",
                "rr":"Risk/Return","exit_price":"Exit Price","pct_gain":"% Gain"
            })

            with st.container(border=True):
                st.markdown("### **Trades**")
                render_trades_table(disp)  # HTML table — no toolbar, no CSV
                if st.button("Extract Report (PDF)", use_container_width=True, key="extract_pdf"):
                    build_and_offer_pdf(disp, internal)

    # -------- In-app Charts --------
    wins = sum(1 for t in st.session_state.bt["trades"] if t["pct_gain"] >= 0)
    losses = sum(1 for t in st.session_state.bt["trades"] if t["pct_gain"] < 0)

    with st.container(border=True):
        st.markdown("### **Win / Loss Breakdown**")
        if plt is None:
            st.error("Matplotlib required for pie chart.")
        else:
            fig, ax = plt.subplots(figsize=(12, 6))
            fig.patch.set_facecolor("black"); ax.set_facecolor("black")
            fig.subplots_adjust(left=0.05, right=0.78, top=0.95, bottom=0.06)
            wedges, _, _ = ax.pie([wins, losses], labels=None,
                                  colors=["#00c853", "#ff1744"],
                                  autopct=lambda p: f"{p:.1f}%",
                                  startangle=90,
                                  textprops={"color":"white","weight":"bold"})
            ax.axis("equal")
            ax.legend(wedges, ["Wins","Losses"], loc="center left",
                      bbox_to_anchor=(1.02, 0.5), frameon=False, labelcolor="white")
            st.pyplot(fig, use_container_width=True)

    with st.container(border=True):
        st.markdown("### **Equity Curve**")
        if plt is None:
            st.info("Install matplotlib to view equity curve.")
        else:
            eq = _equity_series(st.session_state.bt["start_equity"] or 0.0,
                                st.session_state.bt["trades"])
            fig2, ax2 = plt.subplots(figsize=(12, 4))
            ax2.plot(range(len(eq)), eq, marker='o')
            ax2.set_xlabel("Trades"); ax2.set_ylabel("Account Value"); ax2.grid(alpha=0.25)
            st.pyplot(fig2, use_container_width=True)
