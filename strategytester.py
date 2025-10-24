# pptcalculator.py — TP/SL Calculator (Live + Backtest, realistic compounding + partial win)
# Long:  SL = Entry − (SL_mult × ATR)   |   TP = Entry + (2.0 × ATR)
# Short: SL = Entry + (SL_mult × ATR)   |   TP = Entry − (2.0 × ATR)

import streamlit as st
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt

# ---------- Page setup ----------
st.set_page_config(page_title="TP/SL Calculator", page_icon="📈", layout="centered")

# ---------- Styling ----------
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
        "trades": [],          # raw log
        "wins": 0,
        "losses": 0,
        "last_trade": None,    # snapshot of last calculated trade
        "summary_shown": False,
        "start_equity": None,  # user account size
        "equity": None,        # current equity
        "equity_curve": [],    # list of (ts, equity)
    }

def reset_bt():
    st.session_state.bt.update({
        "recording": False,
        "trades": [],
        "wins": 0,
        "losses": 0,
        "last_trade": None,
        "summary_shown": False,
        "start_equity": None,
        "equity": None,
        "equity_curve": [],
    })

def _apply_equity_change(pct_change: float) -> None:
    """Multiply equity by (1 + pct_change)."""
    if st.session_state.bt["equity"] is None:
        st.warning("Start a backtest session and set Account size first.")
        return
    st.session_state.bt["equity"] *= (1.0 + pct_change)
    snap_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.bt["equity_curve"].append((snap_ts, st.session_state.bt["equity"]))

def record_result(result: str):
    """Mark full WIN/LOSS and compound 100% of equity by actual % move to TP/SL."""
    cur = st.session_state.bt["last_trade"]
    if not cur:
        st.warning("Calculate a trade first, then mark Win/Loss.")
        return

    pct_change = (cur["tp_pct"] / 100.0) if result == "WIN" else -(cur["sl_pct"] / 100.0)
    _apply_equity_change(pct_change)

    # Update counters
    if result == "WIN":
        st.session_state.bt["wins"] += 1
    else:
        st.session_state.bt["losses"] += 1

    # Log trade (display names mapped later)
    st.session_state.bt["trades"].append({
        "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "result": result,
        "side": cur["side"],
        "entry": cur["entry"],
        "atr": cur["atr"],
        "sl_mult": cur["sl_mult"],
        "sl": cur["sl"],
        "tp": cur["tp"],
        "rr": cur["rr"],
        "exit": None,
        "pct_gain": (pct_change * 100.0) if result == "WIN" else -(cur["sl_pct"]),
    })

def record_partial_win(exit_price: float = None, profit_delta: float = None):
    """
    Partial win:
      - Provide either exit_price (absolute price) OR profit_delta (price change in your favor).
      - Computes % gain from Entry (long: (exit-entry)/entry, short: (entry-exit)/entry).
      - Caps gain% to TP% (cannot exceed a full take-profit).
      - Records as WIN (partial) and compounds equity accordingly.
    """
    cur = st.session_state.bt["last_trade"]
    if not cur:
        st.warning("Calculate a trade first, then enter exit or profit to mark partial win.")
        return

    entry = float(cur["entry"])
    side  = cur["side"]
    tp_pct_allowed = cur["tp_pct"]  # % to full TP (from earlier calculation)

    if (exit_price is None or exit_price <= 0) and (profit_delta is None or profit_delta == 0):
        st.warning("Enter an **Exit Price** or a **Profit Amount (Δ price)** to record a partial win.")
        return

    # Determine exit price if only delta provided
    ex = None
    if exit_price and exit_price > 0:
        ex = float(exit_price)
    elif profit_delta is not None:
        if side == "Long":
            ex = entry + float(profit_delta)
        else:
            ex = entry - float(profit_delta)

    # Compute % move in favor
    if side == "Long":
        raw_pct = ((ex - entry) / entry) * 100.0
    else:
        raw_pct = ((entry - ex) / entry) * 100.0

    # No negative or zero partial wins
    if raw_pct <= 0:
        st.warning("Partial win must be in profit relative to Entry.")
        return

    # Cap at full TP percent
    pct_used = min(raw_pct, tp_pct_allowed)

    # Apply equity change
    _apply_equity_change(pct_used / 100.0)

    # Update counters (count as a win)
    st.session_state.bt["wins"] += 1

    # Log trade
    st.session_state.bt["trades"].append({
        "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "result": "WIN",  # still a win
        "side": side,
        "entry": entry,
        "atr": cur["atr"],
        "sl_mult": cur["sl_mult"],
        "sl": cur["sl"],
        "tp": cur["tp"],
        "rr": cur["rr"],
        "exit": ex,
        "pct_gain": pct_used,  # % actually gained on this partial
    })

