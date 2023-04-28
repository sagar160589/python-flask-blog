import datetime as dt
import json, html
import smtplib
import redis
import requests
import os
import time
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_bootstrap import Bootstrap
from flask_login import login_user, logout_user, current_user
from oauthlib.oauth2 import WebApplicationClient
from werkzeug.security import generate_password_hash, check_password_hash
from flask_ckeditor import CKEditor
from flask_gravatar import Gravatar

from forms import LoginUserForm, UserForm, PostForm, CommentForm
from models import db, Post, login_manager, User, Comment, User1

app = Flask(__name__)

with app.app_context():
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
    #app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
    Bootstrap(app)
    CKEditor(app)
    GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", None)
    GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", None)
    GOOGLE_DISCOVERY_URL = os.environ.get("GOOGLE_DISCOVERY_URL")
    r = redis.StrictRedis(host='red-cguk152ut4mcfrj3kha0', port=6379, db=0)
    #r = redis.StrictRedis(host='localhost', port=6379, db=0)
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
    #app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///post.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    login_manager.init_app(app)
    client = WebApplicationClient(GOOGLE_CLIENT_ID)
    db.create_all()
    all_blogs = []



def get_google_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()



@login_manager.user_loader
def load_user(user_id):
    user = get_user_from_cache(r.get(user_id))
    return user


@app.route("/chatbot", methods=['GET', 'POST'])
def get_bot_response():
    text = str(request.form['message'])
    print(text)
    data = json.dumps({"sender": "Rasa", "message": text})
    headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
    response = requests.post('https://blog-chatbot.onrender.com/webhooks/rest/webhook', data=data, headers=headers)
    response = response.json()
    print(response)
    return str(response[0]['text'])


@app.route('/')
def home_page():
    if not r.exists('blogs'):
        print('No blogs found in cache')
        '''
            To check the time difference when blogs are retrieved from database
            Time difference calculated was - 0.18599557876586914
        '''
        starttime = time.time()
        all_blogs = Post.query.all()
        print(f"Time difference while fetching from database: {time.time() - starttime}")
        save_blog_in_cache(all_blogs)
    else:
        '''
            To check the tie difference when blogs are retrieved from cache
            Time difference calculated was - 0.010001897811889648
        '''
        starttime = time.time()
        all_blogs = get_blog_from_cache()
        print(f"Time difference while getting details from cache: {time.time() - starttime}")
    return render_template('index.html', blogs=all_blogs, is_logged_in=current_user.is_authenticated)


@app.route('/tips')
def tips_page():
    with open('tips.txt', mode='r') as tips:
        tips_content = tips.readlines()
    return render_template('tips.html', tips=tips_content, is_logged_in=current_user.is_authenticated)

#Get code from google to allbackurl
@app.route("/login/callback")
def callback():
    code = request.args.get("code")
    print(f"Code from google: {code}")
    google_provider_cfg = get_google_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]
    print(f"token endpoint: {token_endpoint}")
    print(f"request.url after auth: {request.url}")
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code
    )
    print(f"token url: {token_url}")
    print(f"headers: {headers}")
    print(f"body: {body}")
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )
    client.parse_request_body_response(json.dumps(token_response.json()))
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)
    print(f"User Response Json: {userinfo_response.json()}")
    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        picture = userinfo_response.json()["picture"]
        users_name = userinfo_response.json()["given_name"]
    else:
        return "User email not available or not verified by Google.", 400
    user = User1(id=unique_id,name=users_name,email=users_email, display_pic=picture)
    login_user(user)
    r.set(user.id, save_user_in_cache(user))
    return redirect(url_for('home_page'))

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    google_provider_cfg = get_google_cfg()
    print(f"google_provider_cfg: {google_provider_cfg}")
    authorization_endpoint = google_provider_cfg['authorization_endpoint']
    print(f"authorization_endpoint: {authorization_endpoint}")
    request_uri = client.prepare_request_uri(authorization_endpoint,
                                             redirect_uri=request.base_url + "/callback",
                                             scope=["openid", "email", "profile"])
    print(f"request uri: {request_uri}")
    return redirect(request_uri)
    # login = LoginUserForm()
    # if login.validate_on_submit():
    #     user = User.query.filter_by(email=login.email.data).first()
    #     if user:
    #         if check_password_hash(user.password, login.password.data):
    #             login_user(user)
    #             r.set(user.id, save_user_in_cache(user))
    #             if session.get('number') is None:
    #                 return redirect(url_for('home_page'))
    #             else:
    #                 number = session.get('number')
    #                 next =request.host_url+"blog/"+str(number)
    #                 return redirect(next or url_for('home_page'))
    #         else:
    #             flash("Invalid username/password. Please try again!")
    #             return redirect(url_for('login_page'))
    #     else:
    #         return redirect(url_for('register_page'))
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
            r.set(new_user.id, save_user_in_cache(new_user))
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
        user = User.query.filter_by(id=current_user.id).first()
        new_post = Post(
            title=html.unescape(post.title.data),
            author=user,
            image_url=post.image_url.data,
            date=dt.datetime.today().strftime("%B %d, %Y"),
            body=html.unescape(post.body.data.replace('<p>', '').replace('</p>', '').strip())
        )
        db.session.add(new_post)
        db.session.commit()
        all_blogs = get_blog_from_cache()
        all_blogs.append(new_post)
        save_blog_in_cache(all_blogs)  # Save in cache eagerly
        return redirect(url_for('home_page'))
    else:
        return render_template('new_post.html', post=post, is_logged_in=current_user.is_authenticated)


