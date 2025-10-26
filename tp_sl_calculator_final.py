# ================================================================
# TP/SL Calculator (Live + Backtest) — Stable Final w/ Δ and PDF
# ================================================================
# UI: Helvetica, single-rectangle sections
# Logic: realistic compounding (full capital each trade)
# Summary/charts appear ONLY after "End Session"
# PDF: standard margins, Helvetica 12, centered bold headings,
#      justified body, bold table headers, labeled equity axes
# ================================================================

import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO

# Optional plotting / PDF libs
try:
    import matplotlib.pyplot as plt
except Exception:
    plt = None

try:
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
    from reportlab.lib import colors
    REPORTLAB_OK = True
except Exception:
    REPORTLAB_OK = False

# ---------- Page ----------
st.set_page_config(page_title="TP/SL Calculator", page_icon="📈", layout="wide")

# ---------- CSS ----------
st.markdown("""
<style>
  * { font-family: Helvetica, Arial, sans-serif !important; }
  h1,h2,h3,h4,strong,b { font-weight: 700 !important; letter-spacing:.2px; }
  .subtitle { font-style: italic; margin-top:-6px; margin-bottom:14px; }
  [data-testid="stContainer"] > div[style*="border: 1px solid"] {
    border: 1px solid rgba(255,255,255,0.85) !important;
    border-radius: 14px !important;
    padding: 12px 16px !important;
    margin-bottom: 14px !important;
  }
  .stNumberInput > div > div > input { font-weight:700; }
  .chip {
    display:inline-block; padding:6px 10px; border-radius:999px;
    border:1px solid rgba(255,255,255,0.14); margin-right:8px;
  }
</style>
""", unsafe_allow_html=True)

TP_MULT = 2.0
DEC = 4

# ---------- State ----------
if "bt" not in st.session_state:
    st.session_state.bt = {
        "recording": False,
        "start_equity": None,
        "equity": None,
        "trades": [],
        "last_calc": None,
        "summary_ready": False,
    }

# ---------- Helpers ----------
def _pct_to_tp_sl(entry, sl, tp, side):
    if side == "Long":
        sl_pct = abs((entry - sl) / entry) * 100.0
        tp_pct = abs((tp - entry) / entry) * 100.0
        dsl = entry - sl
        dtp = tp - entry
    else:
        sl_pct = abs((sl - entry) / entry) * 100.0
        tp_pct = abs((entry - tp) / entry) * 100.0
        dsl = sl - entry
        dtp = entry - tp
    return dsl, dtp, sl_pct, tp_pct

def _pct_from_exit(entry, exit_price, side):
    return ((exit_price - entry) / entry) * 100.0 if side == "Long" else ((entry - exit_price) / entry) * 100.0

def _compound(dec_pct):
    if st.session_state.bt["equity"] is None:
        return
    st.session_state.bt["equity"] *= (1.0 + dec_pct)

def _log_trade(result_label, side, entry, atr, sl_mult, sl, tp, rr, exit_price, pct_gain):
    st.session_state.bt["trades"].append({
        "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "result": result_label,
        "side": side,
        "entry": entry,
        "atr": atr,
        "sl_mult": sl_mult,
        "sl": sl,
        "tp": tp,
        "rr": rr,
        "exit_price": exit_price,
        "pct_gain": pct_gain,
    })

def _equity_series(start_equity, trades):
    eq = [start_equity]
    e = start_equity
    for t in trades:
        e *= (1.0 + (t["pct_gain"] / 100.0))
        eq.append(e)
    return eq

# ---------- Title ----------
st.markdown("# TP/SL Calculator")
st.markdown(
    "<div class='subtitle'>Live & Backtest • Realistic Compounding • Precision-Engineered Strategy Execution</div>",
    unsafe_allow_html=True
)

# ================== Mode ==================
with st.container(border=True):
    mode = st.radio("Mode", ["Live", "Backtest"], horizontal=True)

