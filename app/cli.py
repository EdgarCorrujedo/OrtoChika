"""Comandos de consola (desde la raíz del proyecto):

    flask --app run init-db
    flask --app run seed-catalogo
    flask --app run crear-admin
    flask --app run seed-demo
    flask --app run crear-usuario "Nombre" correo@ejemplo.com vendedor
"""
import os
from datetime import datetime

import click
from sqlalchemy.exc import IntegrityError

from .datos_prueba import CATALOGO_PRUEBA
from .extensions import db
from .models import (ROLES, Cliente, Cotizacion, Especialista, ObservacionServicio,
                     ProductoServicio, Servicio, Usuario)
from .services import registrar_cliente

DEMO_CLIENTE = "cliente.demo@ortochika.com"
DEMO_TELEFONO = "6181234567"  # también es su contraseña inicial


def registrar_comandos(app):
    @app.cli.command("init-db")
    def init_db():
        """Crea en MySQL las tablas definidas en los modelos."""
        db.create_all()
        click.echo("Tablas creadas.")

    @app.cli.command("seed-catalogo")
    def seed_catalogo():
        """Carga productos y servicios de prueba (solo si el catálogo está vacío)."""
        if db.session.scalar(db.select(db.func.count()).select_from(ProductoServicio)):
            raise click.ClickException("El catálogo ya tiene datos; no se cargó nada.")
        db.session.add_all(ProductoServicio(**datos) for datos in CATALOGO_PRUEBA)
        db.session.commit()
        click.echo(f"{len(CATALOGO_PRUEBA)} productos y servicios de prueba cargados.")

    @app.cli.command("crear-admin")
    def crear_admin():
        """Crea (o restablece) la cuenta de administrador con ADMIN_EMAIL y ADMIN_PASSWORD del .env."""
        correo = os.getenv("ADMIN_EMAIL", "").strip().lower()
        password = os.getenv("ADMIN_PASSWORD", "")
        if not correo or not password:
            raise click.ClickException("Define ADMIN_EMAIL y ADMIN_PASSWORD en tu archivo .env.")

        usuario = db.session.scalar(db.select(Usuario).filter_by(correo=correo))
        accion = "actualizada"
        if usuario is None:
            usuario = Usuario(nombre="Administrador", correo=correo)
            db.session.add(usuario)
            accion = "creada"
        usuario.rol = "administrador"
        usuario.set_password(password)
        db.session.commit()
        click.echo(f"Cuenta de administrador {accion}: {correo}")

    @app.cli.command("seed-demo")
    def seed_demo():
        """Crea un cliente de ejemplo con una cotización, un servicio en proceso y uno terminado."""
        productos = db.session.scalars(
            db.select(ProductoServicio).order_by(ProductoServicio.id_producto).limit(3)).all()
        if len(productos) < 3:
            raise click.ClickException("Primero carga el catálogo: flask --app run seed-catalogo")
        if db.session.scalar(db.select(Usuario).filter_by(correo=DEMO_CLIENTE)):
            raise click.ClickException("Los datos de demostración ya existen.")

        cliente = registrar_cliente("Cliente Demo", DEMO_CLIENTE, DEMO_TELEFONO).cliente
        vendedor = Usuario(nombre="Vendedor Demo", correo="vendedor.demo@ortochika.com",
                           telefono="6189876543", rol="vendedor")
        vendedor.set_password("6189876543")
        vendedor.especialista = Especialista(experiencia=5, disponibilidad=True,
                                             habilidades="sillas de ruedas, plantillas")

        def cotizar(producto):
            return Cotizacion(cliente=cliente, producto=producto, monto_estimado=producto.precio_aprox)

        en_proceso = Servicio(cotizacion=cotizar(productos[1]), especialista=vendedor.especialista,
                              estatus="en proceso")
        en_proceso.observaciones = [
            ObservacionServicio(autor=vendedor.nombre, texto="Se recibió el producto."),
            ObservacionServicio(autor=vendedor.nombre, texto="Ajuste programado para esta semana."),
        ]
        terminado = Servicio(cotizacion=cotizar(productos[2]), especialista=vendedor.especialista,
                             estatus="terminado", fecha_cierre=datetime.now())
        terminado.observaciones = [
            ObservacionServicio(autor=vendedor.nombre, texto="Servicio entregado al cliente."),
        ]
        db.session.add_all([vendedor, cotizar(productos[0]), en_proceso, terminado])
        db.session.commit()
        click.echo(f"Datos de demostración creados. Cliente: {DEMO_CLIENTE} / {DEMO_TELEFONO}")

    @app.cli.command("crear-usuario")
    @click.argument("nombre")
    @click.argument("correo")
    @click.argument("rol", type=click.Choice(ROLES))
    @click.password_option()
    def crear_usuario(nombre, correo, rol, password):
        """Crea un usuario de cualquier rol (útil para vendedores, analistas y administradores)."""
        usuario = Usuario(nombre=nombre, correo=correo.strip().lower(), rol=rol)
        usuario.set_password(password)
        if rol == "cliente":
            usuario.cliente = Cliente()
        elif rol == "vendedor":
            usuario.especialista = Especialista(disponibilidad=True)
        db.session.add(usuario)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise click.ClickException("Ya existe un usuario con ese correo.")
        click.echo(f"Usuario '{usuario.correo}' creado con rol {rol}.")
