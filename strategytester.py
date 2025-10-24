# pptcalculator.py — TP/SL Calculator (Live + Backtest), correct layout & realistic compounding
# Long:  SL = Entry − (SL_mult × ATR)   |   TP = Entry + (2.0 × ATR)
# Short: SL = Entry + (SL_mult × ATR)   |   TP = Entry − (2.0 × ATR)

import streamlit as st
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt

# ---------- Page setup ----------
st.set_page_config(page_title="TP/SL Calculator", page_icon="📈", layout="centered")

# ---------- Simple styling ----------
st.markdown("""
<style>
* { font-family: 'Helvetica', sans-serif !important; }
.smallchip { display:inline-block;padding:6px 10px;border-radius:999px;border:1px solid rgba(255,255,255,0.14);margin-right:8px; }
.kpi { display:inline-block;padding:8px 12px;border-radius:10px;border:1px solid rgba(255,255,255,0.14);margin-right:8px;font-weight:600; }
</style>
""", unsafe_allow_html=True)

TP_MULT = 2.0
DECIMALS = 4

# ---------- Session state ----------
if "bt" not in st.session_state:
    st.session_state.bt = {
        "recording": False,
        "start_equity": None,
        "equity": None,
        "trades": [],         # list of dicts
        "last_calc": None,    # last calculated setup
        "summary_ready": False,
    }

def reset_bt():
    st.session_state.bt.update({
        "recording": False,
        "start_equity": None,
        "equity": None,
        "trades": [],
        "last_calc": None,
        "summary_ready": False,
    })

def _pct_to_tp_sl(entry, sl, tp, side):
    """Return (sl_pct, tp_pct) as percentages from entry to SL/TP."""
    if side == "Long":
        sl_pct = abs((entry - sl) / entry) * 100.0
        tp_pct = abs((tp - entry) / entry) * 100.0
    else:
        sl_pct = abs((sl - entry) / entry) * 100.0
        tp_pct = abs((entry - tp) / entry) * 100.0
    return sl_pct, tp_pct

def _pct_from_exit(entry, exit_price, side):
    """% change from entry to exit, positive if in favor of the trade."""
    if side == "Long":
        return ((exit_price - entry) / entry) * 100.0
    else:
        return ((entry - exit_price) / entry) * 100.0

def _compound(pct_change):
    """Apply compounding to full equity."""
    if st.session_state.bt["equity"] is None:
        st.warning("Start a backtesting session first.")
        return
    st.session_state.bt["equity"] *= (1.0 + pct_change)

def _log_trade(result_label, side, entry, atr, sl_mult, sl, tp, rr, exit_price, pct_gain):
    """Append a trade to the raw log."""
    st.session_state.bt["trades"].append({
        "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "result": result_label,   # "WIN", "LOSS", or "CLOSED"
        "side": side,
        "entry": entry,
        "atr": atr,
        "sl_mult": sl_mult,
        "sl": sl,
        "tp": tp,
        "rr": rr,
        "exit_price": exit_price,
        "pct_gain": pct_gain,     # signed percent (e.g., 1.8 or -0.9)
    })

# ---------- Header ----------
st.title("📈 TP/SL Calculator")

# ---------- Mode ----------
mode = st.radio("Mode", ["Live", "Backtest"], horizontal=True)

