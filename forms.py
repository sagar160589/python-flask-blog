from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, EmailField, PasswordField
from wtforms.validators import DataRequired
from flask_ckeditor import CKEditorField

style = {"style": "font-weight: bold; font-size: medium"}

class PostForm(FlaskForm):
    title = StringField(label='Title', validators=[DataRequired()], render_kw=style)
    image_url = StringField(label='Image Url', validators=[DataRequired()], render_kw=style)
    body = CKEditorField(label='Body', validators=[DataRequired()],  render_kw={'class': 'form-control', 'rows': 10, "style": "font-weight: bold; font-size: medium"})
    submit = SubmitField("Submit Post")

class UserForm(FlaskForm):
    name = StringField(label='Name', validators=[DataRequired()])
    email = EmailField(label='Email', validators=[DataRequired()])
    password = PasswordField(label='Password', validators=[DataRequired()])
    submit = SubmitField("Register")

class LoginUserForm(FlaskForm):
    email = EmailField(label='Email', validators=[DataRequired()])
    password = PasswordField(label='Password', validators=[DataRequired()])
    submit = SubmitField("Login")

class CommentForm(FlaskForm):
    text = CKEditorField(label='Comments', validators=[DataRequired()],  render_kw={'class': 'form-control', 'rows': 10, "style": "font-weight: bold; font-size: medium"})
    submit = SubmitField("Add Comment")