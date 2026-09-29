[29-09-2026 14:47] Vamsi CNC WORKS: import os
import requests
import streamlit as st
from datetime import datetime, timezone, timedelta


# ============================================================
# SETTINGS
# ============================================================

TWELVE_API_KEY = os.environ["TWELVE_API_KEY"]

TIMEFRAME = "30min"

# GMT+1
GMT_PLUS_1 = timezone(timedelta(hours=1))

# Tokyo session — GMT+1
TOKYO_START = 0
TOKYO_END = 9

# New York session — GMT+1
NEW_YORK_START = 13
NEW_YORK_END = 22

# Closing-side wick tolerance
WICK_TOLERANCE = 0.25


# ============================================================
# MARKETS
# ============================================================

MARKETS = {
    "XAUUSD": "XAU/USD",
    "BTCUSD": "BTC/USD",
    "EURUSD": "EUR/USD",
}


# ============================================================
# GET CANDLES
# ============================================================

def get_candles(symbol):

    url = "https://api.twelvedata.com/time_series"

    params = {
        "symbol": symbol,
        "interval": TIMEFRAME,
        "outputsize": 20,
        "timezone": "UTC",
        "order": "desc",
        "apikey": TWELVE_API_KEY,
    }

    try:
        response = requests.get(
            url,
            params=params,
            timeout=15
        )

        data = response.json()

    except Exception:
        return []

    if "values" not in data:
        return []

    candles = data["values"]

    candles.sort(
        key=lambda x: x["datetime"],
        reverse=True
    )

    return candles


# ============================================================
# CANDLE TIME
# ============================================================

def candle_datetime_utc(candle):

    return datetime.strptime(
        candle["datetime"],
        "%Y-%m-%d %H:%M:%S"
    ).replace(tzinfo=timezone.utc)


# ============================================================
# ONLY COMPLETELY CLOSED 30-MINUTE CANDLES
# ============================================================

def get_closed_candles(candles):

    now = datetime.now(timezone.utc)

    closed = []

    for candle in candles:

        candle_time = candle_datetime_utc(candle)

        candle_close_time = (
            candle_time + timedelta(minutes=30)
        )

        if candle_close_time <= now:
            closed.append(candle)

    return closed


# ============================================================
# SESSION CHECK
# ============================================================

def get_session(candle):

    utc_time = candle_datetime_utc(candle)

    session_time = utc_time.astimezone(
        GMT_PLUS_1
    )

    hour = session_time.hour

    if TOKYO_START <= hour < TOKYO_END:
        return "TOKYO"

    if NEW_YORK_START <= hour < NEW_YORK_END:
        return "NEW YORK"

    return None


# ============================================================
# CANDLE DATA
# ============================================================

def candle_data(candle):

    candle_open = float(candle["open"])
    candle_high = float(candle["high"])
    candle_low = float(candle["low"])
    candle_close = float(candle["close"])

    body = abs(
        candle_close - candle_open
    )

    upper_wick = (
        candle_high
        - max(candle_open, candle_close)
    )

    lower_wick = (
        min(candle_open, candle_close)
        - candle_low
    )

    return {
        "open": candle_open,
        "high": candle_high,
        "low": candle_low,
        "close": candle_close,
        "body": body,
        "upper_wick": upper_wick,
        "lower_wick": lower_wick,
    }


# ============================================================
# STRATEGY
# ============================================================

def check_setup(candles):

    if len(candles) < 3:
        return "NO DATA", None, None

    closed_candles = get_closed_candles(candles)

    if len(closed_candles) < 2:
        return "NO DATA", None, None

    # Latest completely closed candle
    current = closed_candles[0]
