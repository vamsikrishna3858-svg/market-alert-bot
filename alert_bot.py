message = (
        f"{header}\n\n"
        f"📌 {article['title']}\n\n"
        f"🎯 Markets: {markets}\n"
        f"⚡ Impact: {article['impact']}\n"
        f"📊 View: {article['bias']}\n"
        f"🕐 {published}\n"
        f"📰 Source: {article['source']}\n\n"
    )

    if article["summary"]:

        message += (
            f"💡 {shorten_summary(article['summary'])}\n\n"
        )

    message += (
        f"🔗 {article['link']}\n\n"
        f"⚠️ News information only — "
        f"not a trading signal."
    )

    return message


# ============================================================
# SORT NEWS
# ============================================================

def sort_news(articles):

    # HIGH impact first, then newest.
    return sorted(
        articles,
        key=lambda article: (
            0 if article["impact"] == "HIGH" else 1,
            -article["published"].timestamp(),
        ),
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("VAMSI MARKET NEWS BOT")
    print("=" * 60)

    print("Fetching market news...")

    articles = fetch_news()

    print(
        f"Found {len(articles)} relevant articles."
    )

    if not articles:

        print("No relevant news found.")

        # Optional status message.
        send_telegram(
            "📰 VAMSI MARKET NEWS BOT\n\n"
            "No major XAUUSD / BTCUSD / EURUSD "
            "market news found in the latest scan."
        )

        return

    sent_ids = load_sent_ids()

    new_articles = []

    for article in sort_news(articles):

        if article["id"] in sent_ids:
            continue

        new_articles.append(article)

    print(
        f"New articles: {len(new_articles)}"
    )

    # Send only a limited number per run.
    new_articles = new_articles[
        :MAX_NEWS_PER_RUN
    ]

    for article in new_articles:

        try:

            message = format_news(article)

            send_telegram(message)

            sent_ids.add(article["id"])

            print(
                f"SENT: {article['title']}"
            )

        except Exception as e:

            print(
                f"TELEGRAM ERROR: {e}"
            )

    save_sent_ids(sent_ids)

    print("=" * 60)
    print("NEWS SCAN COMPLETE")
    print("=" * 60)


if name == "main":
    main()

  
