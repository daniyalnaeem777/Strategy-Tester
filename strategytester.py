# pptcalculator.py — TP/SL Calculator with Live + Backtest modes
# Long:  SL = Entry − (SL_mult × ATR)   |   TP = Entry + (2.0 × ATR)
# Short: SL = Entry + (SL_mult × ATR)   |   TP = Entry − (2.0 × ATR)

import streamlit as st
from datetime import datetime

# ---------- Page setup ----------
st.set_page_config(page_title="TP/SL Calculator", page_icon="📈", layout="centered")

# ---------- Global Helvetica + button-like styling ----------
st.markdown("""
<style>
* { font-family: 'Helvetica', sans-serif !important; }
.stMetric, .stAlert { font-weight: 600 !important; }

.sl-group [role="radiogroup"] label {
  border: 1px solid rgba(255,255,255,0.18);
  border-radius: 999px;
  padding: 6px 12px;
  margin-right: 10px;
  cursor: pointer;
}
.sl-group [role="radiogroup"] label:hover { background: rgba(255,255,255,0.06); }
.sl-group [role="radiogroup"] input:checked ~ div {
  background: rgba(130,180,255,0.25);
  border-radius: 999px;
  padding: 6px 12px;
}
.smallchip {
  display:inline-block;padding:6px 10px;border-radius:999px;
  border:1px solid rgba(255,255,255,0.14);margin-right:8px;
}
.kpi {
  display:inline-block; padding:8px 12px; border-radius:10px;
  border:1px solid rgba(255,255,255,0.14); margin-right:8px; font-weight:600;
}
</style>
""", unsafe_allow_html=True)

TP_MULT = 2.0
DECIMALS = 4

# ---------- Session state for backtesting ----------
if "bt" not in st.session_state:
    st.session_state.bt = {
        "recording": False,
        "trades": [],     # list of dicts
        "wins": 0,
        "losses": 0,
        "last_trade": None,  # snapshot of last calculated trade for quick marking
        "summary_shown": False,
    }

def reset_bt():
    st.session_state.bt = {
        "recording": False,
        "trades": [],
        "wins": 0,
        "losses": 0,
        "last_trade": None,
        "summary_shown": False,
    }

def record_result(result: str):
    """Record current calculated trade as win/loss."""
    cur = st.session_state.bt["last_trade"]
    if not cur:
        st.warning("Calculate a trade first, then mark Win/Loss.")
        return
    entry = cur["entry"]
    atr = cur["atr"]
    # Store a compact snapshot
    snap = {
        "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "side": cur["side"],
        "entry": entry,
        "atr": atr,
        "sl_mult": cur["sl_mult"],
        "sl": cur["sl"],
        "tp": cur["tp"],
        "rr": cur["rr"],
        "result": result,  # "WIN" or "LOSS"
    }
    st.session_state.bt["trades"].append(snap)
    if result == "WIN":
        st.session_state.bt["wins"] += 1
    else:
        st.session_state.bt["losses"] += 1

def undo_last():
    if not st.session_state.bt["trades"]:
        st.info("Nothing to undo.")
        return
    last = st.session_state.bt["trades"].pop()
    if last["result"] == "WIN":
        st.session_state.bt["wins"] = max(0, st.session_state.bt["wins"] - 1)
    else:
        st.session_state.bt["losses"] = max(0, st.session_state.bt["losses"] - 1)

# ---------- Header ----------
st.title("📈 TP/SL Calculator")
st.caption("Fast risk targets based on ATR — now with Live & Backtest modes")

# ---------- Mode selector ----------
mode = st.radio("Mode", ["Live", "Backtest"], horizontal=True)

# ---------- SL multiple selector ----------
st.write("**Stop-Loss multiple**")
st.markdown('<div class="sl-group">', unsafe_allow_html=True)
sl_choice = st.radio(
    "Choose SL × ATR",
    ["SL = 1.0 × ATR", "SL = 1.5 × ATR"],
    horizontal=True,
    label_visibility="collapsed",
    index=0
)
st.markdown("</div>", unsafe_allow_html=True)
sl_mult = 1.0 if "1.0" in sl_choice else 1.5

# Chips
st.markdown(
    f"<span class='smallchip'>Current SL = {sl_mult} × ATR</span>"
    f"<span class='smallchip'>TP = {TP_MULT} × ATR</span>",
    unsafe_allow_html=True
)

st.divider()

# ---------- Inputs (no form) ----------
st.markdown("**Direction**")
side = st.radio("Direction", ["Long", "Short"], horizontal=True, label_visibility="collapsed")
c1, c2 = st.columns(2)
with c1:
    entry = st.number_input("Entry price", min_value=0.0, format=f"%.{DECIMALS}f", key="entry")
