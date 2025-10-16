from polygon import RESTClient
from pathlib import Path
from earnings_cache import save_json, load_json
import pandas as pd
from stock_query import fetch_closes_for_date
from option_query import find_nearest_expiry, find_nearest_put_strike, find_nearest_call_strike, get_option_price



CACHE = Path("data/earnings_AAPL.json")

import pandas as pd
from datetime import date

def previous_business_day(earnings_date: str, lookback_period: int) -> date:
    """
    Return the single business date that is `lookback_period` business days 
    before the given earnings_date.

    Args:
        earnings_date (str): Date string in 'YYYY-MM-DD' or 'MM/DD/YYYY' format.
        lookback_period (int): Number of prior business days to look back.

    Returns:
        datetime.date: The business day that is `lookback_period` days before earnings_date.
    """
    # Normalize input date
    dt = pd.to_datetime(earnings_date)

    # Generate a business day range ending before the earnings date
    days = pd.bdate_range(end=dt - pd.Timedelta(days=1), periods=lookback_period)

    # Return as a Python datetime.date
    return days[0].date()


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
    lookback_period = 5
    earnings_period_count = 10
    ticker = 'AXP'
    earnings_data = fetch_and_cache_earnings(ticker, use_cache=True)
    filtered_earnings_data = [item for item in earnings_data if item['date_status'] == 'confirmed' and item['date'] < '2025-10-01']
    
    filtered_earnings_data = sorted(
        filtered_earnings_data,
        key=lambda x: x['date'],
        reverse=True
    )[:earnings_period_count]

    for earnings_item in filtered_earnings_data:
        print(f"{earnings_item['date']} {earnings_item['time']} {earnings_item['date_status']}")
    #print(data)

    # print(f"Loaded {len(data)} records (from {'cache' if CACHE.exists() else 'API'}).")
    # test_downstream()
    # dates = ["10/08/2024", "10/09/2024"]
    
    # result = fetch_closes_for_dates(
    #     dates,
    #     ticker="AAPL"
    # )

    
    strangle_returns = {}
    for earnings_item in filtered_earnings_data:
        earnings_date = earnings_item['date']
        # earnings_date = '2023-08-03'
        print(f"earnings date: {earnings_date}")
        # Get period start date.  ToDo: factor in BMO, AMC
        period_start = previous_business_day(earnings_date, lookback_period)
        print(f"Lookback period start date: {period_start}")
        initial_underlying_price = fetch_closes_for_date(
               period_start,
               ticker=ticker
           )
        print(f"Price of {ticker} on {period_start}: {initial_underlying_price}")
    
        # For each earnings date, find the next available expiry

        expiry = find_nearest_expiry(ticker, earnings_date)
        print(f"First post-earnings option expiration: {expiry}")
        initial_put = find_nearest_put_strike(ticker, period_start, expiry, initial_underlying_price)
        initial_call = find_nearest_call_strike(ticker, period_start, expiry, initial_underlying_price)
        p_strike = initial_put["strike"].iloc[0]
        c_strike = initial_call["strike"].iloc[0]
        initial_strangle_price = round(initial_put["mid_price"].iloc[0] + initial_call["mid_price"].iloc[0],2)

        print(f"strangle strikes: {p_strike}, {c_strike}")
        print(f"initial strangle price: {initial_strangle_price}")

        df_p = get_option_price(ticker, earnings_date, expiry, p_strike, "P")
        df_c = get_option_price(ticker, earnings_date, expiry, c_strike, "C")

        final_strangle_price = round(df_p["mid_price"].iloc[0] + df_c["mid_price"].iloc[0],2)
        print(f"final_strangle_price: {final_strangle_price}")
        strangle_return = round((final_strangle_price - initial_strangle_price) / initial_strangle_price,2)
        print(f"strangle return = {strangle_return}")
        strangle_returns[earnings_date]= float(strangle_return)
    print(strangle_returns)