[29-09-2026 14:47] Vamsi CNC WORKS: # Candle immediately before it
    previous = closed_candles[1]

    # Setup candle must be inside Tokyo or New York
    session = get_session(current)

    if session is None:
        return "NO SETUP", current, None

    first = candle_data(previous)
    second = candle_data(current)

    previous_open = first["open"]
    previous_high = first["high"]
    previous_low = first["low"]
    previous_close = first["close"]
    previous_body = first["body"]

    current_open = second["open"]
    current_high = second["high"]
    current_low = second["low"]
    current_close = second["close"]
    current_body = second["body"]

    # No doji / zero body
    if previous_body <= 0 or current_body <= 0:
        return "NO SETUP", current, session

    # Second candle must have a larger body
    if current_body <= previous_body:
        return "NO SETUP", current, session


    # ========================================================
    # SHORT
    #
    # First candle  = GREEN
    # Second candle = RED
    #
    # Red candle:
    # - sweeps first candle HIGH
    # - closes below first candle LOW
    # - lower/closing-side wick <= 25% of body
    # ========================================================

    previous_green = (
        previous_close > previous_open
    )

    current_red = (
        current_close < current_open
    )

    high_sweep = (
        current_high > previous_high
    )

    close_below = (
        current_close < previous_low
    )

    lower_wick_ok = (
        second["lower_wick"]
        <= current_body * WICK_TOLERANCE
    )

    if (
        previous_green
        and current_red
        and high_sweep
        and close_below
        and lower_wick_ok
    ):

        return "SHORT", current, session


    # ========================================================
    # LONG
    #
    # First candle  = RED
    # Second candle = GREEN
    #
    # Green candle:
    # - sweeps first candle LOW
    # - closes above first candle HIGH
    # - upper/closing-side wick <= 25% of body
    # ========================================================

    previous_red = (
        previous_close < previous_open
    )

    current_green = (
        current_close > current_open
    )

    low_sweep = (
        current_low < previous_low
    )

    close_above = (
        current_close > previous_high
    )

    upper_wick_ok = (
        second["upper_wick"]
        <= current_body * WICK_TOLERANCE
    )

    if (
        previous_red
        and current_green
        and low_sweep
        and close_above
        and upper_wick_ok
    ):

        return "LONG", current, session


    return "NO SETUP", current, session


# ============================================================
# STREAMLIT PAGE
# ============================================================

st.set_page_config(
    page_title="Vamsi Trading Monitor",
    page_icon="📊",
    layout="wide"
)


# ============================================================
# HEADER
# ============================================================

st.title("📊 VAMSI TRADING MONITOR")

st.caption(
    "30-Minute Strategy • Tokyo + New York • GMT+1"
)

st.caption(
    "Monitoring Only • NO TRADE EXECUTION"
)

st.divider()


# ============================================================
# MARKET DISPLAY
# ============================================================

columns = st.columns(3)


for column, (name, symbol) in zip(
    columns,
    MARKETS.items()
):

    with column:

        st.subheader(name)

        candles = get_candles(symbol)

        if not candles:

            st.error("❌ No market data")

            continue

        # Current market price
        try:
            price = float(
                candles[0]["close"]
            )

            st.metric(
                "Current Price",
                f"{price:.5f}"
            )

        except Exception:

            st.warning(
                "Price unavailable"
            )

        # Strategy check
        signal, candle, session = check_setup(
            candles
        )
[29-09-2026 14:47] Vamsi CNC WORKS: # Signal display
        if signal == "LONG":

            st.success(
                "🟢 LONG SETUP"
            )

        elif signal == "SHORT":

            st.error(
                "🔴 SHORT SETUP"
            )

        elif signal == "NO DATA":

            st.warning(
                "⚠️ NO DATA"
            )

        else:

            st.info(
                "⚪ NO SETUP"
            )

        # Signal candle
        if candle:

            st.write(
                f"Signal Candle: "
                f"{candle['datetime']}"
            )

        # Session
        if session:

            st.write(
                f"Session: {session}"
            )

        else:

            st.write(
                "Session: Outside trading session"
            )


# ============================================================
# STATUS
# ============================================================

st.divider()

st.subheader("📋 Monitoring Status")

st.write(
    "🟢 System is monitoring markets"
)

st.write(
    "📊 Markets: XAUUSD • BTCUSD • EURUSD"
)

st.write(
    "⏱️ Timeframe: 30 minutes"
)

st.write(
    "🌍 Session timezone: GMT+1"
)

st.write(
    "❌ Trade execution: DISABLED"
)

st.write(
    "📱 Telegram alerts: Existing bot"
)


# ============================================================
# REFRESH
# ============================================================

if st.button("🔄 Refresh Market Data"):

    st.rerun()

