import datetime as dt
import json
import os
import smtplib

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_bootstrap import Bootstrap
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from models import db, Post, PostForm, login_manager, User, LoginUserForm, UserForm

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)

##Connect to Database

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///post.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
login_manager.init_app(app)
app.app_context().push()
db.create_all()

all_blogs = []


@login_manager.user_loader
def load_user(user_id):
    print(f"The user_id in session is ##### {user_id}")
    return User.query.filter_by(id=user_id).first()


@app.route('/')
def home_page():
    all_blogs = Post.query.all()
    return render_template('index.html', blogs=all_blogs, is_logged_in=current_user.is_authenticated)


@app.route('/tips')
def tips_page():
    with open('tips.txt', mode='r') as tips:
        tips_content = tips.readlines()
    return render_template('tips.html', tips=tips_content)


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    login = LoginUserForm()
    if login.validate_on_submit():
        user = User.query.filter_by(email=login.email.data).first()
        if user:
            if check_password_hash(user.password, login.password.data):
                login_user(user)
                return redirect(url_for('home_page'))
            else:
                flash("Invalid username/password. Please try again!")
                return redirect(url_for('login_page'))
        else:
            flash('User does not exists. Please register to access blogs')
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
@login_required
def add_post():
    post = PostForm()
    if post.validate_on_submit():
        new_post = Post(
            title=post.title.data,
            author=post.author.data,
            image_url=post.image_url.data,
            date=dt.datetime.now().date(),
            body=post.body.data
        )
        db.session.add(new_post)
        db.session.commit()
        all_blogs.append(new_post)
        return redirect(url_for('home_page'))
    else:
        return render_template('new_post.html', post=post, is_logged_in=current_user.is_authenticated)


@app.route("/edit/<int:number>", methods=['GET', 'POST'])
@login_required
def edit_post(number):
    post = PostForm()
    requested_post = Post.query.filter_by(id=number).first()
    if post.validate_on_submit():
        requested_post.title = post.title.data
        requested_post.author = post.author.data
        requested_post.image_url = post.image_url.data
        requested_post.date = dt.datetime.now().date()
        requested_post.body = post.body.data
        db.session.commit()
        return redirect(url_for('home_page'))
    post.title.data = requested_post.title
    post.author.data = requested_post.author
    post.image_url.data = requested_post.image_url
    post.body.data = requested_post.body
    return render_template('edit_post.html', post=post, is_logged_in=current_user.is_authenticated)


@app.route("/blog/<int:number>")
def post_page(number):
    requested_post = Post.query.filter_by(id=number).first()
    return render_template("post.html", blog=requested_post, is_logged_in=current_user.is_authenticated)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('home_page'))


if __name__ == ('__main__'):
    app.run(debug=True)
