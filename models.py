from datetime import datetime
from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash

class HumanUser(db.Model):
    __tablename__ = 'human_user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128))  # Store hashed passwords

class AIAgent(db.Model):
    __tablename__ = 'ai_agent'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    model_parameters = db.Column(db.String(256))  # Could be a JSON string with model details

class Chat(db.Model):
    __tablename__ = 'chat'
    id = db.Column(db.Integer, primary_key=True)
    owner_user_id = db.Column(db.Integer, db.ForeignKey('human_user.id'))
    join_code = db.Column(db.String(36), unique=True, nullable=False)  # Extended for UUID-like strength
    title = db.Column(db.String(100), nullable=False)
    allow_anonymous = db.Column(db.Boolean, default=False)

class ChatParticipant(db.Model):
    __tablename__ = 'chat_participant'
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey('chat.id'))
    user_id = db.Column(db.Integer)  # This could reference either a HumanUser or an AIAgent

class ChatHistory(db.Model):
    __tablename__ = 'chat_history'
    id = db.Column(db.Integer, primary_key=True)
    room_message_id = db.Column(db.Integer, default=0)  # Message number within the room
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    chat_id = db.Column(db.String, db.ForeignKey('chat.id'))  # storing as string for consistency
    sender_id = db.Column(db.Integer)  # placeholder for sender ID
    sender_name = db.Column(db.String(64))  # new field to store the sender’s username
    message = db.Column(db.Text)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    friendly_name = db.Column(db.String(100), nullable=True)
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
