"""Usuarios, Clientes y Especialistas."""
from datetime import date

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from ..extensions import db, login_manager

# El "Prospecto" es un visitante sin cuenta, por eso no se guarda en la BD.
ROLES = ("cliente", "vendedor", "analista", "administrador")


class Usuario(UserMixin, db.Model):
    __tablename__ = "Usuarios"

    id_usuario = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    correo = db.Column(db.String(120), unique=True, nullable=False)
    telefono = db.Column(db.String(20))
    contrasena_hash = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(20), nullable=False, default="cliente")

    cliente = db.relationship("Cliente", back_populates="usuario", uselist=False,
                              cascade="all, delete-orphan")
    especialista = db.relationship("Especialista", back_populates="usuario", uselist=False,
                                   cascade="all, delete-orphan")

    def get_id(self):  # requerido por Flask-Login (la PK no se llama "id")
        return str(self.id_usuario)

    def set_password(self, contrasena):
        self.contrasena_hash = generate_password_hash(contrasena)

    def check_password(self, contrasena):
        return check_password_hash(self.contrasena_hash, contrasena)

    def tiene_rol(self, *roles):
        return self.rol in roles


@login_manager.user_loader
def cargar_usuario(user_id):
    return db.session.get(Usuario, int(user_id))


class Cliente(db.Model):
    __tablename__ = "Clientes"

    id_cliente = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey("Usuarios.id_usuario"),
                           unique=True, nullable=False)
    direccion = db.Column(db.String(255))
    fecha_alta = db.Column(db.Date, default=date.today)

    usuario = db.relationship("Usuario", back_populates="cliente")
    cotizaciones = db.relationship("Cotizacion", back_populates="cliente")
    resenas = db.relationship("Resena", back_populates="cliente")


class Especialista(db.Model):
    __tablename__ = "Especialistas"

    id_especialista = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey("Usuarios.id_usuario"),
                           unique=True, nullable=False)
    experiencia = db.Column(db.Integer)          # años de experiencia
    habilidades = db.Column(db.Text)             # lista separada por comas
    disponibilidad = db.Column(db.Boolean, default=True)

    usuario = db.relationship("Usuario", back_populates="especialista")
    servicios = db.relationship("Servicio", back_populates="especialista")
