"""Factoría de la aplicación OrtoChika Web."""
from flask import Flask

from config import Config

from .extensions import csrf, db, login_manager


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    from . import models  # noqa: F401  (registra modelos y el user_loader)
    from .admin import admin_bp
    from .auth import auth_bp
    from .catalogo import catalogo_bp
    from .cliente import cliente_bp
    from .cli import registrar_comandos
    from .routes import main_bp

    app.register_blueprint(catalogo_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(cliente_bp)
    app.register_blueprint(main_bp)
    registrar_comandos(app)
    return app
