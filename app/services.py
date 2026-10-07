"""Lógica de negocio reutilizable entre módulos."""
import re

from sqlalchemy.exc import IntegrityError

from .extensions import db
from .models import Cliente, Cotizacion, Usuario

CORREO_RE = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")
TELEFONO_RE = re.compile(r"\d{10,15}")


class CorreoDuplicado(Exception):
    """Ya existe un usuario con ese correo."""


def validar_datos_cliente(nombre, correo, telefono):
    """Devuelve un mensaje de error, o None si los datos son válidos."""
    if not nombre or len(nombre) > 100:
        return "Escribe tu nombre completo (máximo 100 caracteres)."
    if len(correo) > 120 or not CORREO_RE.fullmatch(correo):
        return "Escribe un correo electrónico válido."
    if not TELEFONO_RE.fullmatch(telefono):
        return "El teléfono debe tener solo dígitos (de 10 a 15)."
    return None


def registrar_cliente(nombre, correo, telefono):
    """Crea Usuario (rol cliente) + Cliente. La contraseña inicial es el teléfono, con hash."""
    usuario = Usuario(nombre=nombre, correo=correo, telefono=telefono, rol="cliente")
    usuario.set_password(telefono)
    usuario.cliente = Cliente()
    db.session.add(usuario)
    try:
        db.session.commit()
    except IntegrityError:  # el correo es UNIQUE
        db.session.rollback()
        raise CorreoDuplicado(correo)
    return usuario


def crear_cotizacion(cliente, producto):
    """Registra una cotización pendiente; el monto estimado parte del precio aproximado."""
    cotizacion = Cotizacion(id_cliente=cliente.id_cliente, id_producto=producto.id_producto,
                            monto_estimado=producto.precio_aprox)
    db.session.add(cotizacion)
    db.session.commit()
    return cotizacion
