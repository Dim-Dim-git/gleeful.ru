"""
Сайт Gleeful.ru
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

db_path = os.environ.get('DATABASE_PATH', os.path.join(basedir, 'instance', 'party_agency.db'))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

@app.context_processor
def inject_cart_count():
    """
    Контекст-процессор для передачи количества товаров в корзине во все шаблоны.

    """
    return dict(cart_count=get_cart_count())

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Пожалуйста, войдите для доступа к этой странице.'

class User(UserMixin, db.Model):
    """
    Модель пользователя системы.

    Атрибуты:
        id: Уникальный идентификатор пользователя.
        username: Имя пользователя (уникальное, до 80 символов).
        email: Email адрес (уникальный, до 120 символов).
        password_hash: Хеш пароля пользователя.
        is_admin: Флаг административных прав доступа.
        created_at: Дата и время регистрации пользователя.

    """

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    orders = db.relationship('Order', backref='user', lazy=True)
    cart_items = db.relationship('CartItem', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        """
        Устанавливает хеш пароля для пользователя.

        """
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """
        Проверяет соответствие пароля хешу.
        """
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class CartItem(db.Model):
    """
    Товар в корзине пользователя.

    """

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (db.UniqueConstraint('user_id', 'service_id', name='unique_user_service'),)

    def __repr__(self):
        return f'<CartItem User:{self.user_id} Service:{self.service_id}>'

class Service(db.Model):
    """
    Услуги, предоставляемые агентством.

    """

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    image_url = db.Column(db.String(300))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    order_items = db.relationship('OrderItem', backref='service', lazy=True)
    cart_items = db.relationship('CartItem', backref='service', lazy=True)

    def __repr__(self):
        return f'<Service {self.title}>'

class News(db.Model):
    """
    новости на сайте.


    """

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(300))
    date_posted = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<News {self.title}>'

class Portfolio(db.Model):
    """
    Работы в портфолио агентства.

    """

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    image_url = db.Column(db.String(300), nullable=False)
    event_type = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<Portfolio {self.title}>'

class Order(db.Model):
    """
    Заказы.

    """

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total_price = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(50), default='Новый', nullable=False)
    contact_phone = db.Column(db.String(20), nullable=False)
    event_date = db.Column(db.Date, nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    order_items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Order {self.id}>'

class OrderItem(db.Model):
    """
    Позиции в заказе.

    """

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    price_at_moment = db.Column(db.Numeric(10, 2), nullable=False)

    def __repr__(self):
        return f'<OrderItem Order:{self.order_id} Service:{self.service_id}>'

def get_cart_count():
    """
    Возвращает количество товаров в корзине текущего пользователя.

    """
    if current_user.is_authenticated:
        return CartItem.query.filter_by(user_id=current_user.id).count()
    else:
        return len(session.get('cart', []))

def get_cart_items():
    """
    Возвращает список услуг в корзине текущего пользователя.

    """
    if current_user.is_authenticated:
        cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
        return [ci.service for ci in cart_items if ci.service]
    else:
        cart_ids = session.get('cart', [])
        if not cart_ids:
            return []
        return Service.query.filter(Service.id.in_(cart_ids)).all()

def get_cart_total():
    """
    Вычисляет общую стоимость товаров в корзине..
    """
    cart_items = get_cart_items()
    return sum(item.price for item in cart_items)

def merge_cart_to_user(user):
    """
    Переносит товары из сессионной корзины в корзину авторизованного пользователя.
    """
    try:
        session_cart_ids = session.get('cart', [])

        if not session_cart_ids:
            return 0

        existing_cart_service_ids = [
            ci.service_id for ci in CartItem.query.filter_by(user_id=user.id).all()
        ]

        added_count = 0
        for service_id in session_cart_ids:
            service = Service.query.get(service_id)
            if not service:
                continue

            if service_id not in existing_cart_service_ids:
                cart_item = CartItem(
                    user_id=user.id,
                    service_id=service_id
                )
                db.session.add(cart_item)
                added_count += 1

        if added_count > 0:
            db.session.commit()
            app.logger.info(f'Слияние корзины: добавлено {added_count} услуг для пользователя {user.username}')

        session['cart'] = []
        session.modified = True

        return added_count

    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Ошибка при слиянии корзины: {str(e)}')
        return 0

@login_manager.user_loader
def load_user(user_id):
    """
    Загружает пользователя по ID для Flask-Login.
    """
    try:
        user_id = int(user_id)
        user = User.query.get(user_id)

        if user:
            app.logger.debug(f'Пользователь {user.username} успешно загружен')

        return user
    except (ValueError, TypeError) as e:
        app.logger.warning(f'Неверный формат user_id: {user_id}')
        return None
    except Exception as e:
        app.logger.error(f'Ошибка при загрузке пользователя с ID {user_id}: {str(e)}')
        return None

@app.route('/')
def index():
    """
    Главная страница сайта.

    Отображает приветственную страницу с первыми тремя услугами.

    """
    try:
        services = Service.query.limit(3).all()
        return render_template('index.html', services=services)
    except Exception as e:
        app.logger.error(f'Ошибка на главной странице: {str(e)}')
        return render_template('index.html', services=[])

@app.route('/services')
def services():
    """
    Страница каталога услуг.

    Отображает полный список всех доступных услуг.
    """
    try:
        services = Service.query.all()
        return render_template('services.html', services=services)
    except Exception as e:
        app.logger.error(f'Ошибка при загрузке каталога услуг: {str(e)}')
        return render_template('services.html', services=[])

@app.route('/service/<int:id>')
def service_detail(id):
    """
    Страница детальной информации об услуге.

    """
    try:
        service = Service.query.get_or_404(id)
        return render_template('service_detail.html', service=service)
    except Exception as e:
        app.logger.error(f'Ошибка при загрузке деталей услуги {id}: {str(e)}')
        abort(404)

@app.route('/portfolio')
def portfolio():
    """
    Страница портфолио агентства.

    """
    try:
        portfolio_items = Portfolio.query.order_by(Portfolio.created_at.desc()).all()
        return render_template('portfolio.html', portfolio_items=portfolio_items)
    except Exception as e:
        app.logger.error(f'Ошибка при загрузке портфолио: {str(e)}')
        return render_template('portfolio.html', portfolio_items=[])

@app.route('/news')
def news():
    """
    Страница списка новостей.

    Отображает все новости в обратном хронологическом порядке.
    """
    try:
        news_list = News.query.order_by(News.date_posted.desc()).all()
        return render_template('news.html', news_list=news_list)
    except Exception as e:
        app.logger.error(f'Ошибка при загрузке новостей: {str(e)}')
        return render_template('news.html', news_list=[])

@app.route('/news/<int:id>')
def news_detail(id):
    """
    Страница детальной информации о новости.
    """
    try:
        news = News.query.get_or_404(id)
        return render_template('news_detail.html', news=news)
    except Exception as e:
        app.logger.error(f'Ошибка при загрузке деталей новости {id}: {str(e)}')
        abort(404)

@app.route('/about')
def about():
    """
    Страница "О нас".

    Отображает информацию о компании.
    """
    return render_template('about.html')

@app.route('/contacts', methods=['GET', 'POST'])
def contacts():
    """
    Страница контактов и форма обратной связи.

    GET: Отображает форму контактов.
    POST: Обрабатывает отправленное сообщение.
    """
    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip()
            phone = request.form.get('phone', '').strip()
            message = request.form.get('message', '').strip()

            if not name or not email or not message:
                flash('Пожалуйста, заполните все обязательные поля', 'error')
                return render_template('contacts.html')

            flash('Спасибо за ваше сообщение! Мы свяжемся с вами в ближайшее время.', 'success')

            app.logger.info(f"Новое сообщение от {name} ({email}, {phone}): {message}")

            return redirect(url_for('contacts'))

        except Exception as e:
            app.logger.error(f'Ошибка при обработке формы контактов: {str(e)}')
            flash('Произошла ошибка при отправке сообщения. Попробуйте еще раз.', 'error')

    return render_template('contacts.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Страница входа в систему.

    GET: Отображает форму входа.
    POST: Обрабатывает данные для авторизации.
    """
    if current_user.is_authenticated:
        flash('Вы уже вошли в систему', 'info')
        return redirect(url_for('index'))

    if request.method == 'POST':
        try:
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '')
            remember = request.form.get('remember', False)

            if not email or not password:
                flash('Email и пароль обязательны для заполнения', 'error')
                return render_template('login.html')

            user = User.query.filter_by(email=email).first()

            if user and user.check_password(password):
                login_user(user, remember=remember)

                merged_count = merge_cart_to_user(user)

                if user.is_admin:
                    flash(f'Добро пожаловать, администратор {user.username}!', 'success')
                    return redirect(url_for('admin'))
                else:
                    message = f'Добро пожаловать в Gleeful, {user.username}!'
                    if merged_count > 0:
                        message += f' Ваша корзина ({merged_count} услуг) сохранена.'
                    flash(message, 'success')
                    return redirect(url_for('index'))
            else:
                flash('Неверный email или пароль', 'error')
                return render_template('login.html')

        except Exception as e:
            app.logger.error(f'Ошибка при входе пользователя: {str(e)}')
            flash('Произошла ошибка при входе. Попробуйте еще раз.', 'error')
            return render_template('login.html')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Страница регистрации нового пользователя.

    GET: Отображает форму регистрации.
    POST: Обрабатывает данные для создания аккаунта.

    Особенности:
    - Если email уже существует, обновляет пароль (тестовый режим).
    - Username "admin" зарезервирован.
    """
    if current_user.is_authenticated:
        flash('Вы уже вошли в систему', 'info')
        return redirect(url_for('index'))

    if request.method == 'POST':
        try:
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '')
            password_confirm = request.form.get('password_confirm', '')

            errors = []

            if not username:
                errors.append('Имя пользователя обязательно')
            elif len(username) < 3:
                errors.append('Имя пользователя должно содержать минимум 3 символа')
            elif len(username) > 80:
                errors.append('Имя пользователя слишком длинное')

            if not email:
                errors.append('Email обязателен')
            elif '@' not in email:
                errors.append('Введите корректный email')

            if not password:
                errors.append('Пароль обязателен')
            elif len(password) < 6:
                errors.append('Пароль должен содержать минимум 6 символов')

            if password != password_confirm:
                errors.append('Пароли не совпадают')

            if errors:
                for error in errors:
                    flash(error, 'error')
                return render_template('register.html')

            existing_user = User.query.filter_by(email=email).first()

            existing_username = User.query.filter_by(username=username).first()

            if existing_user:
                if existing_user.is_admin:
                    flash('Этот email зарезервирован для администратора. Регистрация невозможна.', 'error')
                    app.logger.warning(f'Попытка перезаписи админского аккаунта: {email}')
                    return render_template('register.html')

                existing_user.set_password(password)

                if existing_user.username != username:
                    if not existing_username or existing_username.id == existing_user.id:
                        existing_user.username = username
                    else:
                        flash('Имя пользователя уже занято другим аккаунтом', 'error')
                        return render_template('register.html')

                db.session.commit()

                flash(f'Добро пожаловать, {existing_user.username}! Пароль обновлён.', 'success')
                app.logger.info(f'Тестовый режим: обновлён пароль для пользователя {existing_user.username} ({email})')

                login_user(existing_user)
                return redirect(url_for('index'))

            if existing_username:
                errors.append('Пользователь с таким именем уже существует')
                for error in errors:
                    flash(error, 'error')
                return render_template('register.html')

            if username.lower() == 'admin':
                flash('Имя пользователя "admin" зарезервировано для администратора.', 'error')
                app.logger.warning(f'Попытка регистрации с username "admin": {email}')
                return render_template('register.html')

            user = User(
                username=username,
                email=email,
                is_admin=False
            )
            user.set_password(password)

            db.session.add(user)
            db.session.commit()

            flash(f'Добро пожаловать в Gleeful, {username}! Регистрация успешна.', 'success')
            app.logger.info(f'Зарегистрирован новый пользователь: {username} ({email})')

            login_user(user)
            return redirect(url_for('index'))

        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Ошибка при регистрации пользователя: {str(e)}')
            flash('Произошла ошибка при регистрации. Попробуйте еще раз.', 'error')
            return render_template('register.html')

    return render_template('register.html')

@app.route('/logout')
def logout():
    """
    Выход пользователя из системы.

    Завершает сессию текущего пользователя и перенаправляет на главную.
    """
    try:
        if current_user.is_authenticated:
            username = current_user.username
            logout_user()
            flash(f'До свидания, {username}! Ждем вас снова в Gleeful!', 'info')
        else:
            flash('Вы не были авторизованы', 'info')
    except Exception as e:
        app.logger.error(f'Ошибка при выходе пользователя: {str(e)}')
        flash('Произошла ошибка, но вы вышли из системы', 'warning')

    return redirect(url_for('index'))

@app.route('/cart/add/<int:id>', methods=['POST'])
def add_to_cart(id):
    """
    Добавление услуги в корзину.
    """
    try:
        service = Service.query.get_or_404(id)

        if current_user.is_authenticated:
            existing_item = CartItem.query.filter_by(
                user_id=current_user.id,
                service_id=id
            ).first()

            if existing_item:
                flash(f'Услуга "{service.title}" уже в корзине!', 'info')
            else:
                cart_item = CartItem(
                    user_id=current_user.id,
                    service_id=id
                )
                db.session.add(cart_item)
                db.session.commit()

                flash(f'Услуга "{service.title}" добавлена в корзину!', 'success')
                app.logger.info(f'Пользователь {current_user.username} добавил услугу {id} в корзину')
        else:
            if 'cart' not in session:
                session['cart'] = []

            cart_ids = session.get('cart', [])

            if id not in cart_ids:
                session['cart'].append(id)
                session.modified = True

                flash(f'Услуга "{service.title}" добавлена в корзину!', 'success')
                app.logger.info(f'Анонимный пользователь добавил услугу {id} в корзину')
            else:
                flash(f'Услуга "{service.title}" уже в корзине!', 'info')

        return redirect(request.referrer or url_for('services'))

    except Exception as e:
        if current_user.is_authenticated:
            db.session.rollback()
        app.logger.error(f'Ошибка при добавлении в корзину: {str(e)}')
        flash('Произошла ошибка при добавлении в корзину', 'error')
        return redirect(request.referrer or url_for('services'))

@app.route('/cart')
def cart():
    """
    Страница корзины с выбранными услугами.

    Отображает все услуги, добавленные в корзину текущего пользователя.
    Очищает недействительные записи и дубликаты.
    """
    try:
        if current_user.is_authenticated:
            cart_items_query = CartItem.query.filter_by(user_id=current_user.id).all()

            valid_items = []
            seen_service_ids = set()
            for item in cart_items_query:
                if item.service:
                    if item.service_id not in seen_service_ids:
                        valid_items.append(item)
                        seen_service_ids.add(item.service_id)
                    else:
                        app.logger.warning(f'Дубликат CartItem {item.id} для user {item.user_id}, service {item.service_id} - удалён')
                        db.session.delete(item)
                else:
                    db.session.delete(item)

            if valid_items:
                db.session.commit()

            cart_items = [item.service for item in valid_items]
        else:
            cart_ids = session.get('cart', [])

            if not cart_ids:
                cart_items = []
            else:
                unique_cart_ids = list(dict.fromkeys(cart_ids))
                if len(unique_cart_ids) < len(cart_ids):
                    session['cart'] = unique_cart_ids
                    session.modified = True
                    app.logger.info(f'Убраны дубликаты из сессии: {len(cart_ids)} -> {len(unique_cart_ids)}')

                cart_items = Service.query.filter(Service.id.in_(unique_cart_ids)).all()

                found_ids = [item.id for item in cart_items]
                missing_ids = set(unique_cart_ids) - set(found_ids)

                if missing_ids:
                    session['cart'] = [id_ for id_ in unique_cart_ids if id_ in found_ids]
                    session.modified = True
                    flash('Некоторые услуги из корзины были удалены', 'warning')

        total = sum(item.price for item in cart_items) if cart_items else 0

        return render_template('cart.html', cart_items=cart_items, total=total)

    except Exception as e:
        if current_user.is_authenticated:
            db.session.rollback()
        app.logger.error(f'Ошибка при загрузке корзины: {str(e)}')
        flash('Произошла ошибка при загрузке корзины', 'error')
        return render_template('cart.html', cart_items=[], total=0)

@app.route('/cart/remove/<int:id>', methods=['POST'])
def remove_from_cart(id):
    """
    Удаление услуги из корзины.
    """
    try:
        service = Service.query.get_or_404(id)

        if current_user.is_authenticated:
            cart_item = CartItem.query.filter_by(
                user_id=current_user.id,
                service_id=id
            ).first()

            if cart_item:
                db.session.delete(cart_item)
                db.session.commit()

                flash(f'Услуга "{service.title}" удалена из корзины', 'success')
                app.logger.info(f'Пользователь {current_user.username} удалил услугу {id} из корзины')
            else:
                flash('Этой услуги нет в вашей корзине', 'warning')
        else:
            cart_ids = session.get('cart', [])

            if id in cart_ids:
                cart_ids.remove(id)
                session['cart'] = cart_ids
                session.modified = True

                flash(f'Услуга "{service.title}" удалена из корзины', 'success')
                app.logger.info(f'Анонимный пользователь удалил услугу {id} из корзины')
            else:
                flash('Этой услуги нет в вашей корзине', 'warning')

        return redirect(url_for('cart'))

    except Exception as e:
        if current_user.is_authenticated:
            db.session.rollback()
        app.logger.error(f'Ошибка при удалении из корзины: {str(e)}')
        flash('Произошла ошибка при удалении из корзины', 'error')
        return redirect(url_for('cart'))

@app.route('/cart/clear', methods=['POST'])
def clear_cart():
    """
    Очистка всей корзины.

    Удаляет все услуги из корзины текущего пользователя.
    """
    try:
        if current_user.is_authenticated:
            cart_count = CartItem.query.filter_by(user_id=current_user.id).count()
            CartItem.query.filter_by(user_id=current_user.id).delete()
            db.session.commit()

            flash(f'Корзина очищена. Удалено услуг: {cart_count}', 'success')
            app.logger.info(f'Пользователь {current_user.username} очистил корзину')
        else:
            cart_count = len(session.get('cart', []))
            session['cart'] = []
            session.modified = True

            flash(f'Корзина очищена. Удалено услуг: {cart_count}', 'success')
            app.logger.info(f'Анонимный пользователь очистил корзину')

        return redirect(url_for('cart'))

    except Exception as e:
        if current_user.is_authenticated:
            db.session.rollback()
        app.logger.error(f'Ошибка при очистке корзины: {str(e)}')
        flash('Произошла ошибка при очистке корзины', 'error')
        return redirect(url_for('cart'))

@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    """
    Оформление заказа.

    GET: Отображает форму оформления заказа с услугами из корзины.
    POST: Создаёт заказ на основе данных формы и очищает корзину.
    """
    try:
        merge_cart_to_user(current_user)

        cart_items_query = CartItem.query.filter_by(user_id=current_user.id).all()

        if not cart_items_query:
            flash('Ваша корзина пуста! Добавьте услуги перед оформлением заказа.', 'error')
            return redirect(url_for('services'))

        cart_items = [item.service for item in cart_items_query if item.service]

        if not cart_items:
            flash('Корзина пуста или услуги недоступны', 'error')
            CartItem.query.filter_by(user_id=current_user.id).delete()
            db.session.commit()
            return redirect(url_for('services'))

        total = sum(item.price for item in cart_items)

        if request.method == 'POST':
            contact_phone = request.form.get('contact_phone', '').strip()
            event_date_str = request.form.get('event_date', '').strip()
            message = request.form.get('message', '').strip()

            errors = []

            if not contact_phone:
                errors.append('Контактный телефон обязателен')
            elif len(contact_phone) < 10:
                errors.append('Телефон должен содержать минимум 10 цифр')

            if not event_date_str:
                errors.append('Дата мероприятия обязательна')

            try:
                event_date = datetime.strptime(event_date_str, '%Y-%m-%d').date()
                if event_date < datetime.now().date():
                    errors.append('Дата мероприятия не может быть в прошлом')
            except ValueError:
                errors.append('Неверный формат даты. Используйте ГГГГ-ММ-ДД')
                event_date = None

            if errors:
                for error in errors:
                    flash(error, 'error')
                return render_template('checkout.html', cart_items=cart_items, total=total)

            try:
                order = Order(
                    user_id=current_user.id,
                    total_price=total,
                    contact_phone=contact_phone,
                    event_date=event_date,
                    status='Новый'
                )

                db.session.add(order)
                db.session.flush()

                for item in cart_items:
                    order_item = OrderItem(
                        order_id=order.id,
                        service_id=item.id,
                        price_at_moment=item.price
                    )
                    db.session.add(order_item)

                CartItem.query.filter_by(user_id=current_user.id).delete()

                db.session.commit()

                flash(f'Заказ №{order.id} успешно оформлен! Мы свяжемся с вами в ближайшее время.', 'success')
                app.logger.info(f'Пользователь {current_user.username} оформил заказ {order.id} на сумму {total}')

                return redirect(url_for('profile'))

            except Exception as db_error:
                db.session.rollback()
                app.logger.error(f'Ошибка базы данных при создании заказа: {str(db_error)}')
                flash('Ошибка при сохранении заказа. Пожалуйста, попробуйте еще раз.', 'error')
                return render_template('checkout.html', cart_items=cart_items, total=total)

        return render_template('checkout.html', cart_items=cart_items, total=total)

    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Ошибка при оформлении заказа: {str(e)}')
        flash('Произошла ошибка при оформлении заказа', 'error')
        return redirect(url_for('cart'))

@app.route('/profile')
@login_required
def profile():
    """
    Личный кабинет пользователя.

    Отображает профиль пользователя с историей его заказов.
    """
    try:
        orders = Order.query.filter_by(user_id=current_user.id)\
                           .order_by(Order.date_created.desc())\
                           .all()

        orders_with_items = []
        for order in orders:
            order_items = db.session.query(OrderItem, Service)\
                                  .join(Service, OrderItem.service_id == Service.id)\
                                  .filter(OrderItem.order_id == order.id)\
                                  .all()

            orders_with_items.append({
                'order': order,
                'order_items': order_items
            })

        return render_template('profile.html', orders=orders_with_items)

    except Exception as e:
        app.logger.error(f'Ошибка при загрузке профиля пользователя {current_user.username}: {str(e)}')
        flash('Произошла ошибка при загрузке профиля', 'error')
        return render_template('profile.html', orders=[])

@app.route('/my-orders')
@login_required
def my_orders():
    """
    Страница заказов пользователя.

    Отображает список всех заказов текущего пользователя с деталями.
    """
    try:
        orders = Order.query.filter_by(user_id=current_user.id)\
                           .order_by(Order.date_created.desc())\
                           .all()

        orders_with_items = []
        for order in orders:
            order_items = db.session.query(OrderItem, Service)\
                                  .join(Service, OrderItem.service_id == Service.id)\
                                  .filter(OrderItem.order_id == order.id)\
                                  .all()

            orders_with_items.append({
                'order': order,
                'items': order_items
            })

        return render_template('my_orders.html', orders=orders_with_items)

    except Exception as e:
        app.logger.error(f'Ошибка при загрузке заказов пользователя {current_user.username}: {str(e)}')
        flash('Произошла ошибка при загрузке заказов', 'error')
        return render_template('my_orders.html', orders=[])

@app.route('/admin')
@login_required
def admin():
    """
    Панель администратора.

    Отображает всю информацию для управления сайтом:
    - Услуги, новости, портфолио, заказы
    - Статистику по всем сущностям
    """
    try:
        if not current_user.is_admin:
            app.logger.warning(f'Пользователь {current_user.username} попытался получить доступ к админ-панели')
            abort(403)

        services = Service.query.order_by(Service.id.desc()).all()
        news = News.query.order_by(News.date_posted.desc()).all()
        portfolio_items = Portfolio.query.order_by(Portfolio.created_at.desc()).all()
        orders = db.session.query(Order, User)\
                         .join(User, Order.user_id == User.id)\
                         .order_by(Order.date_created.desc())\
                         .all()

        services_list = []
        for service in services:
            services_list.append({
                'id': service.id,
                'title': service.title,
                'description': service.description,
                'price': float(service.price) if service.price else 0.0,
                'category': service.category,
                'image_url': service.image_url,
                'created_at': service.created_at.strftime('%d.%m.%Y') if service.created_at else None
            })

        news_list = []
        for news_item in news:
            news_list.append({
                'id': news_item.id,
                'title': news_item.title,
                'content': news_item.content,
                'image_url': news_item.image_url,
                'date_posted': news_item.date_posted.strftime('%d.%m.%Y %H:%M')
            })

        portfolio_list = []
        for item in portfolio_items:
            portfolio_list.append({
                'id': item.id,
                'title': item.title,
                'category': item.category,
                'image_url': item.image_url,
                'event_type': item.event_type,
                'created_at': item.created_at.strftime('%d.%m.%Y') if item.created_at else None
            })

        orders_list = []
        for order, user in orders:
            orders_list.append({
                'id': order.id,
                'status': order.status,
                'total_amount': float(order.total_price),
                'date_created': order.date_created.strftime('%d.%m.%Y %H:%M'),
                'user_name': user.username if user else 'Неизвестный',
                'user_email': user.email if user else 'Неизвестно'
            })

        total_services = Service.query.count()
        total_news = News.query.count()
        total_portfolio = Portfolio.query.count()
        total_orders = Order.query.count()
        new_orders = Order.query.filter_by(status='Новый').count()
        total_users = User.query.count()

        stats = {
            'total_services': total_services,
            'total_news': total_news,
            'total_portfolio': total_portfolio,
            'total_orders': total_orders,
            'new_orders': new_orders,
            'total_users': total_users
        }

        return render_template('admin.html',
                             services=services,
                             news=news,
                             portfolio_items=portfolio_items,
                             orders=orders,
                             services_list=services_list,
                             news_list=news_list,
                             portfolio_list=portfolio_list,
                             orders_list=orders_list,
                             stats=stats)

    except Exception as e:
        app.logger.error(f'Ошибка при загрузке админ-панели: {str(e)}')
        flash('Произошла ошибка при загрузке админ-панели', 'error')
        return redirect(url_for('index'))

@app.route('/admin/service/add', methods=['POST'])
@login_required
def admin_add_service():
    """
    Добавление новой услуги администратором.

    Обрабатывает форму создания услуги с валидацией данных.
    Поддерживает AJAX-запросы.
    """
    try:
        if not current_user.is_admin:
            app.logger.warning(f'Пользователь {current_user.username} попытался добавить услугу без прав')
            abort(403)

        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        price = request.form.get('price', '').strip()
        category = request.form.get('category', '').strip()
        image_url = request.form.get('image_url', '').strip()

        errors = []
        if not title:
            errors.append('Название услуги обязательно')
        if not description:
            errors.append('Описание услуги обязательно')
        if not price:
            errors.append('Цена обязательна')
        else:
            try:
                price = float(price)
                if price <= 0:
                    errors.append('Цена должна быть положительной')
            except ValueError:
                errors.append('Цена должна быть числом')
        if not category:
            errors.append('Категория обязательна')
        elif category not in ['детский', 'взрослый', 'корпоратив', 'Детский', 'Взрослый', 'Корпоративный']:
            errors.append('Неверная категория')

        if errors:
            for error in errors:
                flash(error, 'error')
            return redirect(url_for('admin'))

        service = Service(
            title=title,
            description=description,
            price=price,
            category=category,
            image_url=image_url or None
        )

        db.session.add(service)
        db.session.commit()

        flash(f'Услуга "{title}" успешно добавлена!', 'success')
        app.logger.info(f'Администратор {current_user.username} добавил услугу: {title}')

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'message': f'Услуга "{title}" успешно добавлена!'})

        return redirect(url_for('admin'))

    except Exception as e:
        db.session.rollback()
        error_message = 'Произошла ошибка при добавлении услуги'
        app.logger.error(f'Ошибка при добавлении услуги: {str(e)}')

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': error_message})

        flash(error_message, 'error')
        return redirect(url_for('admin'))

@app.route('/admin/service/edit/<int:id>', methods=['POST'])
@login_required
def admin_edit_service(id):
    """
    Редактирование существующей услуги.
    """
    try:
        if not current_user.is_admin:
            app.logger.warning(f'Пользователь {current_user.username} попытался редактировать услугу без прав')
            abort(403)

        service = Service.query.get_or_404(id)

        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        price = request.form.get('price', '').strip()
        category = request.form.get('category', '').strip()
        image_url = request.form.get('image_url', '').strip()

        errors = []
        if not title:
            errors.append('Название услуги обязательно')
        if not description:
            errors.append('Описание услуги обязательно')
        if not price:
            errors.append('Цена обязательна')
        else:
            try:
                price = float(price)
                if price <= 0:
                    errors.append('Цена должна быть положительной')
            except ValueError:
                errors.append('Цена должна быть числом')
        if not category:
            errors.append('Категория обязательна')
        elif category not in ['детский', 'взрослый', 'корпоратив', 'Детский', 'Взрослый', 'Корпоративный']:
            errors.append('Неверная категория')

        if errors:
            for error in errors:
                flash(error, 'error')
            return redirect(url_for('admin'))

        service.title = title
        service.description = description
        service.price = price
        service.category = category
        service.image_url = image_url or None

        db.session.commit()

        flash(f'Услуга "{title}" успешно обновлена!', 'success')
        app.logger.info(f'Администратор {current_user.username} обновил услугу ID {id}: {title}')

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'message': f'Услуга "{title}" успешно обновлена!'})

        return redirect(url_for('admin'))

    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Ошибка при редактировании услуги {id}: {str(e)}')
        error_message = 'Произошла ошибка при редактировании услуги'

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': error_message})

        flash(error_message, 'error')
        return redirect(url_for('admin'))

@app.route('/admin/service/delete/<int:id>', methods=['POST'])
@login_required
def admin_delete_service(id):
    """
    Удаление услуги.
    """
    try:
        if not current_user.is_admin:
            app.logger.warning(f'Пользователь {current_user.username} попытался удалить услугу без прав')
            abort(403)

        service = Service.query.get_or_404(id)

        order_items = OrderItem.query.filter_by(service_id=id).first()
        if order_items:
            flash('Нельзя удалить услугу, так как она используется в заказах', 'error')
            return redirect(url_for('admin'))

        service_title = service.title

        db.session.delete(service)
        db.session.commit()

        flash(f'Услуга "{service_title}" успешно удалена!', 'success')
        app.logger.info(f'Администратор {current_user.username} удалил услугу ID {id}: {service_title}')

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'success': True, 'message': f'Услуга "{service_title}" успешно удалена!'})
        else:
            return redirect(url_for('admin'))

    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Ошибка при удалении услуги {id}: {str(e)}')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'success': False, 'message': 'Произошла ошибка при удалении услуги'})
        else:
            flash('Произошла ошибка при удалении услуги', 'error')
            return redirect(url_for('admin'))

@app.route('/admin/news/add', methods=['POST'])
@login_required
def admin_add_news():
    """
    Добавление новой новости администратором.
    """
    try:
        if not current_user.is_admin:
            app.logger.warning(f'Пользователь {current_user.username} попытался добавить новость без прав')
            abort(403)

        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        image_url = request.form.get('image_url', '').strip()

        errors = []
        if not title:
            errors.append('Заголовок новости обязателен')
        if not content:
            errors.append('Содержимое новости обязательно')

        if errors:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': '<br>'.join(errors)})
            for error in errors:
                flash(error, 'error')
            return redirect(url_for('admin'))

        news = News(
            title=title,
            content=content,
            image_url=image_url or None,
            date_posted=datetime.utcnow()
        )

        db.session.add(news)
        db.session.commit()

        success_message = f'Новость "{title}" успешно добавлена!'
        app.logger.info(f'Администратор {current_user.username} добавил новость: {title}')

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'message': success_message})

        flash(success_message, 'success')
        return redirect(url_for('admin'))

    except Exception as e:
        db.session.rollback()
        error_message = 'Произошла ошибка при добавлении новости'
        app.logger.error(f'Ошибка при добавлении новости: {str(e)}')

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': error_message})

        flash(error_message, 'error')
        return redirect(url_for('admin'))

@app.route('/admin/news/edit/<int:id>', methods=['POST'])
@login_required
def admin_edit_news(id):
    """
    Редактирование существующей новости.
    """
    try:
        if not current_user.is_admin:
            app.logger.warning(f'Пользователь {current_user.username} попытался редактировать новость без прав')
            abort(403)

        news = News.query.get_or_404(id)

        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        image_url = request.form.get('image_url', '').strip()

        errors = []
        if not title:
            errors.append('Заголовок новости обязателен')
        if not content:
            errors.append('Содержимое новости обязательно')

        if errors:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': '<br>'.join(errors)})
            for error in errors:
                flash(error, 'error')
            return redirect(url_for('admin'))

        news.title = title
        news.content = content
        news.image_url = image_url or None

        db.session.commit()

        success_message = f'Новость "{title}" успешно обновлена!'
        app.logger.info(f'Администратор {current_user.username} обновил новость ID {id}: {title}')

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'message': success_message})

        flash(success_message, 'success')
        return redirect(url_for('admin'))

    except Exception as e:
        db.session.rollback()
        error_message = 'Произошла ошибка при редактировании новости'
        app.logger.error(f'Ошибка при редактировании новости {id}: {str(e)}')

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': error_message})

        flash(error_message, 'error')
        return redirect(url_for('admin'))

@app.route('/admin/news/delete/<int:id>', methods=['POST'])
@login_required
def admin_delete_news(id):
    """
    Удаление новости.
    """
    try:
        if not current_user.is_admin:
            app.logger.warning(f'Пользователь {current_user.username} попытался удалить новость без прав')
            abort(403)

        news = News.query.get_or_404(id)

        news_title = news.title

        db.session.delete(news)
        db.session.commit()

        flash(f'Новость "{news_title}" успешно удалена!', 'success')
        app.logger.info(f'Администратор {current_user.username} удалил новость ID {id}: {news_title}')

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'success': True, 'message': f'Новость "{news_title}" успешно удалена!'})
        else:
            return redirect(url_for('admin'))

    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Ошибка при удалении новости {id}: {str(e)}')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'success': False, 'message': 'Произошла ошибка при удалении новости'})
        else:
            flash('Произошла ошибка при удалении новости', 'error')
            return redirect(url_for('admin'))

@app.route('/admin/order/status/<int:id>', methods=['POST'])
@login_required
def admin_update_order_status(id):
    """
    Обновление статуса заказа администратором.
    """
    try:
        if not current_user.is_admin:
            app.logger.warning(f'Пользователь {current_user.username} попытался обновить статус заказа без прав')
            abort(403)

        order = Order.query.get_or_404(id)

        if request.is_json:
            data = request.get_json()
            new_status = data.get('status', '').strip()
        else:
            new_status = request.form.get('status', '').strip()

        valid_statuses = ['Новый', 'В обработке', 'Подтвержден', 'Выполнен', 'Отменен', 'Завершен']
        if new_status not in valid_statuses:
            flash('Неверный статус заказа', 'error')
            return redirect(url_for('admin'))

        old_status = order.status
        order.status = new_status

        db.session.commit()

        flash(f'Статус заказа #{id} изменен с "{old_status}" на "{new_status}"', 'success')
        app.logger.info(f'Администратор {current_user.username} изменил статус заказа {id}: {old_status} -> {new_status}')

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'success': True, 'message': f'Статус заказа #{id} изменен на "{new_status}"'})
        else:
            return redirect(url_for('admin'))

    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Ошибка при обновлении статуса заказа {id}: {str(e)}')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'success': False, 'message': 'Произошла ошибка при обновлении статуса заказа'})
        else:
            flash('Произошла ошибка при обновлении статуса заказа', 'error')
            return redirect(url_for('admin'))

@app.route('/admin/order/delete/<int:id>', methods=['POST'])
@login_required
def admin_delete_order(id):
    """
    Удаление заказа администратором.
    """
    try:
        if not current_user.is_admin:
            app.logger.warning(f'Пользователь {current_user.username} попытался удалить заказ без прав')
            abort(403)

        order = Order.query.get_or_404(id)

        db.session.delete(order)
        db.session.commit()

        flash(f'Заказ #{id} успешно удален!', 'success')
        app.logger.info(f'Администратор {current_user.username} удалил заказ ID {id}')

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'success': True, 'message': f'Заказ #{id} успешно удален!'})
        else:
            return redirect(url_for('admin'))

    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Ошибка при удалении заказа {id}: {str(e)}')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'success': False, 'message': 'Произошла ошибка при удалении заказа'})
        else:
            flash('Произошла ошибка при удалении заказа', 'error')
            return redirect(url_for('admin'))

@app.route('/admin/portfolio/add', methods=['POST'])
@login_required
def admin_portfolio_add():
    """
    Добавление новой работы в портфолио.
    """
    try:
        if not current_user.is_admin:
            return jsonify({'success': False, 'message': 'Недостаточно прав'}), 403

        title = request.form.get('title', '').strip()
        category = request.form.get('category', '').strip()
        event_type = request.form.get('event_type', '').strip()
        image_url = request.form.get('image_url', '').strip()

        if not title or not category or not image_url:
            return jsonify({'success': False, 'message': 'Заполните все обязательные поля'})

        if category not in ['Детский', 'Взрослый', 'Корпоративный']:
            return jsonify({'success': False, 'message': 'Некорректная категория'})

        portfolio_item = Portfolio(
            title=title,
            category=category,
            event_type=event_type,
            image_url=image_url
        )
        db.session.add(portfolio_item)
        db.session.commit()

        flash('Работа успешно добавлена в портфолио!', 'success')
        app.logger.info(f'Администратор {current_user.username} добавил работу в портфолио: {title}')

        return jsonify({'success': True, 'message': 'Работа успешно добавлена в портфолио!'})

    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Ошибка при добавлении работы в портфолио: {str(e)}')
        return jsonify({'success': False, 'message': 'Произошла ошибка при добавлении'})


@app.route('/admin/portfolio/edit/<int:id>', methods=['POST'])
@login_required
def admin_portfolio_edit(id):
    """
    Редактирование работы в портфолио.
    """
    try:
        if not current_user.is_admin:
            return jsonify({'success': False, 'message': 'Недостаточно прав'}), 403

        portfolio_item = Portfolio.query.get_or_404(id)

        title = request.form.get('title', '').strip()
        category = request.form.get('category', '').strip()
        event_type = request.form.get('event_type', '').strip()
        image_url = request.form.get('image_url', '').strip()

        if not title or not category or not image_url:
            return jsonify({'success': False, 'message': 'Заполните все обязательные поля'})

        if category not in ['Детский', 'Взрослый', 'Корпоративный']:
            return jsonify({'success': False, 'message': 'Некорректная категория'})

        portfolio_item.title = title
        portfolio_item.category = category
        portfolio_item.event_type = event_type
        portfolio_item.image_url = image_url
        db.session.commit()

        flash('Работа успешно обновлена!', 'success')
        app.logger.info(f'Администратор {current_user.username} редактировал работу портфолио ID {id}')

        return jsonify({'success': True, 'message': 'Работа успешно обновлена!'})

    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Ошибка при редактировании работы портфолио {id}: {str(e)}')
        return jsonify({'success': False, 'message': 'Произошла ошибка при сохранении'})


@app.route('/admin/portfolio/delete/<int:id>', methods=['POST'])
@login_required
def admin_portfolio_delete(id):
    """
    Удаление работы из портфолио.
    """
    try:
        if not current_user.is_admin:
            return jsonify({'success': False, 'message': 'Недостаточно прав'}), 403

        portfolio_item = Portfolio.query.get_or_404(id)

        db.session.delete(portfolio_item)
        db.session.commit()

        flash('Работа успешно удалена из портфолио!', 'success')
        app.logger.info(f'Администратор {current_user.username} удалил работу портфолио ID {id}')

        return jsonify({'success': True, 'message': 'Работа успешно удалена из портфолио!'})

    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Ошибка при удалении работы портфолио {id}: {str(e)}')
        return jsonify({'success': False, 'message': 'Произошла ошибка при удалении'})

@app.errorhandler(404)
def page_not_found(e):
    """
    Обработчик ошибки 404 (страница не найдена).
    """
    return render_template('404.html'), 404

def create_dummy_data():
    """
    Создание начальных данных для приложения.

    Создаёт:
    - Администратора (если не существует)
    - Тестовые услуги (если база пуста)
    - Тестовые новости (если база пуста)
    """
    print("🚀 Создание начальных данных для Gleeful...")

    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@gleeful.ru',
            is_admin=True
        )
        admin.set_password('admin')
        db.session.add(admin)
        print("Администратор создан: login=admin, password=admin")
    else:
        print("Администратор уже существует")

    if Service.query.count() == 0:
        services_data = [
            {
                'title': 'Детский День Рождения',
                'description': 'Полная организация детского дня рождения с аниматорами, шоу-программой и праздничным тортом. Включает украшение помещения шарами и фотосессию.',
                'price': 15000.00,
                'category': 'детский',
                'image_url': 'https://via.placeholder.com/400x300/FFD700/FFFFFF?text=Gleeful+День+Рождения'
            },
            {
                'title': 'Свадебная церемония',
                'description': 'Роскошная свадебная церемония под ключ. Организация выезда молодоженов, банкет, ведущий и развлекательная программа.',
                'price': 50000.00,
                'category': 'взрослый',
                'image_url': 'https://via.placeholder.com/400x300/FFD700/FFFFFF?text=Gleeful+Свадьба'
            },
            {
                'title': 'Корпоративный Новый Год',
                'description': 'Новогодняя корпоративная вечеринка с подарками для сотрудников, банкетом, ведущим и развлекательной программой.',
                'price': 80000.00,
                'category': 'корпоратив',
                'image_url': 'https://via.placeholder.com/400x300/FFD700/FFFFFF?text=Gleeful+Новый+Год'
            },
            {
                'title': 'Аниматоры для детей',
                'description': 'Профессиональные аниматоры с костюмами любимых персонажей. Интерактивные игры, фокусы и музыкальное сопровождение.',
                'price': 5000.00,
                'category': 'детский',
                'image_url': 'https://via.placeholder.com/400x300/FFD700/FFFFFF?text=Gleeful+Аниматоры'
            },
            {
                'title': 'Фотосессия на празднике',
                'description': 'Профессиональный фотограф на вашем празднике. Создание живых и ярких моментов, обработка и доставка фотографий.',
                'price': 10000.00,
                'category': 'взрослый',
                'image_url': 'https://via.placeholder.com/400x300/FFD700/FFFFFF?text=Gleeful+Фотосессия'
            },
            {
                'title': 'Оформление зала шарами',
                'description': 'Художественное оформление помещения воздушными шарами различной формы и размера. Создание уникальной атмосферы праздника.',
                'price': 8000.00,
                'category': 'детский',
                'image_url': 'https://via.placeholder.com/400x300/FFD700/FFFFFF?text=Gleeful+Шары'
            },
            {
                'title': 'Тимбилдинг мероприятие',
                'description': 'Командообразующие мероприятия для корпоративных клиентов. Развивающие игры и конкурсы для сплочения коллектива.',
                'price': 35000.00,
                'category': 'корпоратив',
                'image_url': 'https://via.placeholder.com/400x300/FFD700/FFFFFF?text=Gleeful+Тимбилдинг'
            }
        ]

        for service_data in services_data:
            service = Service(**service_data)
            db.session.add(service)

        print("Создано 7 услуг")
    else:
        print("Услуги уже существуют")

    if News.query.count() == 0:
        news_data = [
            {
                'title': 'Открытие нового сезона на gleeful.ru!',
                'content': 'Gleeful рад объявить об открытии нового сезона! Твоя территория радости станет еще ярче. Специальные предложения для постоянных клиентов gleeful.ru.',
                'image_url': 'https://via.placeholder.com/400x200/FFD700/FFFFFF?text=Gleeful+Новый+сезон',
                'date_posted': datetime.utcnow() - timedelta(days=5)
            },
            {
                'title': 'Скидка 20% на детские праздники в марте на gleeful.ru',
                'content': 'Только в марте! Получите скидку 20% на все детские праздники Gleeful. Твоя территория радости стала еще доступнее! Аниматоры, шоу-программы - все по специальной цене.',
                'image_url': 'https://via.placeholder.com/400x200/FFD700/FFFFFF?text=Gleeful+Скидка+20%',
                'date_posted': datetime.utcnow() - timedelta(days=10)
            },
            {
                'title': 'Новая услуга Gleeful: организация выпускных',
                'content': 'Gleeful добавил новую услугу - организация выпускных вечеров! Твоя территория радости расширяется. Профессиональная фото и видеосъемка, ведущий, дискотека на gleeful.ru.',
                'image_url': 'https://via.placeholder.com/400x200/FFD700/FFFFFF?text=Gleeful+Выпускной',
                'date_posted': datetime.utcnow() - timedelta(days=2)
            },
            {
                'title': 'Отзывы клиентов Gleeful: более 500 довольных семей!',
                'content': 'Благодарим всех клиентов Gleeful за доверие! Твоя территория радости уже посетила более 500 счастливых семей. Только положительные отзывы на gleeful.ru!',
                'image_url': 'https://via.placeholder.com/400x200/FFD700/FFFFFF?text=Gleeful+500+клиентов',
                'date_posted': datetime.utcnow() - timedelta(days=1)
            }
        ]

        for news_item in news_data:
            news = News(**news_item)
            db.session.add(news)

        print("Создано 4 новости")
    else:
        print("Новости уже существуют")

    try:
        db.session.commit()
        print("Начальные данные успешно созданы!")
    except Exception as e:
        db.session.rollback()
        print(f"Ошибка при сохранении данных: {str(e)}")

if __name__ == '__main__':
    """
    Точка входа в приложение.
    """
    print("Запуск Gleeful - Твоя территория радости!")

    with app.app_context():
        try:
            db.create_all()
            print("Таблицы базы данных созданы/проверены")

            create_dummy_data()

        except Exception as e:
            print(f"Ошибка при инициализации базы данных: {str(e)}")
            print("Проверьте правильность конфигурации базы данных и прав доступа.")

    try:
        app.run(debug=True, host='127.0.0.1', port=5000)
    except Exception as e:
        print(f"Ошибка запуска приложения: {str(e)}")