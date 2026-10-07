"""Catálogo público de productos y servicios (no requiere sesión). Es la pantalla inicial."""
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user

from .extensions import db
from .models import Cotizacion, ProductoServicio, Resena, Servicio
from .services import CorreoDuplicado, crear_cotizacion, registrar_cliente, validar_datos_cliente

catalogo_bp = Blueprint("catalogo", __name__)


@catalogo_bp.route("/")
def index():
    q = request.args.get("q", "").strip()
    categoria = request.args.get("categoria", "").strip()

    consulta = db.select(ProductoServicio).order_by(ProductoServicio.nombre)
    if q:
        consulta = consulta.where(
            ProductoServicio.nombre.ilike(f"%{q}%") | ProductoServicio.descripcion.ilike(f"%{q}%")
        )
    if categoria:
        consulta = consulta.where(ProductoServicio.categoria == categoria)

    categorias = db.session.scalars(
        db.select(ProductoServicio.categoria)
        .where(ProductoServicio.categoria.is_not(None))
        .distinct()
        .order_by(ProductoServicio.categoria)
    ).all()

    return render_template(
        "catalogo/index.html",
        productos=db.session.scalars(consulta).all(),
        categorias=categorias,
        q=q,
        categoria=categoria,
    )


@catalogo_bp.route("/producto/<int:id_producto>")
def detalle(id_producto):
    producto = db.get_or_404(ProductoServicio, id_producto)
    # Una reseña llega al producto a través de: Reseña -> Servicio -> Cotización -> Producto
    resenas = db.session.scalars(
        db.select(Resena)
        .join(Servicio, Resena.id_servicio == Servicio.id_servicio)
        .join(Cotizacion, Servicio.id_cotizacion == Cotizacion.id_cotizacion)
        .where(Cotizacion.id_producto == id_producto)
    ).all()
    promedio = sum(r.calificacion for r in resenas) / len(resenas) if resenas else None
    return render_template("catalogo/detalle.html", producto=producto, resenas=resenas,
                           promedio=promedio)


@catalogo_bp.route("/producto/<int:id_producto>/cotizar", methods=["GET", "POST"])
def cotizar(id_producto):
    """Un visitante deja sus datos y se le crea la cuenta; un cliente con sesión solo confirma."""
    producto = db.get_or_404(ProductoServicio, id_producto)
    if current_user.is_authenticated and (not current_user.tiene_rol("cliente")
                                          or current_user.cliente is None):
        abort(403)

    if request.method == "POST":
        if current_user.is_authenticated:
            crear_cotizacion(current_user.cliente, producto)
            flash("Cotización registrada. Aquí puedes darle seguimiento.", "success")
            return redirect(url_for("cliente.panel"))

        nombre = request.form.get("nombre", "").strip()
        correo = request.form.get("correo", "").strip().lower()
        telefono = request.form.get("telefono", "").strip()
        error = validar_datos_cliente(nombre, correo, telefono)
        if error:
            flash(error, "danger")
        else:
            try:
                usuario = registrar_cliente(nombre, correo, telefono)
            except CorreoDuplicado:
                flash("Ese correo ya tiene una cuenta. Inicia sesión para solicitar tu cotización.",
                      "warning")
                return redirect(url_for("auth.login"))
            crear_cotizacion(usuario.cliente, producto)
            flash("Cotización registrada y cuenta creada. Inicia sesión con tu correo y tu "
                  "teléfono como contraseña para darle seguimiento.", "success")
            return redirect(url_for("auth.login"))

    return render_template("catalogo/cotizar.html", producto=producto)
