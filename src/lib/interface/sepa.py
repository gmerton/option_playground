import os, asyncio
from datetime import datetime, date
from lib.commons.get_underlying_price import get_underlying_price

from lib.commons.volume_breakout import volume_confirmation_eod
from lib.commons.list_expirations import list_expirations
from lib.commons.pivot_detector import pivot_signal_eod_trading_days
from lib.commons.moving_averages import get_sma, sma_trending_up_trading_days
from lib.commons.high_low import get_52w_high_low
from lib.commons.vol_compression import volatility_compression_trading_days
from dateutil.relativedelta import relativedelta
from lib.commons.list_contracts import list_contracts_for_expiry
from lib.tradier.tradier_client_wrapper import TradierClient
from lib.commons.nyse_arca_list import nyse_list, nyse_arca_list, ravish_list, vrp_list, vrp_list2, nasdaq_list

TRADIER_API_KEY = os.getenv("TRADIER_API_KEY")
TRADIER_ENDPOINT = "https://api.tradier.com/v1"
TRADIER_REQUEST_HEADERS = {
    "Authorization": f"Bearer {TRADIER_API_KEY}", 
    "Accept": "application/json"
}

async def main():
    async with TradierClient(api_key=TRADIER_API_KEY) as t:
        vic_list = ["BCP", "SE", "WSM", "HON", "UDMY", "CABA", 
                    "CTEV", "DERM", "SSNC", "CYTK", "CMCSA", "RNAC", "FOXF", "NSA", "ASIC", "CPHC", "AEVA", "MIR", "CCO","CYRX", "POST", "CHE", "TICAW", "SHEN", "NRP",
        "PRPH", "APPN", "BA", "TPB", "CRMT", "HGV", "NCLH", "CHDN",
        "ROCK", "COMP", "ATL", "CELH", "ASAN", "ODFL", "TTSH", "VOXR","LEN",]

        fool_list = ["AAPL","ABNB","ACN","ADBE","ADSK","ADYE.Y","ALK","ALKS","AMD","AMG","AMGN","AMZN","ANET","ASML","ATZA.F","BAND","BKNG","BLD","BRK.B","BROS","BWA","PHIN","CART","CASY","CBOE","CELH","CGNX","CHWY","CME","CMG","CMI","CNI","COHR","COST","CPNG","CRM","CRUS","CRWD","CTAS","CVS","DAR","DASH","DASTY","DDOG","DGX","DIS","DOCS","DOCU","DXCM","EBAY","PYPL","ECL","ELF","EME","ENPH","EQT","FDX","FICO","FIX","FTNT","FVRR","GEHC","GILD","GLW","GMED","GOOG","GRAB","GRMN","H","HAS","HCA","HEI","HUBS","HWM","IBKR","IDXX","ILMN","INTU","IT","JD","JKHY","KD","KLAR","KMX","KNSL","LKNC.Y","LKQ","LMND","LRCX","LULU","MA","MAR","MASI","MCK","MELI","META","MKC","MNST","MSFT","MTCH","MTH","MTN","NBIX","NDAQ","NET","NFLX","NICE","NKE","NOW","NTDOY","NVDA","NVO","NYT","ODFL","OKTA","ONON","PAC","PAYC","PGR","PSTG","PYPL","RACE","RBLX","RH","RKLB","ROKU","ROL","RPM","SBUX","SFIX","SHOP","SHW","SNOW","SNPS","SPOT","STN","STRL","SYY","TDG","TEAM","TFC","TJX","TMUS","TNC","TOST","TSCO","TSLA","TTAN","TTC","TTD","TTWO","TWLO","TXRH","TXT","TYL","U","UHAL","ULTA","UNP","UPST","V","VEEV","VLTO","VRNS","VRTX","WAB","WDAY","WEX","WING","WIX","WM","WSM","WSO","XYZ","ZBRA","ZM","ZS"]

        oquants_momentum = ["UCO", "USO", "PPTA", "FCX", "UNG", "EWZ", "ZETA", "PBR", "TZA", "MU", "XOP", "VZLA", "RH", "SGML", "QXO","MOS", "AA", "LAC", "SKYT", "STLA", "MLTX", "TMC", "XLE", "KTOS", "INTU"]

        young_list= [
            "BULL", "CRCL","ALAB", "EQPT", "OMDA",
            "RIVN", "CRWV", "RDDT", "CART", "AFRM",
            "PLTR", "PINS", "UBER", "ZM", "DDOG",
            "CRWD", "KNSL"

        ]

        holdings_list = ["AMD", "AMZN", "AXP", "GOOG", "GPGI", "GSL",
                         "POOL", "TSM", "GILD",
                         "USAR", "WDC", "CRUS", "YETI", "ZM", "CRUS", "SNDK", "NXT", "PLXS"]

        finviz_list = ["CALM", "CPRX", "CRMD", "CRUS",
                       "DMLP", "GSL", "IDCC", "INMD", "ITRN",
                       "MCRI", "NRDS", "NTES", "TROW", "YELP",
                       "YETI", "ZM"
                       ]
        new_high_list = [
            "TMO", "AMGN", "SAN", "BBVA", "FCX", "B", "BKR", "ABEV",
            "BBD", "BBDO", "NTR", "KB","MTB", "FITB", "ZM", "SHG",
            "HBAN", "KEP", "TECK", "VIV", "KOF", "BG", "KTOS",
            "ENTG", "BSAC"
        ]

        i=0;
        for ticker in nyse_list:

            # vcp_result = await volatility_compression_trading_days(t,ticker)
            # if not vcp_result.is_compressing:
            #     continue
            
            # print("Is compressing?", vcp_result.is_compressing)
            # print("ATR%:", vcp_result.atr_pct)
            # print("ATR% percentile:", vcp_result.atr_pct_rank)
            # print("Avg ranges (5/20/60):",
            # vcp_result.avg_range_5,
            # vcp_result.avg_range_20,
            # vcp_result.avg_range_60)
            # volume_result = await volume_confirmation_eod(t, ticker, avg_volume_lookback=50, vol_mult=1.5)
            pivot_result = await pivot_signal_eod_trading_days(t, ticker)
            if (i % 100 == 0):
                print(i)
            if pivot_result.signal:
                print(f"{ticker} passes sepa, pivot signal {pivot_result.signal}, overextended {pivot_result.extended}")

            i= i+1;
            continue;
            ma = await get_sma(t, ticker)
            rng = await get_52w_high_low(t, ticker)
            spot = await get_underlying_price(ticker, client=t)
            trend_1m = await sma_trending_up_trading_days(t, ticker, lookback_trading_days=21)
            trend_5m = await sma_trending_up_trading_days(t, ticker, lookback_trading_days=105, min_delta_pct=0.01)
            if ma.sma_150 is None or ma.sma_200 is None or rng.low_52w is None:
                continue
            
            passesRule1= ma.sma_150 is not None and spot > ma.sma_150 and spot > ma.sma_200
            passesRule2 = ma.sma_150 is not None and ma.sma_200 is not None and ma.sma_150 > ma.sma_200
            passesRule3 = trend_1m.is_up and trend_5m.is_up
            passesRule4 = ma.sma_50 > ma.sma_150 and ma.sma_50 > ma.sma_200
            passesRule5 = spot > ma.sma_50
            passesRule6 = spot >= 1.3 * rng.low_52w
            passesRule7 = spot >= 0.75 * rng.high_52w
           
            passesAllRules = passesRule1 and passesRule2 and passesRule3 and passesRule4 and passesRule5 and passesRule6 and passesRule7 
            #and volume_result.signal
            
            color = 'GREEN' if passesAllRules else 'RED'
    
            
            if passesAllRules:
                print(f"{ticker} passes sepa, pivot signal {pivot_result.signal}, overextended {pivot_result.extended}")
                #print(f"{ticker} {color} vcp: {vcp_result.is_compressing}")
                # print(f"{ticker} {color} volume: {volume_result.signal} vcp: {vcp_result.is_compressing}")
                
            # print(f"Rule 1 {passesRule1}")
            # print(f"Rule 2 {passesRule2}")
            # print(f"Rule 3 {passesRule3}")
            # print(f"Rule 4 {passesRule4}")
            # print(f"Rule 5 {passesRule5}")
            # print(f"Rule 6 {passesRule6}")
            # print(f"Rule 7 {passesRule7}")
            # print("")



asyncio.run(main())