# ================== LIVE ==================
if mode == "Live":
    with st.container(border=True):
        st.markdown("### **Direction**")
        side_live = st.radio("Direction", ["Long", "Short"], horizontal=True, label_visibility="collapsed")

    with st.container(border=True):
        st.markdown("### **SL Multiple**")
        sl_choice_live = st.radio("SL × ATR", ["1.0", "1.5"], horizontal=True, label_visibility="collapsed")
        sl_mult_live = float(sl_choice_live)
        st.markdown(
            f"<span class='chip'>Current SL = {sl_mult_live} × ATR</span>"
            f"<span class='chip'>TP = {TP_MULT} × ATR</span>",
            unsafe_allow_html=True
        )

    with st.container(border=True):
        c1, c2 = st.columns(2)
        with c1:
            entry_live = st.number_input("Entry Price", min_value=0.0, format=f"%.{DEC}f")
        with c2:
            atr_live = st.number_input("ATR (14)", min_value=0.0, format=f"%.{DEC}f")

    with st.container(border=True):
        if st.button("Calculate"):
            if entry_live > 0 and atr_live > 0:
                if side_live == "Long":
                    sl = entry_live - sl_mult_live * atr_live
                    tp = entry_live + TP_MULT * atr_live
                    rr = (tp - entry_live) / max(entry_live - sl, 1e-12)
                else:
                    sl = entry_live + sl_mult_live * atr_live
                    tp = entry_live - TP_MULT * atr_live
                    rr = (entry_live - tp) / max(sl - entry_live, 1e-12)

                dsl, dtp, sl_pct, tp_pct = _pct_to_tp_sl(entry_live, sl, tp, side_live)

                a, b, c = st.columns(3)
                with a:
                    st.markdown("**Stop Loss**")
                    st.error(f"**{sl:.{DEC}f}**")
                    st.caption(f"Δ {dsl:.{DEC}f} ({sl_pct:.2f}%)")
                with b:
                    st.markdown("**Take Profit**")
                    st.success(f"**{tp:.{DEC}f}**")
                    st.caption(f"Δ {dtp:.{DEC}f} ({tp_pct:.2f}%)")
                with c:
                    st.markdown("**Reward : Risk**")
                    st.info(f"**{rr:.2f} : 1**")

