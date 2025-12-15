"""
Сайт Gleeful.ru - Агентство праздников
"""

from flask import Flask, render_template, abort
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = '7a3f9e2c8b4d1f6e5a9c3b7d2f8e4a1b6c5d9f3e7a2b8c4d1f6e5a9c3b7d2f8e'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///party_agency.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

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

def create_dummy_data():
    if Service.query.count() == 0:
        services_data = [
            ('Детский День Рождения', 'Полная организация детского дня рождения с аниматорами', 15000, 'детский'),
            ('Свадебная церемония', 'Роскошная свадебная церемония под ключ', 50000, 'взрослый'),
            ('Корпоративный Новый Год', 'Новогодняя корпоративная вечеринка', 80000, 'корпоратив'),
            ('Аниматоры для детей', 'Профессиональные аниматоры с костюмами', 5000, 'детский'),
            ('Фотосессия на празднике', 'Профессиональный фотограф на вашем празднике', 10000, 'взрослый'),
            ('Оформление зала шарами', 'Художественное оформление шарами', 8000, 'детский'),
            ('Тимбилдинг мероприятие', 'Командообразующие мероприятия', 35000, 'корпоратив'),
        ]
        for title, desc, price, cat in services_data:
            db.session.add(Service(title=title, description=desc, price=price, category=cat))

    if News.query.count() == 0:
        news_data = [
            ('Открытие нового сезона!', 'Gleeful рад объявить об открытии нового сезона!'),
            ('Скидка 20% в декабре', 'Только в декабре - скидка 20% на все детские праздники!'),
            ('Новая услуга: выпускные', 'Теперь организуем выпускные вечера!'),
        ]
        for title, content in news_data:
            db.session.add(News(title=title, content=content))

    if Portfolio.query.count() == 0:
        portfolio_data = [
            ('День рождения Маши', 'Детский', 'https://via.placeholder.com/400x300', 'День рождения'),
            ('Свадьба Ивановых', 'Взрослый', 'https://via.placeholder.com/400x300', 'Свадьба'),
            ('Корпоратив TechCorp', 'Корпоративный', 'https://via.placeholder.com/400x300', 'Новый год'),
        ]
        for title, cat, img, evt in portfolio_data:
            db.session.add(Portfolio(title=title, category=cat, image_url=img, event_type=evt))

    db.session.commit()

@app.route('/')
def index():
    services = Service.query.limit(3).all()
    news = News.query.order_by(News.date_posted.desc()).limit(2).all()
    return render_template('index.html', services=services, news=news)

@app.route('/services')
def services():
    services = Service.query.all()
    return render_template('services.html', services=services)

@app.route('/service/<int:id>')
def service_detail(id):
    service = Service.query.get_or_404(id)
    return render_template('service_detail.html', service=service)

@app.route('/portfolio')
def portfolio():
    items = Portfolio.query.order_by(Portfolio.created_at.desc()).all()
    return render_template('portfolio.html', portfolio_items=items)

@app.route('/news')
def news():
    news_list = News.query.order_by(News.date_posted.desc()).all()
    return render_template('news.html', news_list=news_list)

@app.route('/news/<int:id>')
def news_detail(id):
    news = News.query.get_or_404(id)
    return render_template('news_detail.html', news=news)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contacts')
def contacts():
    return render_template('contacts.html')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_dummy_data()
    app.run(debug=True)
