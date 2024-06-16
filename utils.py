import datetime
import os

if "ACCEPT_TC" not in os.environ:
    os.environ["ACCEPT_TC"] = "tôi đồng ý"
from vnstock3 import Vnstock

def get_latest_price(symbol):
    stock = Vnstock().stock(symbol=symbol, source='TCBS')
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    try:
        df = stock.quote.history(start=today, end=today, interval='1D', to_df=True)
        if not df.empty and 'close' in df.columns and not df['close'].isnull().all():
            return df['close'].iloc[-1]
        else:
            return None
    except Exception as e:
        print(f"Error fetching price for {symbol}: {e}")
        return None

def get_stock_history(symbol, start_date, end_date):
    stock = Vnstock().stock(symbol=symbol, source='TCBS')
    try:
        df = stock.quote.history(start=start_date, end=end_date, interval='1D')
        print(f"Data for {symbol} from {start_date} to {end_date}:")
        print(df)
        if df is not None and not df.empty:
            return df
        else:
            return None
    except Exception as e:
        print(f"Error fetching history for {symbol}: {e} {start_date}")
        return None

def check_stock_info(symbol):
    try:
        stock = Vnstock().stock(symbol=symbol, source='TCBS')
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        df = stock.quote.history(start=today, end=today, interval='1D', to_df=True)
        return not df.empty
    except Exception as e:
        print(f"Error checking stock info for {symbol}: {e}")
        return False
