def run_test():
    telegram_send(
        "✅ VAMSI AI NEWS BOT TEST SUCCESSFUL\n\n"
        "Markets: XAUUSD, BTCUSD, EURUSD\n"
        "News monitoring is configured.\n"
        "This is a test message, not a trading signal."
    )
    print("Telegram test message sent successfully.")


def main():
    if "--test" in sys.argv:
        run_test()
        return

    previous_state = load_state()
    first_run = previous_state is None
    seen = previous_state if previous_state is not None else set()

    # Collect feeds before changing the saved state.
    feeds = {}
    for market, query in MARKETS.items():
        try:
            feeds[market] = get_feed(market, query)
            print(f"{market}: fetched {len(feeds[market])} articles")
        except Exception as exc:
            print(f"ERROR fetching {market}: {exc}")
            raise

    new_seen = set(seen)
    messages = []

    for market, entries in feeds.items():
        unseen = [
            entry for entry in entries
            if article_id(entry) not in seen
        ]

        # First run sends only the newest article for each market,
        # rather than flooding Telegram with old headlines.
        limit = 1 if first_run else MAX_ARTICLES_PER_MARKET

        for entry in unseen[:limit]:
            messages.append(format_article(market, entry))

        for entry in entries:
            new_seen.add(article_id(entry))

    if not messages:
        print("No new articles. Nothing to send.")
    else:
        for message in messages:
            telegram_send(message)
            print("Telegram alert sent.")
            time.sleep(1)

    save_state(new_seen)
    print(f"Finished. Sent {len(messages)} article(s).")


if name == "main":
    try:
        main()
    except Exception as exc:
        print(f"FATAL ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
      

 

