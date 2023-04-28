from flask_login import UserMixin,LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from sqlalchemy.orm import relationship
from wtforms import StringField, TextAreaField, SubmitField, EmailField, PasswordField
from wtforms.validators import DataRequired
from flask_ckeditor import CKEditorField

db = SQLAlchemy()
login_manager = LoginManager()


class Post(db.Model):
    __tablename__ = 'post'
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    title = db.Column(db.String(250), nullable=False)
    author = relationship("User", back_populates="post")
    image_url = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.String(1000), nullable=False)
    comment = relationship("Comment", cascade="all,delete", back_populates='parent_post')


class User(UserMixin,db.Model):
    __tablename__ = 'user'
    id = db.Column(db.String(200), primary_key=True)
    name = db.Column(db.String(150), unique=True,nullable=False)
    email = db.Column(db.String(100))
    profile_pic = db.Column(db.String())
    post = relationship("Post", back_populates="author")
    comment = relationship("Comment", back_populates="comment_author")


class Comment(UserMixin,db.Model):
    __tablename__ = 'comment'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(500), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    comment_author = relationship("User", back_populates='comment')
    parent_post = relationship("Post", back_populates='comment')







