from flask import Flask, render_template, request, redirect, url_for, flash, session  # <-- import session
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI', 'sqlite:///aimultichat.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Import db and socketio from extensions and initialize them
from extensions import db, socketio, load_personalities
db.init_app(app)
socketio.init_app(app, async_mode='threading')  # Return to default async mode

# Import models and blueprints
from models import HumanUser, AIAgent, Chat, ChatParticipant, ChatHistory, User
from auth import auth_bp
from auth.admin import admin_bp
from auth.admin_chat import admin_chat_bp

# Register Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(admin_chat_bp)

# Import the event handlers AFTER socketio is initialized.
import socketio_events

# 1) Load personalities exactly once, store in app.loaded_personalities
app.loaded_personalities = load_personalities()

@app.route('/')
def index():
    """
    The homepage.
    We'll sort app.loaded_personalities.values() by .name and pass them to index.html
    """
    personalities_list = sorted(
        app.loaded_personalities.values(),
        key=lambda p: p["name"].lower()
    )

    return render_template('index.html', personalities=personalities_list)

@app.route('/chat/<string:join_code>')
def chat_room(join_code):
    """
    Shows the chat page for a specific chat,
    using the alpha-sorted list of personality keys for the left column.
    """
    chat = Chat.query.filter_by(join_code=join_code).first()
    if not chat:
        flash('Error: Chat room not found.', 'danger')
        return redirect(url_for('index'))

    numeric_chat_id = str(chat.id)

    # Retrieve messages from DB
    messages = ChatHistory.query.filter_by(chat_id=numeric_chat_id).order_by(ChatHistory.id).all()

    # Instead of LOADED_PERSONALITIES, we do:
    sorted_personality_keys = sorted(app.loaded_personalities.keys(), key=str.lower)

    # If the user is admin, build up a list of all chats or some subset
    available_chats = []
    if session.get('is_admin'):
        # For example, show all
        available_chats = Chat.query.all()

    return render_template(
        'chat.html',
        chat_id=join_code,  # Pass the join_code for the user
        messages=messages,
        personalities=sorted_personality_keys,
        is_admin=session.get('is_admin', False),
        available_chats=available_chats  # pass it here
    )

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Ensure tables are created

        # Auto-create Admin account if none exists
        if User.query.count() == 0:
            admin = User(
                username='admin@example.com',
                friendly_name='Admin',
                is_admin=True
            )
            admin.set_password('admin123')  # Known password for initial setup
            db.session.add(admin)
            db.session.commit()

    print("🚀 Starting in development mode (no SSL)")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
