from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from extensions import db
from models import Chat
import uuid  # For generating unique join codes

admin_chat_bp = Blueprint('admin_chat', __name__, url_prefix='/admin/chats')

# Admin-only access decorator
def admin_required(f):
    def wrapper(*args, **kwargs):
        if not session.get('is_admin'):
            flash('Access denied. Admin only.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__  # Flask expects function names
    return wrapper

# List chats
@admin_chat_bp.route('/')
@admin_required
def chat_list():
    chats = Chat.query.all()
    return render_template('admin/chat_list.html', chats=chats)

# Add or Edit a chat
@admin_chat_bp.route('/edit/<string:join_code>', methods=['GET', 'POST'])
@admin_chat_bp.route('/add', methods=['GET', 'POST'])
@admin_required
def chat_form(join_code=None):
    chat = Chat.query.filter_by(join_code=join_code).first() if join_code else None

    if request.method == 'POST':
        title = request.form['title']
        allow_anonymous = 'allow_anonymous' in request.form

        if chat:  # Editing
            chat.title = title
            chat.allow_anonymous = allow_anonymous
        else:  # Adding
            join_code = str(uuid.uuid4())  # 36-character UUID
            new_chat = Chat(title=title, allow_anonymous=allow_anonymous, join_code=join_code, owner_user_id=session['user_id'])
            db.session.add(new_chat)

        db.session.commit()
        flash('Chat saved successfully.', 'success')
        return redirect(url_for('admin_chat.chat_list'))

    return render_template('admin/chat_edit.html', chat=chat)

# Delete chat
@admin_chat_bp.route('/delete/<string:join_code>', methods=['POST'])
@admin_required
def chat_delete(join_code):
    chat = Chat.query.filter_by(join_code=join_code).first()
    if chat:
        db.session.delete(chat)
        db.session.commit()
        flash('Chat deleted successfully.', 'success')
    else:
        flash('Chat not found.', 'danger')
    return redirect(url_for('admin_chat.chat_list'))

