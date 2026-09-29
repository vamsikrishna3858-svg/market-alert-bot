import os
import requests
import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta


# ============================================================
# SETTINGS
# ============================================================

TWELVE_API_KEY = os.environ["TWELVE_API_KEY"]

TIMEFRAME = "30min"

# Fixed GMT+1 session timezone
GMT_PLUS_1 = timezone(timedelta(hours=1))

# ------------------------------------------------------------
# SESSION TIMES — GMT+1
# Change these ONLY if your TradingView Sessions indicator
# uses different Tokyo / New York hours.
# ------------------------------------------------------------

TOKYO_START = 0
TOKYO_END = 9

NEW_YORK_START = 13
NEW_YORK_END = 22

# Closing-side wick tolerance
# Example:
# SHORT = lower wick must be <= 25% of candle body
# LONG  = upper wick must be <= 25% of candle body
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

    # Newest candle first
    candles.sort(
        key=lambda x: x["datetime"],
        reverse=True
    )

    return candles


# ============================================================
# PARSE CANDLE TIME
# ============================================================

def candle_datetime_utc(candle):

    return datetime.strptime(
        candle["datetime"],
        "%Y-%m-%d %H:%M:%S"
    ).replace(tzinfo=timezone.utc)


# ============================================================
# CHECK WHETHER CANDLE IS FULLY CLOSED
# ============================================================

def get_closed_candles(candles):

    now = datetime.now(timezone.utc)

    closed = []

    for candle in candles:

        candle_time = candle_datetime_utc(candle)

        # 30-minute candle must have completely finished.
        #
        # A candle timestamp represents its opening time.
        # Therefore add 30 minutes before considering it closed.

        candle_close_time = candle_time + timedelta(minutes=30)

        if candle_close_time <= now:
            closed.append(candle)

    return closed


# ============================================================
# SESSION CHECK — GMT+1
# ============================================================

def is_trading_session(candle):

    utc_time = candle_datetime_utc(candle)

    # Convert UTC → fixed GMT+1
    session_time = utc_time.astimezone(GMT_PLUS_1)

    hour = session_time.hour

    # Tokyo
    if TOKYO_START <= hour < TOKYO_END:
        return "TOKYO"

    # New York
    if NEW_YORK_START <= hour < NEW_YORK_END:
        return "NEW YORK"

    return None


# ============================================================
# CANDLE INFORMATION
# ============================================================

def candle_data(candle):

    candle_open = float(candle["open"])
    candle_high = float(candle["high"])
    candle_low = float(candle["low"])
    candle_close = float(candle["close"])

    body = abs(candle_close - candle_open)

    upper_wick = candle_high - max(
        candle_open,
        candle_close
    )

    lower_wick = min(
        candle_open,
        candle_close
    ) - candle_low
