"""Panel de administración: solo accesible con rol administrador."""
import os
import uuid
from decimal import Decimal, InvalidOperation

from flask import (Blueprint, abort, current_app, flash, redirect, render_template, request,
                   url_for)
from flask_login import current_user

from .extensions import db, login_manager
from .models import Cliente, Cotizacion, Especialista, ProductoServicio, Servicio, Usuario

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

EXTENSIONES_IMAGEN = {"png", "jpg", "jpeg", "webp"}
PRECIO_MAXIMO = Decimal("99999999.99")  # límite de la columna NUMERIC(10, 2)


@admin_bp.before_request
def solo_administradores():
    if not current_user.is_authenticated:
        return login_manager.unauthorized()
    if not current_user.tiene_rol("administrador"):
        abort(403)


def _contar(modelo, condicion=None):
    consulta = db.select(db.func.count()).select_from(modelo)
    if condicion is not None:
        consulta = consulta.where(condicion)
    return db.session.scalar(consulta)


@admin_bp.route("/")
def resumen():
    # Un servicio existe desde que el cliente contrata; está terminado cuando tiene fecha de cierre.
    contratados = _contar(Servicio)
    terminados = _contar(Servicio, Servicio.fecha_cierre.is_not(None))
    indicadores = {
        "Cotizados": _contar(Cotizacion),
        "Contratados": contratados,
        "En proceso": contratados - terminados,
        "Terminados": terminados,
    }
    totales = {
        "Clientes": _contar(Cliente),
        "Especialistas": _contar(Especialista),
        "Productos y servicios": _contar(ProductoServicio),
    }
    return render_template("admin/resumen.html", indicadores=indicadores, totales=totales)


# ---------------------------------------------------------------- Catálogo (alta, edición, baja)

def _categorias():
    return db.session.scalars(
        db.select(ProductoServicio.categoria)
        .where(ProductoServicio.categoria.is_not(None))
        .distinct()
        .order_by(ProductoServicio.categoria)
    ).all()


def _leer_formulario():
    """Valida el formulario del producto. Devuelve (datos, None) o (None, mensaje_de_error)."""
    nombre = request.form.get("nombre", "").strip()
    categoria = request.form.get("categoria", "").strip()
    descripcion = request.form.get("descripcion", "").strip()
    precio_texto = request.form.get("precio_aprox", "").strip().replace(",", "")

    if not nombre or len(nombre) > 120:
        return None, "El nombre es obligatorio (máximo 120 caracteres)."
    if not categoria or len(categoria) > 60:
        return None, "La categoría es obligatoria (máximo 60 caracteres)."

    precio = None
    if precio_texto:
        try:
            precio = Decimal(precio_texto)
        except InvalidOperation:
            return None, "El precio debe ser un número."
        if not precio.is_finite() or precio < 0 or precio > PRECIO_MAXIMO:
            return None, "El precio debe estar entre 0 y 99,999,999.99."
        precio = precio.quantize(Decimal("0.01"))

    return {"nombre": nombre, "categoria": categoria,
            "descripcion": descripcion or None, "precio_aprox": precio}, None


def _guardar_imagen(archivo):
    """Guarda la imagen subida en static/img. Devuelve su nombre, None si no se subió ninguna,
    o lanza ValueError si el formato no es válido."""
    if archivo is None or not archivo.filename:
        return None
    extension = archivo.filename.rsplit(".", 1)[-1].lower() if "." in archivo.filename else ""
    if extension not in EXTENSIONES_IMAGEN:
        raise ValueError("La imagen debe ser PNG, JPG o WEBP.")
    carpeta = os.path.join(current_app.static_folder, "img")
    os.makedirs(carpeta, exist_ok=True)
    nombre = f"{uuid.uuid4().hex}.{extension}"
    archivo.save(os.path.join(carpeta, nombre))
    return nombre


def _borrar_imagen(nombre):
    if nombre:
        ruta = os.path.join(current_app.static_folder, "img", os.path.basename(nombre))
        if os.path.isfile(ruta):
            os.remove(ruta)