# ============= BACKTEST MODE =============
if mode == "Backtest":
    # --- Top controls: Start / End ---
    st.subheader("🔁 Backtesting Controls")

    colA, colB, colC = st.columns([2,1,1])
    with colA:
        start_equity = st.number_input(
            "Account size (starting equity)",
            min_value=0.0,
            value=float(st.session_state.bt["start_equity"] or 0.0),
            step=100.0,
            format="%.2f",
            help="Required before you can start recording trades."
        )
    with colB:
        if not st.session_state.bt["recording"]:
            if st.button("Start Session"):
                if start_equity <= 0:
                    st.error("Please enter a positive account size.")
                else:
                    st.session_state.bt["start_equity"] = start_equity
                    st.session_state.bt["equity"] = start_equity
                    st.session_state.bt["trades"] = []
                    st.session_state.bt["summary_ready"] = False
                    st.session_state.bt["recording"] = True
                    st.success("Backtesting started.")
        else:
            st.markdown("<span class='kpi'>Recording…</span>", unsafe_allow_html=True)
    with colC:
        if st.button("End Backtesting"):
            if st.session_state.bt["recording"]:
                st.session_state.bt["recording"] = False
                st.session_state.bt["summary_ready"] = True
                st.info("Backtesting ended. Summary below.")
            else:
                st.info("No active session.")
    st.divider()

    # --- Calculator (below controls) ---
    st.subheader("Calculator")

    # Stop-loss multiple
    sl_choice = st.radio("Stop-Loss multiple (× ATR)", ["1.0", "1.5"], horizontal=True, index=0)
    sl_mult = 1.0 if sl_choice == "1.0" else 1.5
    st.markdown(
        f"<span class='smallchip'>Current SL = {sl_mult} × ATR</span>"
        f"<span class='smallchip'>TP = {TP_MULT} × ATR</span>",
        unsafe_allow_html=True
    )

    # Direction, Entry, ATR
    st.markdown("**Direction**")
    side = st.radio("Direction", ["Long", "Short"], horizontal=True, label_visibility="collapsed")

    c1, c2 = st.columns(2)
    with c1:
        entry = st.number_input("Entry price", min_value=0.0, format=f"%.{DECIMALS}f", key="bt_entry")
    with c2:
        atr = st.number_input("ATR (14)", min_value=0.0, format=f"%.{DECIMALS}f", key="bt_atr")

    # Calculate TP / SL (instant)
    if entry > 0 and atr > 0:
        if side == "Long":
            sl = entry - sl_mult * atr
            tp = entry + TP_MULT * atr
            rr = (tp - entry) / max(entry - sl, 1e-12)
            dsl = entry - sl
            dtp = tp - entry
        else:
            sl = entry + sl_mult * atr
            tp = entry - TP_MULT * atr
            rr = (entry - tp) / max(sl - entry, 1e-12)
            dsl = sl - entry
            dtp = entry - tp

        # % distances
        sl_pct, tp_pct = _pct_to_tp_sl(entry, sl, tp, side)

        # Show results
        st.subheader("Levels")
        a, b, c = st.columns(3)
        with a:
            st.markdown("**SL**")
            st.error(f"**{sl:.{DECIMALS}f}**")
            st.caption(f"Δ {dsl:.{DECIMALS}f} ({sl_pct:.2f}%)")
        with b:
            st.markdown("**TP**")
            st.success(f"**{tp:.{DECIMALS}f}**")
            st.caption(f"Δ {dtp:.{DECIMALS}f} ({tp_pct:.2f}%)")
        with c:
            st.markdown("**Reward : Risk**")
            st.info(f"**{rr:.2f} : 1**")

        # Save last calc snapshot for record buttons
        st.session_state.bt["last_calc"] = {
            "side": side, "entry": entry, "atr": atr,
            "sl_mult": sl_mult, "sl": sl, "tp": tp, "rr": rr,
            "sl_pct": sl_pct, "tp_pct": tp_pct
        }

        st.divider()
        st.subheader("Record Trade")

        # Exit-price field for 'Closed at selected price'
        exit_price = st.number_input("Exit Price (for 'Closed at selected price')", min_value=0.0, format=f"%.{DECIMALS}f")

        cA, cB, cC, cD = st.columns([1,1,2,2])
        with cA:
            if st.button("Record Win ✅", use_container_width=True, disabled=not st.session_state.bt["recording"]):
                calc = st.session_state.bt["last_calc"]
                _compound(calc["tp_pct"] / 100.0)
                _log_trade("WIN", calc["side"], calc["entry"], calc["atr"], calc["sl_mult"],
                           calc["sl"], calc["tp"], calc["rr"], exit_price=None, pct_gain=calc["tp_pct"])
                st.success("Recorded full TP win.")
        with cB:
            if st.button("Record Loss ❌", use_container_width=True, disabled=not st.session_state.bt["recording"]):
                calc = st.session_state.bt["last_calc"]
                _compound(-(calc["sl_pct"] / 100.0))
                _log_trade("LOSS", calc["side"], calc["entry"], calc["atr"], calc["sl_mult"],
                           calc["sl"], calc["tp"], calc["rr"], exit_price=None, pct_gain=-calc["sl_pct"])
                st.warning("Recorded full SL loss.")
        with cC:
            closed_clicked = st.button("Closed at selected price 🟩", use_container_width=True, disabled=not st.session_state.bt["recording"])
        with cD:
            # live equity readout
            if st.session_state.bt["equity"] is not None and st.session_state.bt["start_equity"]:
                chg = (st.session_state.bt["equity"] / st.session_state.bt["start_equity"] - 1.0) * 100.0
                st.metric("Equity", f"{st.session_state.bt['equity']:.2f}", f"{chg:.2f}%")

        if closed_clicked:
            if exit_price <= 0:
                st.error("Enter a valid **Exit Price** first.")
            else:
                calc = st.session_state.bt["last_calc"]
                pct = _pct_from_exit(calc["entry"], exit_price, calc["side"])  # can be <TP or >TP
                _compound(pct / 100.0)
                _log_trade("CLOSED", calc["side"], calc["entry"], calc["atr"], calc["sl_mult"],
                           calc["sl"], calc["tp"], calc["rr"], exit_price=exit_price, pct_gain=pct)
                st.info(f"Recorded CLOSED at {exit_price:.{DECIMALS}f} ({pct:.2f}%).")

    else:
        st.info("Enter **Entry** and **ATR** to see levels and record trades.")

    # --- Summary after ending backtesting ---
    if st.session_state.bt["summary_ready"]:
        st.divider()
        st.subheader("📊 Backtest Summary")

        total = len(st.session_state.bt["trades"])
        # Count wins/losses (CLOSED counts to win/loss by sign of pct_gain)
        wins = sum(1 for t in st.session_state.bt["trades"] if (t["result"] == "WIN") or (t["result"] == "CLOSED" and t["pct_gain"] >= 0))
        losses = sum(1 for t in st.session_state.bt["trades"] if (t["result"] == "LOSS") or (t["result"] == "CLOSED" and t["pct_gain"] < 0))
        winrate = (wins / total * 100.0) if total else 0.0

        s1, s2, s3 = st.columns(3)
        with s1: st.metric("Total Trades", total)
        with s2: st.metric("Winning Ratio", f"{winrate:.1f}%")
        with s3:
            if st.session_state.bt["equity"] and st.session_state.bt["start_equity"]:
                ret_total = (st.session_state.bt["equity"] / st.session_state.bt["start_equity"] - 1.0) * 100.0
                st.metric("Total Return", f"{ret_total:.2f}%")

        # Pie chart
        fig1, ax1 = plt.subplots()
        ax1.pie([wins, losses], labels=["Wins", "Losses"], autopct=lambda p: f"{p:.1f}%" if p > 0 else "", startangle=90)
        ax1.axis("equal")
        st.pyplot(fig1, use_container_width=True)

        # Table with exact headings + exit/pct
        if total > 0:
            df = pd.DataFrame(st.session_state.bt["trades"])
            df = df[["ts","result","side","entry","atr","sl_mult","sl","tp","rr","exit_price","pct_gain"]].copy()

            # Serial Number first
            df.insert(0, "Serial Number", range(1, len(df) + 1))

            # Rename per your spec + add two clear extra columns
            df = df.rename(columns={
                "ts": "Time",
                "result": "Result",
                "side": "Side",
                "entry": "Entry",
                "atr": "ATR",
                "sl_mult": "stop-loss_multiple",
                "sl": "SL",
                "tp": "TP",
                "rr": "Risk/Return",
                "exit_price": "Exit Price",
                "pct_gain": "Pct Gain"
            })

            st.dataframe(df, use_container_width=True)

