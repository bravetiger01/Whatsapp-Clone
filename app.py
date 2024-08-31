from flask import Flask,redirect,render_template,url_for,session
import os
from flask_sqlalchemy import SQLAlchemy
from flask import jsonify


app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecretkey'

UPLOAD_FOLDER = 'uploads'

# SQLite Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat.db'
# Initialize the database
db = SQLAlchemy(app)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'txt', 'docx', 'xlsx'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    avatar = db.Column(db.String(100), nullable=True)  # Store avatar filename

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.now())

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
def home():
    # Load all users and their last message from the database
    users = User.query.all()
    chats = []

    for user in users:
        last_message = Message.query.filter_by(user_id=user.id).order_by(Message.timestamp.desc()).first()
        chats.append({
            'user': user,
            'last_message': last_message
        })
    
    return render_template("index.html", chats=chats)

if __name__ == '__main__':
    app.run(debug=True)