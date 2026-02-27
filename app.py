import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
import pytz

# -------------------------------------------------
# Page Config
# -------------------------------------------------
st.set_page_config(page_title="Index Dashboard", layout="wide")
st.title("📈 2 Days Index Dashboard")

# -------------------------------------------------
# Index List
# -------------------------------------------------
indices = {
    "^NSEI": "Nifty 50 (India)",
    "^NSEBANK": "BankNifty (India)",
    "^BSESN": "Sensex (India)",
}

# -------------------------------------------------
# Auto Refresh Every 15 Seconds
# -------------------------------------------------
st.markdown(
    """
    <script>
        setTimeout(function(){
           window.location.reload();
        }, 15000);
    </script>
    """,
    unsafe_allow_html=True
)

# -------------------------------------------------
# Fetch Data (NO manual market time logic)
# -------------------------------------------------
@st.cache_data(ttl=15)
def get_data(symbols):
    rows = []
    intraday_data = {}

    for sym, name in symbols.items():
        try:
            ticker = yf.Ticker(sym)
            hist = ticker.history(period="1d", interval="5m")

            if hist.empty:
                continue

            # Store full intraday data
            intraday_data[sym] = hist

            open_price = hist["Open"].iloc[0]
            high_price = hist["High"].max()
            low_price = hist["Low"].min()
            current_price = hist["Close"].iloc[-1]

            gain = high_price - open_price
            pct_gain = (gain / open_price) * 100 if open_price != 0 else 0

            loss = low_price - open_price
            pct_loss = (loss / open_price) * 100 if open_price != 0 else 0

            # -------------------------
            # Breakout Detection
            # -------------------------
            breakout_signal = "None"

            if len(hist) > 1:
                prev_high = hist["High"].iloc[:-1].max()
                prev_low = hist["Low"].iloc[:-1].min()

                if current_price > prev_high:
                    breakout_signal = "Bullish Breakout 🚀"
                elif current_price < prev_low:
                    breakout_signal = "Bearish Breakdown 🔻"

            rows.append({
                "Index": name,
                "Open": open_price,
                "High": high_price,
                "Low": low_price,
                "Current": current_price,
                "Gain": gain,
                "% Gain": pct_gain,
                "Loss": loss,
                "% Loss": pct_loss,
                "Signal": breakout_signal
            })

        except Exception:
            continue

    return pd.DataFrame(rows), intraday_data


df, intraday_data = get_data(indices)

st.write(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")

# -------------------------------------------------
# Slider based on AVAILABLE candles
# -------------------------------------------------
if intraday_data:
    first_key = list(intraday_data.keys())[0]
    available_blocks = len(intraday_data[first_key])
else:
    available_blocks = 1

selected_blocks = st.slider(
    "Select time window (5-minute candles)",
    min_value=1,
    max_value=max(1, available_blocks),
    value=min(12, available_blocks)
)

selected_minutes = selected_blocks * 5

# -------------------------------------------------
# Styled Table
# -------------------------------------------------
if not df.empty:

    numeric_cols = ["Open", "High", "Low", "Current", "Gain", "% Gain", "Loss", "% Loss"]

    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    def color_positive(val):
        if pd.isna(val):
            return ""
        return "color: green; font-weight:bold;" if val > 0 else "color: red; font-weight:bold;"

    def color_signal(val):
        if "Bullish" in str(val):
            return "color: green; font-weight:bold;"
        elif "Bearish" in str(val):
            return "color: red; font-weight:bold;"
        return ""

    styled = (
        df.style
        .format({col: "{:.2f}" for col in numeric_cols})
        .applymap(color_positive, subset=["Gain", "% Gain"])
        .applymap(color_positive, subset=["Loss", "% Loss"])
        .applymap(color_signal, subset=["Signal"])
    )

    st.dataframe(styled, use_container_width=True)

else:
    st.warning("No intraday data available yet")

# -------------------------------------------------
# Charts Section
# -------------------------------------------------
st.subheader(f"Last {selected_minutes} Minutes")

cols = st.columns(len(indices))

for col, (sym, name) in zip(cols, indices.items()):
    with col:
        st.markdown(f"### {name}")

        if sym in intraday_data:

            data = intraday_data[sym].tail(selected_blocks)

            day_high = intraday_data[sym]["High"].max()
            day_low = intraday_data[sym]["Low"].min()
            current_price = intraday_data[sym]["Close"].iloc[-1]

            fig = go.Figure()

            # Price line
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=data["Close"],
                    mode="lines",
                    line=dict(width=2),
                    name="Close"
                )
            )

            # Day High
            fig.add_hline(
                y=day_high,
                line_dash="dash",
                annotation_text="Day High",
                annotation_position="top right"
            )

            # Day Low
            fig.add_hline(
                y=day_low,
                line_dash="dash",
                annotation_text="Day Low",
                annotation_position="bottom right"
            )

            # Current Price
            fig.add_hline(
                y=current_price,
                line_dash="dot",
                annotation_text="Current",
                annotation_position="right"
            )

            # Breakout Annotation
            if len(data) > 1:
                prev_high = data["High"].iloc[:-1].max()
                prev_low = data["Low"].iloc[:-1].min()
                last_close = data["Close"].iloc[-1]

                if last_close > prev_high:
                    fig.add_annotation(
                        x=data.index[-1],
                        y=last_close,
                        text="🚀 Breakout",
                        showarrow=True,
                        arrowhead=2
                    )
                elif last_close < prev_low:
                    fig.add_annotation(
                        x=data.index[-1],
                        y=last_close,
                        text="🔻 Breakdown",
                        showarrow=True,
                        arrowhead=2
                    )

            fig.update_layout(
                height=300,
                margin=dict(l=10, r=10, t=20, b=10),
                template="plotly_white",
                xaxis=dict(rangeslider=dict(visible=False))
            )

            st.plotly_chart(fig, use_container_width=True)

        else:
            st.write("No data available")
