import os
import requests
from datetime import datetime, timezone, time
from zoneinfo import ZoneInfo

TWELVE_API_KEY = os.environ["TWELVE_API_KEY"]
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

MARKETS = {
    "XAU/USD": "XAUUSD",
    "BTC/USD": "BTCUSD",
    "EUR/USD": "EURUSD",
}

# =========================
# SESSION SETTINGS - INDIA TIME
# =========================

# Asian Session
ASIAN_START = time(5, 30)
ASIAN_END = time(14, 30)

# New York Session
NY_START = time(17, 30)
NY_END = time(2, 30)

IST = ZoneInfo("Asia/Kolkata")


def is_allowed_session(candle_datetime):
    """
    Check whether the candle belongs to
    Asian or New York trading session.
    """

    # Twelve Data datetime normally comes without timezone.
    # Treat it as UTC.
    try:
        candle_time = datetime.fromisoformat(
            candle_datetime.replace("Z", "+00:00")
        )
    except Exception:
        candle_time = datetime.strptime(
            candle_datetime, "%Y-%m-%d %H:%M:%S"
        ).replace(tzinfo=timezone.utc)

    # Convert to India time
    india_time = candle_time.astimezone(IST)
    current_time = india_time.time()

    # Asian session
    asian_session = (
        ASIAN_START <= current_time <= ASIAN_END
    )

    # New York session crosses midnight
    ny_session = (
        current_time >= NY_START
        or current_time <= NY_END
    )

    return asian_session or ny_session


def get_candles(symbol):
    url = "https://api.twelvedata.com/time_series"

    params = {
        "symbol": symbol,
        "interval": "30min",
        "outputsize": 3,
        "apikey": TWELVE_API_KEY,
    }

    r = requests.get(url, params=params, timeout=20)
    data = r.json()

    if "values" not in data:
        raise Exception(f"{symbol}: {data}")

    return data["values"]


def candle_body(candle):
    return abs(float(candle["close"]) - float(candle["open"]))


def check_setup(symbol, name):
    candles = get_candles(symbol)

    # Latest candle may still be forming.
    # We use the two candles immediately before it.
    current = candles[1]
    previous = candles[2]

    # =========================
    # SESSION CHECK
    # =========================

    if not is_allowed_session(current["datetime"]):
        return None, current

    current_open = float(current["open"])
    current_close = float(current["close"])
    previous_open = float(previous["open"])
    previous_close = float(previous["close"])

    current_body = candle_body(current)
    previous_body = candle_body(previous)

    # LONG
    long_setup = (
        previous_close < previous_open
        and current_close > current_open
        and current_body > previous_body
    )

    # SHORT
    short_setup = (
        previous_close > previous_open
        and current_close < current_open
        and current_body > previous_body
    )

    if long_setup:
        return "🟢 LONG", current

    if short_setup:
        return "🔴 SHORT", current

    return None, current


def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    requests.post(
        url,
        data={
            "chat_id": CHAT_ID,
            "text": message,
        },
        timeout=20,
    )


def main():
    for symbol, name in MARKETS.items():
        try:
            signal, candle = check_setup(symbol, name)

            if signal:
                message = (
                    f"{signal} SETUP\n\n"
                    f"Market: {name}\n"
                    f"Timeframe: 30M\n"
                    f"Open: {candle['open']}\n"
                    f"Close: {candle['close']}\n"
                    f"Body: {candle_body(candle):.5f}\n"
                    f"Candle: {candle['datetime']}\n\n"
                    f"⚠️ Candle-close signal"
                )

                send_telegram(message)
                print(message)

            else:
                print(f"{name}: No setup / Outside session")

        except Exception as e:
            print(f"{name}: ERROR - {e}")


if __name__ == "__main__":
    main()