def _valores_producto(producto):
    """Valores iniciales del formulario al editar."""
    return {
        "nombre": producto.nombre,
        "categoria": producto.categoria or "",
        "descripcion": producto.descripcion or "",
        "precio_aprox": "" if producto.precio_aprox is None else f"{producto.precio_aprox:.2f}",
    }


@admin_bp.route("/catalogo")
def catalogo():
    productos = db.session.scalars(
        db.select(ProductoServicio).order_by(ProductoServicio.categoria, ProductoServicio.nombre)
    ).all()
    return render_template("admin/catalogo.html", productos=productos)


@admin_bp.route("/catalogo/nuevo", methods=["GET", "POST"])
def producto_nuevo():
    if request.method == "POST":
        imagen = None
        datos, error = _leer_formulario()
        if not error:
            try:
                imagen = _guardar_imagen(request.files.get("imagen"))
            except ValueError as e:
                error = str(e)
        if error:
            flash(error, "danger")
        else:
            db.session.add(ProductoServicio(imagen=imagen, **datos))
            db.session.commit()
            flash("Producto agregado al catálogo.", "success")
            return redirect(url_for("admin.catalogo"))

    valores = request.form if request.method == "POST" else {}
    return render_template("admin/producto_form.html", producto=None, valores=valores,
                           categorias=_categorias())


@admin_bp.route("/catalogo/<int:id_producto>/editar", methods=["GET", "POST"])
def producto_editar(id_producto):
    producto = db.get_or_404(ProductoServicio, id_producto)

    if request.method == "POST":
        imagen_nueva = None
        datos, error = _leer_formulario()
        if not error:
            try:
                imagen_nueva = _guardar_imagen(request.files.get("imagen"))
            except ValueError as e:
                error = str(e)
        if error:
            flash(error, "danger")
        else:
            imagen_vieja = producto.imagen
            for campo, valor in datos.items():
                setattr(producto, campo, valor)
            if imagen_nueva:
                producto.imagen = imagen_nueva
            elif request.form.get("quitar_imagen"):
                producto.imagen = None
            db.session.commit()
            if imagen_vieja != producto.imagen:
                _borrar_imagen(imagen_vieja)
            flash("Producto actualizado.", "success")
            return redirect(url_for("admin.catalogo"))

    valores = request.form if request.method == "POST" else _valores_producto(producto)
    return render_template("admin/producto_form.html", producto=producto, valores=valores,
                           categorias=_categorias())


@admin_bp.post("/catalogo/<int:id_producto>/eliminar")
def producto_eliminar(id_producto):
    producto = db.get_or_404(ProductoServicio, id_producto)
    if _contar(Cotizacion, Cotizacion.id_producto == id_producto):
        flash("No se puede eliminar: el producto tiene cotizaciones asociadas.", "danger")
        return redirect(url_for("admin.catalogo"))

    imagen = producto.imagen
    db.session.delete(producto)
    db.session.commit()
    _borrar_imagen(imagen)
    flash("Producto eliminado del catálogo.", "success")
    return redirect(url_for("admin.catalogo"))


# ---------------------------------------------------------------- Otras secciones del menú

@admin_bp.route("/usuarios")
def usuarios():
    lista = db.session.scalars(db.select(Usuario).order_by(Usuario.rol, Usuario.nombre)).all()
    return render_template("admin/usuarios.html", usuarios=lista)


@admin_bp.route("/asignacion")
def asignacion():
    return render_template(
        "admin/proximamente.html",
        titulo="Reglas de asignación",
        descripcion="Aquí configurarás cómo se asigna cada servicio a un especialista "
                    "(experiencia, habilidades y disponibilidad).",
    )


@admin_bp.route("/reportes")
def reportes():
    return render_template(
        "admin/proximamente.html",
        titulo="Reportes",
        descripcion="Aquí generarás y exportarás reportes de servicios cotizados, contratados, "
                    "en proceso y terminados.",
    )