@app.route("/edit/<int:number>", methods=['GET', 'POST'])
def edit_post(number):
    post = PostForm()
    requested_post = Post.query.filter_by(id=number).first()
    if post.validate_on_submit():
        if not current_user.is_authenticated:
            session['number'] = number
            flash('You need to login to edit your post. Please login 👇 to continue...!')
            return redirect(url_for('login_page'))
        requested_post.title = html.unescape(post.title.data)
        requested_post.image_url = post.image_url.data
        requested_post.date = dt.datetime.today().strftime("%B %d, %Y")
        requested_post.body = html.unescape(post.body.data.replace('<p>', '').replace('</p>', '').strip())
        db.session.commit()
        return redirect(url_for('home_page'))
    post.title.data = requested_post.title
    post.image_url.data = requested_post.image_url
    post.body.data = requested_post.body
    return render_template('edit_post.html', post=post, is_logged_in=current_user.is_authenticated)


@app.route("/blog/<int:number>", methods=['GET', 'POST'])
def post_page(number):
    comment = CommentForm()
    requested_post = Post.query.filter_by(id=number).first()
    if comment.validate_on_submit():
        if not current_user.is_authenticated:
            session['number'] = number
            flash('You need to login to add comments to any post. Please login 👇 to continue...!')
            return redirect(url_for('login_page'))
        user = User.query.filter_by(id=current_user.id).first()
        new_comment = Comment(
            text=html.unescape(comment.text.data.replace('<p>', '').replace('</p>', '').strip()),
            date=dt.datetime.today().strftime("%B %d, %Y"),
            comment_author=user,
            parent_post=requested_post
        )
        db.session.add(new_comment)
        db.session.commit()
    return render_template("post.html", blog=requested_post, is_logged_in=current_user.is_authenticated,
                           comment=comment)


@app.route("/delete-blog/<int:number>", methods=['GET', 'POST'])
def delete_post(number):
    requested_post = Post.query.filter_by(id=number).first()
    db.session.delete(requested_post)
    db.session.commit()
    all_blogs = Post.query.all()
    save_blog_in_cache(all_blogs)
    return redirect(url_for('home_page'))


@app.route("/logout")
def logout():
    print(f"Deleting user from redis with user_id: {current_user.id}")
    r.delete(current_user.id)
    session.pop('number', None)
    logout_user()
    return redirect(url_for('home_page'))


def save_user_in_cache(user):
    return json.dumps({'id': user.id, 'name': user.name, 'email': user.email, 'password': user.password})


def get_user_from_cache(user):
    user_des = json.loads(user)
    return User(id=user_des['id'], name=user_des['name'], email=user_des['email'], password=user_des['password'])


def save_blog_in_cache(all_blogs):
    all_blogs_list = [{"id": blog.id, "title": blog.title, "author_id": blog.author_id,
                       "image_url": blog.image_url, "date": blog.date,
                       "body": blog.body} for blog in all_blogs]
    r.lpush('blogs', json.dumps(all_blogs_list))


def get_blog_from_cache():
    print('Blogs found in cache')
    blogs_ser = r.lrange('blogs', 0, -1)
    all_blogs_des = [json.loads(blog) for blog in blogs_ser]
    all_blogs = [Post(id=blog['id'], title=blog['title'], author_id=blog['author_id'], image_url=blog['image_url'],
                      date=blog['date'], body=blog['body']) for blog in all_blogs_des[0]]
    r.expire('blogs', 120)
    return all_blogs


if __name__ == ('__main__'):
    app.run(debug=True)
