"""Rutas generales. Pendientes: paneles de vendedor y analista."""
from flask import Blueprint, current_app, jsonify, redirect, render_template, url_for
from flask_login import current_user, login_required
from sqlalchemy import text

from .extensions import db

main_bp = Blueprint("main", __name__)


@main_bp.route("/dashboard")
@login_required
def dashboard():
    if current_user.tiene_rol("administrador"):
        return redirect(url_for("admin.resumen"))
    if current_user.tiene_rol("cliente"):
        return redirect(url_for("cliente.panel"))
    return render_template("dashboard.html")


@main_bp.route("/health/db")
def health_db():
    """Verifica la conexión con MySQL: abre http://127.0.0.1:5000/health/db"""
    try:
        db.session.execute(text("SELECT 1"))
        return jsonify(status="ok")
    except Exception:
        current_app.logger.exception("Fallo la conexión a la base de datos")
        return jsonify(status="error"), 500
