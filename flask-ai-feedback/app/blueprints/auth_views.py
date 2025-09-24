import traceback # 新增导入
from flask import Blueprint, render_template, redirect, url_for, flash, session, current_app
from flask_login import login_user, logout_user, login_required
from .. import oauth
from ..models import User

# 创建一个名为 'auth' 的蓝图
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login')
def login():
    redirect_uri = url_for('auth.authorize', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

@auth_bp.route('/auth')
def authorize():
    try:
        token = oauth.google.authorize_access_token()
        user_info = oauth.google.get('userinfo').json()
        user_email = user_info.get('email')

        if user_email in current_app.config['AUTHORIZED_EMAILS']:
            user = User(user_id=user_email)
            login_user(user)
            session['profile'] = user_info
            return redirect(url_for('auth.dashboard'))
        else:
            flash('Sorry, your account is not authorized to access this dashboard.')
            return redirect(url_for('auth.unauthorized'))
    except Exception as e:
        print(f"An error occurred during authentication: {e}")
        flash('An error occurred during authentication. Please try again.')
        return redirect(url_for('auth.unauthorized'))



@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop('profile', None)
    return redirect("https://accounts.google.com/logout")

@auth_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@auth_bp.route('/create')
@login_required
def create_page():
    return render_template('creator.html')
    
@auth_bp.route('/unauthorized')
def unauthorized():
    return "<h1>Access Denied</h1><p>Your account is not authorized to view this page.</p>", 403

@auth_bp.route('/edit-problems')
@login_required
def edit_problems_page():
    """渲染问题编辑页面"""
    return render_template('edit_problems.html')