# ============= LIVE MODE =============
if mode == "Live":
    st.subheader("Live Calculator")

    # Stop-loss multiple
    sl_choice_live = st.radio("Stop-Loss multiple (× ATR)", ["1.0", "1.5"], horizontal=True, index=0, key="live_sl_choice")
    sl_mult_live = 1.0 if sl_choice_live == "1.0" else 1.5
    st.markdown(
        f"<span class='smallchip'>Current SL = {sl_mult_live} × ATR</span>"
        f"<span class='smallchip'>TP = {TP_MULT} × ATR</span>",
        unsafe_allow_html=True
    )

    st.markdown("**Direction**")
    side_live = st.radio("Direction", ["Long", "Short"], horizontal=True, label_visibility="collapsed", key="live_side")

    c1, c2 = st.columns(2)
    with c1:
        entry_live = st.number_input("Entry price", min_value=0.0, format=f"%.{DECIMALS}f", key="live_entry")
    with c2:
        atr_live = st.number_input("ATR (14)", min_value=0.0, format=f"%.{DECIMALS}f", key="live_atr")

    if st.button("Calculate (Live)"):
        if entry_live <= 0 or atr_live <= 0:
            st.error("Please enter positive numbers for **Entry** and **ATR**.")
        else:
            if side_live == "Long":
                sl = entry_live - sl_mult_live * atr_live
                tp = entry_live + TP_MULT * atr_live
                rr = (tp - entry_live) / max(entry_live - sl, 1e-12)
                dsl = entry_live - sl
                dtp = tp - entry_live
            else:
                sl = entry_live + sl_mult_live * atr_live
                tp = entry_live - TP_MULT * atr_live
                rr = (entry_live - tp) / max(sl - entry_live, 1e-12)
                dsl = sl - entry_live
                dtp = entry_live - tp

            sl_pct, tp_pct = _pct_to_tp_sl(entry_live, sl, tp, side_live)

            st.subheader("Results")
            a, b, c = st.columns(3)
            with a:
                st.markdown("**SL**")
                st.error(f"**{sl:.{DECIMALS}f}**")
                st.caption(f"Δ {dsl:.{DECIMALS}f} ({sl_pct:.2f}%)")
            with b:
                st.markdown("**TP**")
                st.success(f"**{tp:.{DECIMALS}f}**")
                st.caption(f"Δ {dtp:.{DECIMALS}f} ({tp_pct:.2f}%)")
            with c:
                st.markdown("**Reward : Risk**")
                st.info(f"**{rr:.2f} : 1**")
