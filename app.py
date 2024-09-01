from flask import Flask,redirect,render_template,url_for,session,flash,request
import os
from flask_sqlalchemy import SQLAlchemy
from flask import jsonify

from flask_login import UserMixin, login_user, LoginManager,login_required, logout_user, current_user
from webforms import LoginForm,RegistrationForm
from authlib.integrations.flask_client import OAuth

from datetime import datetime

from flask import json
from werkzeug.exceptions import HTTPException

from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash

from api_key import GITHUB_CLIENT_ID,GITHUB_CLIENT_SECRET,CLIENT_ID,CLIENT_SECRET

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecretkey'

UPLOAD_FOLDER = 'uploads'

# SQLite Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat.db'
# Initialize the database
db = SQLAlchemy(app)
migrate = Migrate(app, db)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'txt', 'docx', 'xlsx'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Database Models
# --------------------------------------------Models----------------------------------------
class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(20), nullable=True, unique=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    date_join = db.Column(db.DateTime, default=datetime.now)
    # Do some password stuff!
    password_hash = db.Column(db.String(200),nullable=True)
    group_id = db.Column(db.String(4),db.ForeignKey('groups.id'), nullable=True)

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
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.now())

    user = db.relationship('Users', backref='messages')
    group = db.relationship('Groups', backref='messages1')

class Groups(db.Model):
    id = db.Column(db.String(4), primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.String(200), nullable=False)
    messages = db.Column(db.String(10000), db.ForeignKey('message.content'),nullable=True)

    messages = db.relationship('Message', backref='group2', lazy=True)

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
                    id = Users.query.filter_by(username=loginform.username.data).first()
                    session["name"] = loginform.username.data
                    session["id"] = id.id
                    return redirect(url_for('home',id=id.id))
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
        return redirect(url_for('home', id=id.id))
    return render_template('login.html', signupform=signupform, loginform=loginform)

@app.route("/chat/<int:user_id>")
def get_chat(user_id):
    messages = Message.query.filter_by(user_id=user_id).order_by(Message.timestamp).all()
    message_data = [{
        'content': message.content,
        'timestamp': message.timestamp.strftime('%I:%M %p'),
        'sender': 'me' if message.user_id == session.get('user_id') else 'them'
    } for message in messages]

    return jsonify({'messages': message_data})


@app.route("/", methods=["GET", "POST"])
@app.route("/home", methods=["GET", "POST"])
@app.route("/home/<int:id>", methods=["GET","POST"])
@login_required
def home(id=None):
    # Load all users and their last message from the database
    # users = Users.query.all()
    # chats1 = []

    # for user in users:
    #     last_message = Message.query.filter_by(user_id=user.id).order_by(Message.timestamp.desc()).first()
    #     chats1.append({
    #         'user': "Name",
    #         'last_message': "Message"
    #     })

    if id is None:
        print("Hello WOrld")
        # Handle the case where no ID is provided (e.g., use current user's ID)
        try:
            if id in session["id"]:
                id = current_user.id
            else:
                return redirect(url_for('login'))
        except:
            flash("You need to be logged in first!")
            return redirect(url_for('login'))


    
    groups = Groups.query.filter_by(user_id=id)
    messages = Groups.query.filter_by(user_id=id)
    
    return render_template("index.html",groups=groups,messages=messages,id=id)


if __name__ == '__main__':
    app.run(debug=True)