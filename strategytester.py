# tp_sl_calculator.py — Single-border sections, Helvetica, Live + Backtest
# Long:  SL = Entry − (SL_mult × ATR)   |   TP = Entry + (2.0 × ATR)
# Short: SL = Entry + (SL_mult × ATR)   |   TP = Entry − (2.0 × ATR)

import streamlit as st
from datetime import datetime
import pandas as pd

# Charts
try:
    import matplotlib.pyplot as plt
except ModuleNotFoundError:
    plt = None

st.set_page_config(page_title="TP/SL Calculator", page_icon="📈", layout="centered")

# ========================= CSS =========================
st.markdown("""
<style>
  /* Typography */
  * { font-family: Helvetica, Arial, sans-serif !important; }
  h1,h2,h3,h4,strong,b { font-weight: 700 !important; letter-spacing:.2px; }
  .subtitle { font-style: italic; margin-top:-6px; margin-bottom:14px; }

  /* Single-border sections (only we draw borders) */
  .section {
    border: 1px solid rgba(255,255,255,0.85);
    border-radius: 14px;
    padding: 14px 18px;
    margin: 14px 0;
    background: transparent;
  }

  /* Kill Streamlit's extra wrapper boxes and spacing */
  [data-testid="stVerticalBlock"] > div:not(.section) {
    border: none !important;
    background: transparent !important;
    box-shadow: none !important;
  }
  [data-testid="stVerticalBlock"] > div {
    padding-top: 0 !important;
    padding-bottom: 0 !important;
    margin-top: 0 !important;
    margin-bottom: 0 !important;
  }
  [data-testid="stHorizontalBlock"] > div[style*="border"] {
    border: none !important;
    background: transparent !important;
  }

  /* Bold radio labels for Direction */
  .boldlabel label > div:first-child { font-weight: 700 !important; }

  /* Small “chip” indicators */
  .chip {
    display:inline-block; padding:6px 10px; border-radius:999px;
    border:1px solid rgba(255,255,255,0.14); margin-right:8px;
  }

  /* Inputs a touch bolder */
  .stNumberInput input { font-weight: 700; }
</style>
""", unsafe_allow_html=True)

# ========================= Constants =========================
TP_MULT = 2.0
DEC = 4

# ========================= State =========================
if "bt" not in st.session_state:
    st.session_state.bt = {
        "recording": False,
        "start_equity": None,
        "equity": None,
        "trades": [],          # list of dicts
        "last_calc": None,     # snapshot for record buttons
        "summary_ready": False,
    }

# ========================= Helpers =========================
def _pct_to_tp_sl(entry, sl, tp, side):
    if side == "Long":
        sl_pct = abs((entry - sl) / entry) * 100.0
        tp_pct = abs((tp - entry) / entry) * 100.0
    else:
        sl_pct = abs((sl - entry) / entry) * 100.0
        tp_pct = abs((entry - tp) / entry) * 100.0
    return sl_pct, tp_pct

def _pct_from_exit(entry, exit_price, side):
    if side == "Long":
        return ((exit_price - entry) / entry) * 100.0
    else:
        return ((entry - exit_price) / entry) * 100.0

def _compound(dec_pct):
    """Multiply full equity by (1 + dec_pct); dec_pct is decimal (e.g., +0.018)."""
    if st.session_state.bt["equity"] is None:
        st.warning("Start a backtesting session first.")
        return
    st.session_state.bt["equity"] *= (1.0 + dec_pct)

def _log_trade(result_label, side, entry, atr, sl_mult, sl, tp, rr, exit_price, pct_gain):
    st.session_state.bt["trades"].append({
        "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "result": result_label,         # "WIN" | "LOSS" | "CLOSED"
        "side": side,
        "entry": entry,
        "atr": atr,
        "sl_mult": sl_mult,
        "sl": sl,
        "tp": tp,
        "rr": rr,
        "exit_price": exit_price,       # may be None
        "pct_gain": pct_gain            # signed %
    })

