"""Autenticación: inicio de sesión, registro de clientes, cambio de contraseña y cierre de sesión."""
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from .extensions import db
from .models import Usuario
from .services import CorreoDuplicado, registrar_cliente, validar_datos_cliente

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        correo = request.form.get("correo", "").strip().lower()
        contrasena = request.form.get("contrasena", "")

        usuario = db.session.scalar(db.select(Usuario).filter_by(correo=correo))
        if usuario and usuario.check_password(contrasena):
            login_user(usuario)
            return redirect(url_for("main.dashboard"))
        flash("Correo o contraseña incorrectos.", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/registro", methods=["GET", "POST"])
def registro():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        correo = request.form.get("correo", "").strip().lower()
        telefono = request.form.get("telefono", "").strip()

        error = validar_datos_cliente(nombre, correo, telefono)
        if error:
            flash(error, "danger")
        else:
            try:
                registrar_cliente(nombre, correo, telefono)
            except CorreoDuplicado:
                flash("Este correo ya está registrado. Intenta iniciar sesión.", "warning")
            else:
                flash("Registro exitoso. Inicia sesión con tu correo y tu teléfono como contraseña.",
                      "success")
                return redirect(url_for("auth.login"))

    return render_template("auth/registro.html")


@auth_bp.route("/cuenta/contrasena", methods=["GET", "POST"])
@login_required
def cambiar_contrasena():
    if request.method == "POST":
        actual = request.form.get("actual", "")
        nueva = request.form.get("nueva", "")
        confirmar = request.form.get("confirmar", "")

        if not current_user.check_password(actual):
            flash("La contraseña actual no es correcta.", "danger")
        elif not 8 <= len(nueva) <= 128:
            flash("La nueva contraseña debe tener entre 8 y 128 caracteres.", "danger")
        elif nueva != confirmar:
            flash("La confirmación no coincide con la nueva contraseña.", "danger")
        elif nueva == actual:
            flash("La nueva contraseña debe ser distinta de la actual.", "danger")
        else:
            current_user.set_password(nueva)
            db.session.commit()
            flash("Contraseña actualizada.", "success")
            return redirect(url_for("main.dashboard"))

    return render_template("auth/cambiar_contrasena.html")


@auth_bp.post("/logout")
@login_required
def logout():
    logout_user()
    flash("Has cerrado sesión.", "info")
    return redirect(url_for("auth.login"))
