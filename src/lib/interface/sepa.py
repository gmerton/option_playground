import os, asyncio
from datetime import datetime, date
from lib.commons.get_underlying_price import get_underlying_price

from lib.commons.list_expirations import list_expirations
from lib.commons.moving_averages import get_sma, sma_trending_up_trading_days
from lib.commons.high_low import get_52w_high_low
from dateutil.relativedelta import relativedelta
from lib.commons.nyse_arca_list import nyse_arca_list, ravish_list, vrp_list, vrp_list2, nasdaq_list
from lib.commons.list_contracts import list_contracts_for_expiry
from lib.tradier.tradier_client_wrapper import TradierClient

TRADIER_API_KEY = os.getenv("TRADIER_API_KEY")
TRADIER_ENDPOINT = "https://api.tradier.com/v1"
TRADIER_REQUEST_HEADERS = {
    "Authorization": f"Bearer {TRADIER_API_KEY}", 
    "Accept": "application/json"
}

async def main():
    async with TradierClient(api_key=TRADIER_API_KEY) as t:
        ticker = "AAPL"
        ma = await get_sma(t, ticker)
        rng = await get_52w_high_low(t, ticker)
        spot = await get_underlying_price(ticker, client=t)
        trend_1m = await sma_trending_up_trading_days(t, ticker, lookback_trading_days=21)
        trend_5m = await sma_trending_up_trading_days(t, ticker, lookback_trading_days=105, min_delta_pct=0.01)

        print(trend_1m)
        print(trend_5m)

        passesRule1= spot > ma.sma_150 and spot > ma.sma_200
        passesRule2 = ma.sma_150 > ma.sma_200
        passesRule3 = trend_1m.is_up and trend_5m.is_up
        passesRule4 = ma.sma_50 > ma.sma_150 and ma.sma_50 > ma.sma_200
        passesRule5 = spot > ma.sma_50
        passesRule6 = spot >= 1.3 * rng.low_52w
        passesRule7 = spot >= 0.75 * rng.high_52w
        print(ma)
        print(rng)
        print(spot)

        print(f"Rule 1 {passesRule1}")
        print(f"Rule 2 {passesRule2}")
        print(f"Rule 3 {passesRule3}")
        print(f"Rule 4 {passesRule4}")
        print(f"Rule 5 {passesRule5}")
        print(f"Rule 6 {passesRule6}")
        print(f"Rule 7 {passesRule7}")


asyncio.run(main())