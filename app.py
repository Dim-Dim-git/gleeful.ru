"""
Сайт Gleeful.ru - Агентство праздников
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config['SECRET_KEY'] = '7a3f9e2c8b4d1f6e5a9c3b7d2f8e4a1b6c5d9f3e7a2b8c4d1f6e5a9c3b7d2f8e'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///party_agency.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

@app.route('/')
def index():
    return '<h1>Gleeful - Твоя территория радости!</h1><p>Сайт в разработке...</p>'

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
