from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from utils import get_latest_price, check_stock_info  # Import các hàm từ utils.py
from models import db, User, Stock
from datetime import datetime
from dotenv import load_dotenv
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
    return render_template('index.html', stocks=stock_data)

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

    return render_template('add_stock.html')

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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
