from flask import Flask,render_template,request,session,redirect
import sqlalchemy as sql
import json
from flask_mail import Mail
import os
from werkzeug.utils import secure_filename




with open('config.json','r') as c:
    params = json.load(c)['params']

local_server = params['local_server']



app = Flask(__name__)
app.secret_key = '01@Ug1992'
app.config['UPLOAD_FOLDER'] = params['upload_location']
app.config.update(MAIL_SERVER = 'smtp.gmail.com',
                  MAIL_PORT = '465',
                  MAIL_USE_SSL = True,
                  MAIL_USERNAME = params['gmail_user'],
                  MAIL_PASSWORD = params['gmail_password'])
mail = Mail(app)

if (local_server):
    x=sql.create_engine(params['local_uri'])
    conn = x.raw_connection()
    cur = conn.cursor()
else:
    x = sql.create_engine(params['production_uri'])
    conn = x.raw_connection()
    cur = conn.cursor()



@app.route("/")
def home():
    cur.execute('select title,sub_title,date,slug,content from welcome')
    data = cur.fetchall()
    length_of_data = len(data)
    int_params = int(params['post_no'])

    return render_template('index.html', params=params,data=data,length_of_data=length_of_data,int_params=int_params)


#AdminLogin
@app.route("/dashboard",methods=['GET','POST'])
def dashboard():
    if 'user' in session and session['user'] == params['admin_user']:
        cur.execute('select sno,title,date,slug from welcome')
        table_data = cur.fetchall()

        return render_template('loggedin_dashboard.html',params=params,table_data=table_data)
    if request.method == 'POST':
        username = request.form.get('u_name')


        userpasswrd = request.form.get('pass')

        if(username == params['admin_user'] and userpasswrd == params['admin_password']):
            session['user'] = username
            cur.execute('select sno,title,date from welcome')
            table_data = cur.fetchall()

            return render_template('loggedin_dashboard.html', params=params,table_data=table_data)
        else:

            print_data='**Details not matched**'

            return render_template('dashboard.html', params=params,print_data = print_data)
    return render_template('dashboard.html', params=params)


#UploaderForAdmin
@app.route("/uploader",methods=['GET','POST'])
def uploader():
    if 'user' in session and session['user'] == params['admin_user']:
        if request.method == 'POST':
            f = request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'],secure_filename(f.filename)))
            return '<h4>uploaded successfully</h4>\n <a href="/dashboard">Dashboard</a>'




#AboutWebsite
@app.route("/about")
def about():
    return render_template('about.html',params=params)


@app.route("/logout")
def logout():
    session.pop('user')
    return redirect('/dashboard')


@app.route("/delete/<string:sno>")
def delete(sno):
    if 'user' in session and session['user'] == params['admin_user']:
        if '-' not in sno:
            cur.execute(f"delete from welcome where sno={sno}")
            conn.commit()
            return redirect('/dashboard')
        else:
            cur.execute(f"delete from welcome where slug='{sno}'")
            conn.commit()
            return redirect('/')


    return redirect('/dashboard')


#ContactPageForViewers
@app.route("/contact",methods = ['GET','POST'])
def contact():
    if request.method == 'POST' :
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        cur.execute(f"insert into contactmsg(name,e_address,phone_no,message) value('{name}','{email}','{phone}','{message}')")
        conn.commit()
        mail.send_message(f'New message in blog from {name}',sender = email, recipients = [params['gmail_user']],body = f'{message}\n {phone}\n{email}')
        return '<h1>message submit successfully</h1>\n <a href="/">Home Page</a>'
    else:
        return render_template('contact.html',params=params)


#ForPostRendring
@app.route("/post/<string:post_slug>",methods=['GET'])
def post(post_slug):
    cur.execute(f"select content,title,sub_title,date,img_name,sno from welcome where slug ='{post_slug}' ")
    data = cur.fetchall()
    content=data[0][0]

    title=data[0][1]
    sub_title=data[0][2]
    date=data[0][3]
    img = data[0][4]
    sno = data[0][5]

    return render_template('post.html',params=params,content=content,title=title,sub_title=sub_title,date=date,img=img,sno=sno,post_slug=post_slug)



@app.route("/edit/<string:sno>",methods=['GET','POST'])
def edit(sno):
    if 'user' in session and session['user'] == params['admin_user']:
        if request.method == 'POST':
            title = request.form.get('title')
            sub_title = request.form.get('sub_title')
            slug = request.form.get('slug')
            content = request.form.get('content')
            image_name = request.form.get('image_name')
            if sno == '0':
                cur.execute(f"""insert into welcome(title,sub_title,slug,content,img_name) value("{title}","{sub_title}","{slug}","{content}","{image_name}")""")
                conn.commit()

                return redirect(f"/post/{slug}")
            else:
                cur.execute(f"""update welcome set title="{title}",sub_title="{sub_title}",slug='{slug}',content="{content}",img_name='{image_name}' where sno='{sno}'""")
                conn.commit()
                return redirect(f"/post/{slug}")

        cur.execute(f"select title,sub_title,slug,content,img_name,sno from welcome where sno={sno}")
        data = cur.fetchall()

        if sno == '0':
            return render_template('adding_new_post.html',params=params,sno=sno)
        return render_template('edit.html',params=params,data=data)



@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html',params=params),404




if __name__ == "__main__":
    app.run(debug=True)