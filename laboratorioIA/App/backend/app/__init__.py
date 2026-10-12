from flask import Flask, render_template, send_from_directory
from flask_cors import CORS

from config import config_by_name


def create_app(config_name: str = "development") -> Flask:
    from pathlib import Path

    cfg = config_by_name.get(config_name, config_by_name["default"])

    app = Flask(
        __name__,
        template_folder=cfg.TEMPLATE_FOLDER,
        static_folder=cfg.STATIC_FOLDER,
        static_url_path="/static",
    )
    app.config.from_object(cfg)

    from app.extensions import db, jwt, limiter, migrate

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    limiter.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Security headers (SPEC-002)
    @app.after_request
    def set_security_headers(response):
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
            "font-src 'self' https://cdn.jsdelivr.net https://fonts.gstatic.com; "
            "img-src 'self' data:; "
            "connect-src 'self'"
        )
        if not app.debug:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

    # Blueprints API
    from app.api.academic import academic_bp
    from app.api.system_api import system_bp
    from app.api.users import users_bp
    from app.auth.routes import auth_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(academic_bp)
    app.register_blueprint(system_bp)

    # SPEC-029: asegurar columna user_question en LogIA (BD ya existentes)
    with app.app_context():
        try:
            from app.services.ai_agent_log import ensure_schema

            ensure_schema()
        except Exception:
            pass

    # Favicon en raíz (petición automática del navegador)
    @app.route("/favicon.ico")
    def favicon():
        return send_from_directory(
            app.static_folder,
            "img/favicon.ico",
            mimetype="image/x-icon",
        )

    # Frontend pages
    @app.route("/")
    def index():
        return render_template("login.html", system_name=app.config["SYSTEM_NAME"])

    @app.route("/app/")
    @app.route("/app/<path:page>")
    def spa(page="dashboard"):
        return render_template(
            "app.html",
            system_name=app.config["SYSTEM_NAME"],
            page=page,
        )

    @app.cli.command("init-db")
    def init_db():
        """Crea tablas y carga seeds."""
        import sys
        from pathlib import Path

        seeds_path = Path(__file__).resolve().parents[2] / "database" / "seeds"
        sys.path.insert(0, str(seeds_path))
        from seed_data import seed_all

        db.create_all()
        created = seed_all(app)
        print("Base de datos inicializada." if created else "Seeds ya existentes.")

    return app