# ========================= UI =========================
st.markdown("# TP/SL Calculator")
st.markdown("<div class='subtitle'>Live & Backtest • realistic compounding • clean single-border layout</div>", unsafe_allow_html=True)

# -------- Mode (single bordered section) --------
st.markdown("<div class='section'>", unsafe_allow_html=True)
mode = st.radio("Mode", ["Live", "Backtest"], horizontal=True, key="mode_radio")
st.markdown("</div>", unsafe_allow_html=True)

# ========================= LIVE =========================
if mode == "Live":
    # Direction
    st.markdown("<div class='section boldlabel'>", unsafe_allow_html=True)
    st.markdown("### **Direction**")
    side_live = st.radio("Direction", ["Long", "Short"], horizontal=True, label_visibility="collapsed", key="live_dir")
    st.markdown("</div>", unsafe_allow_html=True)

    # Stop-Loss Multiple
    st.markdown("<div class='section'>", unsafe_allow_html=True)
    st.markdown("### **Stop-Loss Multiple**")
    sl_choice_live = st.radio("SL × ATR", ["1.0", "1.5"], horizontal=True, label_visibility="collapsed", key="live_sl")
    sl_mult_live = 1.0 if sl_choice_live == "1.0" else 1.5
    st.markdown(
        f"<span class='chip'>Current SL = {sl_mult_live} × ATR</span>"
        f"<span class='chip'>TP = {TP_MULT} × ATR</span>",
        unsafe_allow_html=True
    )
    st.markdown("</div>", unsafe_allow_html=True)

    # Inputs
    st.markdown("<div class='section'>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        entry_live = st.number_input("Entry Price", min_value=0.0, format=f"%.{DEC}f")
    with c2:
        atr_live = st.number_input("ATR (14)", min_value=0.0, format=f"%.{DEC}f")
    st.markdown("</div>", unsafe_allow_html=True)

    # Calculate + Results
    st.markdown("<div class='section'>", unsafe_allow_html=True)
    if st.button("Calculate", key="calc_live"):
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

            sl_pct, tp_pct = _pct_to_tp_sl(entry_live, sl, tp, side_live)

            a, b, c = st.columns(3)
            with a:
                st.markdown("**SL**")
                st.error(f"**{sl:.{DEC}f}**")
                st.caption(f"Δ {dsl:.{DEC}f} ({sl_pct:.2f}%)")
            with b:
                st.markdown("**TP**")
                st.success(f"**{tp:.{DEC}f}**")
                st.caption(f"Δ {dtp:.{DEC}f} ({tp_pct:.2f}%)")
            with c:
                st.markdown("**Reward : Risk**")
                st.info(f"**{rr:.2f} : 1**")
    st.markdown("</div>", unsafe_allow_html=True)

# ========================= BACKTEST =========================
if mode == "Backtest":
    # Controls
    st.markdown("<div class='section'>", unsafe_allow_html=True)
    st.markdown("### **Backtesting Controls**")
    start_equity = st.number_input(
        "Account Size (Starting Equity)",
        min_value=0.0,
        value=float(st.session_state.bt["start_equity"] or 0.0),
        step=100.0,
        format="%.2f",
    )
    start_clicked = st.button("Start Session", use_container_width=True)
    end_clicked   = st.button("End Session",   use_container_width=True)

    if start_clicked:
        if start_equity <= 0:
            st.error("Please enter a positive account size.")
        else:
            st.session_state.bt.update({
                "recording": True,
                "start_equity": start_equity,
                "equity": start_equity,
                "trades": [],
                "summary_ready": False,
                "last_calc": None,
            })
            st.success("Backtesting started.")
    if end_clicked:
        if st.session_state.bt["recording"]:
            st.session_state.bt["recording"] = False
            st.session_state.bt["summary_ready"] = True
            st.info("Backtesting ended. Summary below.")
        else:
            st.info("No active session to end.")
    st.markdown("</div>", unsafe_allow_html=True)

    # Calculator
    st.markdown("<div class='section'>", unsafe_allow_html=True)
    st.markdown("### **Calculator**")

    st.markdown("<div class='boldlabel'>", unsafe_allow_html=True)
    st.markdown("**Direction**")
    side = st.radio("Direction", ["Long", "Short"], horizontal=True, label_visibility="collapsed")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("**Stop-Loss Multiple**")
    sl_choice = st.radio("SL × ATR", ["1.0", "1.5"], horizontal=True, label_visibility="collapsed")
    sl_mult = 1.0 if sl_choice == "1.0" else 1.5
    st.markdown(
        f"<span class='chip'>Current SL = {sl_mult} × ATR</span>"
        f"<span class='chip'>TP = {TP_MULT} × ATR</span>",
        unsafe_allow_html=True
    )

    c1, c2 = st.columns(2)
    with c1:
        entry = st.number_input("Entry Price", min_value=0.0, format=f"%.{DEC}f")
    with c2:
        atr = st.number_input("ATR (14)", min_value=0.0, format=f"%.{DEC}f")

    if entry > 0 and atr > 0:
        if side == "Long":
            sl = entry - sl_mult * atr
            tp = entry + TP_MULT * atr
            rr = (tp - entry) / max(entry - sl, 1e-12)
            dsl, dtp = entry - sl, tp - entry
        else:
            sl = entry + sl_mult * atr
            tp = entry - TP_MULT * atr
            rr = (entry - tp) / max(sl - entry, 1e-12)
            dsl, dtp = sl - entry, entry - tp

        sl_pct, tp_pct = _pct_to_tp_sl(entry, sl, tp, side)

        a, b, c = st.columns(3)
        with a:
            st.markdown("**SL**")
            st.error(f"**{sl:.{DEC}f}**")
            st.caption(f"Δ {dsl:.{DEC}f} ({sl_pct:.2f}%)")
        with b:
            st.markdown("**TP**")
            st.success(f"**{tp:.{DEC}f}**")
            st.caption(f"Δ {dtp:.{DEC}f} ({tp_pct:.2f}%)")
        with c:
            st.markdown("**Reward : Risk**")
            st.info(f"**{rr:.2f} : 1**")

        # Snapshot for record buttons
        st.session_state.bt["last_calc"] = {
            "side": side, "entry": entry, "atr": atr,
            "sl_mult": sl_mult, "sl": sl, "tp": tp, "rr": rr,
            "sl_pct": sl_pct, "tp_pct": tp_pct
        }

        st.markdown("---")
        st.markdown("**Record Trade**")
        exit_price = st.number_input("Exit Price (for 'Closed at selected price')", min_value=0.0, format=f"%.{DEC}f")

        cA, cB, cC = st.columns(3)
        with cA:
            if st.button("Record Win ✅", use_container_width=True, disabled=not st.session_state.bt["recording"]):
                calc = st.session_state.bt["last_calc"]
                _compound(calc["tp_pct"] / 100.0)
                _log_trade("WIN", calc["side"], calc["entry"], calc["atr"], calc["sl_mult"],
                           calc["sl"], calc["tp"], calc["rr"], None, calc["tp_pct"])
                st.success("Recorded full TP win.")
        with cB:
            if st.button("Record Loss ❌", use_container_width=True, disabled=not st.session_state.bt["recording"]):
                calc = st.session_state.bt["last_calc"]
                _compound(-(calc["sl_pct"] / 100.0))
                _log_trade("LOSS", calc["side"], calc["entry"], calc["atr"], calc["sl_mult"],
                           calc["sl"], calc["tp"], calc["rr"], None, -calc["sl_pct"])
                st.warning("Recorded full SL loss.")
        with cC:
            if st.button("Closed at selected price 🟩", use_container_width=True, disabled=not st.session_state.bt["recording"]):
                if exit_price <= 0:
                    st.error("Enter a valid Exit Price.")
                else:
                    calc = st.session_state.bt["last_calc"]
                    pct = _pct_from_exit(calc["entry"], exit_price, calc["side"])  # can be <TP or >TP
                    _compound(pct / 100.0)
                    _log_trade("CLOSED", calc["side"], calc["entry"], calc["atr"], calc["sl_mult"],
                               calc["sl"], calc["tp"], calc["rr"], exit_price, pct)
                    st.info(f"Recorded CLOSED at {exit_price:.{DEC}f} ({'▲' if pct>=0 else '▼'}{abs(pct):.2f}%).")
    else:
        st.info("Enter **Entry** and **ATR** to see levels and record trades.")
    st.markdown("</div>", unsafe_allow_html=True)  # end Calculator section

    # Summary (after End Session)
    if st.session_state.bt["summary_ready"]:
        # Trades table first
        raw = pd.DataFrame(st.session_state.bt["trades"])
        if not raw.empty:
            cols = ["ts","result","side","entry","atr","sl_mult","sl","tp","rr","exit_price","pct_gain"]
            raw = raw[[c for c in cols if c in raw.columns]].copy()
            raw.insert(0, "Serial Number", range(1, len(raw)+1))
            raw = raw.rename(columns={
                "ts": "Time", "result":"Result", "side":"Side", "entry":"Entry", "atr":"ATR",
                "sl_mult":"stop-loss_multiple", "sl":"SL", "tp":"TP", "rr":"Risk/Return",
                "exit_price":"Exit Price", "pct_gain":"Pct Gain"
            })
            st.markdown("<div class='section'>", unsafe_allow_html=True)
            st.markdown("### **Trades**")
            st.dataframe(raw, use_container_width=True)
            st.download_button("⬇️ Download CSV", raw.to_csv(index=False).encode("utf-8"), "backtest_log.csv", "text/csv")
            st.markdown("</div>", unsafe_allow_html=True)

        # Pie chart: black bg, green wins, red losses, bold % inside, key
        wins = sum(1 for t in st.session_state.bt["trades"]
                   if (t["result"] == "WIN") or (t["result"] == "CLOSED" and t["pct_gain"] >= 0))
        losses = sum(1 for t in st.session_state.bt["trades"]
                     if (t["result"] == "LOSS") or (t["result"] == "CLOSED" and t["pct_gain"] < 0))

        st.markdown("<div class='section'>", unsafe_allow_html=True)
        st.markdown("### **Win / Loss Breakdown**")
        if plt is None:
            st.error("Matplotlib is required for the styled pie chart. Add `matplotlib` to requirements.txt.")
        else:
            fig, ax = plt.subplots()
            fig.patch.set_facecolor("black")
            ax.set_facecolor("black")
            wedges, _, _ = ax.pie(
                [wins, losses],
                colors=["#00c853", "#ff1744"],            # green, red
                autopct=lambda p: f"{p:.1f}%",
                startangle=90,
                textprops={"color":"white","weight":"bold"}
            )
            ax.axis("equal")
            ax.legend(wedges, ["Wins", "Losses"], loc="center", bbox_to_anchor=(0.85, 0.5),
                      frameon=False, labelcolor="white")
            st.pyplot(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # Equity curve
        st.markdown("<div class='section'>", unsafe_allow_html=True)
        st.markdown("### **Equity Curve**")
        if plt is None:
            st.info("Install matplotlib to view the equity curve.")
        else:
            eq = [st.session_state.bt["start_equity"] or 0.0]
            e = eq[0]
            for t in st.session_state.bt["trades"]:
                e *= (1.0 + (t["pct_gain"]/100.0))
                eq.append(e)
            fig2, ax2 = plt.subplots()
            ax2.plot(range(len(eq)), eq, marker='o')
            ax2.set_xlabel("Trades")
            ax2.set_ylabel("Account Value")
            st.pyplot(fig2, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
