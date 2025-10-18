import os, asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from datetime import datetime, date

TRADIER_API_KEY = os.getenv("TRADIER_API_KEY")
TRADIER_ENDPOINT = "https://api.tradier.com/v1"
TRADIER_REQUEST_HEADERS = {
    "Authorization": f"Bearer {TRADIER_API_KEY}", 
    "Accept": "application/json"
}

def retrieveOptionChain(ticker, expiry):
    