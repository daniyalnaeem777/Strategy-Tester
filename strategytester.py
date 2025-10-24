# tp_sl_calculator.py — TP/SL (Live + Backtest) • wide charts • polished UI
# Long:  SL = Entry − (SL_mult × ATR)   |   TP = Entry + (2.0 × ATR)
# Short: SL = Entry + (SL_mult × ATR)   |   TP = Entry − (2.0 × ATR)

import streamlit as st
from datetime import datetime
import pandas as pd

# Charts for pie + equity
try:
    import matplotlib.pyplot as plt
except ModuleNotFoundError:
    plt = None

# ---------- Page (wide so charts aren't tiny) ----------
st.set_page_config(page_title="TP/SL Calculator", page_icon="📈", layout="wide")

# ---------- CSS ----------
st.markdown("""
<style>
  * { font-family: Helvetica, Arial, sans-serif !important; }
  h1,h2,h3,h4,strong,b { font-weight: 700 !important; letter-spacing:.2px; }
  .subtitle { font-style: italic; margin-top:-6px; margin-bottom:14px; }

  /* Single rectangle per section */
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
  .boldlabel label > div:first-child { font-weight: 700 !important; }
  .stNumberInput > div > div > input { font-weight:700; }
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
    else:
        sl_pct = abs((sl - entry) / entry) * 100.0
        tp_pct = abs((entry - tp) / entry) * 100.0
    return sl_pct, tp_pct

def _pct_from_exit(entry, exit_price, side):
    return ((exit_price - entry) / entry) * 100.0 if side == "Long" else ((entry - exit_price) / entry) * 100.0

def _compound(dec_pct):
    if st.session_state.bt["equity"] is None:
        st.warning("Start a backtesting session first.")
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

# ---------- Title ----------
st.markdown("# TP/SL Calculator")
st.markdown(
    "<div class='subtitle'>Live & Backtest • Realistic Compounding • Precision-Engineered Strategy Execution</div>",
    unsafe_allow_html=True
)

# ================== SECTION 1: Mode ==================
with st.container(border=True):
    mode = st.radio("Mode", ["Live", "Backtest"], horizontal=True, key="mode_radio")

# ================== LIVE MODE ==================
if mode == "Live":
    with st.container(border=True):
        st.markdown("### **Direction**")
        st.markdown("<div class='boldlabel'>", unsafe_allow_html=True)
        side_live = st.radio("Direction", ["Long", "Short"], horizontal=True, label_visibility="collapsed", key="live_dir")
        st.markdown("</div>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("### **SL Multiple**")
        sl_choice_live = st.radio("SL × ATR", ["1.0", "1.5"], horizontal=True, label_visibility="collapsed", key="live_sl")
        sl_mult_live = 1.0 if sl_choice_live == "1.0" else 1.5
        st.markdown(
            f"<span class='chip'>Current SL = {sl_mult_live} × ATR</span>"
            f"<span class='chip'>TP = {TP_MULT} × ATR</span>",
            unsafe_allow_html=True
        )

    with st.container(border=True):
        c1, c2 = st.columns(2)
        with c1:
            entry_live = st.number_input("Entry Price", min_value=0.0, format=f"%.{DEC}f", key="live_entry")
        with c2:
            atr_live = st.number_input("ATR (14)", min_value=0.0, format=f"%.{DEC}f", key="live_atr")

    with st.container(border=True):
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

# ================== BACKTEST MODE ==================
if mode == "Backtest":
    with st.container(border=True):
        st.markdown("### **Backtesting Controls**")
        start_equity = st.number_input(
            "Account Size (Starting Equity)",
            min_value=0.0,
            value=float(st.session_state.bt["start_equity"] or 0.0),
            step=100.0,
            format="%.2f",
        )
        start_clicked = st.button("Start Session", use_container_width=True, key="start_bt")
        end_clicked = st.button("End Session", use_container_width=True, key="end_bt")

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

    with st.container(border=True):
        # Direction
        st.markdown("**Direction**")
        st.markdown("<div class='boldlabel'>", unsafe_allow_html=True)
        side = st.radio("Direction", ["Long", "Short"], horizontal=True, label_visibility="collapsed", key="bt_dir")
        st.markdown("</div>", unsafe_allow_html=True)

        # SL Multiple
        st.markdown("**SL Multiple**")
        sl_choice = st.radio("SL × ATR", ["1.0", "1.5"], horizontal=True, label_visibility="collapsed", key="bt_sl")
        sl_mult = 1.0 if sl_choice == "1.0" else 1.5
        st.markdown(
            f"<span class='chip'>Current SL = {sl_mult} × ATR</span>"
            f"<span class='chip'>TP = {TP_MULT} × ATR</span>",
            unsafe_allow_html=True
        )

        # Entry + ATR
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
            exit_price = st.number_input("Exit Price (for Closed at 'Selected Price')",
                                         min_value=0.0, format=f"%.{DEC}f", key="bt_exit")

            r1, r2, r3 = st.columns(3)
            with r1:
                if st.button("Record Win", use_container_width=True,
                             disabled=not st.session_state.bt["recording"], key="rec_win"):
                    calc = st.session_state.bt["last_calc"]
                    _compound(calc["tp_pct"] / 100.0)
                    _log_trade("WIN", calc["side"], calc["entry"], calc["atr"], calc["sl_mult"],
                               calc["sl"], calc["tp"], calc["rr"], None, calc["tp_pct"])
                    st.success("Recorded full TP win.")
            with r2:
                if st.button("Record Loss", use_container_width=True,
                             disabled=not st.session_state.bt["recording"], key="rec_loss"):
                    calc = st.session_state.bt["last_calc"]
                    _compound(-(calc["sl_pct"] / 100.0))
                    _log_trade("LOSS", calc["side"], calc["entry"], calc["atr"], calc["sl_mult"],
                               calc["sl"], calc["tp"], calc["rr"], None, -calc["sl_pct"])
                    st.warning("Recorded full SL loss.")
            with r3:
                if st.button("Closed at 'Selected Price'", use_container_width=True,
                             disabled=not st.session_state.bt["recording"], key="rec_closed"):
                    if exit_price <= 0:
                        st.error("Enter a valid Exit Price.")
                    else:
                        calc = st.session_state.bt["last_calc"]
                        pct = _pct_from_exit(calc["entry"], exit_price, calc["side"])
                        _compound(pct / 100.0)
                        _log_trade("CLOSED", calc["side"], calc["entry"], calc["atr"], calc["sl_mult"],
                                   calc["sl"], calc["tp"], calc["rr"], exit_price, pct)
                        st.info(f"Recorded CLOSED at {exit_price:.{DEC}f} "
                                f"({'▲' if pct>=0 else '▼'}{abs(pct):.2f}%).")
        else:
            st.info("Enter **Entry** and **ATR** to see TP/SL and record trades.")

    # Summary (after End Session)
    if st.session_state.bt["summary_ready"]:
        raw = pd.DataFrame(st.session_state.bt["trades"])
        if not raw.empty:
            cols = ["ts","result","side","entry","atr","sl_mult","sl","tp","rr","exit_price","pct_gain"]
            raw = raw[[c for c in cols if c in raw.columns]].copy()
            raw.insert(0, "Serial Number", range(1, len(raw)+1))
            raw = raw.rename(columns={
                "ts":"Time", "result":"Result", "side":"Side", "entry":"Entry", "atr":"ATR",
                "sl_mult":"SL Multiple", "sl":"SL", "tp":"TP", "rr":"Risk/Return",
                "exit_price":"Exit Price", "pct_gain":"% Gain"
            })
            with st.container(border=True):
                st.markdown("### **Trades**")
                st.dataframe(raw, use_container_width=True)
                st.download_button("⬇️ Download CSV", raw.to_csv(index=False).encode("utf-8"),
                                   "backtest_log.csv", "text/csv")

        wins = sum(1 for t in st.session_state.bt["trades"]
                   if (t["result"]=="WIN") or (t["result"]=="CLOSED" and t["pct_gain"]>=0))
        losses = sum(1 for t in st.session_state.bt["trades"]
                     if (t["result"]=="LOSS") or (t["result"]=="CLOSED" and t["pct_gain"]<0))

        with st.container(border=True):
            st.markdown("### **Win / Loss Breakdown**")
            if plt is None:
                st.error("Matplotlib required for pie chart.")
            else:
                values = [wins, losses]
                labels = ["Wins", "Losses"]
                colors = ["#00c853", "#ff1744"]  # green, red

                # Bigger figure + reserved space for legend outside
                fig, ax = plt.subplots(figsize=(12, 6))
                fig.patch.set_facecolor("black")
                ax.set_facecolor("black")
                fig.subplots_adjust(left=0.05, right=0.78, top=0.95, bottom=0.06)

                wedges, _, _ = ax.pie(
                    values,
                    labels=None,  # legend handles labels
                    colors=colors,
                    autopct=lambda p: f"{p:.1f}%",
                    startangle=90,
                    textprops={"color": "white", "weight": "bold"}
                )
                ax.axis("equal")
                ax.legend(
                    wedges, labels,
                    loc="center left",
                    bbox_to_anchor=(1.02, 0.5),
                    frameon=False,
                    labelcolor="white"
                )
                st.pyplot(fig, use_container_width=True)

        with st.container(border=True):
            st.markdown("### **Equity Curve**")
            if plt is None:
                st.info("Install matplotlib to view equity curve.")
            else:
                eq = [st.session_state.bt["start_equity"] or 0.0]
                e = eq[0]
                for t in st.session_state.bt["trades"]:
                    e *= (1.0 + (t["pct_gain"]/100.0))
                    eq.append(e)

                fig2, ax2 = plt.subplots(figsize=(12, 4))
                ax2.plot(range(len(eq)), eq, marker='o')
                ax2.set_xlabel("Trades")
                ax2.set_ylabel("Account Value")
                ax2.grid(alpha=0.25)
                st.pyplot(fig2, use_container_width=True)
