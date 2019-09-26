from flask_wtf import FlaskForm
from wtforms import (StringField, PasswordField, TextAreaField,
                     IntegerField, DateField, FieldList, FormField)
from wtforms.validators import (DataRequired, Regexp, ValidationError,
                                Email, Length, EqualTo)

from models import User, Entry, Tag


def email_exists(form, field):
    if User.select().where(User.email == field.data).exists():
        raise ValidationError('User with that email already exists.')


def name_exists(form, field):
    if User.select().where(User.username == field.data).exists():
        raise ValidationError('User with that username already exists.')


class RegisterForm(FlaskForm):
    username = StringField(
        'Username', validators=[DataRequired(), name_exists]
        )
    email = StringField(
        'Email', validators=[DataRequired(), Email(), email_exists]
        )
    password = PasswordField(
        'Password', validators=[DataRequired(),Length(min=8),
        EqualTo('pass2')]
        )
    pass2 = PasswordField('Confirm Password', validators=[DataRequired()])


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])


class TagForm(FlaskForm):
    tag = StringField('Tag')


class AddEntryForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    date = DateField('Date')
    time_spent = IntegerField('Time Spent', validators=[DataRequired()])
    content = TextAreaField(
        'What I Have Learned', validators=[DataRequired()]
        )
    resources = TextAreaField('Resources', validators=[DataRequired()])
    tags = StringField('Tags', validators=[DataRequired()])
