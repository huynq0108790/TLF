from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from utils import get_latest_price, check_stock_info  # Import các hàm từ utils.py

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgre:gWRSMQ18BiaF89X6TpE7b5fQ86etCQ5k@dpg-cpo0086ehbks738etiu0-a.5432/stockpg'
#internal db postgres://postgre:gWRSMQ18BiaF89X6TpE7b5fQ86etCQ5k@dpg-cpo0086ehbks738etiu0-a/stockpg
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'supersecretkey'  # Thêm khóa bí mật để sử dụng flash messages
# app.config.from_object(Configdb)
db = SQLAlchemy(app)


class Stock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(10), nullable=False)
    buy_price = db.Column(db.Float, nullable=False)
    target1 = db.Column(db.Float, nullable=True)
    target2 = db.Column(db.Float, nullable=True)
    cut_loss = db.Column(db.Float, nullable=True)
    note = db.Column(db.String(200), nullable=True)

    def __repr__(self):
        return f'<Stock {self.symbol}>'


@app.route('/')
def index():
    stocks = Stock.query.all()
    stock_data = []
    for stock in stocks:
        latest_price = get_latest_price(stock.symbol)
        #latest_price = 0
        stock_data.append({
            'id': stock.id,
            'symbol': stock.symbol,
            'buy_price': stock.buy_price,
            'latest_price': latest_price,
            'target1': stock.target1,
            'target2': stock.target2,
            'cut_loss': stock.cut_loss,
            'note': stock.note
        })

    return render_template('index.html', stocks=stock_data)


@app.route('/add', methods=['GET', 'POST'])
def add_stock():
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

        new_stock = Stock(symbol=symbol, buy_price=buy_price, target1=target1, target2=target2, cut_loss=cut_loss, note=note)
        db.session.add(new_stock)
        db.session.commit()

        flash('Cổ phiếu đã được thêm thành công!', 'success')
        return redirect(url_for('index'))

    return render_template('add_stock.html')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_stock(id):
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
def delete_stock(id):
    stock = Stock.query.get_or_404(id)
    db.session.delete(stock)
    db.session.commit()
    flash('Cổ phiếu đã được xóa thành công!', 'success')
    return redirect(url_for('index'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
