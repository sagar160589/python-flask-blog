from flask_login import UserMixin,LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, EmailField, PasswordField
from wtforms.validators import DataRequired

db = SQLAlchemy()
login_manager = LoginManager()


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), nullable=False)
    author = db.Column(db.String(250), nullable=False)
    image_url = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.String(1000), nullable=False)

style = {"style": "font-weight: bold; font-size: medium"}

class PostForm(FlaskForm):
    title = StringField(label='Title', validators=[DataRequired()], render_kw=style)
    author = StringField(label='Author', validators=[DataRequired()], render_kw=style)
    image_url = StringField(label='Image Url', validators=[DataRequired()], render_kw=style)
    body = TextAreaField(label='Body', validators=[DataRequired()],  render_kw={'class': 'form-control', 'rows': 10, "style": "font-weight: bold; font-size: medium"})
    submit = SubmitField(label='Submit', render_kw=style)

class User(UserMixin,db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True,nullable=False)
    email = db.Column(db.String(100))
    password = db.Column(db.String(100))

class UserForm(FlaskForm):
    name = StringField(label='Name', validators=[DataRequired()])
    email = EmailField(label='Email', validators=[DataRequired()])
    password = PasswordField(label='Password', validators=[DataRequired()])
    submit = SubmitField(label='Submit')

# class LoginUser(UserMixin,db.Model):
#     email = db.Column(db.String(100), unique=True)
#     password = db.Column(db.String(100))

class LoginUserForm(FlaskForm):
    email = EmailField(label='Email', validators=[DataRequired()])
    password = PasswordField(label='Password', validators=[DataRequired()])
    submit = SubmitField(label='Submit')
