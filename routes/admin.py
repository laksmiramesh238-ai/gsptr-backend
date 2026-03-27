from flask import Blueprint, render_template
from flask_login import login_required

admin = Blueprint('admin', __name__)


@admin.route('/')
@admin.route('/dashboard')
@login_required
def dashboard():
    return render_template('admin/dashboard.html')
