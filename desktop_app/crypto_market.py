import requests

COMMON_ALIASES = {
    "btc": "BTCUSDT",
    "биткоин": "BTCUSDT",
    "биток": "BTCUSDT",
    "bitcoin": "BTCUSDT",
    "eth": "ETHUSDT",
    "эфир": "ETHUSDT",
    "ethereum": "ETHUSDT",
    "sol": "SOLUSDT",
    "солана": "SOLUSDT",
    "solana": "SOLUSDT",
    "ton": "TONUSDT",
    "тон": "TONUSDT",
    "doge": "DOGEUSDT",
    "доги": "DOGEUSDT",
    "xrp": "XRPUSDT",
    "рипл": "XRPUSDT",
    "bnb": "BNBUSDT",
    "pepe": "PEPEUSDT",
    "not": "NOTUSDT",
    "нот": "NOTUSDT",
    "sui": "SUIUSDT",
    "near": "NEARUSDT",
    "apt": "APTUSDT",
    "avax": "AVAXUSDT"
}


def normalize_symbol(user_input):
    clean = user_input.strip().lower().replace("/", "").replace("-", "")
    if clean in COMMON_ALIASES:
        return COMMON_ALIASES[clean]
    if not clean.endswith("usdt"):
        cand = clean.upper() + "USDT"
    else:
        cand = clean.upper()
    return cand


def fetch_crypto_ticker(symbol_or_coin):
    """
    Получает живые биржевые котировки с Binance API без необходимости API-ключа.
    """
    pair = normalize_symbol(symbol_or_coin)
    url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={pair}"

    try:
        resp = requests.get(url, timeout=3.5)
        if resp.status_code == 200:
            d = resp.json()
            last_price = float(d["lastPrice"])
            change_pct = float(d["priceChangePercent"])
            high_price = float(d["highPrice"])
            low_price = float(d["lowPrice"])
            vol = float(d.get("quoteVolume", 0))

            # Форматирование цены в зависимости от величины
            if last_price >= 100:
                price_str = f"${last_price:,.2f}"
            elif last_price >= 1:
                price_str = f"${last_price:,.4f}"
            else:
                price_str = f"${last_price:,.6f}"

            direction = "+" if change_pct >= 0 else ""

            return {
                "ok": True,
                "pair": f"{pair.replace('USDT', '')}/USDT",
                "price": price_str,
                "change": f"{direction}{change_pct:.2f}%",
                "is_positive": change_pct >= 0,
                "high": f"${high_price:,.2f}" if high_price >= 10 else f"${high_price:,.4f}",
                "low": f"${low_price:,.2f}" if low_price >= 10 else f"${low_price:,.4f}",
                "volume": f"${vol/1_000_000:,.1f}M"
            }
        else:
            return {"ok": False, "error": f"Пара {pair} не найдена на бирже"}
    except Exception as e:
        return {"ok": False, "error": f"Сбой сети котировок: {str(e)[:40]}"}


def fetch_top_crypto_summary():
    """
    Краткая сводка по топ-монетам (BTC, ETH, SOL, TON) для бегущей строки или панели.
    """
    results = []
    for sym, label in [("BTCUSDT", "BTC"), ("ETHUSDT", "ETH"), ("SOLUSDT", "SOL"), ("TONUSDT", "TON")]:
        try:
            r = requests.get(f"https://api.binance.com/api/v3/ticker/24hr?symbol={sym}", timeout=2.5)
            if r.status_code == 200:
                d = r.json()
                p = float(d["lastPrice"])
                ch = float(d["priceChangePercent"])
                sign = "+" if ch >= 0 else ""
                results.append(f"{label}: ${p:,.0f} ({sign}{ch:.1f}%)")
        except Exception:
            pass
    return " | ".join(results) if results else "BTC, ETH, SOL, TON онлайн"
