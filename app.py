import os
from flask import Flask
from flask_login import LoginManager
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

def create_app():
    app = Flask(__name__)
    app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

    # Trust X-Forwarded-Proto from Render's proxy so OAuth redirect uses https://
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    # Initialize database
    from database.db import init_db
    init_db()

    # Flask-Login configuration
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        from models.user import User
        return User.get(int(user_id))

    # Register blueprints
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.mentor import mentor_bp
    from routes.roadmap import roadmap_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(mentor_bp, url_prefix='/dashboard')
    app.register_blueprint(roadmap_bp, url_prefix='/dashboard')

    # Redirect root to dashboard
    @app.route('/')
    def root():
        from flask import redirect, url_for
        return redirect(url_for('dashboard.index'))

    return app


# Single module-level app instance for gunicorn
app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
