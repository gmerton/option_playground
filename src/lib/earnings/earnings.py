from polygon import RESTClient
from pathlib import Path
from earnings_cache import save_json, load_json
import pandas as pd
from queries import fetch_closes_for_dates



CACHE = Path("data/earnings_AAPL.json")

def previous_business_days(earnings_date: str, lookback_period: int) -> list[str]:
    """
    Return the previous `lookback_period` business days before the given earnings_date.

    Args:
        earnings_date (str): Date string in 'YYYY-MM-DD' or 'MM/DD/YYYY' format.
        lookback_period (int): Number of prior business days to return.

    Returns:
        list[str]: List of date strings (YYYY-MM-DD) sorted ascending.
    """
    # Normalize input date
    date = pd.to_datetime(earnings_date)
    # Generate a range of business days ending *before* the earnings date
    days = pd.bdate_range(end=date - pd.Timedelta(days=1), periods=lookback_period)
    return [d.strftime("%Y-%m-%d") for d in days]


def fetch_and_cache_earnings(ticker: str = "AAPL", use_cache: bool = True):
    if use_cache and CACHE.exists():
        return load_json(CACHE)

    client = RESTClient("kM4B15NPLQj2QBxzQXUwaKdVytI7DrFs")
    earnings = list(client.list_benzinga_earnings(
        ticker=ticker, limit=50, sort="date.desc"
    ))
    save_json(earnings, CACHE)
    return load_json(CACHE)   # return plain dicts downstream


def test_downstream():
    data = load_json("data/earnings_AAPL.json")
    # ... use dicts directly, e.g.:
    earnings_data = data[12]
    print(data[12])
    earnings_time = earnings_data["time"]
    earnings_date = earnings_data["date"]
    lookback_period = 3
    assert data[12]["ticker"] == "AAPL"
    



if __name__ == "__main__":
    # data = fetch_and_cache_earnings("AAPL", use_cache=True)
    # print(f"Loaded {len(data)} records (from {'cache' if CACHE.exists() else 'API'}).")
    # test_downstream()
    # print(previous_business_days("10/10/2025", 2))
    dates = ["10/08/2024", "10/09/2024"]
    
    result = fetch_closes_for_dates(
        dates,
        ticker="AAPL"
    )



    print(result)
    
