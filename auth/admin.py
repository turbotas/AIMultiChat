from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from extensions import db
from models import User
from werkzeug.security import generate_password_hash

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Admin-only access decorator
def admin_required(f):
    def wrapper(*args, **kwargs):
        if not session.get('is_admin'):
            flash('Access denied. Admin only.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__  # Flask expects function names
    return wrapper

# List users
@admin_bp.route('/users')
@admin_required
def user_list():
    users = User.query.all()
    return render_template('admin/user_list.html', users=users)

# Add or Edit user
@admin_bp.route('/user_edit/<int:user_id>', methods=['GET', 'POST'])
@admin_bp.route('/user_edit', methods=['GET', 'POST'])  # Corrected for "Add User"
@admin_required
def user_edit(user_id=None):
    user = User.query.get(user_id) if user_id else None

    if request.method == 'POST':
        email = request.form['email']
        password = request.form.get('password')
        friendly_name = request.form['friendly_name']
        is_admin = 'is_admin' in request.form

        if user:  # Editing
            user.username = email
            user.friendly_name = friendly_name
            user.is_admin = is_admin
            if password:  # Only update the password if provided
                user.password_hash = generate_password_hash(password)
        else:  # Adding new user
            if User.query.filter_by(username=email).first():
                flash('Email is already registered.', 'danger')
                return redirect(url_for('admin.user_list'))

            hashed_password = generate_password_hash(password)
            new_user = User(username=email, password_hash=hashed_password, friendly_name=friendly_name, is_admin=is_admin)
            db.session.add(new_user)

        db.session.commit()
        flash('User saved successfully.', 'success')
        return redirect(url_for('admin.user_list'))

    return render_template('admin/user_edit.html', user=user)

# Delete user
@admin_bp.route('/user_delete/<int:user_id>', methods=['POST'])
@admin_required
def user_delete(user_id):
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        flash('User deleted successfully.', 'success')
    else:
        flash('User not found.', 'danger')
    return redirect(url_for('admin.user_list'))
