 (cd "$(git rev-parse --show-toplevel)" && git apply --3way <<'EOF' 
diff --git a/README.md b/README.md
new file mode 100644
index 0000000000000000000000000000000000000000..9528f75eb5a2834c459fd646925b1785c38fb0fd
--- /dev/null
+++ b/README.md
@@ -0,0 +1,38 @@
+# 2days Index Dashboard
+
+A Streamlit dashboard that tracks intraday movements (5-minute candles) for:
+
+- Nifty 50 (`^NSEI`)
+- BankNifty (`^NSEBANK`)
+- Sensex (`^BSESN`)
+
+It shows open/high/low/current values, gain/loss percentages, breakout signals, and intraday charts.
+
+## Run locally
+
+```bash
+python -m venv .venv
+source .venv/bin/activate
+pip install -r requirements.txt
+streamlit run app.py
+```
+
+## Deploy on Render
+
+### Option 1: Blueprint deploy (recommended)
+
+1. Push this repo to GitHub.
+2. In Render, click **New +** → **Blueprint**.
+3. Connect your GitHub repo.
+4. Render will read `render.yaml` and create the web service automatically.
+
+### Option 2: Manual web service
+
+- **Environment**: Python
+- **Build command**: `pip install -r requirements.txt`
+- **Start command**: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
+
+## Notes
+
+- The dashboard auto-refreshes every 15 seconds.
+- NSE market hours are considered as 09:15–15:30 IST for time-window limits.
 
EOF
)
