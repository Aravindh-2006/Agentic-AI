import os
import requests
from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models.user import User

auth_bp = Blueprint('auth', __name__)

def get_google_provider_cfg():
    """
    Retrieves Google's OAuth 2.0 configuration endpoints.
    """
    try:
        response = requests.get("https://accounts.google.com/.well-known/openid-configuration", timeout=5)
        return response.json()
    except Exception as e:
        print(f"Error fetching Google OpenID config: {e}")
        return None


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
        
    google_configured = bool(os.getenv("GOOGLE_CLIENT_ID") and os.getenv("GOOGLE_CLIENT_SECRET"))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        if not email or not password:
            flash('Please fill in all fields.', 'danger')
            return render_template('login.html', google_configured=google_configured)
            
        user = User.get_by_email(email)
        if user and user.password_hash and check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard.index'))
        else:
            flash('Invalid email or password.', 'danger')
            
    return render_template('login.html', google_configured=google_configured)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
        
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        if not username or not email or not password:
            flash('Please fill in all fields.', 'danger')
            return render_template('register.html')
            
        # Check if email or username exists
        if User.get_by_email(email):
            flash('Email address already registered.', 'danger')
            return render_template('register.html')
            
        # Simple username conflict check
        from database.db import get_db
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        existing_username = cursor.fetchone()
        conn.close()
        
        if existing_username:
            flash('Username already taken.', 'danger')
            return render_template('register.html')
            
        try:
            pw_hash = generate_password_hash(password)
            User.create(username=username, email=email, password_hash=pw_hash)
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            flash(f'An error occurred during registration: {e}', 'danger')
            
    return render_template('register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('auth.login'))


@auth_bp.route('/login/google')
def google_login():
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        flash("Google OAuth is not configured on this server.", "warning")
        return redirect(url_for('auth.login'))
        
    google_provider_cfg = get_google_provider_cfg()
    if not google_provider_cfg:
        flash("Failed to reach Google OAuth services. Try again later.", "danger")
        return redirect(url_for('auth.login'))
        
    authorization_endpoint = google_provider_cfg.get("authorization_endpoint")
    
    # Dynamic redirect URI
    # Build standard callback URL pointing to oauth endpoint
    base_url = request.url_root.rstrip('/')
    redirect_uri = f"{base_url}{url_for('auth.google_callback')}"
    
    # Store dynamic state/callback in session for validation
    session['oauth_state'] = os.urandom(8).hex()
    
    # Prepare URL arguments
    auth_url = (
        f"{authorization_endpoint}?"
        f"response_type=code&"
        f"client_id={client_id}&"
        f"redirect_uri={redirect_uri}&"
        f"scope=openid%20email%20profile&"
        f"state={session['oauth_state']}"
    )
    
    return redirect(auth_url)


@auth_bp.route('/login/google/callback')
def google_callback():
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    
    # Retrieve OAuth params
    code = request.args.get("code")
    state = request.args.get("state")
    
    if not code:
        flash("Authorization failed: no code provided by Google.", "danger")
        return redirect(url_for('auth.login'))
        
    # Validate State
    saved_state = session.pop('oauth_state', None)
    if not state or state != saved_state:
        flash("Session state mismatch error. Login aborted for security.", "danger")
        return redirect(url_for('auth.login'))
        
    google_provider_cfg = get_google_provider_cfg()
    if not google_provider_cfg:
        flash("Could not obtain Google configuration endpoint.", "danger")
        return redirect(url_for('auth.login'))
        
    token_endpoint = google_provider_cfg.get("token_endpoint")
    userinfo_endpoint = google_provider_cfg.get("userinfo_endpoint")
    
    base_url = request.url_root.rstrip('/')
    redirect_uri = f"{base_url}{url_for('auth.google_callback')}"
    
    # Exchange authorization code for tokens
    try:
        token_response = requests.post(
            token_endpoint,
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri
            },
            timeout=10
        )
        token_data = token_response.json()
    except Exception as e:
        flash(f"Failed to connect to Google Token services: {e}", "danger")
        return redirect(url_for('auth.login'))
        
    access_token = token_data.get("access_token")
    if not access_token:
        flash("Google failed to grant an access token.", "danger")
        return redirect(url_for('auth.login'))
        
    # Get user profile information
    try:
        userinfo_response = requests.get(
            userinfo_endpoint,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        user_info = userinfo_response.json()
    except Exception as e:
        flash(f"Failed to fetch profile information from Google: {e}", "danger")
        return redirect(url_for('auth.login'))
        
    # Check openid claims
    if not user_info.get("email_verified"):
        flash("User email not verified by Google.", "danger")
        return redirect(url_for('auth.login'))
        
    google_id = user_info.get("sub")
    email = user_info.get("email")
    given_name = user_info.get("given_name")
    family_name = user_info.get("family_name")
    
    # Fallback username construction
    username = user_info.get("name")
    if not username:
        username = f"{given_name}_{family_name}" if given_name and family_name else email.split('@')[0]
        
    # Query if user exists by Google ID
    user = User.get_by_google_id(google_id)
    if not user:
        # Check if user exists with the same email
        user = User.get_by_email(email)
        if user:
            # Connect Google ID to existing user email
            from database.db import get_db
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET google_id = ? WHERE id = ?", (google_id, user.id))
            conn.commit()
            conn.close()
            user = User.get(user.id)
        else:
            # Create a new user
            try:
                user = User.create(username=username, email=email, google_id=google_id)
            except Exception as e:
                # If username conflicts, make it unique
                import random
                unique_username = f"{username}_{random.randint(1000, 9999)}"
                user = User.create(username=unique_username, email=email, google_id=google_id)
                
    login_user(user)
    flash("Successfully authenticated with Google OAuth!", "success")
    return redirect(url_for('dashboard.index'))
