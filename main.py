from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from vnstock import stock_intraday_data
from utils import get_latest_price, check_stock_info  # Import các hàm từ utils.py
from models import db, User, Stock
from datetime import datetime
from dotenv import load_dotenv
import pandas as pd
import time

import os
if "ACCEPT_TC" not in os.environ:
    os.environ["ACCEPT_TC"] = "tôi đồng ý"

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.getenv('SECRET_KEY')

db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    stocks = Stock.query.all()
    stock_data = []
    for stock in stocks:
        latest_price = get_latest_price(stock.symbol)
        profit_loss = (latest_price - stock.buy_price) * 100 / stock.buy_price  # Tính toán lãi/lỗ theo %
        timestamp_str = stock.timestamp if stock.timestamp else 'N/A'
        stock_data.append({
            'id': stock.id,
            'symbol': stock.symbol,
            'buy_price': stock.buy_price,
            'latest_price': latest_price,
            'profit_loss': profit_loss,
            'target1': stock.target1,
            'target2': stock.target2,
            'cut_loss': stock.cut_loss,
            'note': stock.note,
            'timestamp': timestamp_str

        })
    return render_template('index.html', stocks=stock_data, segment='index')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
        is_admin = request.form.get('is_admin') == 'on'
        user = User(username=username, password=password, is_admin=is_admin)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_stock():
    if not current_user.is_admin:
        flash('Admin access required', 'danger')
        return redirect(url_for('index'))
    if request.method == 'POST':
        symbol = request.form['symbol']
        buy_price = request.form['buy_price']
        target1 = request.form['target1'] if request.form['target1'] else None
        target2 = request.form['target2'] if request.form['target2'] else None
        cut_loss = request.form['cut_loss'] if request.form['cut_loss'] else None
        note = request.form['note']

        # Kiểm tra thông tin cổ phiếu
        if not check_stock_info(symbol):
            flash('Cổ phiếu không tồn tại hoặc sai thông tin!', 'danger')
            return redirect(url_for('add_stock'))

        new_stock = Stock(
            symbol=symbol,
            buy_price=buy_price,
            target1=target1,
            target2=target2,
            cut_loss=cut_loss,
            note=note,
            timestamp=datetime.utcnow())
        db.session.add(new_stock)
        db.session.commit()

        flash('Cổ phiếu đã được thêm thành công!', 'success')
        return redirect(url_for('index'))

    return render_template('add_stock.html',segment='add_stock')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_stock(id):
    if not current_user.is_admin:
        flash('Admin access required', 'danger')
        return redirect(url_for('index'))
    stock = Stock.query.get_or_404(id)
    if request.method == 'POST':
        stock.symbol = request.form['symbol']
        stock.buy_price = request.form['buy_price']
        stock.target1 = request.form['target1'] if request.form['target1'] else None
        stock.target2 = request.form['target2'] if request.form['target2'] else None
        stock.cut_loss = request.form['cut_loss'] if request.form['cut_loss'] else None
        stock.note = request.form['note']

        db.session.commit()
        flash('Cổ phiếu đã được cập nhật thành công!', 'success')
        return redirect(url_for('index'))

    return render_template('edit_stock.html', stock=stock)

@app.route('/delete/<int:id>')
@login_required
def delete_stock(id):
    if not current_user.is_admin:
        flash('Admin access required', 'danger')
        return redirect(url_for('index'))
    stock = Stock.query.get_or_404(id)
    db.session.delete(stock)
    db.session.commit()
    flash('Cổ phiếu đã được xóa thành công!', 'success')
    return redirect(url_for('index'))

