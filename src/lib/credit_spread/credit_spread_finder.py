import  asyncio
import os
from lib.commons.get_daily_history import screen
from lib.tradier.tradier_client_wrapper import TradierClient
TRADIER_API_KEY = os.getenv("TRADIER_API_KEY")
TRADIER_ENDPOINT = "https://api.tradier.com/v1"
TRADIER_REQUEST_HEADERS = {
    "Authorization": f"Bearer {TRADIER_API_KEY}", 
    "Accept": "application/json"
}
    
async def main():
    print("Hello")
    async with TradierClient(api_key=TRADIER_API_KEY) as client:
        for ticker in ["SPY", "SPX"]:
            print(ticker)
            await screen(ticker, client, verbose=True)
   
if __name__ == "__main__":
    asyncio.run(main())
    

    
     
 
 