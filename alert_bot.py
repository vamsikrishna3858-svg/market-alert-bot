import os
import requests
from datetime import datetime, timezone

TWELVE_API_KEY = os.environ["TWELVE_API_KEY"]
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

MARKETS = {
    "XAU/USD": "XAUUSD",
    "BTC/USD": "BTCUSD",
    "EUR/USD": "EURUSD",
    "USD/JPY": "USDJPY",
}


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

    current_open = float(current["open"])
    current_close = float(current["close"])
    previous_open = float(previous["open"])
    previous_close = float(previous["close"])

    current_body = candle_body(current)
    previous_body = candle_body(previous)

    # LONG: previous RED + current GREEN + current body bigger
    long_setup = (
        previous_close < previous_open
        and current_close > current_open
        and current_body > previous_body
    )

    # SHORT: previous GREEN + current RED + current body bigger
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
                print(f"{name}: No setup")

        except Exception as e:
            print(f"{name}: ERROR - {e}")


if __name__ == "__main__":
    main()
