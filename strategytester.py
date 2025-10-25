import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import uuid
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib import colors
import io

# Streamlit UI setup
st.set_page_config(page_title="Backtest Logger", layout="wide")
st.title("📊 Backtest Logger")
st.markdown("### Live & Backtest • Realistic Compounding • Precision-Engineered Strategy Execution")

# Session State Initialization
if "trades" not in st.session_state:
    st.session_state.trades = []
if "equity" not in st.session_state:
    st.session_state.equity = 100  # Starting equity

# Trade Entry
with st.expander("➕ Enter New Trade"):
    col1, col2, col3 = st.columns(3)
    with col1:
        side = st.selectbox("Trade Direction", ["Long", "Short"])
        entry_price = st.number_input("Entry Price", min_value=0.0, value=3500.0)
    with col2:
        atr = st.number_input("ATR", min_value=0.0, value=100.0)
        sl_multiple = st.number_input("SL Multiple", min_value=0.1, value=1.0)
    with col3:
        rr = st.number_input("Reward:Risk", min_value=0.1, value=2.0)

    if st.button("Calculate"):
        if side == "Long":
            sl = entry_price - atr * sl_multiple
            tp = entry_price + atr * sl_multiple * rr
        else:
            sl = entry_price + atr * sl_multiple
            tp = entry_price - atr * sl_multiple * rr

        reward = abs(tp - entry_price)
        risk = abs(entry_price - sl)
        rr_ratio = round(reward / risk, 2)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("#### Stop Loss")
            st.markdown(f"<div style='background-color:#3b2326;padding:1.5em;border-radius:10px'><h3 style='color:#f08080'>{sl:.4f}</h3></div>", unsafe_allow_html=True)
            st.markdown(f"<span style='color:gray'>Δ {abs(entry_price - sl):.4f} ({abs((entry_price - sl) / entry_price * 100):.2f}%)</span>", unsafe_allow_html=True)
        with col2:
            st.markdown("#### Take Profit")
            st.markdown(f"<div style='background-color:#21372b;padding:1.5em;border-radius:10px'><h3 style='color:#90ee90'>{tp:.4f}</h3></div>", unsafe_allow_html=True)
            st.markdown(f"<span style='color:gray'>Δ {abs(entry_price - tp):.4f} ({abs((tp - entry_price) / entry_price * 100):.2f}%)</span>", unsafe_allow_html=True)
        with col3:
            st.markdown("#### Reward : Risk")
            st.markdown(f"<div style='background-color:#1e2b40;padding:1.5em;border-radius:10px'><h3 style='color:#6495ED'>{rr_ratio:.2f} : 1</h3></div>", unsafe_allow_html=True)

# Record Trade
st.subheader("📈 Record Trade")
exit_price = st.number_input("Exit Price (for 'Closed At Selected Price')", min_value=0.0, value=0.0)
col1, col2, col3 = st.columns(3)

if col1.button("Record Win ✅"):
    change = abs(tp - entry_price)
    pct_gain = round(change / entry_price * 100, 4)
    st.session_state.trades.append({"Side": side, "Entry": entry_price, "ATR": atr, "SL_MULTIPLE": sl_multiple, "SL": sl, "TP": tp, "Risk/Return": rr, "Exit Price": tp, "Pct Gain %": pct_gain})
    st.session_state.equity += pct_gain

if col2.button("Record Loss ❌"):
    change = abs(entry_price - sl)
    pct_loss = -round(change / entry_price * 100, 4)
    st.session_state.trades.append({"Side": side, "Entry": entry_price, "ATR": atr, "SL_MULTIPLE": sl_multiple, "SL": sl, "TP": tp, "Risk/Return": rr, "Exit Price": sl, "Pct Gain %": pct_loss})
    st.session_state.equity += pct_loss

if col3.button("Closed At Selected Price"):
    change = exit_price - entry_price if side == "Long" else entry_price - exit_price
    pct_change = round(change / entry_price * 100, 4)
    st.session_state.trades.append({"Side": side, "Entry": entry_price, "ATR": atr, "SL_MULTIPLE": sl_multiple, "SL": sl, "TP": tp, "Risk/Return": rr, "Exit Price": exit_price, "Pct Gain %": pct_change})
    st.session_state.equity += pct_change

# Trade Metrics
st.subheader("📊 Win / Loss Breakdown")
df = pd.DataFrame(st.session_state.trades)
if not df.empty:
    win_count = (df["Pct Gain %"] > 0).sum()
    loss_count = (df["Pct Gain %"] <= 0).sum()
    total = len(df)

    pie_fig, ax = plt.subplots(figsize=(4, 4))
    ax.pie([win_count, loss_count], labels=["Win", "Loss"], autopct="%1.1f%%", startangle=90, colors=["green", "red"])
    st.pyplot(pie_fig)

    st.subheader("📈 Equity Curve")
    df["Equity"] = 100 + df["Pct Gain %"].cumsum()
    eq_fig, ax2 = plt.subplots(figsize=(10, 4))
    ax2.plot(df.index + 1, df["Equity"], marker='o')
    ax2.set_xlabel("Trade Number")
    ax2.set_ylabel("Equity")
    st.pyplot(eq_fig)

    st.subheader("📋 Trades")
    st.dataframe(df.style.format({"Pct Gain %": "{:.4f}"}))

    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download CSV", csv, "trades.csv", "text/csv")

    # PDF EXPORT
    def generate_pdf():
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter,
                                leftMargin=40, rightMargin=40, topMargin=50, bottomMargin=40)
        styles = getSampleStyleSheet()
        elements = []
        title_style = ParagraphStyle('CenterTitle', parent=styles['Title'], alignment=1, fontName='Helvetica', fontSize=12)
        elements.append(Paragraph("Trade Metrics", title_style))
        elements.append(Spacer(1, 12))

        # Add equity curve image
        eq_buf = io.BytesIO()
        eq_fig.savefig(eq_buf, format='png')
        eq_buf.seek(0)
        elements.append(RLImage(eq_buf, width=6*inch, height=2.5*inch))
        elements.append(Spacer(1, 12))

        # Add trade table
        table_data = [["#", "Trade Direction", "Result", "% Gain/Loss", "Equity Δ"]]
        for i, row in df.iterrows():
            result = "Win" if row["Pct Gain %"] > 0 else "Loss"
            table_data.append([i+1, row["Side"], result, f"{row['Pct Gain %']:.2f}%", f"{row['Equity'] - 100:.2f}"])

        table = Table(table_data, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.gray),
            ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
            ('ALIGN',(0,0),(-1,-1),'CENTER'),
            ('FONTSIZE', (0,0), (-1,-1), 10),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND',(0,1),(-1,-1),colors.beige),
            ('GRID', (0,0), (-1,-1), 1, colors.black)
        ]))
        elements.append(table)

        # Summary Metrics
        summary = f"Total Trades: {total}, Win Rate: {win_count}/{total} ({win_count/total*100:.2f}%)"
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(summary, styles['Normal']))

        # Add pie chart image
        pie_buf = io.BytesIO()
        pie_fig.savefig(pie_buf, format='png')
        pie_buf.seek(0)
        elements.append(Spacer(1, 12))
        elements.append(RLImage(pie_buf, width=3*inch, height=3*inch))

        doc.build(elements)
        return buffer.getvalue()

    pdf_bytes = generate_pdf()
    st.download_button("📤 Extract Report (PDF)", data=pdf_bytes, file_name="backtest_report.pdf", mime="application/pdf")
