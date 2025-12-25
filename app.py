"""
Сайт Gleeful.ru - Агентство праздников
Версия с корзиной и базовой админ-панелью
"""

from flask import Flask, render_template, request, redirect, url_for, flash, abort, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SECRET_KEY'] = '7a3f9e2c8b4d1f6e5a9c3b7d2f8e4a1b6c5d9f3e7a2b8c4d1f6e5a9c3b7d2f8e'
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "instance", "party_agency.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

@app.context_processor
def inject_cart_count():
    return dict(cart_count=get_cart_count())

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    orders = db.relationship('Order', backref='user', lazy=True)
    cart_items = db.relationship('CartItem', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    image_url = db.Column(db.String(300))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(300))
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)

class Portfolio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    image_url = db.Column(db.String(300), nullable=False)
    event_type = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total_price = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(50), default='Новый', nullable=False)
    contact_phone = db.Column(db.String(20), nullable=False)
    event_date = db.Column(db.Date, nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    price_at_moment = db.Column(db.Numeric(10, 2), nullable=False)

def get_cart_count():
    if current_user.is_authenticated:
        return CartItem.query.filter_by(user_id=current_user.id).count()
    return len(session.get('cart', []))

def get_cart_items():
    if current_user.is_authenticated:
        return [ci.service for ci in CartItem.query.filter_by(user_id=current_user.id).all() if ci.service]
    return Service.query.filter(Service.id.in_(session.get('cart', []))).all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_dummy_data():
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', email='admin@gleeful.ru', is_admin=True)
        admin.set_password('admin')
        db.session.add(admin)

    if Service.query.count() == 0:
        services = [
            ('Детский День Рождения', 'Полная организация детского дня рождения', 15000, 'детский'),
            ('Свадебная церемония', 'Роскошная свадебная церемония под ключ', 50000, 'взрослый'),
            ('Корпоративный Новый Год', 'Новогодняя корпоративная вечеринка', 80000, 'корпоратив'),
        ]
        for title, desc, price, cat in services:
            db.session.add(Service(title=title, description=desc, price=price, category=cat))
    db.session.commit()

@app.route('/')
def index():
    return render_template('index.html', services=Service.query.limit(3).all())

@app.route('/services')
def services():
    return render_template('services.html', services=Service.query.all())

@app.route('/cart/add/<int:id>', methods=['POST'])
def add_to_cart(id):
    service = Service.query.get_or_404(id)
    if current_user.is_authenticated:
        if not CartItem.query.filter_by(user_id=current_user.id, service_id=id).first():
            db.session.add(CartItem(user_id=current_user.id, service_id=id))
            db.session.commit()
    else:
        if 'cart' not in session:
            session['cart'] = []
        if id not in session['cart']:
            session['cart'].append(id)
            session.modified = True
    flash(f'Услуга "{service.title}" добавлена в корзину!', 'success')
    return redirect(request.referrer or url_for('services'))

@app.route('/cart')
def cart():
    cart_items = get_cart_items()
    total = sum(item.price for item in cart_items)
    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form.get('email')).first()
        if user and user.check_password(request.form.get('password')):
            login_user(user)
            return redirect(url_for('index'))
        flash('Неверный email или пароль', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user = User(username=request.form.get('username'), email=request.form.get('email'))
        user.set_password(request.form.get('password'))
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        abort(403)
    return render_template('admin.html',
                         services=Service.query.all(),
                         news=News.query.all(),
                         portfolio_items=Portfolio.query.all(),
                         orders=db.session.query(Order, User).join(User).all())

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_dummy_data()
    app.run(debug=True)
