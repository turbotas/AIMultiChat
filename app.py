from flask import Flask, render_template, request, redirect, url_for, flash, session
from dotenv import load_dotenv
import os
import markdown

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI', 'sqlite:///aimultichat.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Import db and socketio from extensions and initialize them
from extensions import db, socketio, load_personalities
db.init_app(app)
socketio.init_app(app, async_mode='threading')

# Import models and blueprints
from models import AIAgent, Chat, ChatParticipant, ChatHistory, User
from auth import auth_bp
from auth.admin import admin_bp
from auth.admin_chat import admin_chat_bp

app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(admin_chat_bp)

import socketio_events

app.loaded_personalities = load_personalities()

@app.route('/')
def index():
    """
    The homepage.
    We'll sort app.loaded_personalities.values() by .name and pass them to index.html,
    AND load README.md -> HTML to display on the page as well.
    """
    readme_md = ""
    try:
        with open("README.md", "r", encoding="utf-8") as f:
            readme_md = f.read()
    except FileNotFoundError:
        readme_md = "# Welcome to AIMultiChat\n*(No README.md found.)*"

    readme_html = markdown.markdown(
        readme_md,
        extensions=["fenced_code", "codehilite"],
        extension_configs={
            "codehilite": {
                "css_class": "highlight",
                "linenums": False
            }
        }
    )

    personalities_list = sorted(
        app.loaded_personalities.values(),
        key=lambda p: p["name"].lower()
    )

    return render_template(
        'index.html',
        personalities=personalities_list,
        readme_html=readme_html
    )

@app.route('/chat/<string:join_code>')
def chat_room(join_code):
    chat = Chat.query.filter_by(join_code=join_code).first()
    if not chat:
        flash('Error: Chat room not found.', 'danger')
        return redirect(url_for('index'))

    numeric_chat_id = str(chat.id)
    messages = ChatHistory.query.filter_by(chat_id=numeric_chat_id).order_by(ChatHistory.id).all()
    sorted_personality_keys = sorted(app.loaded_personalities.keys(), key=str.lower)

    available_chats = []
    if session.get('is_admin'):
        available_chats = Chat.query.all()

    return render_template(
        'chat.html',
        chat_id=join_code,
        chat_title=chat.title,
        messages=messages,
        personalities=sorted_personality_keys,
        is_admin=session.get('is_admin', False),
        available_chats=available_chats
    )

# --------------------------------------------------------------------------
# NEW: run db.create_all() + default admin at import time (for Gunicorn, etc.)
# --------------------------------------------------------------------------
with app.app_context():
    db.create_all()
    if User.query.count() == 0:
        print("No users found. Creating default admin user.")
        admin = User(
            username='test@aimultichat.null',
            friendly_name='Temporary Administrator',
            is_admin=True
        )
        admin.set_password('F7svijfIin')
        db.session.add(admin)
        db.session.commit()
        print("Created default admin user!")
    else:
        print("User table already populated; skipping creation.")

if __name__ == '__main__':
    print("🚀 Starting in development mode (no SSL)")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
