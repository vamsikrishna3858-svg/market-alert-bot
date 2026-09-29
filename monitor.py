import os
import requests
import streamlit as st
import pandas as pd

TWELVE_API_KEY = os.environ["TWELVE_API_KEY"]

MARKETS = {
    "XAUUSD": "XAU/USD",
    "BTCUSD": "BTC/USD",
    "EURUSD": "EUR/USD",
}


def get_candles(symbol):
    url = "https://api.twelvedata.com/time_series"

    params = {
        "symbol": symbol,
        "interval": "30min",
        "outputsize": 20,
        "apikey": TWELVE_API_KEY,
    }

    response = requests.get(url, params=params, timeout=15)
    data = response.json()

    if "values" not in data:
        return []

    return data["values"]


def check_setup(candles):
    if len(candles) < 3:
        return "NO DATA", None

    current = candles[1]
    previous = candles[2]

    current_open = float(current["open"])
    current_close = float(current["close"])

    previous_open = float(previous["open"])
    previous_close = float(previous["close"])

    current_body = abs(current_close - current_open)
    previous_body = abs(previous_close - previous_open)

    # LONG
    if (
        previous_close < previous_open
        and current_close > current_open
        and current_body > previous_body
    ):
        return "LONG", current

    # SHORT
    if (
        previous_close > previous_open
        and current_close < current_open
        and current_body > previous_body
    ):
        return "SHORT", current

    return "NO SETUP", current


st.set_page_config(
    page_title="Vamsi Trading Monitor",
    page_icon="📊",
    layout="wide"
)

st.title("📊 VAMSI TRADING MONITOR")
st.caption("30-Minute Strategy • Monitoring Only • NO TRADE EXECUTION")

st.divider()

columns = st.columns(4)

for column, (name, symbol) in zip(columns, MARKETS.items()):

    with column:

        candles = get_candles(symbol)

        if not candles:
            st.error(f"{name}\n\nNo data")
            continue

        signal, candle = check_setup(candles)

        price = float(candles[0]["close"])

        st.subheader(name)

        st.metric(
            "Current Price",
            f"{price:.5f}"
        )

        if signal == "LONG":
            st.success("🟢 LONG SETUP")

        elif signal == "SHORT":
            st.error("🔴 SHORT SETUP")

        else:
            st.info("⚪ NO SETUP")

        if candle:
            st.write(
                f"Candle: {candle['datetime']}"
            )

st.divider()

st.subheader("📋 Monitoring Status")

st.write(
    "🟢 System is monitoring markets\n\n"
    "❌ Trade execution: DISABLED\n\n"
    "📱 Telegram alerts: Existing bot\n\n"
    "⏱️ Timeframe: 30 minutes"
)

if st.button("🔄 Refresh Market Data"):
    st.rerun()
