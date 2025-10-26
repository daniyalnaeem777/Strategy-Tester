# ================================================================
# TP/SL Calculator (Live + Backtest) — Final
# - Δ price/% under SL/TP
# - Summary only after End Session (no mid-session charts/tables)
# - Professional PDF export (landscape, Helvetica 12, justified)
# - Status panel + progress bar during PDF build
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
    from reportlab.lib.pagesizes import letter, landscape
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

# ---------- PDF builder (professional layout) ----------
def _fmt_num(x, nd=2):
    try:
        return f"{float(x):,.{nd}f}"
    except Exception:
        return str(x)

def build_backtest_pdf(trades_df: pd.DataFrame, start_equity: float, eq_fig) -> BytesIO:
    """
    Build a professional PDF:
    - Landscape letter, 1" margins
    - Helvetica 12, centered bold headings, justified body
    - Clean, banded table with formatted numeric values
    """
    df = trades_df.copy()

    # Ensure consistent column order
    cols = ["Serial Number","Time","Result","Side","Entry","ATR","SL Multiple",
            "Stop Loss","Take Profit","Risk/Return","Exit Price","% Gain"]
    df = df[cols]

    # Replace NaNs in Exit Price with 'None', format numerics/percentages
    df["Entry"]       = df["Entry"].apply(lambda v: _fmt_num(v, 4))
    df["ATR"]         = df["ATR"].apply(lambda v: _fmt_num(v, 4))
    df["SL Multiple"] = df["SL Multiple"].apply(lambda v: _fmt_num(v, 2))
    df["Stop Loss"]   = df["Stop Loss"].apply(lambda v: _fmt_num(v, 4))
    df["Take Profit"] = df["Take Profit"].apply(lambda v: _fmt_num(v, 4))
    df["Risk/Return"] = df["Risk/Return"].apply(lambda v: _fmt_num(v, 2))
    df["Exit Price"]  = df["Exit Price"].apply(lambda v: "None" if pd.isna(v) else _fmt_num(v, 4))
    df["% Gain"]      = df["% Gain"].apply(lambda v: f"{float(v):.2f}%")

    table_rows = [cols] + df.values.tolist()

    # Equity fig to buffer
    buf_eq = BytesIO()
    eq_fig.savefig(buf_eq, format="png", bbox_inches="tight", dpi=200)
    buf_eq.seek(0)

    pdf_buf = BytesIO()
    doc = SimpleDocTemplate(
        pdf_buf,
        pagesize=landscape(letter),
        leftMargin=72, rightMargin=72, topMargin=72, bottomMargin=72
    )

    styles = getSampleStyleSheet()
    H1 = ParagraphStyle("H1", parent=styles["Heading1"], fontName="Helvetica-Bold",
                        fontSize=16, leading=18, alignment=TA_CENTER, spaceAfter=10)
    H2 = ParagraphStyle("H2", parent=styles["Heading2"], fontName="Helvetica-Bold",
                        fontSize=13, leading=16, alignment=TA_CENTER, spaceBefore=8, spaceAfter=8)
    Body = ParagraphStyle("Body", parent=styles["Normal"], fontName="Helvetica",
                          fontSize=12, leading=15, alignment=TA_JUSTIFY)

    story = []
    story.append(Paragraph("Backtesting Performance Metrics", H1))
    story.append(Spacer(0, 6))

    # Trades table
    story.append(Paragraph("Trades Table", H2))
    col_widths = [  # tuned for landscape letter
        70, 140, 70, 60, 85, 85, 85, 95, 95, 85, 85, 80
    ]
    tbl = Table(table_rows, colWidths=col_widths, repeatRows=1)

    numeric_cols = [4,5,6,7,8,9,10,11]  # indexes in table_rows
    tbl_style = TableStyle([
        ("FONT", (0,0), (-1,-1), "Helvetica", 12),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("BACKGROUND", (0,0), (-1,0), colors.whitesmoke),
        ("TEXTCOLOR", (0,0), (-1,0), colors.black),

        ("ALIGN", (0,0), (-1,0), "CENTER"),      # header
        ("ALIGN", (0,1), (3,-1), "CENTER"),      # text cols centered
    ])
    for c in numeric_cols:
        tbl_style.add("ALIGN", (c,1), (c,-1), "RIGHT")
    tbl_style.add("GRID", (0,0), (-1,-1), 0.25, colors.lightgrey)
    tbl_style.add("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.Color(0.97,0.97,0.97), colors.white])

    tbl.setStyle(tbl_style)
    story.append(tbl)
    story.append(Spacer(0, 12))

    # Summary
    total = len(trades_df)
    wins = sum(1 for x in trades_df["% Gain"] if float(x) >= 0)
    win_pct = (wins/total*100.0) if total else 0.0
    summary_html = (
        f"Total Trades: <b>{total}</b><br/>"
        f"Winning Trades: <b>{wins}</b><br/>"
        f"Winning Percentage: <b>{win_pct:.2f}%</b>"
    )
    story.append(Paragraph("Summary", H2))
    story.append(Paragraph(summary_html, Body))
    story.append(Spacer(0, 16))

    # Equity curve
    story.append(Paragraph("Equity Curve", H2))
    story.append(RLImage(buf_eq, width=700, height=240))
    story.append(Spacer(0, 8))

    doc.build(story)
    pdf_buf.seek(0)
    return pdf_buf

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
        # Build display table
        trades_raw = pd.DataFrame(st.session_state.bt["trades"])
        trades_disp = trades_raw.copy()
        trades_disp.insert(0, "Serial Number", range(1, len(trades_disp) + 1))
        trades_disp = trades_disp.rename(columns={
            "ts": "Time", "result": "Result", "side": "Side", "entry": "Entry",
            "atr": "ATR", "sl_mult": "SL Multiple", "sl": "Stop Loss",
            "tp": "Take Profit", "rr": "Risk/Return", "exit_price": "Exit Price",
            "pct_gain": "% Gain"
        })

        with st.container(border=True):
            st.markdown("### **Trades Table**")
            st.dataframe(trades_disp, use_container_width=True)

            wins = (trades_disp["% Gain"] >= 0).sum()
            total = len(trades_disp)
            win_pct = (wins / total * 100.0) if total > 0 else 0.0

            st.markdown("### **Total Number of Trades**")
            st.write(f"**Total Trades:** {total}")
            st.write(f"**Winning Trades:** {wins}")
            st.write(f"**Winning Percentage:** {win_pct:.2f}%")

            # Equity Curve (and keep a figure handle for PDF)
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

            # -------- Extract Report with Status + Progress --------
            if st.button("Extract Report (PDF)", use_container_width=True):
                if not (REPORTLAB_OK and plt is not None and eq_fig is not None):
                    st.error("Install `reportlab` and `matplotlib` to export the PDF.")
                else:
                    # Prefer st.status if available (1.31+), else fallback to progress+spinner
                    status_ctx = getattr(st, "status", None)
                    if status_ctx is not None:
                        status = st.status("Preparing report…", expanded=True)
                        try:
                            p = st.progress(0, text="Starting…")

                            status.write("Step 1/4: Formatting table")
                            # Slightly reformat display DF for the PDF function
                            p.progress(25, text="Formatting table…")

                            status.write("Step 2/4: Rendering equity curve")
                            # (fig already rendered; nothing to do)
                            p.progress(50, text="Rendering equity curve…")

                            status.write("Step 3/4: Building PDF")
                            pdf_buf = build_backtest_pdf(trades_disp, float(st.session_state.bt["start_equity"]), eq_fig)
                            p.progress(85, text="Building PDF…")

                            status.write("Step 4/4: Finalizing")
                            p.progress(100, text="Done")

                            status.update(label="Report ready ✓", state="complete")
                            st.download_button(
                                "⬇️ Download Report (PDF)",
                                data=pdf_buf,
                                file_name="Backtesting_Report.pdf",
                                mime="application/pdf",
                                use_container_width=True
                            )
                        except Exception as e:
                            status.update(label="Failed ❌", state="error")
                            st.error(str(e))
                    else:
                        # Fallback for older Streamlit
                        progress = st.progress(0, text="Starting…")
                        try:
                            progress.progress(25, text="Formatting table…")
                            progress.progress(50, text="Rendering equity curve…")
                            progress.progress(75, text="Building PDF…")
                            pdf_buf = build_backtest_pdf(trades_disp, float(st.session_state.bt["start_equity"]), eq_fig)
                            progress.progress(100, text="Done")
                            st.success("Report ready ✓")
                            st.download_button(
                                "⬇️ Download Report (PDF)",
                                data=pdf_buf,
                                file_name="Backtesting_Report.pdf",
                                mime="application/pdf",
                                use_container_width=True
                            )
                        except Exception as e:
                            st.error(str(e))
