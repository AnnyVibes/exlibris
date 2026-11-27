# Ex Libris · Comandos de la terminal (Windows, PowerShell)

Todo se escribe en la terminal de VS Code. Cada bloque va en **su propia terminal** (botón **+** del panel de terminal).

---

## A. Cada vez que quieras usar el sitio

Antes de empezar: abre **Docker Desktop** y espera a que diga *Engine running*.

### Terminal 1 · n8n (la IA)
```powershell
docker run -it --rm --name n8n -p 5678:5678 -v n8n_data:/home/node/.n8n --add-host=host.docker.internal:host-gateway docker.n8n.io/n8nio/n8n
```
Listo cuando dice `Editor is now accessible via: http://localhost:5678`. **No la cierres.**

### Terminal 2 · Ex Libris (el sitio web)
```powershell
cd C:\Users\Rafae\exlibris
.\venv\Scripts\Activate.ps1
git pull
pip install -r requirements.txt
python manage.py migrate
$env:EXLIBRIS_API_URL = "http://host.docker.internal:8000"
python manage.py runserver 0.0.0.0:8000
```
Abre **http://127.0.0.1:8000** en el navegador (si no ves cambios: **Ctrl + F5**). **No la cierres.**

### Terminal 3 · Celular (opcional)
```powershell
cloudflared tunnel --url http://localhost:8000
```
Abre en el celular el enlace `https://….trycloudflare.com` que aparece en el cuadro.

### Para apagar todo
`Ctrl + C` en cada terminal.

---

## B. Solo si algo no funciona

| Problema | Comando |
|---|---|
| No deja activar el `venv` (error de permisos) | `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned` y repite `.\venv\Scripts\Activate.ps1` |
| `cloudflared` no se reconoce | `$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")` |
| Docker: *failed to connect to the docker API* | Abre Docker Desktop y espera *Engine running*; comprueba con `docker info` |
| Docker: *container name "/n8n" is already in use* | `docker rm -f n8n` y vuelve a ejecutar el comando de la Terminal 1 |
| Aviso *You have unapplied migrations* | `python manage.py migrate` |
| `git pull` dice *local changes would be overwritten* | `git checkout -- .` y luego `git pull` (descarta cambios locales sin guardar en git) |
| Comprobar que n8n + Gemini responden | ver el comando de prueba abajo |

**Prueba de n8n + Gemini** (en cualquier terminal, con n8n encendido):
```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:5678/webhook/exlibris-tarea -ContentType "application/json; charset=utf-8" -Body '{"tarea":"clasificar","titulo":"Cien anos de soledad","autores":"Gabriel Garcia Marquez","descripcion":"","generos":["Novela","Cuento","Poesia","Fantasia"]}'
```
Debe responder con `genero` y `etiquetas`.

---

## C. Cuenta de demostración

| Comando | Para qué |
|---|---|
| `python manage.py datos_demo` | Crea la cuenta `demo` (contraseña `exlibris-demo`) sin borrar nada |
| `python manage.py datos_demo --vaciar` | Deja la cuenta `demo` sin libros |
| `python manage.py datos_demo --ejemplos` | Carga 8 libros de ejemplo en `demo` (borra los que tenga) |
| `python manage.py changepassword demo` | Cambiar la contraseña de una cuenta |
| `python manage.py test` | Correr las pruebas automáticas |

---

## D. Instalación desde cero (solo la primera vez en una PC nueva)

```powershell
git clone https://github.com/AnnyVibes/exlibris.git
cd exlibris
py -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py datos_demo
winget install Docker.DockerDesktop
winget install --id Cloudflare.cloudflared
```
Después: reinicia la PC, abre Docker Desktop y sigue la guía `n8n/README.md` para importar los workflows,
poner la API key de Gemini (modelo `models/gemini-3.5-flash`) y pulsar **Publish**.