with c2:
    atr = st.number_input("ATR (14)", min_value=0.0, format=f"%.{DECIMALS}f", key="atr")

# ---------- Compute on button ----------
calc_pressed = st.button("Calculate")

if calc_pressed:
    if entry <= 0 or atr <= 0:
        st.error("Please enter positive numbers for **Entry** and **ATR**.")
    else:
        # core logic
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

        fmt = f"{{:.{DECIMALS}f}}"
        sl_pct = (dsl / entry) * 100 if entry > 0 else 0.0
        tp_pct = (dtp / entry) * 100 if entry > 0 else 0.0

        st.subheader("Results")
        a, b, c = st.columns(3)
        with a:
            st.markdown("**Stop Loss**")
            st.error(f"**{fmt.format(sl)}**")
            st.caption(f"Δ {fmt.format(dsl)} ({sl_pct:.2f}%)")
        with b:
            st.markdown("**Take Profit**")
            st.success(f"**{fmt.format(tp)}**")
            st.caption(f"Δ {fmt.format(dtp)} ({tp_pct:.2f}%)")
        with c:
            st.markdown("**Reward : Risk**")
            st.info(f"**{rr:.2f} : 1**")

        st.divider()
        st.markdown("**Formulae**")
        sign_sl = "-" if side == "Long" else "+"
        sign_tp = "+" if side == "Long" else "-"
        st.code(
            f"{side.upper()}\n"
            f"SL = Entry {sign_sl} {sl_mult} × ATR\n"
            f"TP = Entry {sign_tp} {TP_MULT} × ATR",
            language="text"
        )

        # Save last calculation for backtest quick-marking
        st.session_state.bt["last_trade"] = {
            "side": side, "entry": entry, "atr": atr,
            "sl_mult": sl_mult, "sl": sl, "tp": tp, "rr": rr
        }

# ---------- Backtest controls ----------
if mode == "Backtest":
    st.divider()
    st.subheader("🔁 Backtest Session")

    # Start / Reset row
    start_col, reset_col, spacer = st.columns([1,1,4])
    with start_col:
        if not st.session_state.bt["recording"]:
            if st.button("Start session"):
                st.session_state.bt["recording"] = True
                st.session_state.bt["summary_shown"] = False
                st.success("Backtest session started. Calculate a setup, then mark Win/Loss after checking Replay.")
        else:
            st.markdown("<span class='kpi'>Recording…</span>", unsafe_allow_html=True)

    with reset_col:
        if st.button("Reset session", help="Clear all recorded trades for a fresh run"):
            reset_bt()
            st.info("Session reset.")

    # When recording, show mark buttons and live counters
    if st.session_state.bt["recording"]:
        k1, k2, k3 = st.columns(3)
        with k1:
            st.metric("Trades", len(st.session_state.bt["trades"]))
        with k2:
            st.metric("Wins", st.session_state.bt["wins"])
        with k3:
            st.metric("Losses", st.session_state.bt["losses"])

        act1, act2, act3, act4 = st.columns([1,1,1,2])
        with act1:
            if st.button("Mark Win ✅", use_container_width=True):
                record_result("WIN")
        with act2:
            if st.button("Mark Loss ❌", use_container_width=True):
                record_result("LOSS")
        with act3:
            if st.button("Undo last ↩️", use_container_width=True):
                undo_last()
        with act4:
            if st.button("Done ▶️ Show Summary", use_container_width=True):
                st.session_state.bt["recording"] = False
                st.session_state.bt["summary_shown"] = True

    # Summary after Done
    if (not st.session_state.bt["recording"]) and st.session_state.bt["summary_shown"]:
        total = len(st.session_state.bt["trades"])
        wins = st.session_state.bt["wins"]
        losses = st.session_state.bt["losses"]
        st.divider()
        st.subheader("📊 Backtest Summary")
        s1, s2, s3, s4 = st.columns(4)
        with s1: st.metric("Total trades", total)
        with s2: st.metric("Wins", wins)
        with s3: st.metric("Losses", losses)
        with s4:
            winrate = (wins / total * 100) if total > 0 else 0.0
            st.metric("Win rate", f"{winrate:.1f}%")

        # (Optional) Show a compact table of recorded trades
        if st.checkbox("Show trade log"):
            import pandas as pd
            df = pd.DataFrame(st.session_state.bt["trades"])
            # Order columns for readability
            cols = ["ts","result","side","entry","atr","sl_mult","sl","tp","rr"]
            df = df[[c for c in cols if c in df.columns]]
            st.dataframe(df, use_container_width=True)

# ---------- Live mode footer (small hint) ----------
if mode == "Live":
    st.caption("Tip: Switch to **Backtest** to log wins/losses while using TradingView Replay.")
