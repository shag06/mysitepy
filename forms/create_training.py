from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms import SubmitField, BooleanField
from wtforms.validators import DataRequired


class TrainingForm(FlaskForm):
    title = StringField('Название', validators=[DataRequired()])
    content = TextAreaField("Содержание")
    book = TextAreaField("Решение (будет отображаться для авторизованных пользователей)")
    is_private = BooleanField("Скрыть от посторонних")
    submit = SubmitField('Применить')