# ================== BACKTEST ==================
if mode == "Backtest":

    # ---- Controls ----
    with st.container(border=True):
        st.markdown("### **Backtesting Controls**")
        start_equity = st.number_input("Account Size (Starting Equity)", min_value=0.0, step=100.0, format="%.2f")
        colA, colB = st.columns(2)
        with colA:
            start_clicked = st.button("Start Session", use_container_width=True)
        with colB:
            end_clicked = st.button("End Session", use_container_width=True)

        if start_clicked:
            if start_equity > 0:
                st.session_state.bt.update({
                    "recording": True,
                    "start_equity": start_equity,
                    "equity": start_equity,
                    "trades": [],
                    "summary_ready": False
                })
                st.success("Backtesting started.")

        if end_clicked:
            st.session_state.bt["recording"] = False
            st.session_state.bt["summary_ready"] = True
            st.info("Backtesting ended. Summary shown below.")

    # ---- Trade input & record (only while recording) ----
    if st.session_state.bt["recording"]:
        with st.container(border=True):
            st.markdown("### **Record Trade**")

            side = st.radio("Direction", ["Long", "Short"], horizontal=True, key="bt_side")
            sl_choice = st.radio("SL × ATR", ["1.0", "1.5"], horizontal=True, label_visibility="collapsed", key="bt_sl")
            sl_mult = float(sl_choice)

            c1, c2 = st.columns(2)
            with c1:
                entry = st.number_input("Entry Price", min_value=0.0, format=f"%.{DEC}f", key="bt_entry")
            with c2:
                atr = st.number_input("ATR (14)", min_value=0.0, format=f"%.{DEC}f", key="bt_atr")

            if entry > 0 and atr > 0:
                if side == "Long":
                    sl = entry - sl_mult * atr
                    tp = entry + TP_MULT * atr
                    rr = (tp - entry) / max(entry - sl, 1e-12)
                else:
                    sl = entry + sl_mult * atr
                    tp = entry - TP_MULT * atr
                    rr = (entry - tp) / max(sl - entry, 1e-12)

                dsl, dtp, sl_pct, tp_pct = _pct_to_tp_sl(entry, sl, tp, side)

                a, b, c = st.columns(3)
                with a:
                    st.markdown("**Stop Loss**")
                    st.error(f"**{sl:.{DEC}f}**")
                    st.caption(f"Δ {dsl:.{DEC}f} ({sl_pct:.2f}%)")
                with b:
                    st.markdown("**Take Profit**")
                    st.success(f"**{tp:.{DEC}f}**")
                    st.caption(f"Δ {dtp:.{DEC}f} ({tp_pct:.2f}%)")
                with c:
                    st.markdown("**Reward : Risk**")
                    st.info(f"**{rr:.2f} : 1**")

                st.session_state.bt["last_calc"] = {
                    "side": side, "entry": entry, "atr": atr,
                    "sl_mult": sl_mult, "sl": sl, "tp": tp, "rr": rr,
                    "dsl": dsl, "dtp": dtp, "sl_pct": sl_pct, "tp_pct": tp_pct
                }

                st.markdown("---")
                exit_price = st.number_input("Exit Price (for Closed at 'Selected Price')",
                                             min_value=0.0, format=f"%.{DEC}f")

                r1, r2, r3 = st.columns(3)
                with r1:
                    if st.button("Record Win ✅", use_container_width=True):
                        calc = st.session_state.bt["last_calc"]
                        _compound(calc["tp_pct"] / 100.0)
                        _log_trade("WIN", calc["side"], calc["entry"], calc["atr"], calc["sl_mult"],
                                   calc["sl"], calc["tp"], calc["rr"], None, calc["tp_pct"])
                        st.success("Recorded WIN.")
                with r2:
                    if st.button("Record Loss ❌", use_container_width=True):
                        calc = st.session_state.bt["last_calc"]
                        _compound(-(calc["sl_pct"] / 100.0))
                        _log_trade("LOSS", calc["side"], calc["entry"], calc["atr"], calc["sl_mult"],
                                   calc["sl"], calc["tp"], calc["rr"], None, -calc["sl_pct"])
                        st.warning("Recorded LOSS.")
                with r3:
                    if st.button("Closed at 'Selected Price'", use_container_width=True):
                        if exit_price > 0:
                            calc = st.session_state.bt["last_calc"]
                            pct = _pct_from_exit(calc["entry"], exit_price, calc["side"])
                            _compound(pct / 100.0)
                            _log_trade("CLOSED", calc["side"], calc["entry"], calc["atr"], calc["sl_mult"],
                                       calc["sl"], calc["tp"], calc["rr"], exit_price, pct)
                            st.info(f"Recorded CLOSED ({pct:.2f}%).")

    # ---- Summary (only AFTER End Session) ----
    if st.session_state.bt["summary_ready"] and st.session_state.bt["trades"]:
        trades = pd.DataFrame(st.session_state.bt["trades"])
        trades.insert(0, "Serial Number", range(1, len(trades) + 1))
        trades = trades.rename(columns={
            "ts": "Time", "result": "Result", "side": "Side", "entry": "Entry",
            "atr": "ATR", "sl_mult": "SL Multiple", "sl": "Stop Loss",
            "tp": "Take Profit", "rr": "Risk/Return", "exit_price": "Exit Price",
            "pct_gain": "% Gain"
        })

        with st.container(border=True):
            st.markdown("### **Trades Table**")
            st.dataframe(trades, use_container_width=True)

            wins = (trades["% Gain"] >= 0).sum()
            total = len(trades)
            win_pct = (wins / total * 100.0) if total > 0 else 0.0

            st.markdown("### **Total Number of Trades**")
            st.write(f"**Total Trades:** {total}")
            st.write(f"**Winning Trades:** {wins}")
            st.write(f"**Winning Percentage:** {win_pct:.2f}%")

            # Equity curve
            eq_fig = None
            if plt is not None:
                eq_vals = _equity_series(st.session_state.bt["start_equity"], st.session_state.bt["trades"])
                fig, ax = plt.subplots(figsize=(10, 4))
                ax.plot(range(len(eq_vals)), eq_vals, marker='o')
                ax.set_xlabel("Number of Trades")
                ax.set_ylabel("Account Size")
                ax.grid(alpha=0.25)
                st.pyplot(fig, use_container_width=True)
                eq_fig = fig

            # PDF Export
            if st.button("Extract Report (PDF)", use_container_width=True):
                if not REPORTLAB_OK or plt is None or eq_fig is None:
                    st.error("Install `reportlab` + `matplotlib` to export the PDF.")
                else:
                    # Save equity fig to buffer
                    buf_eq = BytesIO()
                    eq_fig.savefig(buf_eq, format="png", bbox_inches="tight", dpi=200)
                    buf_eq.seek(0)

                    # Build PDF (standard margins = 1in/72pt)
                    pdf_buf = BytesIO()
                    doc = SimpleDocTemplate(
                        pdf_buf,
                        leftMargin=72, rightMargin=72, topMargin=72, bottomMargin=72
                    )
                    styles = getSampleStyleSheet()
                    h_center = ParagraphStyle(
                        "HCenter", parent=styles["Heading1"], fontName="Helvetica-Bold",
                        fontSize=16, leading=18, alignment=TA_CENTER, spaceAfter=8
                    )
                    h_sub = ParagraphStyle(
                        "HSub", parent=styles["Heading2"], fontName="Helvetica-Bold",
                        fontSize=13, leading=16, alignment=TA_CENTER, spaceBefore=6, spaceAfter=6
                    )
                    body = ParagraphStyle(
                        "Body", parent=styles["Normal"], fontName="Helvetica",
                        fontSize=12, leading=15, alignment=TA_JUSTIFY
                    )

                    # Table rows
                    rows = [list(trades.columns)] + trades.values.tolist()

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

                    story = []
                    story.append(Paragraph("Backtesting Performance Metrics", h_center))
                    story.append(Spacer(0, 10))

                    story.append(Paragraph("Trades Table", h_sub))
                    story.append(tbl)
                    story.append(Spacer(0, 12))

                    # Summary block
                    summary_html = (
                        f"Total Trades: <b>{total}</b><br/>"
                        f"Winning Trades: <b>{wins}</b><br/>"
                        f"Winning Percentage: <b>{win_pct:.2f}%</b>"
                    )
                    story.append(Paragraph(summary_html, body))
                    story.append(Spacer(0, 16))

                    story.append(Paragraph("Equity Curve", h_sub))
                    story.append(RLImage(buf_eq, width=500, height=170))
                    story.append(Spacer(0, 6))

                    doc.build(story)
                    pdf_buf.seek(0)

                    st.download_button(
                        "⬇️ Download Report (PDF)",
                        data=pdf_buf,
                        file_name="Backtesting_Report.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
