"""
Сайт Gleeful.ru - Агентство праздников
"""

from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = '7a3f9e2c8b4d1f6e5a9c3b7d2f8e4a1b6c5d9f3e7a2b8c4d1f6e5a9c3b7d2f8e'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///party_agency.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

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

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

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

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_dummy_data():
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', email='admin@gleeful.ru', is_admin=True)
        admin.set_password('admin')
        db.session.add(admin)

    if Service.query.count() == 0:
        services_data = [
            ('Детский День Рождения', 'Полная организация детского дня рождения', 15000, 'детский'),
            ('Свадебная церемония', 'Роскошная свадебная церемония под ключ', 50000, 'взрослый'),
            ('Корпоративный Новый Год', 'Новогодняя корпоративная вечеринка', 80000, 'корпоратив'),
        ]
        for title, desc, price, cat in services_data:
            db.session.add(Service(title=title, description=desc, price=price, category=cat))

    db.session.commit()

@app.route('/')
def index():
    services = Service.query.limit(3).all()
    return render_template('index.html', services=services)

@app.route('/services')
def services():
    return render_template('services.html', services=Service.query.all())

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contacts')
def contacts():
    return render_template('contacts.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            flash(f'Добро пожаловать, {user.username}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Неверный email или пароль', 'error')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        password_confirm = request.form.get('password_confirm', '')

        if not username or len(username) < 3:
            flash('Имя пользователя должно содержать минимум 3 символа', 'error')
        elif not email or '@' not in email:
            flash('Введите корректный email', 'error')
        elif not password or len(password) < 6:
            flash('Пароль должен содержать минимум 6 символов', 'error')
        elif password != password_confirm:
            flash('Пароли не совпадают', 'error')
        elif User.query.filter_by(email=email).first():
            flash('Пользователь с таким email уже существует', 'error')
        elif User.query.filter_by(username=username).first():
            flash('Пользователь с таким именем уже существует', 'error')
        else:
            user = User(username=username, email=email, is_admin=False)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash(f'Добро пожаловать в Gleeful, {username}!', 'success')
            login_user(user)
            return redirect(url_for('index'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    logout_user()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_dummy_data()
    app.run(debug=True)
