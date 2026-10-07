"""Catálogo de productos y servicios."""
from ..extensions import db


class ProductoServicio(db.Model):
    __tablename__ = "Productos_Servicios"

    id_producto = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    descripcion = db.Column(db.Text)
    categoria = db.Column(db.String(60))
    precio_aprox = db.Column(db.Numeric(10, 2))
    imagen = db.Column(db.String(255))           # ruta/nombre dentro de static/img

    cotizaciones = db.relationship("Cotizacion", back_populates="producto")
