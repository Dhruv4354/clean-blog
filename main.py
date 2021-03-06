

from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.utils import secure_filename
import json
import os
import math
from flask_mail import Mail
app = Flask(__name__)
app.secret_key = "Hellothissecretkey"
with open("config.json", "r") as c:
    params = json.load(c)["params"]
app.config['UPLOAD_FOLDER'] = params['upload_location']

local_server = params["local_server"]
prod_URI = False

app.config.update(
    MAIL_SERVER="smtp.gmail.com",
    MAIL_PORT=465,
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params["gmail_user"],
    MAIL_PASSWORD=params["gmail_passwd"]
)
mail = Mail(app)

if local_server:
    app.config['SQLALCHEMY_DATABASE_URI'] = params["local_server_URI"]

elif prod_URI:
    app.config['SQLALCHEMY_DATABASE_URI'] = params["pord_server_URI"]

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Contacts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    phone_num = db.Column(db.Integer(), nullable=False)
    mes = db.Column(db.String(50), nullable=False)
    date = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), nullable=False)


class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500), nullable=False)
    img_file = db.Column(db.String(120), nullable=False)
    slug = db.Column(db.String(), nullable=False)
    tagline = db.Column(db.String(), nullable=False)
    content = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=False)
# sno title slug content  date


@app.route("/")
def home():
    posts = Posts.query.filter_by().all()
    last = math.ceil(len(posts)/int(params["no_of_post"]))
    page = request.args.get('page')
    if (not str(page).isnumeric()):
        page = 1
    page = int(page)
    posts = posts[((page-1)*int(params["no_of_post"])):((page-1) * int(params["no_of_post"]) + int(params["no_of_post"]))]
    if page==1:
        prev = "#"
        next = "/?page="+ str(page+1)
    elif page==last:
        prev = "/?page="+ str(page-1)
        next = "#"
    else:
        prev = "/?page="+ str(page-1)
        next = "/?page="+ str(page+1)
    return render_template('index.html', params=params, prev=prev, next=next, posts=posts)

@app.route('/about/')
def about():
    
    
    return render_template('about.html', params=params)


@app.route('/post/<string:post_slug>', methods=["GET"])
def post(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template('post.html',  params=params, post=post)


@app.route('/dashboard/', methods=["GET", "POST"])
def dashboard():
   if 'user' in session and session['user'] == params['admin_user']:
       posts = Posts.query.all()
       return render_template('dashboard.html', params=params, post=posts)
   if request.method == 'POST':
       username = request.form.get('uname')
       userpass = request.form.get('pass')
       if username == params['admin_user'] and userpass == params['admin_passwd']:
           session['user'] = username
   posts = Posts.query.all()
   return render_template('login.html', params=params, post=posts)

@app.route('/contact/', methods=["GET", "POST"])
def contact():
    if request.method == 'POST':
        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        msg = request.form.get("msg")
        entry = Contacts(name=name, email=email, phone_num=phone,
                         mes=msg, date=datetime.utcnow())
        db.session.add(entry)
        db.session.commit()
        mail.send_message(f"New Message From: {name}", sender=email, recipients=[
                          params["gmail_user"]], body=msg + "\n" + str(datetime.utcnow()))

    return render_template('contact.html', params=params)


@app.route("/edit/<string:sno>" , methods=['GET', 'POST'])
def edit(sno):
    if "user" in session and session['user']==params['admin_user']:
        if request.method=="POST":
             boxtitle = request.form.get('title')
             tline = request.form.get('tline')
             slug = request.form.get('slug')
             content = request.form.get('content')
             img_file = request.form.get('img_file')
             date = datetime.now()
        
             if sno=='0':
                post = Posts(title=boxtitle, slug=slug, content=content, tagline=tline, img_file=img_file, date=date)
                db.session.add(post)
                db.session.commit()
             else:
                post = Posts.query.filter_by(sno=sno).first()
                post.title  = boxtitle
                post.slug = slug
                post.content = content
                post.tagline = tline
                post.img_file = img_file
                post.date = date
                db.session.commit()
                return redirect('/edit/' + sno)
        post = Posts.query.filter_by(sno=sno).first()
        return render_template('edit.html', params=params,sno=sno,post=post)

@app.route('/uploader/', methods=['GET','POST'])
def uploader():
    if "user" in session and session['user']==params['admin_user']:
        if request.method=="POST":
            f = request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
    return "<center><b><h1>FILE UPLOADED SUCCESSFULLY</h1></b></center>"

@app.route("/logout/")
def logout():
    session.pop('user')
    return redirect('/dashboard')
@app.route("/delete/<string:sno>" , methods=['GET','POST'])

def delete(sno):
    if "user" in session and session['user']==params['admin_user']:
      post =Posts.query.filter_by(sno=sno).first()
      db.session.delete(post)
      db.session.commit()
    return redirect('/dashboard')

if __name__ == '__main__':
    app.run(debug=True, port=8000)
