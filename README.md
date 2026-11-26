# 📚 Ex Libris · Biblioteca personal con IA

Proyecto final de **Tópicos Especiales II** (Prof. Regis Rivera) · Anllelina Varcasia

Aplicación web en Django, usable desde el celular, para registrar libros **escaneando su código ISBN con la cámara**
o escribiéndolo a mano, con los datos traídos automáticamente de Open Library / Google Books; llevar una biblioteca
virtual con **reseñas**, **anotaciones con conteo**, **control de préstamos** y **estadísticas**; y (fase 2) un agente de
**IA generativa** con n8n + LLM gratuito.

## Estado

| Fase | Contenido | Estado |
|---|---|---|
| 1 | Biblioteca, escáner, ISBN manual, catálogo, reseñas, anotaciones, préstamos, estadísticas, diseño, pruebas y CI | ✅ |
| 2 | IA: clasificar, resumir anotaciones, borrador de reseña, agente conversacional (n8n + Gemini/Ollama) | ✅ — ver [`n8n/README.md`](n8n/README.md) |

Auditoría de diseño en [`docs/auditoria-ux.md`](docs/auditoria-ux.md). Especificación en [`specs/`](specs/) (outcomes, requisitos, reglas, modelo de datos, arquitectura) y registro de IA en
[`AI_LOG.md`](AI_LOG.md).

## Tecnología (todo gratuito)

Python 3.12+, Django 5.2, Pillow (portadas), SQLite, CSS propio (tipografía del sistema, paleta lila), html5-qrcode 2.3.8 y Chart.js 4.4.1 por CDN,
Open Library y Google Books (sin API key), GitHub Actions.

## Instalación

```bash
git clone https://github.com/AnnyVibes/exlibris.git
cd exlibris
python -m venv venv
source venv/bin/activate          # Windows (PowerShell): .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py datos_demo       # crea la cuenta demo (contraseña exlibris-demo) con la biblioteca vacía
python manage.py runserver
```

Abre http://127.0.0.1:8000 y entra con `demo` / `exlibris-demo`, o crea tu cuenta.

| Comando | Qué hace |
|---|---|
| `python manage.py datos_demo` | Crea la cuenta `demo` si no existe. **No borra nada.** |
| `python manage.py datos_demo --vaciar` | Borra todos los libros de `demo` para empezar de cero. |
| `python manage.py datos_demo --ejemplos` | Reemplaza la biblioteca de `demo` por 8 libros de ejemplo (capturas, pruebas). |

Las portadas que subes se guardan en la carpeta `media/` (no se sube a GitHub).

## Escanear desde el celular

Los navegadores solo dan acceso a la cámara en **HTTPS** (o en `localhost`). Para usar el celular con el servidor
de tu PC, crea un túnel gratuito con [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/do-more-with-tunnels/trycloudflare/):

```bash
python manage.py runserver 8000
cloudflared tunnel --url http://localhost:8000
```

Abre en el celular la URL `https://….trycloudflare.com` que muestra el comando (ya está permitida en `ALLOWED_HOSTS`
y `CSRF_TRUSTED_ORIGINS`), ve a **Escanear**, activa la cámara y apunta al código de barras de la contraportada.

## Pruebas

```bash
python manage.py test
```

69 pruebas: validación de ISBN, catálogo (con respuestas simuladas), géneros, portadas subidas, filtros, alta por escaneo y manual, duplicados,
aislamiento entre usuarios, progreso, reseñas, anotaciones y conteo, préstamos (reglas, vencidos, redirección segura)
estadísticas y el comando demo. Se ejecutan en CI en cada push (`.github/workflows/tests.yml`).

## Estructura

```
exlibris/
├── exlibris_site/          configuración de Django
├── biblioteca/
│   ├── models.py           Libro, Resena, Anotacion, Prestamo
│   ├── services/           isbn, catalogo, prestamos, estadisticas
│   ├── views.py · urls.py · forms.py
│   ├── templates/          base (3 columnas) + páginas
│   ├── static/biblioteca/  exlibris.css, libros.svg
│   ├── management/commands/datos_demo.py
│   └── tests/
├── specs/                  ODD / SDD
└── AI_LOG.md
```
