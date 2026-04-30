from flask import Flask, redirect, url_for
from flask_login import LoginManager
from mongoengine import connect
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')

# MongoDB
connect(
    db=os.getenv('DB_NAME', 'course_platform'),
    host=os.getenv('MONGO_URI')
)

login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'

# Blueprints
from flask_cors import CORS
from routes.auth import auth
from routes.admin import admin
from routes.courses import courses_bp
from routes.s3_routes import s3_bp
from routes.student_auth import student_auth
from routes.student_courses import student_courses_bp
from routes.enrollment import enrollment_bp
from routes.exam_admin import exam_admin_bp
from routes.admin_enrollment import admin_enroll_bp
from routes.student_exams import student_exams_bp
from routes.exam_enrollment import exam_enrollment_bp
from routes.student_assessments import student_assessments_bp
from utils.cdn import cdn_url

CORS(app, resources={r'/api/*': {'origins': '*'}})
app.jinja_env.globals['cdn_url'] = cdn_url

app.register_blueprint(auth, url_prefix='/auth')
app.register_blueprint(admin, url_prefix='/admin')
app.register_blueprint(courses_bp, url_prefix='/admin/courses')
app.register_blueprint(s3_bp, url_prefix='/s3')
app.register_blueprint(student_auth, url_prefix='/api/auth')
app.register_blueprint(student_courses_bp, url_prefix='/api/courses')
app.register_blueprint(enrollment_bp, url_prefix='/api/enroll')
app.register_blueprint(exam_admin_bp, url_prefix='/admin/exams')
app.register_blueprint(admin_enroll_bp, url_prefix='/admin/enrollments')
app.register_blueprint(student_exams_bp, url_prefix='/api/exams')
app.register_blueprint(exam_enrollment_bp, url_prefix='/api/exam-enroll')
app.register_blueprint(student_assessments_bp, url_prefix='/api/assessments')

from routes.auth import AdminUser

@login_manager.user_loader
def load_user(user_id):
    if user_id == 'admin':
        return AdminUser()
    return None

@app.route('/')
def index():
    return redirect(url_for('auth.login'))

if __name__ == '__main__':
    debug = os.getenv('FLASK_DEBUG', '0').lower() in ('1', 'true')
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=debug)
