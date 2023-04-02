import datetime as dt
import json,html
import os
import smtplib
import uuid

from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_bootstrap import Bootstrap
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_ckeditor import CKEditor
from flask_gravatar import Gravatar
from flask_session import Session
from flask_wtf.csrf import CSRFProtect

from forms import LoginUserForm, UserForm, PostForm, CommentForm
from models import db, Post, login_manager, User, Comment

app = Flask(__name__)
# app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
Bootstrap(app)
CKEditor(app)
csrf = CSRFProtect()
gravatar = Gravatar(app,
                    size=80,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)

##Connect to Database
db_url = os.environ.get('DB_URL')
database_url = db_url.replace('postgres://',
               'postgresql://',
               1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
login_manager.init_app(app)
csrf.init_app(app)
app.app_context().push()
db.create_all()

all_blogs = []


@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(id=user_id).first()


@app.route('/')
def home_page():
    all_blogs = Post.query.all()
    if 'user_id' not in session:
        return render_template('index.html', blogs=all_blogs, is_logged_in=False)
    return render_template('index.html', blogs=all_blogs, is_logged_in=current_user.is_authenticated)


@app.route('/tips')
def tips_page():
    with open('tips.txt', mode='r') as tips:
        tips_content = tips.readlines()
    return render_template('tips.html', tips=tips_content, is_logged_in=current_user.is_authenticated)


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    login = LoginUserForm()
    if login.validate_on_submit():
        user = User.query.filter_by(email=login.email.data).first()
        if user:
            if check_password_hash(user.password, login.password.data):
                session['user_id'] = user.id
                login_user(user)
                return redirect(url_for('home_page'))
            else:
                flash("Invalid username/password. Please try again!")
                return redirect(url_for('login_page'))
        else:
            return redirect(url_for('register_page'))
    return render_template('login.html', login=login, is_logged_in=current_user.is_authenticated)


@app.route('/register', methods=['GET', 'POST'])
def register_page():
    user = UserForm()
    if user.validate_on_submit():
        new_user = User.query.filter_by(email=user.email.data).first()
        if new_user:
            flash("User already exists. Please login to continue...")
            return redirect(url_for('login_page'))
        else:
            new_user = User(
                name=user.name.data,
                email=user.email.data,
                password=generate_password_hash(user.password.data, method='pbkdf2:sha256', salt_length=8)
            )
            db.session.add(new_user)
            db.session.commit()
            session['user_id'] = new_user.id
            login_user(new_user)
            return redirect(url_for('home_page'))
    return render_template('register.html', register=user, is_logged_in=current_user.is_authenticated)


@app.route('/contact', methods=['GET', 'POST'])
def contact_page():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        phone_no = request.form['phone']
        message = request.form['message']
        print(f"{username}\n{email}\n{phone_no}\n{message}\n")

        # send email
        with open('config.json', mode='r') as email_config:
            email_details = json.load(email_config)
            from_email = email_details['from_email']
            password = email_details['password']

            with smtplib.SMTP('smtp.gmail.com') as connection:
                connection.starttls()
                connection.login(user=from_email, password=password)
                connection.sendmail(from_addr=from_email, to_addrs=email, msg=f"Subject: Contact form details\n\n"
                                                                              f"Details are - username = {username},\n"
                                                                              f"email = {email},\n"
                                                                              f"phone_no = {phone_no},\n"
                                                                              f"message = {message},\n")
        return render_template('contact.html', contact='Form Submitted Successfuly',
                               is_logged_in=current_user.is_authenticated)
    return render_template('contact.html', contact='Contact Me', is_logged_in=current_user.is_authenticated)


@app.route("/post", methods=['GET', 'POST'])
def add_post():
    if not current_user.is_authenticated:
        flash('You need to login to add new blog post. Please login 👇 to continue...!')
        return redirect(url_for('login_page'))
    post = PostForm()
    if post.validate_on_submit():
        new_post = Post(
            title=html.unescape(post.title.data),
            author=current_user,
            image_url=post.image_url.data,
            date=dt.datetime.today().strftime("%B %d, %Y"),
            body=html.unescape(post.body.data.replace('<p>','').replace('</p>','').strip())
        )
        db.session.add(new_post)
        db.session.commit()
        all_blogs.append(new_post)
        return redirect(url_for('home_page'))
    else:
        return render_template('new_post.html', post=post, is_logged_in=current_user.is_authenticated)


@app.route("/edit/<int:number>", methods=['GET', 'POST'])
def edit_post(number):
    post = PostForm()
    requested_post = Post.query.filter_by(id=number).first()
    if post.validate_on_submit():
        requested_post.title = html.unescape(post.title.data)
        requested_post.image_url = post.image_url.data
        requested_post.date = dt.datetime.today().strftime("%B %d, %Y")
        requested_post.body = html.unescape(post.body.data.replace('<p>','').replace('</p>','').strip())
        db.session.commit()
        return redirect(url_for('home_page'))
    post.title.data = requested_post.title
    post.image_url.data = requested_post.image_url
    post.body.data = requested_post.body
    return render_template('edit_post.html', post=post, is_logged_in=current_user.is_authenticated)


@app.route("/blog/<int:number>", methods=['GET','POST'])
def post_page(number):
    comment = CommentForm()
    requested_post = Post.query.filter_by(id=number).first()
    if comment.validate_on_submit():
        new_comment = Comment(
            text = html.unescape(comment.text.data.replace('<p>','').replace('</p>','').strip()),
            date = dt.datetime.today().strftime("%B %d, %Y"),
            comment_author = current_user,
            parent_post = requested_post
        )
        db.session.add(new_comment)
        db.session.commit()
    return render_template("post.html", blog=requested_post, is_logged_in=current_user.is_authenticated, comment=comment)

@app.route("/delete-blog/<int:number>", methods=['GET','POST'])
def delete_post(number):
    requested_post = Post.query.filter_by(id=number).first()
    db.session.delete(requested_post)
    db.session.commit()
    return redirect(url_for('home_page'))


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home_page'))


if __name__ == ('__main__'):
    app.run(debug=True)
