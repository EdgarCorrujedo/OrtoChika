"""Configuración central de OrtoChika Web. Todo se lee desde el archivo .env."""
import os

from dotenv import load_dotenv
from sqlalchemy.engine import URL

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-inseguro-cambiar")

    USE_SQLITE = os.getenv("USE_SQLITE", "").strip().lower() in {
        "1", "true", "yes", "y", "on"
    }
    DB_USER = os.getenv("DB_USER", "root").strip()
    DB_PASSWORD = os.getenv("DB_PASSWORD", "").strip()
    DB_HOST = os.getenv("DB_HOST", "localhost").strip()
    DB_PORT = int(os.getenv("DB_PORT", "3306"))
    DB_NAME = os.getenv("DB_NAME", "ortochika").strip()

    if USE_SQLITE or (not DB_PASSWORD and DB_HOST in {"", "localhost", "127.0.0.1"}):
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'ortochika.db')}"
    else:
        # URL.create escapa correctamente contraseñas con caracteres especiales (@, :, /...)
        SQLALCHEMY_DATABASE_URI = URL.create(
            drivername="mysql+pymysql",
            username=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            query={"charset": "utf8mb4"},
        )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # imágenes del catálogo: máximo 2 MB
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True, "pool_recycle": 280}
