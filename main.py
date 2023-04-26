from flask import Flask, render_template, redirect, make_response, session, abort, request, send_file
from data import db_session
from data.users import User
from data.news import News
from forms.user import RegisterForm
from forms.loginform import LoginForm
from forms.news import NewsForm
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from forms.create_training import TrainingForm
from forms.answer_training1 import AnswerTraining1
import random

words = {"машина": "car", "дом": "house",
         "стол": "table", "бегать": "run", "рыба": "fish", "работать": "work", "семья": "family",
         "игрушка": "toy", "играть": "play", "поезд": "train", "перчатка": "glove", "гитара": "guitar",
         "ключ": "key", "видеть": "see", "добрый": "kind", "говорить": "speak", "мяч": "ball",
         "плавать": "swim", "наручные часы": "watch", "друг": "friend", "печь": "bake", "гараж": "garage",
         "нести": "carry", "цветок": "flower", "мыть": "clean", "надеяться": "hope", "магазин": "shop"}
words_list = ["машина", "дом", "стол", "бегать", "рыба", "работать", "семья", "игрушка", "играть",
              "поезд", "перчатка", "гитара", "ключ", "видеть", "добрый", "говорить", "мяч",
              "плавать", "наручные часы", "друг", "печь", "гараж", "нести", "цветок", "мыть", "надеяться",
              "магазин"]

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'

login_manager = LoginManager()
login_manager.init_app(app)
db_session.global_init("db/blogs.db")


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route("/cookie_test")
def cookie_test():
    visits_count = int(request.cookies.get("visits_count", 0))
    if visits_count:
        res = make_response(
            f"Вы пришли на эту страницу {visits_count + 1} раз")
        res.set_cookie("visits_count", str(visits_count + 1),
                       max_age=60 * 60 * 24 * 365 * 2)
    else:
        res = make_response(
            "Вы пришли на эту страницу в первый раз за последние 2 года")
        res.set_cookie("visits_count", '1',
                       max_age=60 * 60 * 24 * 365 * 2)
    return res


@app.route("/session_test")
def session_test():
    visits_count = session.get('visits_count', 0)
    session['visits_count'] = visits_count + 1
    return make_response(
        f"Вы пришли на эту страницу {visits_count + 1} раз")


@app.route("/")
def home_screen():
    return render_template('homescreen.html')


@app.route("/new-reed")
def index():
    db_sess = db_session.create_session()
    if current_user.is_authenticated:
        news = db_sess.query(News).filter(
            ((News.user == current_user) | (News.is_private != True)) & (News.is_training == False))
    else:
        news = db_sess.query(News).filter((News.is_private != True) & (News.is_training == False))
    return render_template("index2.html", news=news)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        if form.pay_code.data == "asdfqwerty":
            pay_code = True
        else:
            pay_code = False
        user = User(
            name=form.name.data,
            email=form.email.data,
            about=form.about.data,
            pay_code=pay_code
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/news', methods=['GET', 'POST'])
@login_required
def add_news():
    form = NewsForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        news = News()
        news.title = form.title.data
        news.content = form.content.data
        news.is_private = form.is_private.data
        news.is_training = False
        current_user.news.append(news)
        db_sess.merge(current_user)
        db_sess.commit()
        return redirect('/new-reed')
    return render_template('news.html', title='Добавление новости',
                           form=form)


@app.route('/news/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_news(id):
    form = NewsForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        news = db_sess.query(News).filter(News.id == id, News.user == current_user).first()
        if news:
            form.title.data = news.title
            form.content.data = news.content
            form.is_private.data = news.is_private
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        news = db_sess.query(News).filter(News.id == id,
                                          News.user == current_user
                                          ).first()
        if news:
            news.title = form.title.data
            news.content = form.content.data
            news.is_private = form.is_private.data
            news.is_training = False
            db_sess.commit()
            return redirect('/new-reed')
        else:
            abort(404)
    return render_template('news.html',
                           title='Редактирование новости',
                           form=form
                           )


@app.route('/news_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def news_delete(id):
    db_sess = db_session.create_session()
    news = db_sess.query(News).filter(News.id == id,
                                      News.user == current_user
                                      ).first()
    if news:
        db_sess.delete(news)
        db_sess.commit()
    else:
        abort(404)
    return redirect('/new-reed')


@app.route("/training_reed")
def index2():
    db_sess = db_session.create_session()
    training = db_sess.query(News).filter(News.is_training == True)
    return render_template("index3.html", news=training)


@app.route('/create_training', methods=['GET', 'POST'])
@login_required
def add_training():
    form = TrainingForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        training = News()
        training.title = form.title.data
        training.content = form.content.data
        training.is_private = form.is_private.data
        training.is_training = True
        training.book = form.book.data
        current_user.news.append(training)
        db_sess.merge(current_user)
        db_sess.commit()
        return redirect('/training_reed')
    return render_template('free_training.html', title='Задача',
                           form=form)


@app.route('/training/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_training(id):
    form = TrainingForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        training = db_sess.query(News).filter(News.id == id, News.user == current_user).first()
        if training:
            form.title.data = training.title
            form.content.data = training.content
            form.is_private.data = training.is_private
            form.book.data = training.book
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        training = db_sess.query(News).filter(News.id == id,
                                          News.user == current_user
                                          ).first()
        if training:
            training.title = form.title.data
            training.content = form.content.data
            training.is_private = form.is_private.data
            training.is_training = True
            training.book = form.book.data
            db_sess.commit()
            return redirect('/training_reed')
        else:
            abort(404)
    return render_template('free_training.html',
                           title='Редактирование новости',
                           form=form
                           )


@app.route('/training_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def training_delete(id):
    db_sess = db_session.create_session()
    training = db_sess.query(News).filter(News.id == id,
                                      News.user == current_user
                                      ).first()
    if training:
        db_sess.delete(training)
        db_sess.commit()
    else:
        abort(404)
    return redirect('/training_reed')


@app.route('/pay_training')
def pay_training_reed():
    db_sess = db_session.create_session()
    if current_user.is_authenticated:
        user = db_sess.query(User).filter(current_user.pay_code == True).first()
        return render_template("pay_training.html", user=user)
    return render_template("pay_training.html")


@app.route('/return-file-1')
def return_file_1():
    return send_file('D:\\pythonprogsasha\\pythonProject3\\static\\files\\Hello.pdf')


@app.route('/return-file-2')
def return_file_2():
    return send_file('D:\\pythonprogsasha\\pythonProject3\\static\\files\\Hello2.pdf')


@app.route('/pay-training-1', methods=['GET', 'POST'])
@login_required
def training1():
    word = random.choice(words_list)
    form = AnswerTraining1()
    if form.validate_on_submit():
        return render_template('training1.html', title='Переведи слово',
                               form=form, code=words[word], word=word)
    return render_template('training1.html', title='Переведи слово',
                           form=form, code=words[word], word=word)


def main():
    db_session.global_init("db/blogs.db")
    app.run(port=8080, host='127.0.0.1', debug=True)


if __name__ == '__main__':
    main()
