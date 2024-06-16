import datetime
from vnstock3 import Vnstock

def get_today_price(symbol):
    stock = Vnstock().stock(symbol=symbol, source='TCBS')
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    df = stock.quote.history(start=today, end=today, interval='1D', to_df=True)
    if not df.empty:
        today_price = df
        print(f"Today's price for {symbol}:")
        print(today_price)
        return today_price
    else:
        print(f"No data available for {symbol} on {today}")
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

# Thay 'VND' bằng mã cổ phiếu bạn muốn kiểm tra
check_stock_info('SHB')
