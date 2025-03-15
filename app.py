from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv
from extensions import load_personalities
import os

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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat/<string:join_code>')
def chat_room(join_code):
    # Lookup the chat via join_code
    chat = Chat.query.filter_by(join_code=join_code).first()
    if not chat:
        flash('Error: Chat room not found.', 'danger')
        return redirect(url_for('index'))

    # Convert numeric chat.id -> string to store in ChatHistory
    numeric_chat_id = str(chat.id)

    # Retrieve messages from DB via numeric ID
    messages = ChatHistory.query.filter_by(chat_id=numeric_chat_id).order_by(ChatHistory.id).all()

    # Provide chat_id to the template as the join_code (used by the client & socket events)
    # Also load the personalities so the dropdown isn't empty
    personalities_list = list(load_personalities().keys())

    return render_template(
        'chat.html',
        chat_id=join_code,  # Pass the join_code for the user
        messages=messages,
        personalities=personalities_list
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