# Route cho trang intraday_data
@app.route('/intraday_data', methods=['GET', 'POST'])
def intraday_data():
    symbol = None
    if request.method == 'POST':
        symbol = request.form['symbol']
        page_size = 5000

        # Gọi hàm stock_intraday_data từ thư viện vnstock
        start_time = time.time()
        df = stock_intraday_data(symbol=symbol, page_size=page_size)
        end_time = time.time()
        print(f"Data fetch time: {end_time - start_time} seconds")

        # Lọc DataFrame để chỉ hiển thị các dòng có investorType là 'WOLF' hoặc 'SHARK'
        df_filtered = df[df['investorType'].isin(['WOLF', 'SHARK'])]
        # Thêm cột Total
        df_filtered['Total'] = df_filtered['volume'] * df_filtered['averagePrice']

        # Tạo bảng thống kê số lượng giao dịch và tổng giá trị giao dịch
        summary_df = df_filtered.groupby(['investorType', 'orderType']).agg(
            trade_count=('orderType', 'size'),
            total_value=('Total', 'sum')
        ).reset_index()

        # Tạo bảng pivot để hiển thị theo định dạng yêu cầu
        pivot_df = summary_df.pivot(index='investorType', columns='orderType', values=['trade_count', 'total_value']).fillna(0)
        pivot_df.columns = [f'{i}_{j}' for i, j in pivot_df.columns]
        pivot_df = pivot_df.reset_index()

        # Định dạng lại các cột giá trị tổng
        pivot_df['total_value_Buy Up'] = pivot_df['total_value_Buy Up'].apply(lambda x: "{:,.0f}".format(x).replace(",", "."))
        pivot_df['total_value_Sell Down'] = pivot_df['total_value_Sell Down'].apply(lambda x: "{:,.0f}".format(x).replace(",", "."))

        # Tạo HTML cho bảng thống kê
        summary_html = '<div class="card card-body border-0 shadow table-wrapper table-responsive">'
        summary_html += '<table class="table table-hover">'
        summary_html += '<thead><tr>'
        summary_html += '<th class="border-gray-200">INVESTORTYPE</th>'
        summary_html += '<th class="border-gray-200">COUNT BUY</th>'
        summary_html += '<th class="border-gray-200">VALUE BUY</th>'
        summary_html += '<th class="border-gray-200">COUNT SELL</th>'
        summary_html += '<th class="border-gray-200">VALUE SELL</th>'
        summary_html += '</tr></thead>'
        summary_html += '<tbody>'

        for index, row in pivot_df.iterrows():
            summary_html += '<tr>'
            summary_html += f'<td>{row["investorType"]}</td>'
            summary_html += f'<td>{int(row["trade_count_Buy Up"])}</td>'
            summary_html += f'<td>{row["total_value_Buy Up"]}</td>'
            summary_html += f'<td>{int(row["trade_count_Sell Down"])}</td>'
            summary_html += f'<td>{row["total_value_Sell Down"]}</td>'
            summary_html += '</tr>'

        summary_html += '</tbody></table>'
        summary_html += '</div>'

        # Lọc cột cần thiết cho bảng chính
        selected_columns = ['ticker', 'time', 'investorType', 'orderType', 'volume', 'averagePrice', 'Total']
        df_selected = df_filtered[selected_columns]

        # Định dạng các số trong các cột volume, averagePrice, và Total
        df_selected['volume'] = df_selected['volume'].apply(lambda x: "{:,.0f}".format(x).replace(",", "."))
        df_selected['averagePrice'] = df_selected['averagePrice'].apply(lambda x: "{:,.0f}".format(x).replace(",", "."))
        df_selected['Total'] = df_selected['Total'].apply(lambda x: "{:,.0f}".format(x).replace(",", "."))

        # Tạo HTML cho bảng chính
        table_html = '<div class="card card-body border-0 shadow table-wrapper table-responsive">'
        table_html += '<table class="table table-hover">'
        table_html += '<thead><tr>'
        for col in df_selected.columns:
            table_html += f'<th class="border-gray-200">{col}</th>'
        table_html += '</tr></thead>'
        table_html += '<tbody>'

        # Sử dụng Pandas để tạo HTML table với định dạng và class
        def get_row_class(row):
            return 'fw-bold' if row['investorType'] == 'SHARK' else ''

        def get_order_class(order_type):
            if order_type == 'Sell Down':
                return 'text-danger'
            elif order_type == 'Buy Up':
                return 'text-success'
            return ''

        for index, row in df_selected.iterrows():
            row_class = get_row_class(row)
            table_html += f'<tr class="{row_class}">'
            for col, value in row.items():
                if col == 'orderType':
                    order_class = get_order_class(value)
                    table_html += f'<td class="{order_class}">{value}</td>'
                else:
                    table_html += f'<td>{value}</td>'
            table_html += '</tr>'

        table_html += '</tbody></table>'
        table_html += '</div>'

        return render_template('intraday_data.html', tables=table_html, symbol=symbol,
                               summary_html=summary_html)

    return render_template('intraday_data.html')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
