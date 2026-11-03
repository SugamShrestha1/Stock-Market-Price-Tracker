
import requests
from django.conf import settings


FINNHUB_BASE_URL = "https://finnhub.io/api/v1"


def get_current_price(symbol):
    """
    Fetch the latest stock quote from Finnhub.
    Example: get_current_price("AAPL")
    """

    if not settings.FINNHUB_API_KEY:
        raise ValueError("Finnhub API key is not configured.")

    url = f"{FINNHUB_BASE_URL}/quote"

    params = {
        "symbol": symbol.upper(),
    }

    headers = {
        "X-Finnhub-Token": settings.FINNHUB_API_KEY,
    }

    response = requests.get(url, params=params, headers=headers, timeout=10)
    response.raise_for_status()

    data = response.json()

    if not data.get("c"):
        raise ValueError(f"No price data available for {symbol}.")

    return {
        "symbol": symbol.upper(),
        "current_price": data["c"],
        "change": data["d"],
        "percentage_change": data["dp"],
        "high": data["h"],
        "low": data["l"],
        "open": data["o"],
        "previous_close": data["pc"],
    }


def get_historical_prices(symbol, resolution, from_timestamp, to_timestamp):
    """
    Fetch daily historical candle data from Alpha Vantage for a stock symbol.
    Example: get_historical_prices("AAPL", "D", 1690000000, 1695000000)
    """
    normalized_symbol = symbol.upper()

    if resolution is None or str(resolution).upper() != "D":
        raise ValueError("Unsupported resolution. Only daily resolution 'D' is supported.")

    if not settings.ALPHA_VANTAGE_API_KEY:
        raise ValueError("Alpha Vantage API key is not configured.")

    url = "https://www.alphavantage.co/query"

    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": normalized_symbol,
        "outputsize": "compact",
        "apikey": settings.ALPHA_VANTAGE_API_KEY,
    }

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()

    data = response.json() or {}

    if data.get("Error Message"):
        raise ValueError("Alpha Vantage returned an error for the requested symbol.")

    if data.get("Note"):
        raise ValueError("Alpha Vantage API limit reached. Please try again later.")

    if data.get("Information"):
        raise ValueError("Alpha Vantage returned an informational message; please try again later.")

    time_series = data.get("Time Series (Daily)")
    if not isinstance(time_series, dict) or not time_series:
        raise ValueError(f"No historical data available for {normalized_symbol}.")

    from datetime import datetime, timezone

    records = []
    for date_label, values in time_series.items():
        try:
            timestamp = int(
                datetime.strptime(date_label, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp()
            )
            open_price = float(values.get("1. open"))
            high_price = float(values.get("2. high"))
            low_price = float(values.get("3. low"))
            close_price = float(values.get("4. close"))
            volume = int(values.get("5. volume"))
        except (TypeError, ValueError):
            continue

        if timestamp < from_timestamp or timestamp > to_timestamp:
            continue

        records.append(
            {
                "open_price": open_price,
                "high_price": high_price,
                "low_price": low_price,
                "close_price": close_price,
                "volume": volume,
                "timestamp": timestamp,
            }
        )

    if not records:
        raise ValueError(f"No historical data available for {normalized_symbol} in the requested date range.")

    return sorted(records, key=lambda item: item["timestamp"])
