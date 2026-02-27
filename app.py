 (cd "$(git rev-parse --show-toplevel)" && git apply --3way <<'EOF' 
diff --git a/app.py b/app.py
new file mode 100644
index 0000000000000000000000000000000000000000..4b133e7a1841486873722b68786b8c7a46d5811b
--- /dev/null
+++ b/app.py
@@ -0,0 +1,239 @@
+import streamlit as st
+import yfinance as yf
+import pandas as pd
+from datetime import datetime
+import plotly.graph_objects as go
+import pytz
+
+st.set_page_config(page_title="Index Dashboard", layout="wide")
+
+st.title("2days Index")
+
+indices = {
+    "^NSEI": "Nifty 50 (India)",
+    "^NSEBANK": "BankNifty (India)",
+    "^BSESN": "Sensex (India)",
+}
+
+st.markdown(
+    """
+    <script>
+        setTimeout(function(){
+           window.location.reload();
+        }, 15000);
+    </script>
+    """,
+    unsafe_allow_html=True,
+)
+
+ist = pytz.timezone("Asia/Kolkata")
+now = datetime.now(ist)
+
+market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
+market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
+
+if now < market_open:
+    minutes_passed = 0
+elif now > market_close:
+    minutes_passed = 375
+else:
+    minutes_passed = int((now - market_open).total_seconds() / 60)
+
+max_blocks = max(1, minutes_passed // 5)
+
+selected_blocks = st.slider(
+    "Select time window (5-minute steps)",
+    min_value=1,
+    max_value=max_blocks,
+    value=min(12, max_blocks),
+)
+
+selected_minutes = selected_blocks * 5
+
+
+@st.cache_data(ttl=10)
+def get_data(symbols, blocks, today_date):
+    rows = []
+    intraday_data = {}
+
+    for sym, name in symbols.items():
+        ticker = yf.Ticker(sym)
+        hist = ticker.history(period="1d", interval="5m")
+
+        if hist.empty:
+            continue
+
+        hist = hist[hist.index.date == today_date]
+        if hist.empty:
+            continue
+
+        intraday_data[sym] = hist.tail(blocks)
+
+        open_price = hist["Open"].iloc[0]
+        high_price = hist["High"].max()
+        low_price = hist["Low"].min()
+        current_price = hist["Close"].iloc[-1]
+
+        gain = high_price - open_price
+        pct_gain = (gain / open_price) * 100 if open_price != 0 else None
+        loss = low_price - open_price
+        pct_loss = (loss / open_price) * 100 if open_price != 0 else None
+
+        breakout_signal = "None"
+        if len(hist) > 1:
+            prev_high = hist["High"].iloc[:-1].max()
+            prev_low = hist["Low"].iloc[:-1].min()
+
+            if current_price > prev_high:
+                breakout_signal = "Bullish Breakout 🚀"
+            elif current_price < prev_low:
+                breakout_signal = "Bearish Breakdown 🔻"
+
+        rows.append(
+            {
+                "Index": name,
+                "Open": open_price,
+                "High": high_price,
+                "Low": low_price,
+                "Current": current_price,
+                "Gain (High - Open)": gain,
+                "% Gain": pct_gain,
+                "Loss (Low - Open)": loss,
+                "% Loss": pct_loss,
+                "Signal": breakout_signal,
+            }
+        )
+
+    return pd.DataFrame(rows), intraday_data
+
+
+df, intraday_data = get_data(indices, selected_blocks, now.date())
+
+st.write(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")
+
+if not df.empty:
+    numeric_cols = [
+        "Open",
+        "High",
+        "Low",
+        "Current",
+        "Gain (High - Open)",
+        "% Gain",
+        "Loss (Low - Open)",
+        "% Loss",
+    ]
+
+    for col in numeric_cols:
+        df[col] = pd.to_numeric(df[col], errors="coerce")
+
+    def color_gain(val):
+        if pd.isna(val):
+            return ""
+        return (
+            "color: green; font-weight:bold;"
+            if val > 0
+            else "color: red; font-weight:bold;"
+        )
+
+    def color_signal(val):
+        if "Bullish" in str(val):
+            return "color: green; font-weight:bold;"
+        if "Bearish" in str(val):
+            return "color: red; font-weight:bold;"
+        return ""
+
+    styled = (
+        df.style.format({col: "{:.2f}" for col in numeric_cols})
+        .applymap(color_gain, subset=["Gain (High - Open)", "% Gain"])
+        .applymap(color_gain, subset=["Loss (Low - Open)", "% Loss"])
+        .applymap(color_signal, subset=["Signal"])
+    )
+
+    st.dataframe(styled, use_container_width=True)
+else:
+    st.warning("No data available yet")
+
+st.subheader(f"Last {selected_minutes} Minutes")
+
+cols = st.columns(len(indices))
+
+for col, (sym, name) in zip(cols, indices.items()):
+    with col:
+        st.markdown(f"**{name}**")
+
+        if sym in intraday_data:
+            data = intraday_data[sym]
+
+            day_high = df[df["Index"] == name]["High"].values[0]
+            day_low = df[df["Index"] == name]["Low"].values[0]
+            current_price = df[df["Index"] == name]["Current"].values[0]
+
+            fig = go.Figure()
+            fig.add_trace(
+                go.Scatter(
+                    x=data.index,
+                    y=data["Close"],
+                    mode="lines",
+                    line=dict(width=2),
+                    name="Close",
+                )
+            )
+
+            fig.add_hline(
+                y=day_high,
+                line_dash="dash",
+                line_color="green",
+                annotation_text="Day High",
+                annotation_position="top right",
+            )
+
+            fig.add_hline(
+                y=day_low,
+                line_dash="dash",
+                line_color="red",
+                annotation_text="Day Low",
+                annotation_position="bottom right",
+            )
+
+            fig.add_hline(
+                y=current_price,
+                line_dash="dot",
+                line_color="blue",
+                annotation_text="Current",
+                annotation_position="right",
+            )
+
+            last_close = data["Close"].iloc[-1]
+            if len(data) > 1:
+                prev_high = data["High"].iloc[:-1].max()
+                prev_low = data["Low"].iloc[:-1].min()
+
+                if last_close > prev_high:
+                    fig.add_annotation(
+                        x=data.index[-1],
+                        y=last_close,
+                        text="🚀 Breakout",
+                        showarrow=True,
+                        arrowhead=2,
+                        font=dict(color="green", size=12),
+                    )
+                elif last_close < prev_low:
+                    fig.add_annotation(
+                        x=data.index[-1],
+                        y=last_close,
+                        text="🔻 Breakdown",
+                        showarrow=True,
+                        arrowhead=2,
+                        font=dict(color="red", size=12),
+                    )
+
+            fig.update_layout(
+                height=300,
+                margin=dict(l=10, r=10, t=20, b=10),
+                template="plotly_white",
+                xaxis=dict(rangeslider=dict(visible=False)),
+            )
+
+            st.plotly_chart(fig, use_container_width=True)
+        else:
+            st.write("No intraday data")
 
EOF
)
