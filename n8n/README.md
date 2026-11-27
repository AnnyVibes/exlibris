# Ex Libris · IA con n8n (fase 2)

La app no llama al modelo de IA directamente. Envía cada tarea a un **webhook de n8n** y n8n usa un LLM gratuito:
**Google Gemini** (capa gratuita, con API key) u **Ollama** (modelo local, sin key). Es la misma idea del Lab 14.

```
Ex Libris (Django) ──POST──▶ n8n /webhook/exlibris-tarea  ──▶ Switch ──▶ Cadena LLM + Parser ──▶ JSON
                   ──POST──▶ n8n /webhook/exlibris-agente ──▶ Agente IA (memoria + 5 herramientas) ──▶ JSON
                                                                   │
                         ◀──GET /api/ia/... (token firmado)────────┘  las herramientas consultan la biblioteca
```

| Archivo | Qué hace |
|---|---|
| `exlibris-tareas.json` | **Clasificar** un libro (género de la lista + etiquetas), **resumir** las anotaciones, **borrador de reseña**, **escribir sinopsis** y **completar datos** (con título y autor). Switch por `tarea` → 5 *Basic LLM Chain* con *Structured Output Parser* → *Respond to Webhook*. |
| `exlibris-agente.json` | **Asistente «Pregúntale a tu biblioteca»**: *AI Agent* con memoria por conversación y 6 herramientas HTTP: 5 de consulta (`buscar_libros`, `ver_libro`, `libros_compartidos`, `buscar_anotaciones`, `resumen_biblioteca`) y 1 de escritura (`agregar_libro`: busca el ISBN por título y autor y agrega el libro). |
| `*-ollama.json` | Los mismos workflows con **Ollama** en lugar de Gemini. |
| `generar_workflows.py` | Script que genera los cuatro JSON (prompts, esquemas y lista de géneros salen del código de la app). |

## Puesta en marcha (gratis)

1. **Instala y abre n8n** en tu PC (n8n 2.x necesita **Node.js 24 o superior**; revisa con `node -v`):
   ```powershell
   npx n8n
   ```
   Se abre en http://localhost:5678. La primera vez te pide crear una cuenta local.
2. **Importa los workflows**: *Create workflow* → menú `⋯` (junto al nombre) → **Import ▸ From File…** → `exlibris-tareas.json`.
   n8n 2.x muestra la ventana **«Importing this from an AI tool?»**: pulsa **Skip** y entonces aparecen los nodos
   (si cierras con la ✕ o la ignoras, el lienzo queda vacío). Repite con `exlibris-agente.json` en otro workflow.
   Alternativa: abre el `.json` en VS Code, copia todo (Ctrl + A, Ctrl + C), haz clic en el lienzo vacío y pega (Ctrl + V).
   Último recurso con Docker (importa por línea de comandos y luego recarga n8n con F5):
   ```powershell
   docker cp n8n\exlibris-tareas.json n8n:/tmp/tareas.json
   docker exec n8n n8n import:workflow --input=/tmp/tareas.json
   ```
3. **Conecta el modelo** (en cada nodo con el triángulo rojo ⚠):
   - **Gemini**: abre el nodo → *Credential* → *Create new* → pega tu API key de https://aistudio.google.com/apikey.
     El modelo es `gemini-3.5-flash` (estable). Evita el más nuevo (`gemini-3.8-flash`): suele responder 503 por saturación y n8n se queda minutos reintentando. Si `3.5-flash` también da 503, usa `gemini-3.5-flash-lite`.
   - **Ollama** (alternativa): instala https://ollama.com, ejecuta `ollama pull llama3.2` e importa los archivos `-ollama`.
4. **Activa** cada workflow con el botón **Publish** (arriba a la derecha). Sin publicar, los webhooks no responden.
5. **Arranca Ex Libris** normalmente (`python manage.py runserver`). Por defecto busca n8n en
   `http://localhost:5678/webhook`. Si usas otra dirección:
   ```powershell
   $env:N8N_URL = "http://localhost:5678/webhook"
   $env:EXLIBRIS_API_URL = "http://localhost:8000"   # dirección con la que n8n llega a Django
   python manage.py runserver
   ```

## Opción con Docker (recomendada en Windows)

Docker trae su propio Node, así que no hay problemas de versiones.

1. Instala **Docker Desktop** (`winget install Docker.DockerDesktop`), reinicia la PC y abre Docker Desktop
   hasta que diga *Engine running*.
2. Arranca n8n (los datos quedan en el volumen `n8n_data` y se conservan entre reinicios):
   ```powershell
   docker run -it --rm --name n8n -p 5678:5678 -v n8n_data:/home/node/.n8n --add-host=host.docker.internal:host-gateway docker.n8n.io/n8nio/n8n
   ```
3. Arranca Django **escuchando en todas las interfaces** e indicando cómo lo encuentra n8n:
   ```powershell
   $env:EXLIBRIS_API_URL = "http://host.docker.internal:8000"
   python manage.py runserver 0.0.0.0:8000
   ```
   Dentro del contenedor, `localhost` es el propio contenedor: por eso las herramientas del agente usan
   `host.docker.internal`. Django sigue llamando a n8n en `http://localhost:5678` (el puerto está publicado).
4. Con **Ollama** en Docker, la credencial de Ollama en n8n debe usar `http://host.docker.internal:11434`.

## Dónde aparece la IA en la app

| Pantalla | Botón | Qué hace |
|---|---|---|
| Agregar / editar libro | **Sugerir con IA** (junto a Género) | Elige el género de la lista y propone etiquetas. Tú decides si lo dejas. |
| Ficha del libro · Mi reseña | **Sugerir borrador con IA** | Escribe un borrador según tus anotaciones y tus estrellas. No se guarda hasta que pulses «Guardar reseña». |
| Ficha del libro · Anotaciones | **Resumir con IA** | Agrupa tus notas por temas y guarda el resumen (con fecha). |
| Menú · **Asistente IA** | Chat | Responde preguntas como «¿A quién le presté Rayuela?» consultando tu biblioteca con herramientas. |

Si n8n está apagado, la app sigue funcionando y muestra «La IA no está disponible. ¿Está encendido n8n?».

## Seguridad

- El agente solo ve la biblioteca de quien pregunta y su **única acción de escritura** es `agregar_libro` (no edita ni borra): cada pregunta lleva un token firmado por Django
  que identifica a la persona y **caduca a los 15 minutos**. Las rutas `/api/ia/` son de lectura (GET), salvo `POST /api/ia/libros/agregar/`.
- Opcional: define `N8N_SECRET` y Django enviará la cabecera `X-ExLibris-Secret`; en el nodo Webhook activa
  *Authentication → Header Auth* con ese mismo valor.
- La API key de Gemini vive solo en n8n (credenciales), nunca en el código ni en la app.

## Cómo se probó

- 24 pruebas automáticas en `biblioteca/tests/test_ia.py` (n8n simulado): normalización de respuestas, errores, límites
  de texto, token caducado, aislamiento entre usuarios y que la API sea de solo lectura.
- Los workflows se importaron en **n8n 2.49** sin errores de configuración (`docs/capturas/n8n/`).
- Prueba de punta a punta con n8n real y un servidor que imita a Ollama: la app clasificó, resumió, generó el borrador
  y el agente llamó a la herramienta `libros_compartidos`, que pidió `/api/ia/compartidos/` a Django con el token y
  recibió los datos (`docs/capturas/desk-asistente-prueba.png`). Falta probarlo con la API key real de Gemini.
