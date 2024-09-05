from flask import Flask,redirect,render_template,url_for,session,flash,request,send_from_directory
import os
from flask_sqlalchemy import SQLAlchemy
from flask import jsonify
from flask_socketio import send,SocketIO

from flask_login import UserMixin, login_user, LoginManager,login_required, logout_user, current_user
from webforms import LoginForm,RegistrationForm,GroupForm,JoinForm
from authlib.integrations.flask_client import OAuth

from datetime import datetime
from string import ascii_uppercase

from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash

from werkzeug.utils import secure_filename

from api_key import GITHUB_CLIENT_ID,GITHUB_CLIENT_SECRET,CLIENT_ID,CLIENT_SECRET

import random
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecretkey'

UPLOAD_FOLDER = 'uploads'

# SQLite Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat.db'
# Initialize the database
db = SQLAlchemy(app)

MAX_BUFFER_SIZE = 50 * 1000 * 1000  # 50 MB
socketio = SocketIO(app,max_http_buffer_size=MAX_BUFFER_SIZE)

migrate = Migrate(app, db)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'txt', 'docx', 'xlsx'}
def allowed_file(filename):
    """
    Check if the uploaded file is allowed based on its extension.
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Flask Login Stuff
login_manager = LoginManager()
login_manager.init_app(app)

app.config['LOGIN_VIEW'] = 'login'

oauth = OAuth(app)

google = oauth.register(
    name='google',
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    authorize_url='https://accounts.google.com/o/oauth2/v2/auth',
    access_token_url="https://oauth2.googleapis.com/token",
    authorization_base_url="https://accounts.google.com/o/oauth2/v2/auth",
    token_url="https://oauth2.googleapis.com/token",
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs = {'scope': 'openid profile email'},
    access_token_method="POST"
)

github = oauth.register(
    name='github',
    client_id=GITHUB_CLIENT_ID,
    client_secret=GITHUB_CLIENT_SECRET,
    authorize_url='https://github.com/login/oauth/authorize',
    authorize_params=None,
    access_token_url='https://github.com/login/oauth/access_token',
    access_token_params=None,
    client_kwargs={'scope': 'user:email'},
)



if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Database Models
# --------------------------------------------Models----------------------------------------
# Association table for Many-to-Many relationship between Users and Groups
group_user_association = db.Table('group_user_association',
    db.Column('group_id', db.Integer, db.ForeignKey('groups.id')),
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'))
)

class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(20), nullable=True, unique=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    date_join = db.Column(db.DateTime, default=datetime.now)
    # Do some password stuff!
    password_hash = db.Column(db.String(200),nullable=True)
    
    # Relationship with groups (many-to-many)
    groups = db.relationship('Groups', secondary=group_user_association, backref='members')

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute!')
    @password.setter
    def password(self, password):
         self.password_hash = generate_password_hash(password)
    
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    # Create A String
    def __repr__(self):
        return '<Name %r>' % self.name

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.now())

    user = db.relationship('Users', backref='messages')
    group = db.relationship('Groups', backref='messages1')

class Groups(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(200), nullable=False,unique=True)
    code = db.Column(db.String(4), nullable=False,unique=True)
    description = db.Column(db.Text, nullable=True)

def generate_unique_code(length):
    """
    its required for unique codes for create a room
    """
    while True:
        code = ""
        code = ''.join(random.choice(ascii_uppercase) for _ in range(length))
        if not Groups.query.filter_by(code=code).first():  # Check if room code exists in the database
            break
    
    return code

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

@app.route('/login/google')
def login_google():
	try:
		redirect_uri = url_for('authorize_google', _external=True)
		return google.authorize_redirect(redirect_uri, prompt='select_account')
	except Exception as e:
		app.logger.error(f"Error during login: {str(e)}")
		return "Error occured during login", 500

# Authorize For Google
@app.route("/authorize/google")
def authorize_google():
	token = google.authorize_access_token()
	userinfo_endpoint = google.server_metadata['userinfo_endpoint']
	response = google.get(userinfo_endpoint)
	user_info = response.json()
	email = user_info['email']

	user = Users.query.filter_by(email=email).first()
	
	if user is None:
		user = Users(email=email, name=user_info['name'], password="")
		db.session.add(user)
		db.session.commit()
		flash("User Created Successfully!")
		login_user(user)
		return redirect(url_for('hello_world'))
	else:
		login_user(user)
		return redirect(url_for('hello_world'))



# Login Page
@app.route('/login', methods=['GET', 'POST'])
def login():
        loginform = LoginForm()
        signupform = RegistrationForm()

        if loginform.validate_on_submit():
            user = Users.query.filter_by(username=loginform.username.data).first()
            if user:
                # Check the hash
                if check_password_hash(user.password_hash, loginform.password.data):
                    login_user(user)
                    session["name"] = loginform.username.data
                    session["id"] = user.id
                    # register -> home
                    return redirect(url_for('chatroom',username=user.username))
                else:
                    flash("Wrong Credentials - Try Again!", "danger")
            else:
                flash("User Does Not Exist!", "danger")
        return render_template('login.html', loginform=loginform, signupform=signupform)

# Logout Page
@app.route('/logout/<int:id>')
@login_required
def logout(id):
    print("Hello World")
    user = Users.query.filter_by(id=id).first()
    logout_user()
    flash("You Have Been Logged Out!")
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    signupform = RegistrationForm()
    loginform = LoginForm()
    if signupform.validate_on_submit():
        username = signupform.username.data
        email = signupform.email.data
        if Users.query.filter_by(username=username).first():
            flash("Username already exists. Please choose a different username.")
            return redirect(url_for('login'))
        if Users.query.filter_by(email=email).first():
            flash("Email already exists. Please choose a different Email.")
            return redirect(url_for('login'))
        hashed_password = generate_password_hash(signupform.password.data)
        new_user = Users(name=signupform.name.data,username=signupform.username.data, email=signupform.email.data, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        id = Users.query.filter_by(username=username).first()
        session["name"] = username
        session["id"] = id.id
        # register->home
        return redirect(url_for('chatroom',username=id.username))
    
    return render_template('login.html', signupform=signupform, loginform=loginform)

@app.route("/addGroup/<username>", methods=["GET","POST"])
@login_required
def addGroup(username):
    form = GroupForm()
    user = Users.query.filter_by(username=username).first()
    if form.validate_on_submit():
        print("Hello")
        name = form.name.data
        description = form.description.data
        code = generate_unique_code(4)
        new_group = Groups(name=name, description=description,code=code)
        # groups=Groups.query.filter_by(user_id=user.id)
        user.groups.append(new_group)
        db.session.add(new_group)
        db.session.commit()
        return redirect(url_for('chatroom', username=username))

    return render_template("add_group.html",groupform=form,user=user)


@app.route("/joinGroup/<username>", methods=["GET","POST"])
@login_required
def joinGroup(username):
    form = JoinForm()
    user = Users.query.filter_by(username=username).first()
    if form.validate_on_submit():
        code = form.code.data
        group = Groups.query.filter_by(code=code).first()
        print(group)
        user = Users.query.filter_by(username=username).first()
        print(user)
        if group:
            print("Hello World")
            session["room"] = code
            session["name"] = username

            user.groups.append(group)

            db.session.commit()
                
            return redirect(url_for("chatroom", username=username))
        else:
            flash("Room not found.")
            return render_template("join_group.html",username=user.username)
    return render_template("join_group.html",joinform=form,user=user)

@app.route('/get_messages/<group_name>')
def get_messages(group_name):
    group = Groups.query.filter_by(name=group_name).first()
    if not group:
        return jsonify({"error": "Group not found"}), 404
    
    messages = Message.query.filter_by(group_id=group.id).order_by(Message.timestamp).all()

    # Format the messages in a list of dictionaries
    message_data = []
    for msg in messages:
        user = Users.query.filter_by(id=msg.user_id).first()
        message_data.append({
            "content": msg.content,
            "sender_id": msg.user_id,
            "sender_name":user.username,
            "timestamp": msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    print(jsonify(message_data))

    return message_data

@app.route('/leave_group/<group_name>', methods=['POST','GET'])
@login_required
def leave_group(group_name):
    group = Groups.query.filter_by(name=group_name).first_or_404()
    
    if group in current_user.groups:
        current_user.groups.remove(group)
        db.session.commit()
        print(f'You have left the group {group.name}.')
        return redirect(url_for('chatroom',username=current_user.username))
    else:
        print('You are not a member of this group.')
    
    message = "You are not a member of this group."

    return message

@app.route("/", methods=["GET", "POST"])
@app.route("/chatroom/<username>", methods=["GET","POST"])
@login_required
def chatroom(username):
    # Load all users and their last message from the database
    # users = Users.query.all()
    # chats1 = []

    # for user in users:
    #     last_message = Message.query.filter_by(user_id=user.id).order_by(Message.timestamp.desc()).first()
    #     chats1.append({
    #         'user': "Name",
    #         'last_message': "Message"
    #     })

    if username is None:
        print("Hello WOrld")
        # Handle the case where no ID is provided (e.g., use current user's ID)
        try:
            if username in session["username"]:
                username = current_user.username
            else:
                return redirect(url_for('login'))
        except:
            flash("You need to be logged in first!")
            return redirect(url_for('login'))


    print(username)
    user = Users.query.filter_by(username=username).first()
    print(user.id)
    groups = user.groups

    for group in groups:
        print(group.name)
    messages = Message.query.filter_by(user_id=user.id).all()
    
    return render_template("index.html",groups=groups,messages=messages,user=user,id=user.id)

@app.route("/upload_file", methods=["POST","GET"])
def upload_file():
    if 'file' not in request.files:
        return {"success": False, "message": "No file part"}
    
    file = request.files['file']
    
    if file.filename == '':
        return {"success": False, "message": "No selected file"}
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        file_url = url_for('uploaded_file', filename=filename)
        return {"success": True, "file_url": file_url}
    
    return {"success": False, "message": "File type not allowed"}

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@socketio.on("message") 
def message(data):
    # group = session.get("room")
    # rooms = db.session.query(Users.room).distinct().all()
    # print(rooms)
    # rooms1 = []
    # for i in rooms:
    #     for j in i:
    #         rooms1.append(j)
    # if room not in rooms1:
    #     return

    # print(data)
    # print(data['group_name'])
    group = Groups.query.filter_by(name=data['group_name']).first()
    print(group)
    if group:
        new_message = Message(user_id=data['sender_id'],group_id=group.id,content=data['data'],timestamp=datetime.now())  # Create a new message instance
        # Save message to the database
        db.session.add(new_message)  # Add the message to the session
        db.session.commit()  # Commit the session to save the message
        print("Sent!")
        
    
    # content = {
    #     "name": session.get("name"),
    #     "message": data["data"]
    # }


    # send(content, to=room)
    # print(f"{session.get('name')} said: {data['data']}")



## Create Custom Error Pages
# Invalid URL
@app.errorhandler(401)
def page_not_found(e):
	return redirect(url_for("login")),401

if __name__ == '__main__':
    socketio.run(app,debug=True)