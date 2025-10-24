# TP/SL Calculator (Live + Backtest)
# Long:  SL = Entry − (SL_mult × ATR)   |   TP = Entry + (2.0 × ATR)
# Short: SL = Entry + (SL_mult × ATR)   |   TP = Entry − (2.0 × ATR)

import streamlit as st
from datetime import datetime
import pandas as pd

# ---- Try matplotlib for the custom pie + equity styling ----
try:
    import matplotlib.pyplot as plt
except ModuleNotFoundError:
    plt = None

# ---------- Page setup ----------
st.set_page_config(page_title="TP/SL Calculator", page_icon="📈", layout="centered")

# ---------- Global Helvetica + card styling ----------
st.markdown("""
<style>
* { font-family: 'Helvetica', sans-serif !important; }
.card {
  border: 1px solid rgba(255,255,255,0.18);
  border-radius: 14px;
  padding: 16px 16px;
  margin: 10px 0;
  background: rgba(255,255,255,0.03);
}
.hstack > div { width: 100%; }
.boldlabel label > div:first-child { font-weight: 700 !important; }
.smallchip {
  display:inline-block;padding:6px 10px;border-radius:999px;
  border:1px solid rgba(255,255,255,0.14);margin-right:8px;
}
.btn-row button { width: 100% !important; }
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
        "trades": [],         # each: dict
        "last_calc": None,    # snapshot for quick record buttons
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
    if side == "Long":
        return ((exit_price - entry) / entry) * 100.0
    else:
        return ((entry - exit_price) / entry) * 100.0

def _compound(pct_change):
    """Multiply full equity by (1 + pct_change). pct_change is decimal (e.g., +0.018)."""
    if st.session_state.bt["equity"] is None:
        st.warning("Start a backtesting session first.")
        return
    st.session_state.bt["equity"] *= (1.0 + pct_change)

def _log_trade(result_label, side, entry, atr, sl_mult, sl, tp, rr, exit_price, pct_gain):
    st.session_state.bt["trades"].append({
        "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "result": result_label,   # "WIN", "LOSS", "CLOSED"
        "Side": side,
        "Entry": entry,
        "ATR": atr,
        "stop-loss_multiple": sl_mult,
        "SL": sl,
        "TP": tp,
        "Risk/Return": rr,
        "Exit Price": exit_price,
        "Pct Gain": pct_gain,     # signed %
    })

# ============================================================
#                        MODE CARD
# ============================================================
with st.container():
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    mode = st.radio("Mode", ["Live", "Backtest"], horizontal=True, key="mode_radio")
    st.markdown("</div>", unsafe_allow_html=True)

# ============================================================
#                          LIVE MODE
# ============================================================
if mode == "Live":
    # Direction card (bold labels)
    st.markdown("<div class='card boldlabel'>", unsafe_allow_html=True)
    st.markdown("**Direction**")
    side_live = st.radio("Direction", ["Long", "Short"], horizontal=True, label_visibility="collapsed", key="live_side")
    st.markdown("</div>", unsafe_allow_html=True)

    # Stop-loss multiple card
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("**Stop-Loss Multiple**")
    sl_choice_live = st.radio("SL × ATR", ["1.0", "1.5"], horizontal=True, label_visibility="collapsed", key="live_sl")
    sl_mult_live = 1.0 if sl_choice_live == "1.0" else 1.5
    st.markdown(
        f"<span class='smallchip'>Current SL = {sl_mult_live} × ATR</span>"
        f"<span class='smallchip'>TP = {TP_MULT} × ATR</span>",
        unsafe_allow_html=True
    )
    st.markdown("</div>", unsafe_allow_html=True)

    # Entry/ATR card
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        entry_live = st.number_input("Entry Price", min_value=0.0, format=f"%.{DECIMALS}f", key="live_entry")
    with c2:
        atr_live = st.number_input("ATR (14)", min_value=0.0, format=f"%.{DECIMALS}f", key="live_atr")
    st.markdown("</div>", unsafe_allow_html=True)

    # Calculate button card
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    if st.button("Calculate", key="live_calc_btn"):
        if entry_live <= 0 or atr_live <= 0:
            st.error("Please enter positive numbers for Entry and ATR.")
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
    st.markdown("</div>", unsafe_allow_html=True)

# ============================================================
#                         BACKTEST MODE
# ============================================================
if mode == "Backtest":
    # ---------- Backtesting Controls card ----------
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("**Backtesting Controls**")

    start_equity = st.number_input(
        "Account Size (Starting Equity)",
        min_value=0.0,
        value=float(st.session_state.bt["start_equity"] or 0.0),
        step=100.0,
        format="%.2f",
        key="acct_size",
    )

    # Vertical buttons, same width
    col_btn = st.container()
    with col_btn:
        st.markdown("<div class='btn-row'>", unsafe_allow_html=True)
        start_clicked = st.button("Start Session", key="start_bt")
        end_clicked   = st.button("End Session", key="end_bt")
        st.markdown("</div>", unsafe_allow_html=True)

    if start_clicked:
        if start_equity <= 0:
            st.error("Please enter a positive account size.")
        else:
            st.session_state.bt["start_equity"] = start_equity
            st.session_state.bt["equity"] = start_equity
            st.session_state.bt["trades"] = []
            st.session_state.bt["summary_ready"] = False
            st.session_state.bt["recording"] = True
            st.success("Backtesting started.")

    if end_clicked:
        if st.session_state.bt["recording"]:
            st.session_state.bt["recording"] = False
            st.session_state.bt["summary_ready"] = True
            st.info("Backtesting ended. Summary below.")
        else:
            st.info("No active session to end.")

    st.markdown("</div>", unsafe_allow_html=True)

    # ---------- Calculator card ----------
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("**Calculator**")

    # Direction (bold)
    st.markdown("<div class='boldlabel'>", unsafe_allow_html=True)
    st.markdown("**Direction**")
    side = st.radio("Direction", ["Long", "Short"], horizontal=True, label_visibility="collapsed", key="bt_dir")
    st.markdown("</div>", unsafe_allow_html=True)

    # Stop-Loss Multiple
    st.markdown("**Stop-Loss Multiple**")
    sl_choice = st.radio("SL × ATR", ["1.0", "1.5"], horizontal=True, label_visibility="collapsed", key="bt_sl")
    sl_mult = 1.0 if sl_choice == "1.0" else 1.5
    st.markdown(
        f"<span class='smallchip'>Current SL = {sl_mult} × ATR</span>"
        f"<span class='smallchip'>TP = {TP_MULT} × ATR</span>",
        unsafe_allow_html=True
    )

    # Entry + ATR
    c1, c2 = st.columns(2)
    with c1:
        entry = st.number_input("Entry Price", min_value=0.0, format=f"%.{DECIMALS}f", key="bt_entry")
    with c2:
        atr = st.number_input("ATR (14)", min_value=0.0, format=f"%.{DECIMALS}f", key="bt_atr")

    # Compute levels immediately when fields are valid
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

        sl_pct, tp_pct = _pct_to_tp_sl(entry, sl, tp, side)

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

        # snapshot for record buttons
        st.session_state.bt["last_calc"] = {
            "side": side, "entry": entry, "atr": atr,
            "sl_mult": sl_mult, "sl": sl, "tp": tp, "rr": rr,
            "sl_pct": sl_pct, "tp_pct": tp_pct
        }

        st.divider()
        st.markdown("**Record Trade**")
        exit_price = st.number_input("Exit Price (for 'Closed at selected price')", min_value=0.0, format=f"%.{DECIMALS}f", key="bt_exit")

        # Buttons: Win / Loss / Closed-at-price
        r1, r2, r3 = st.columns(3)
        with r1:
            if st.button("Record Win ✅", use_container_width=True, key="rec_win",
                         disabled=not st.session_state.bt["recording"]):
                calc = st.session_state.bt["last_calc"]
                _compound(calc["tp_pct"] / 100.0)
                _log_trade("WIN", calc["side"], calc["entry"], calc["atr"], calc["sl_mult"],
                           calc["sl"], calc["tp"], calc["rr"], exit_price=None, pct_gain=calc["tp_pct"])
                st.success("Recorded full TP win.")
        with r2:
            if st.button("Record Loss ❌", use_container_width=True, key="rec_loss",
                         disabled=not st.session_state.bt["recording"]):
                calc = st.session_state.bt["last_calc"]
                _compound(-(calc["sl_pct"] / 100.0))
                _log_trade("LOSS", calc["side"], calc["entry"], calc["atr"], calc["sl_mult"],
                           calc["sl"], calc["tp"], calc["rr"], exit_price=None, pct_gain=-calc["sl_pct"])
                st.warning("Recorded full SL loss.")
        with r3:
            if st.button("Closed at selected price 🟩", use_container_width=True, key="rec_closed",
                         disabled=not st.session_state.bt["recording"]):
                if exit_price <= 0:
                    st.error("Enter a valid Exit Price.")
                else:
                    calc = st.session_state.bt["last_calc"]
                    pct = _pct_from_exit(calc["entry"], exit_price, calc["side"])  # can be <TP or >TP
                    _compound(pct / 100.0)
                    _log_trade("CLOSED", calc["side"], calc["entry"], calc["atr"], calc["sl_mult"],
                               calc["sl"], calc["tp"], calc["rr"], exit_price=exit_price, pct_gain=pct)
                    sign = "▲" if pct >= 0 else "▼"
                    st.info(f"Recorded CLOSED at {exit_price:.{DECIMALS}f} ({sign}{abs(pct):.2f}%).")

    st.markdown("</div>", unsafe_allow_html=True)  # end Calculator card

    # ---------- Summary after End Session ----------
    if st.session_state.bt["summary_ready"]:
        # 1) Trades table (first)
        if len(st.session_state.bt["trades"]) == 0:
            st.warning("No trades recorded.")
        else:
            # Build display with your requested headings first
            raw = pd.DataFrame(st.session_state.bt["trades"])

            # Order base columns
            col_order = ["ts","result","Side","Entry","ATR","stop-loss_multiple","SL","TP","Risk/Return","Exit Price","Pct Gain"]
            raw = raw[[c for c in col_order if c in raw.columns]].copy()

            # Serial Number as the first column
            raw.insert(0, "Serial Number", range(1, len(raw) + 1))

            # Rename exact headings you requested
            raw = raw.rename(columns={
                "ts": "Time",
                "result": "Result",
                # keep Side, Entry, ATR as-is (already capitalized)
                # keep stop-loss_multiple as-is (exact string requested)
                # SL, TP, Risk/Return already match your spec
            })

            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown("**Trades**")
            st.dataframe(raw, use_container_width=True)

            # CSV export
            csv = raw.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Download CSV", csv, "backtest_log.csv", "text/csv")
            st.markdown("</div>", unsafe_allow_html=True)

        # 2) Pie chart (black background, green wins, red losses, bold % inside, key)
        wins = sum(1 for t in st.session_state.bt["trades"]
                   if (t["result"] == "WIN") or (t["result"] == "CLOSED" and t["Pct Gain"] >= 0))
        losses = sum(1 for t in st.session_state.bt["trades"]
                     if (t["result"] == "LOSS") or (t["result"] == "CLOSED" and t["Pct Gain"] < 0))

        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("**Win / Loss Breakdown**")
        if plt is None:
            st.error("Matplotlib is required for the styled pie chart. Please `pip install matplotlib` or add it to requirements.txt.")
        else:
            fig, ax = plt.subplots()
            # Black background
            fig.patch.set_facecolor("black")
            ax.set_facecolor("black")
            # Pie with requested colors
            values = [wins, losses]
            labels = ["Wins", "Losses"]
            colors = ["#00c853", "#ff1744"]  # green, red
            wedges, texts, autotexts = ax.pie(
                values,
                labels=None,  # legend key handled below
                colors=colors,
                autopct=lambda p: f"{p:.1f}%",
                startangle=90,
                textprops={"color":"white","weight":"bold"}
            )
            ax.axis("equal")

            # In-chart key (legend)
            leg = ax.legend(wedges, labels, title=None, loc="center",
                            bbox_to_anchor=(0.85, 0.5), frameon=False,
                            labelcolor="white")
            # Move legend a bit inside the pie
            for txt in leg.get_texts():
                txt.set_color("white")
                txt.set_weight("bold")

            st.pyplot(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # 3) Equity curve
        if plt is None:
            st.info("Install matplotlib to view the equity curve chart.")
        else:
            # Rebuild equity from start and trade sequence (already compounded live; but rebuild for the curve)
            eq = [st.session_state.bt["start_equity"] or 0.0]
            e = eq[0]
            for t in st.session_state.bt["trades"]:
                pct = t["Pct Gain"] / 100.0
                e *= (1.0 + pct)
                eq.append(e)

            fig2, ax2 = plt.subplots()
            ax2.plot(range(len(eq)), eq, marker='o')
            ax2.set_title("Equity Curve")
            ax2.set_xlabel("Trades")
            ax2.set_ylabel("Account Value")
            st.pyplot(fig2, use_container_width=True)
