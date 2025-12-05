"""
Сайт Gleeful.ru - Агентство праздников
"""

from flask import Flask, render_template

app = Flask(__name__)
app.config['SECRET_KEY'] = '7a3f9e2c8b4d1f6e5a9c3b7d2f8e4a1b6c5d9f3e7a2b8c4d1f6e5a9c3b7d2f8e'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/services')
def services():
    return '<h1>Каталог услуг</h1><p>Скоро здесь появится список наших услуг...</p>'

@app.route('/about')
def about():
    return '<h1>О нас</h1><p>Информация о компании Gleeful</p>'

@app.route('/contacts')
def contacts():
    return '<h1>Контакты</h1><p>Свяжитесь с нами</p>'

if __name__ == '__main__':
    app.run(debug=True)