def undo_last():
    """Undo last trade and equity step."""
    if not st.session_state.bt["trades"]:
        st.info("Nothing to undo.")
        return
    last = st.session_state.bt["trades"].pop()

    # Determine pct_change that was applied
    if last["result"] == "WIN" and last.get("pct_gain") is not None:
        pct_change = last["pct_gain"] / 100.0
    else:
        # reconstruct from entry/sl/tp as full win or loss
        entry = float(last["entry"])
        sl = float(last["sl"])
        tp = float(last["tp"])
        if last["result"] == "WIN":
            pct_change = abs((tp - entry) / entry)
        else:
            pct_change = -abs((entry - sl) / entry)

    # Reverse equity step
    if st.session_state.bt["equity"] is not None and st.session_state.bt["equity_curve"]:
        after = st.session_state.bt["equity"]
        denom = (1.0 + pct_change) if (1.0 + pct_change) != 0 else 1e-12
        st.session_state.bt["equity"] = after / denom
        st.session_state.bt["equity_curve"].pop()

    # Adjust counters
    if last["result"] == "WIN":
        st.session_state.bt["wins"] = max(0, st.session_state.bt["wins"] - 1)
    else:
        st.session_state.bt["losses"] = max(0, st.session_state.bt["losses"] - 1)

# ---------- Header ----------
st.title("📈 TP/SL Calculator")
st.caption("Live & Backtest • Realistic compounding with full-capital deployment + Partial Wins")

# ---------- Mode ----------
mode = st.radio("Mode", ["Live", "Backtest"], horizontal=True)

# ---------- Inputs ----------
st.write("**Stop-Loss multiple**")
sl_choice = st.radio("SL × ATR", ["1.0", "1.5"], horizontal=True, label_visibility="collapsed")
sl_mult = 1.0 if sl_choice == "1.0" else 1.5
st.markdown(
    f"<span class='smallchip'>Current SL = {sl_mult} × ATR</span>"
    f"<span class='smallchip'>TP = {TP_MULT} × ATR</span>",
    unsafe_allow_html=True
)
st.divider()

st.markdown("**Direction**")
side = st.radio("Direction", ["Long", "Short"], horizontal=True, label_visibility="collapsed")
c1, c2 = st.columns(2)
with c1:
    entry = st.number_input("Entry price", min_value=0.0, format=f"%.{DECIMALS}f")
with c2:
    atr = st.number_input("ATR (14)", min_value=0.0, format=f"%.{DECIMALS}f")

# ---------- Calculate ----------
if st.button("Calculate"):
    if entry <= 0 or atr <= 0:
        st.error("Please enter positive numbers for **Entry** and **ATR**.")
    else:
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

        # % distances for compounding
        sl_pct = (dsl / entry) * 100 if entry > 0 else 0.0
        tp_pct = (dtp / entry) * 100 if entry > 0 else 0.0

        st.session_state.bt["last_trade"] = {
            "side": side, "entry": entry, "atr": atr,
            "sl_mult": sl_mult, "sl": sl, "tp": tp, "rr": rr,
            "sl_pct": sl_pct, "tp_pct": tp_pct,
        }

        # UI
        st.subheader("Results")
        a, b, c = st.columns(3)
        with a:
            st.markdown("**Stop Loss**")
            st.error(f"**{sl:.{DECIMALS}f}**")
            st.caption(f"Δ {dsl:.{DECIMALS}f} ({sl_pct:.2f}%)")
        with b:
            st.markdown("**Take Profit**")
            st.success(f"**{tp:.{DECIMALS}f}**")
            st.caption(f"Δ {dtp:.{DECIMALS}f} ({tp_pct:.2f}%)")
        with c:
            st.markdown("**Reward : Risk**")
            st.info(f"**{rr:.2f} : 1**")

        st.divider()
        sign_sl = "-" if side == "Long" else "+"
        sign_tp = "+" if side == "Long" else "-"
        st.code(
            f"{side.upper()}\n"
            f"SL = Entry {sign_sl} {sl_mult} × ATR\n"
            f"TP = Entry {sign_tp} {TP_MULT} × ATR",
            language="text"
        )

