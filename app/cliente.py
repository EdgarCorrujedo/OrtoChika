"""Panel del cliente: historial de cotizaciones y servicios, y calificación de servicios terminados."""
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user

from .extensions import db, login_manager
from .models import Cotizacion, Resena

cliente_bp = Blueprint("cliente", __name__, url_prefix="/cliente")

PESTANAS = {"cotizaciones": "Cotizaciones", "proceso": "En proceso", "terminados": "Terminados"}


@cliente_bp.before_request
def solo_clientes():
    if not current_user.is_authenticated:
        return login_manager.unauthorized()
    if not current_user.tiene_rol("cliente") or current_user.cliente is None:
        abort(403)


def _cotizacion_propia_o_404(id_cotizacion):
    cotizacion = db.get_or_404(Cotizacion, id_cotizacion)
    if cotizacion.id_cliente != current_user.cliente.id_cliente:
        abort(404)  # no revelar que existe una cotización de otro cliente
    return cotizacion


def _mi_resena(servicio):
    """Reseña que el cliente en sesión ya dejó sobre el servicio, o None."""
    id_cliente = current_user.cliente.id_cliente
    return next((r for r in servicio.resenas if r.id_cliente == id_cliente), None)


@cliente_bp.route("/")
def panel():
    pestana = request.args.get("tab", "cotizaciones")
    if pestana not in PESTANAS:
        pestana = "cotizaciones"

    todas = db.session.scalars(
        db.select(Cotizacion)
        .where(Cotizacion.id_cliente == current_user.cliente.id_cliente)
        .order_by(Cotizacion.fecha.desc())
    ).all()
    grupos = {
        "cotizaciones": [c for c in todas if c.servicio is None],
        "proceso": [c for c in todas if c.servicio and c.servicio.fecha_cierre is None],
        "terminados": [c for c in todas if c.servicio and c.servicio.fecha_cierre is not None],
    }
    calificados = {r.id_servicio for r in current_user.cliente.resenas}
    return render_template("cliente/panel.html", pestanas=PESTANAS, pestana=pestana,
                           grupos=grupos, filas=grupos[pestana], calificados=calificados)


@cliente_bp.route("/cotizacion/<int:id_cotizacion>")
def detalle(id_cotizacion):
    cotizacion = _cotizacion_propia_o_404(id_cotizacion)
    resena = _mi_resena(cotizacion.servicio) if cotizacion.servicio else None
    return render_template("cliente/detalle.html", cotizacion=cotizacion, resena=resena)


@cliente_bp.route("/cotizacion/<int:id_cotizacion>/calificar", methods=["GET", "POST"])
def calificar(id_cotizacion):
    cotizacion = _cotizacion_propia_o_404(id_cotizacion)
    servicio = cotizacion.servicio
    if servicio is None or servicio.fecha_cierre is None:
        abort(404)  # solo se califica un servicio terminado
    if _mi_resena(servicio):
        flash("Ya calificaste este servicio.", "info")
        return redirect(url_for("cliente.detalle", id_cotizacion=id_cotizacion))

    if request.method == "POST":
        try:
            calificacion = int(request.form.get("calificacion", ""))
        except ValueError:
            calificacion = 0
        comentario = request.form.get("comentario", "").strip()

        if calificacion not in range(1, 6):
            flash("Elige una calificación de 1 a 5 estrellas.", "danger")
        elif len(comentario) > 1000:
            flash("El comentario puede tener máximo 1000 caracteres.", "danger")
        else:
            db.session.add(Resena(id_cliente=current_user.cliente.id_cliente,
                                  id_servicio=servicio.id_servicio,
                                  calificacion=calificacion, comentario=comentario or None))
            db.session.commit()
            flash("¡Gracias por tu reseña!", "success")
            return redirect(url_for("cliente.panel", tab="terminados"))

    return render_template("cliente/calificar.html", cotizacion=cotizacion)
