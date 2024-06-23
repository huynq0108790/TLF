from flask import Flask, render_template, request
from vnstock import stock_intraday_data  # Đảm bảo bạn đã import hàm stock_intraday_data từ thư viện vnstock
import pandas as pd

app = Flask(__name__)

# Route cho trang intraday_data
@app.route('/intraday_data', methods=['GET', 'POST'])
def intraday_data():
    symbol = None
    if request.method == 'POST':
        symbol = request.form['symbol']
        page_size = 5000

        # Gọi hàm stock_intraday_data từ thư viện vnstock
        df = stock_intraday_data(symbol=symbol, page_size=page_size)

        # Chuyển đổi DataFrame thành HTML
        df_html = df.to_html(classes='data', header="true").replace('\n', '')

        return render_template('intraday_data.html', tables=df, symbol=symbol)

    return render_template('intraday_data.html')

if __name__ == '__main__':
    app.run(debug=True)