# ---------- Backtest ----------
if mode == "Backtest":
    st.divider()
    st.subheader("🔁 Backtest Session")

    # Account size + start
    col_a, col_b, col_c = st.columns([2,1,1])
    with col_a:
        acct = st.number_input("Account size (starting equity)", min_value=0.0,
                               value=float(st.session_state.bt["start_equity"] or 0.0),
                               step=100.0, format="%.2f")
    with col_b:
        if not st.session_state.bt["recording"]:
            if st.button("Start session"):
                if acct <= 0:
                    st.error("Please enter a positive **Account size** to begin.")
                else:
                    st.session_state.bt["start_equity"] = acct
                    st.session_state.bt["equity"] = acct
                    st.session_state.bt["equity_curve"] = []
                    st.session_state.bt["recording"] = True
                    st.session_state.bt["summary_shown"] = False
                    st.success("Backtest started. Calculate a setup, then mark Win/Loss after checking Replay.")
        else:
            st.markdown("<span class='kpi'>Recording…</span>", unsafe_allow_html=True)
    with col_c:
        if st.button("Reset session"):
            reset_bt()
            st.info("Session reset.")

    # Partial win controls
    st.markdown("**Partial Win (optional)**")
    pw1, pw2, pw3 = st.columns([1,1,1])
    with pw1:
        partial_exit = st.number_input("Exit Price (optional)", min_value=0.0, format=f"%.{DECIMALS}f")
    with pw2:
        profit_delta = st.number_input("Profit Amount Δ (price)", value=0.0, format=f"%.{DECIMALS}f")
    with pw3:
        if st.button("Mark Partial Win 🟩", use_container_width=True):
            ex = partial_exit if partial_exit > 0 else None
            pdlt = profit_delta if profit_delta != 0 else None
            record_partial_win(exit_price=ex, profit_delta=pdlt)

    # Live counters + actions
    if st.session_state.bt["recording"]:
        k1, k2, k3, k4 = st.columns(4)
        with k1: st.metric("Trades", len(st.session_state.bt["trades"]))
        with k2: st.metric("Wins", st.session_state.bt["wins"])
        with k3: st.metric("Losses", st.session_state.bt["losses"])
        with k4:
            if st.session_state.bt["equity"] is not None and st.session_state.bt["start_equity"]:
                chg = (st.session_state.bt["equity"] / st.session_state.bt["start_equity"] - 1.0) * 100.0
                st.metric("Equity", f"{st.session_state.bt['equity']:.2f}", f"{chg:.2f}%")

        b1, b2, b3, b4 = st.columns([1,1,1,2])
        with b1:
            if st.button("Mark Win ✅", use_container_width=True):
                record_result("WIN")
        with b2:
            if st.button("Mark Loss ❌", use_container_width=True):
                record_result("LOSS")
        with b3:
            if st.button("Undo last ↩️", use_container_width=True):
                undo_last()
        with b4:
            if st.button("Done ▶️ Show Summary", use_container_width=True):
                st.session_state.bt["recording"] = False
                st.session_state.bt["summary_shown"] = True

    # Summary (table + charts)
    if (not st.session_state.bt["recording"]) and st.session_state.bt["summary_shown"]:
        total = len(st.session_state.bt["trades"])
        wins = st.session_state.bt["wins"]
        losses = st.session_state.bt["losses"]

        st.divider()
        st.subheader("📊 Backtest Summary")
        s1, s2, s3, s4, s5 = st.columns(5)
        with s1: st.metric("Total trades", total)
        with s2: st.metric("Wins", wins)
        with s3: st.metric("Losses", losses)
        with s4: st.metric("Win rate", f"{(wins/total*100):.1f}%" if total else "0.0%")
        with s5:
            if st.session_state.bt["equity"] and st.session_state.bt["start_equity"]:
                ret_total = (st.session_state.bt["equity"] / st.session_state.bt["start_equity"] - 1.0) * 100.0
                st.metric("Total return", f"{ret_total:.2f}%")

        if total > 0:
            # Build display table exactly as requested
            raw = pd.DataFrame(st.session_state.bt["trades"])
            raw = raw[["ts","result","side","entry","atr","sl_mult","sl","tp","rr"]].copy()

            # Insert Serial Number first (1-based)
            raw.insert(0, "Serial Number", range(1, len(raw) + 1))

            # Rename headings precisely
            raw = raw.rename(columns={
                "ts": "Time",
                "result": "Result",
                "side": "Side",
                "entry": "Entry",
                "atr": "ATR",
                "sl_mult": "stop-loss_multiple",
                "sl": "SL",
                "tp": "TP",
                "rr": "Risk/Return",
            })

            st.dataframe(raw, use_container_width=True)

            # Download CSV
            csv = raw.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Download trade log (CSV)", csv, "backtest_log.csv", "text/csv")

        # Pie: Wins vs Losses
        fig1, ax1 = plt.subplots()
        ax1.pie([wins, losses], labels=["Wins", "Losses"], autopct=lambda p: f"{p:.1f}%" if p > 0 else "", startangle=90)
        ax1.axis("equal")
        st.pyplot(fig1, use_container_width=True)

        # Equity curve
        if st.session_state.bt["equity_curve"]:
            ec = pd.DataFrame(st.session_state.bt["equity_curve"], columns=["Time", "Equity"])
            st.line_chart(ec.set_index("Time"))
