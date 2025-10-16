import awswrangler as wr
import pandas as pd
from datetime import date


# -----------------------------
# Athena / Catalog configuration
# -----------------------------
CATALOG   = "awsdatacatalog/s3tablescatalog/gm-equity-tbl-bucket"  # from QueryExecutionContext
WORKGROUP = "dev-v3"                                               # Athena engine v3
S3_OUTPUT = "s3://athena-919061006621/"                            # WG output location (safe to keep)
DB        = "silver"
TABLE     = "options_daily_v2"                                     # referenced as silver.options_daily_v2



def find_nearest_expiry(ticker:str, trade_date: date)->date:
    sql = f"""
        select MIN(expiry) as min_expiry from options_daily_v2 
        where trade_date=DATE('{trade_date}') 
            and ticker = '{ticker}' 
            and expiry >= DATE('{trade_date}') 
        """
    df = athena(sql)
    expiry_value = df['min_expiry'].iloc[0]
    return expiry_value


def get_option_price(ticker: str, trade_date:date, expiry:date, strike, cp):
    sql = f"""
        SELECT strike, (bid+ask)/2 as mid_price, (bid_iv + ask_iv)/2 as mid_iv
        FROM options_daily_v2
        WHERE trade_date = DATE('{trade_date}')
        AND ticker = '{ticker}'
        AND expiry = DATE('{expiry}')
        AND cp = '{cp}'
        AND strike = {strike}
        """
    
    df = athena(sql)
    # strike = df['strike'].iloc[0]
    return df

def find_nearest_call_strike(ticker: str, trade_date:date, expiry:date, current_price):
    sql = f"""
        SELECT strike, (bid+ask)/2 as mid_price, (bid_iv + ask_iv)/2 as mid_iv
        FROM options_daily_v2
        WHERE trade_date = DATE('{trade_date}')
        AND ticker = '{ticker}'
        AND expiry = DATE('{expiry}')
        AND cp = 'C'
        AND strike >= {current_price}
        ORDER by strike asc
        LIMIT 1
        """
    
    df = athena(sql)
    strike = df['strike'].iloc[0]
    return df

def find_nearest_put_strike(ticker: str, trade_date: date, expiry:date, current_price):
    sql = f"""
        SELECT strike, (bid+ask)/2 as mid_price, (bid_iv + ask_iv)/2 as mid_iv
        FROM options_daily_v2
        WHERE trade_date = DATE('{trade_date}')
        AND ticker = '{ticker}'
        AND expiry = DATE('{expiry}')
        AND cp = 'P'
        AND strike <= {current_price}
        ORDER by strike desc
        LIMIT 1
        """
    
    df = athena(sql)
    strike = df['strike'].iloc[0]
    return df


def find_nearest_strike(ticker: str, trade_date: date, expiry: date, current_price):
    sql = f"""
        SELECT *
        FROM options_daily_v2
        WHERE ticker = '{ticker}'
        AND trade_date = DATE('{trade_date}')
        AND strike = (
        SELECT strike
        FROM options_daily_v2
        WHERE ticker = '{ticker}'
        AND expiry = DATE('{expiry}')
        AND trade_date = DATE('{trade_date}')
        ORDER BY ABS(strike - {current_price})
        LIMIT 1
  )
    """

    #sql = f"select * from options_daily_v2 where ticker='{ticker}' and trade_date = DATE('{trade_date}') limit 10"
    print(sql)
    return athena(sql)

def athena(sql: str) -> pd.DataFrame:
    """Single path for all Athena queries against the S3 Tables catalog."""
    return wr.athena.read_sql_query(
        sql=sql,
        database=DB,
        workgroup=WORKGROUP,
        data_source=CATALOG,   # IMPORTANT: non-AwsDataCatalog
        s3_output=S3_OUTPUT,
        ctas_approach=False    # REQUIRED when data_source != AwsDataCatalog
    )