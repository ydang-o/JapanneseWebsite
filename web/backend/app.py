from flask import Flask
from flask_cors import CORS
from .config import AppConfig
from .extensions import db, redis_client
from .db_init import ensure_database_initialized


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(AppConfig)

    # Initialize extensions
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    db.init_app(app)

    # Auto DB init
    with app.app_context():
        try:
            ensure_database_initialized(app)
        except Exception:
            # Do not crash app startup; errors will surface via endpoints
            pass

    # Lazily initialize Redis to avoid failure at import time
    @app.before_request
    def _ensure_redis_connected():
        if not hasattr(app, "redis"):
            app.redis = redis_client(app.config)

    # Register blueprints
    from .login import login_bp
    from .register import register_bp
    from .user import user_bp
    from .home import home_bp
    from .Administrator import admin_bp

    app.register_blueprint(login_bp, url_prefix="/api/auth")
    app.register_blueprint(register_bp, url_prefix="/api/auth")
    app.register_blueprint(user_bp, url_prefix="/api/user")
    app.register_blueprint(home_bp, url_prefix="/api/home")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")

    @app.get("/")
    def root():
        return "Backend OK. Visit frontend at http://127.0.0.1:5173"

    @app.get("/api/health")
    def health_check():
        return {"status": "ok"}

    return app


if __name__ == "__main__":
    application = create_app()
    application.run(host="0.0.0.0", port=5000, debug=True) 