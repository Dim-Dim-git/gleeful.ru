"""
Сайт Gleeful.ru - Агентство праздников
"""

from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = '7a3f9e2c8b4d1f6e5a9c3b7d2f8e4a1b6c5d9f3e7a2b8c4d1f6e5a9c3b7d2f8e'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///party_agency.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Модели данных
class Service(db.Model):
    """Услуги агентства"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    image_url = db.Column(db.String(300))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Service {self.title}>'

class News(db.Model):
    """Новости сайта"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(300))
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<News {self.title}>'

class Portfolio(db.Model):
    """Работы в портфолио"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    image_url = db.Column(db.String(300), nullable=False)
    event_type = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Portfolio {self.title}>'

def create_dummy_data():
    """Создание тестовых данных"""
    if Service.query.count() == 0:
        services = [
            Service(title='Детский День Рождения',
                   description='Полная организация детского дня рождения с аниматорами',
                   price=15000.00, category='детский',
                   image_url='https://via.placeholder.com/400x300/FFD700/FFFFFF?text=День+Рождения'),
            Service(title='Свадебная церемония',
                   description='Роскошная свадебная церемония под ключ',
                   price=50000.00, category='взрослый',
                   image_url='https://via.placeholder.com/400x300/FFD700/FFFFFF?text=Свадьба'),
            Service(title='Корпоративный Новый Год',
                   description='Новогодняя корпоративная вечеринка',
                   price=80000.00, category='корпоратив',
                   image_url='https://via.placeholder.com/400x300/FFD700/FFFFFF?text=Новый+Год'),
        ]
        for s in services:
            db.session.add(s)
        print("Создано 3 услуги")

    if News.query.count() == 0:
        news = [
            News(title='Открытие нового сезона!',
                 content='Gleeful рад объявить об открытии нового сезона!'),
            News(title='Скидка 20% на детские праздники',
                 content='Только в этом месяце - скидка 20% на все детские праздники!'),
        ]
        for n in news:
            db.session.add(n)
        print("Создано 2 новости")

    db.session.commit()

@app.route('/')
def index():
    services = Service.query.limit(3).all()
    return render_template('index.html', services=services)

@app.route('/services')
def services():
    services = Service.query.all()
    return render_template('services.html', services=services)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contacts')
def contacts():
    return render_template('contacts.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_dummy_data()
    app.run(debug=True)
