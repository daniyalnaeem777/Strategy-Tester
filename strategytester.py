import streamlit as st

# ---------- Page setup ----------
st.set_page_config(page_title="TP/SL Calculator", page_icon="📈", layout="centered")

# ---------- Custom CSS ----------
st.markdown("""
    <style>
        html, body, [class*="css"]  {
            font-family: Helvetica, sans-serif !important;
        }
        .stButton > button {
            border-radius: 10px;
            padding: 0.4rem 1rem;
            border: 1px solid #555;
            background-color: #111;
            color: white;
            transition: all 0.2s;
        }
        .stButton > button:hover {
            background-color: #333;
        }
        .selected-button {
            background-color: #0044ff !important;
            color: white !important;
            font-weight: 600 !important;
        }
        .result-box {
            border-radius: 10px;
            padding: 0.8rem;
            text-align: center;
            font-size: 1.2rem;
            font-weight: bold;
        }
    </style>
""", unsafe_allow_html=True)

# ---------- Title ----------
st.title("📈 TP/SL Calculator")
st.caption("Fast risk targets based on ATR")

# ---------- Mode Selection ----------
st.subheader("Mode")
mode = st.radio("Select mode", ["Live", "Backtesting"], horizontal=True)

# Initialize backtesting state
if "sl_mult" not in st.session_state:
    st.session_state.sl_mult = 1.0
if "wins" not in st.session_state:
    st.session_state.wins = 0
if "losses" not in st.session_state:
    st.session_state.losses = 0
if "backtesting_done" not in st.session_state:
    st.session_state.backtesting_done = False

# ---------- ATR Multiple Buttons ----------
st.subheader("Stop-Loss multiple")
cols = st.columns(2)

if cols[0].button("SL = 1.0 × ATR"):
    st.session_state.sl_mult = 1.0
if cols[1].button("SL = 1.5 × ATR"):
    st.session_state.sl_mult = 1.5

tp_mult = 2.0  # Fixed take-profit multiplier

st.caption(f"Current SL = {st.session_state.sl_mult} × ATR  TP = {tp_mult} × ATR")

st.markdown("---")

# ---------- Input form ----------
with st.form("calc_form"):
    st.subheader("Direction")
    side = st.radio("Direction", ["Long", "Short"], horizontal=True)

    c1, c2 = st.columns(2)
    with c1:
        entry = st.number_input("Entry price", min_value=0.0, format="%.4f")
    with c2:
        atr = st.number_input("ATR (14)", min_value=0.0, format="%.4f")

    submitted = st.form_submit_button("Calculate")

# ---------- Calculation ----------
if submitted:
    if entry <= 0 or atr <= 0:
        st.error("Please enter positive numbers for both **Entry** and **ATR**.")
    else:
        sl_mult = st.session_state.sl_mult

        if side == "Long":
            sl = entry - sl_mult * atr
            tp = entry + tp_mult * atr
            rr = (tp - entry) / (entry - sl)
            dsl = entry - sl
            dtp = tp - entry
        else:
            sl = entry + sl_mult * atr
            tp = entry - tp_mult * atr
            rr = (entry - tp) / (sl - entry)
            dsl = sl - entry
            dtp = entry - tp

        sl_pct = (dsl / entry) * 100
        tp_pct = (dtp / entry) * 100

        # ---------- Output ----------
        st.subheader("Results")
        a, b, c = st.columns(3)
        with a:
            st.markdown("**Stop Loss**")
            st.markdown(f"<div class='result-box' style='background-color:#3b1d1d;color:#ff6b6b;'>{sl:.4f}</div>", unsafe_allow_html=True)
            st.caption(f"Δ {dsl:.4f} ({sl_pct:.2f}%)")
        with b:
            st.markdown("**Take Profit**")
            st.markdown(f"<div class='result-box' style='background-color:#1d3b1d;color:#66ff91;'>{tp:.4f}</div>", unsafe_allow_html=True)
            st.caption(f"Δ {dtp:.4f} ({tp_pct:.2f}%)")
        with c:
            st.markdown("**Reward : Risk**")
            st.markdown(f"<div class='result-box' style='background-color:#1d263b;color:#7bb5ff;'>{rr:.2f} : 1</div>", unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("Formulae")
        sign_sl = "-" if side == "Long" else "+"
        sign_tp = "+" if side == "Long" else "-"
        st.code(
            f"{side.upper()}\n"
            f"SL = Entry {sign_sl} {sl_mult} × ATR\n"
            f"TP = Entry {sign_tp} {tp_mult} × ATR",
            language="text"
        )

        # ---------- Backtesting-specific features ----------
        if mode == "Backtesting":
            if not st.session_state.backtesting_done:
                st.markdown("---")
                st.subheader("Record Trade Outcome (based on TradingView replay)")
                col1, col2, col3 = st.columns(3)
                if col1.button("Win (Hit TP)"):
                    st.session_state.wins += 1
                    st.success("Recorded as Win!")
                if col2.button("Loss (Hit SL)"):
                    st.session_state.losses += 1
                    st.success("Recorded as Loss!")
                if col3.button("Done"):
                    st.session_state.backtesting_done = True

            if st.session_state.backtesting_done:
                total = st.session_state.wins + st.session_state.losses
                st.markdown("---")
                st.subheader("Backtesting Results")
                st.write(f"Total trades: {total}")
                st.write(f"Number of wins: {st.session_state.wins}")
                st.write(f"Number of losses: {st.session_state.losses}")
                if st.button("Reset Backtesting"):
                    st.session_state.wins = 0
                    st.session_state.losses = 0
                    st.session_state.backtesting_done = False
