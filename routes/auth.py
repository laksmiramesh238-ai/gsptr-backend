from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import UserMixin, login_user, logout_user, login_required

auth = Blueprint('auth', __name__)

# Hardcoded admin credentials
ADMIN_EMAIL = 'admin@admin.com'
ADMIN_PASSWORD = 'admin123'


class AdminUser(UserMixin):
    def get_id(self):
        return 'admin'


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
            login_user(AdminUser())
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid email or password.', 'error')

    return render_template('auth/login.html')


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
