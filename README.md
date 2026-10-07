# OrtoChika Web

Plataforma de catÃ¡logo, cotizaciÃ³n y gestiÃ³n de servicios ortopÃ©dicos (Flask + SQLAlchemy + MySQL).

## Puesta en marcha local

```bash
python -m venv venv
venv\Scripts\activate            # Windows  (Linux/Mac: source venv/bin/activate)
pip install -r requirements.txt

copy .env.example .env           # Linux/Mac: cp .env.example .env  -> y edita tus datos de MySQL
```

1. Crea una base de datos **vacÃ­a** llamada `ortochika` en MySQL (Workbench o XAMPP).
2. Crea las tablas: `flask --app run init-db`
3. Carga el catÃ¡logo de prueba: `flask --app run seed-catalogo`
4. Crea la cuenta de administrador: `flask --app run crear-admin`
   (usa `ADMIN_EMAIL` y `ADMIN_PASSWORD` de tu `.env`; con el `.env.example` sin cambios queda
   `admin@ortochika.com` / `Admin2026!`. CÃ¡mbialos, sobre todo antes de desplegar.)
5. (Opcional) datos de demostraciÃ³n para ver el panel del cliente:
   `flask --app run seed-demo` crea `cliente.demo@ortochika.com` con contraseÃ±a `6181234567`
   (una cotizaciÃ³n, un servicio en proceso y uno terminado para calificar). Solo para uso local.
6. Arranca: `python run.py` y abre http://127.0.0.1:5000

Otros roles: `flask --app run crear-usuario "Ana GÃ³mez" ana@correo.com vendedor`
(roles: `cliente`, `vendedor`, `analista`, `administrador`).

## QuÃ© hace cada rol

- **Visitante:** ve el catÃ¡logo, pide cotizaciÃ³n (se le crea la cuenta; su telÃ©fono es su contraseÃ±a inicial) o se registra.
- **Cliente:** panel con pestaÃ±as Cotizaciones / En proceso / Terminados, detalle con seguimiento, calificar servicios terminados, cambiar contraseÃ±a.
- **Administrador:** entra a `/admin` (resumen, alta/ediciÃ³n/baja de productos con imagen, usuarios).

Las imÃ¡genes del catÃ¡logo se guardan en `app/static/img/`. Comprobar la conexiÃ³n a la BD: `/health/db`.

## Estructura

- `app/models/` â€“ modelos SQLAlchemy (tablas del anteproyecto)
- `app/catalogo.py` â€“ catÃ¡logo pÃºblico: pantalla inicial, detalle y solicitud de cotizaciÃ³n
- `app/auth.py` â€“ login, registro y logout
- `app/admin.py` â€“ panel del administrador (resumen, catÃ¡logo CRUD, usuarios)
- `app/cliente.py` â€“ panel del cliente (cotizaciones, servicios, reseÃ±as)
- `app/services.py` â€“ lÃ³gica reutilizable (alta de clientes)
- `app/routes.py` â€“ panel por rol y health check
- `app/cli.py` â€“ comandos de consola (`init-db`, `seed-catalogo`, `crear-admin`, `seed-demo`, `crear-usuario`)
- `app/datos_prueba.py` â€“ productos y servicios de ejemplo

