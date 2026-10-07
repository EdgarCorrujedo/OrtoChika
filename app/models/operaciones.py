"""Cotizaciones, servicios, observaciones y reseñas."""
from ..extensions import db


class Cotizacion(db.Model):
    __tablename__ = "Cotizaciones"

    id_cotizacion = db.Column(db.Integer, primary_key=True)
    id_cliente = db.Column(db.Integer, db.ForeignKey("Clientes.id_cliente"), nullable=False)
    id_producto = db.Column(db.Integer, db.ForeignKey("Productos_Servicios.id_producto"),
                            nullable=False)
    fecha = db.Column(db.DateTime, server_default=db.func.now())
    estatus = db.Column(db.String(30), nullable=False, default="pendiente")
    monto_estimado = db.Column(db.Numeric(10, 2))

    cliente = db.relationship("Cliente", back_populates="cotizaciones")
    producto = db.relationship("ProductoServicio", back_populates="cotizaciones")
    servicio = db.relationship("Servicio", back_populates="cotizacion", uselist=False)


class Servicio(db.Model):
    __tablename__ = "Servicios"

    id_servicio = db.Column(db.Integer, primary_key=True)
    id_cotizacion = db.Column(db.Integer, db.ForeignKey("Cotizaciones.id_cotizacion"),
                              nullable=False)
    # Nullable: el servicio nace sin especialista hasta que el motor de asignación actúe.
    id_especialista = db.Column(db.Integer, db.ForeignKey("Especialistas.id_especialista"))
    estatus = db.Column(db.String(30), nullable=False, default="asignado")
    fecha_inicio = db.Column(db.DateTime, server_default=db.func.now())
    fecha_cierre = db.Column(db.DateTime)

    cotizacion = db.relationship("Cotizacion", back_populates="servicio")
    especialista = db.relationship("Especialista", back_populates="servicios")
    observaciones = db.relationship("ObservacionServicio", back_populates="servicio",
                                    cascade="all, delete-orphan",
                                    order_by="ObservacionServicio.fecha")
    resenas = db.relationship("Resena", back_populates="servicio")


class ObservacionServicio(db.Model):
    __tablename__ = "Observaciones_Servicio"

    id_observacion = db.Column(db.Integer, primary_key=True)
    id_servicio = db.Column(db.Integer, db.ForeignKey("Servicios.id_servicio"), nullable=False)
    fecha = db.Column(db.DateTime, server_default=db.func.now())
    autor = db.Column(db.String(100))
    texto = db.Column(db.Text, nullable=False)

    servicio = db.relationship("Servicio", back_populates="observaciones")


class Resena(db.Model):
    __tablename__ = "Reseñas"   # con ñ, igual que en MySQL; ver nota sobre mayúsculas/ñ

    id_resena = db.Column(db.Integer, primary_key=True)
    id_cliente = db.Column(db.Integer, db.ForeignKey("Clientes.id_cliente"), nullable=False)
    id_servicio = db.Column(db.Integer, db.ForeignKey("Servicios.id_servicio"), nullable=False)
    calificacion = db.Column(db.SmallInteger, nullable=False)   # 1 a 5
    comentario = db.Column(db.Text)

    cliente = db.relationship("Cliente", back_populates="resenas")
    servicio = db.relationship("Servicio", back_populates="resenas")
