from flask import Flask, render_template, request, redirect, url_for
from dotenv import load_dotenv
from extensions import load_personalities
import os, uuid  # Remove SSL, waitress, gunicorn imports

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI', 'sqlite:///aimultichat.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Import db and socketio from extensions and initialize them
from extensions import db, socketio
db.init_app(app)
socketio.init_app(app, async_mode='threading')  # Return to default async mode

# Import the event handlers AFTER socketio is initialized.
import socketio_events

from models import HumanUser, AIAgent, Chat, ChatParticipant, ChatHistory

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create_chat', methods=['POST'])
def create_chat():
    join_code = uuid.uuid4().hex[:8]
    owner_user_id = 1  # Placeholder for now
    new_chat = Chat(owner_user_id=owner_user_id, join_code=join_code)
    db.session.add(new_chat)
    db.session.commit()
    return redirect(url_for('chat_room', chat_id=new_chat.id))

@app.route('/chat/<int:chat_id>')
def chat_room(chat_id):
    personalities = load_personalities().keys()  # Load personalities
    messages = ChatHistory.query.filter_by(chat_id=str(chat_id)).order_by(ChatHistory.id).all()
    return render_template('chat.html', chat_id=chat_id, messages=messages, personalities=personalities)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Ensure tables are created
    print("🚀 Starting in development mode (no SSL)")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
