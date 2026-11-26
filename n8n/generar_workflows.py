"""Genera los workflows de n8n de Ex Libris (fase 2) listos para importar.

  python n8n/generar_workflows.py

Crea cuatro archivos en n8n/:
  exlibris-tareas.json         Tareas de IA con Google Gemini (clasificar, resumir, borrador de reseña)
  exlibris-agente.json         Agente «Pregúntale a tu biblioteca» con Gemini, memoria y herramientas HTTP
  exlibris-tareas-ollama.json  Igual que el primero, con Ollama (modelo local, sin API key)
  exlibris-agente-ollama.json  Igual que el segundo, con Ollama
"""

import copy
import json
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
from biblioteca.services.generos import GENEROS  # noqa: E402

GEMINI = {"parameters": {"modelName": "models/gemini-2.5-flash", "options": {"temperature": 0.3}},
          "type": "@n8n/n8n-nodes-langchain.lmChatGoogleGemini", "typeVersion": 1}
OLLAMA = {"parameters": {"model": "llama3.2", "options": {"temperature": 0.3}},
          "type": "@n8n/n8n-nodes-langchain.lmChatOllama", "typeVersion": 1}


def modelo(nombre, id_, pos, base):
    n = copy.deepcopy(base)
    n.update({"id": id_, "name": nombre, "position": pos})
    return n


def webhook(ruta, pos):
    return {"parameters": {"httpMethod": "POST", "path": ruta, "responseMode": "responseNode", "options": {}},
            "id": f"w-{ruta}", "name": "Webhook", "type": "n8n-nodes-base.webhook", "typeVersion": 2,
            "position": pos, "webhookId": ruta}


def responder(nombre, id_, cuerpo, pos):
    return {"parameters": {"respondWith": "json", "responseBody": cuerpo, "options": {}},
            "id": id_, "name": nombre, "type": "n8n-nodes-base.respondToWebhook", "typeVersion": 1.1, "position": pos}


def cadena(nombre, id_, prompt, pos):
    return {"parameters": {"promptType": "define", "text": prompt, "hasOutputParser": True},
            "id": id_, "name": nombre, "type": "@n8n/n8n-nodes-langchain.chainLlm", "typeVersion": 1.5, "position": pos}


def parser(nombre, id_, esquema, pos):
    return {"parameters": {"schemaType": "manual", "inputSchema": json.dumps(esquema, ensure_ascii=False, indent=1)},
            "id": id_, "name": nombre, "type": "@n8n/n8n-nodes-langchain.outputParserStructured",
            "typeVersion": 1.2, "position": pos}


# ------------------------------------------------------------------ Tareas
P_CLASIFICAR = """=Eres bibliotecaria. Clasifica este libro.

Título: {{ $json.body.titulo }}
Autor(es): {{ $json.body.autores || "desconocido" }}
Descripción: {{ $json.body.descripcion || "sin descripción" }}

Reglas:
- "genero": elige EXACTAMENTE uno de esta lista (copia el texto tal cual): {{ $json.body.generos.join(" | ") }}
- "etiquetas": de 3 a 5 palabras o frases cortas en español y en minúsculas que describan temas, época o estilo.
- Si no conoces el libro, deduce por el título y el autor. No inventes datos."""

P_RESUMIR = """=Estas son las anotaciones que una persona escribió mientras leía «{{ $json.body.libro.titulo }}» de {{ $json.body.libro.autores || "autor desconocido" }}:

{{ $json.body.anotaciones.map(n => (n.pagina ? "[p. " + n.pagina + "] " : "- ") + n.texto).join("\\n") }}

Escribe en "resumen" un resumen en español de 2 a 4 párrafos cortos que agrupe las ideas por temas.
Usa solo lo que está en las anotaciones (no agregues datos del libro que la persona no escribió) y habla de «tus notas»."""

P_RESENA = """=Redacta un borrador de reseña personal, en primera persona y en español, del libro «{{ $json.body.libro.titulo }}» de {{ $json.body.libro.autores || "autor desconocido" }}.
Calificación que le dio la persona: {{ $json.body.calificacion ? $json.body.calificacion + " de 5 estrellas" : "sin calificar" }}.
Sus anotaciones:
{{ $json.body.anotaciones.length ? $json.body.anotaciones.map(n => "- " + n.texto).join("\\n") : "(no tiene anotaciones)" }}

Escribe en "resena" entre 80 y 150 palabras, con un tono acorde a la calificación, basándote en sus anotaciones.
Si no hay anotaciones, escribe una reseña breve y general sin inventar detalles de la trama."""

ESQ_CLASIFICAR = {"type": "object", "properties": {
    "genero": {"type": "string", "enum": GENEROS},
    "etiquetas": {"type": "array", "items": {"type": "string"}, "maxItems": 5}},
    "required": ["genero", "etiquetas"]}
ESQ_RESUMIR = {"type": "object", "properties": {"resumen": {"type": "string"}}, "required": ["resumen"]}
ESQ_RESENA = {"type": "object", "properties": {"resena": {"type": "string"}}, "required": ["resena"]}


def regla(id_, valor):
    return {"conditions": {"options": {"caseSensitive": True, "leftValue": "", "typeValidation": "strict"},
                           "conditions": [{"id": id_, "leftValue": "={{ $json.body.tarea }}", "rightValue": valor,
                                           "operator": {"type": "string", "operation": "equals"}}],
                           "combinator": "and"},
            "renameOutput": True, "outputKey": valor}


def tareas(base):
    nodos = [
        webhook("exlibris-tarea", [0, 200]),
        {"parameters": {"rules": {"values": [regla("r1", "clasificar"), regla("r2", "resumir"), regla("r3", "resena")]},
                        "options": {}},
         "id": "n-switch", "name": "Switch (tarea)", "type": "n8n-nodes-base.switch", "typeVersion": 3.2, "position": [220, 200]},
        cadena("Clasificar libro", "c-clas", P_CLASIFICAR, [500, 0]),
        cadena("Resumir anotaciones", "c-res", P_RESUMIR, [500, 300]),
        cadena("Borrador de reseña", "c-resena", P_RESENA, [500, 600]),
        modelo("Modelo (clasificar)", "m-clas", [440, 160], base),
        modelo("Modelo (resumir)", "m-res", [440, 460], base),
        modelo("Modelo (reseña)", "m-resena", [440, 760], base),
        parser("Parser (clasificar)", "p-clas", ESQ_CLASIFICAR, [640, 160]),
        parser("Parser (resumir)", "p-res", ESQ_RESUMIR, [640, 460]),
        parser("Parser (reseña)", "p-resena", ESQ_RESENA, [640, 760]),
        responder("Responder a Ex Libris", "n-resp", "={{ JSON.stringify($json.output) }}", [900, 300]),
    ]
    conexiones = {
        "Webhook": {"main": [[{"node": "Switch (tarea)", "type": "main", "index": 0}]]},
        "Switch (tarea)": {"main": [[{"node": "Clasificar libro", "type": "main", "index": 0}],
                                    [{"node": "Resumir anotaciones", "type": "main", "index": 0}],
                                    [{"node": "Borrador de reseña", "type": "main", "index": 0}]]},
    }
    for cadena_, mod, par in (("Clasificar libro", "Modelo (clasificar)", "Parser (clasificar)"),
                              ("Resumir anotaciones", "Modelo (resumir)", "Parser (resumir)"),
                              ("Borrador de reseña", "Modelo (reseña)", "Parser (reseña)")):
        conexiones[cadena_] = {"main": [[{"node": "Responder a Ex Libris", "type": "main", "index": 0}]]}
        conexiones[mod] = {"ai_languageModel": [[{"node": cadena_, "type": "ai_languageModel", "index": 0}]]}
        conexiones[par] = {"ai_outputParser": [[{"node": cadena_, "type": "ai_outputParser", "index": 0}]]}
    return {"name": "Ex Libris · Tareas de IA", "nodes": nodos, "connections": conexiones, "settings": {}, "pinData": {}}


# ------------------------------------------------------------------ Agente
SISTEMA = """=Eres el asistente de «Ex Libris», la biblioteca personal de {{ $('Webhook').item.json.body.persona.nombre }} ({{ $('Webhook').item.json.body.persona.tratamiento }}).
Hoy es {{ $now.toFormat('dd/MM/yyyy') }}.

- Responde siempre en español, de forma breve y amable.
- Para cualquier dato de su biblioteca USA LAS HERRAMIENTAS: nunca inventes libros, personas, fechas ni anotaciones.
- «Compartido» significa prestado: usa la herramienta de compartidos para saber quién tiene un libro y desde hace cuántos días.
- Si te piden recomendaciones, básate en los géneros y calificaciones de lo que ya leyó; puedes sugerir libros que no tiene, pero aclara que no están en su biblioteca.
- Si una herramienta no encuentra nada, dilo con honestidad."""


def herramienta(nombre, id_, descripcion, ruta, pos, consulta=None, marcadores=None):
    p = {"toolDescription": descripcion, "method": "GET",
         "url": "={{ $('Webhook').item.json.body.api }}" + ruta,
         "sendHeaders": True, "specifyHeaders": "keypair",
         "parametersHeaders": {"values": [{"name": "X-ExLibris-Token", "valueProvider": "fieldValue",
                                           "value": "={{ $('Webhook').item.json.body.token }}"}]},
         "optimizeResponse": False}
    if consulta:
        p.update({"sendQuery": True, "specifyQuery": "keypair",
                  "parametersQuery": {"values": [{"name": n, "valueProvider": "modelOptional", "description": d} for n, d in consulta]}})
    if marcadores:
        p["placeholderDefinitions"] = {"values": [{"name": n, "description": d, "type": t} for n, d, t in marcadores]}
    return {"parameters": p, "id": id_, "name": nombre, "type": "@n8n/n8n-nodes-langchain.toolHttpRequest",
            "typeVersion": 1.1, "position": pos}


def agente(base):
    nodos = [
        webhook("exlibris-agente", [0, 0]),
        {"parameters": {"promptType": "define", "text": "={{ $json.body.mensaje }}", "options": {"systemMessage": SISTEMA}},
         "id": "n-agente", "name": "Agente Ex Libris", "type": "@n8n/n8n-nodes-langchain.agent", "typeVersion": 1.7, "position": [260, 0]},
        modelo("Modelo", "m-agente", [100, 260], base),
        {"parameters": {"sessionIdType": "customKey", "sessionKey": "={{ $('Webhook').item.json.body.sesion }}", "contextWindowLength": 10},
         "id": "n-memoria", "name": "Memoria", "type": "@n8n/n8n-nodes-langchain.memoryBufferWindow", "typeVersion": 1.3, "position": [260, 260]},
        herramienta("buscar_libros", "t-libros",
                    "Busca libros de la biblioteca. Devuelve título, autor, género, estado (Por leer, Leyendo, Leído), progreso, calificación, número de anotaciones y con quién está compartido. Sin parámetros devuelve todos.",
                    "/libros/", [420, 260],
                    consulta=[("q", "texto a buscar en título, autor o ISBN"), ("estado", "por_leer, leyendo o leido"), ("genero", "género exacto, p. ej. Novela")]),
        herramienta("ver_libro", "t-libro",
                    "Muestra el detalle de un libro por su id (de buscar_libros): descripción, reseña, anotaciones, resumen de notas e historial de compartidos.",
                    "/libros/{id}/", [580, 260], marcadores=[("id", "id numérico del libro", "number")]),
        herramienta("libros_compartidos", "t-compartidos",
                    "Lista los libros compartidos (prestados) ahora: con quién, contacto, desde cuándo, cuántos días y si la devolución está vencida. Con todos=1 incluye el historial.",
                    "/compartidos/", [740, 260], consulta=[("todos", "1 para incluir los ya devueltos")]),
        herramienta("buscar_anotaciones", "t-notas",
                    "Busca en las anotaciones que la persona escribió mientras leía. Devuelve el libro, la página y el texto.",
                    "/anotaciones/", [900, 260], consulta=[("q", "palabra o tema a buscar")]),
        herramienta("resumen_biblioteca", "t-resumen",
                    "Totales de la biblioteca: libros, leídos, leyendo, anotaciones, compartidos, páginas leídas, calificación media y libros por género.",
                    "/resumen/", [1060, 260]),
        responder("Responder a Ex Libris", "n-resp", "={{ JSON.stringify({ respuesta: $json.output }) }}", [560, 0]),
    ]
    conexiones = {
        "Webhook": {"main": [[{"node": "Agente Ex Libris", "type": "main", "index": 0}]]},
        "Agente Ex Libris": {"main": [[{"node": "Responder a Ex Libris", "type": "main", "index": 0}]]},
        "Modelo": {"ai_languageModel": [[{"node": "Agente Ex Libris", "type": "ai_languageModel", "index": 0}]]},
        "Memoria": {"ai_memory": [[{"node": "Agente Ex Libris", "type": "ai_memory", "index": 0}]]},
    }
    for t in ("buscar_libros", "ver_libro", "libros_compartidos", "buscar_anotaciones", "resumen_biblioteca"):
        conexiones[t] = {"ai_tool": [[{"node": "Agente Ex Libris", "type": "ai_tool", "index": 0}]]}
    return {"name": "Ex Libris · Agente", "nodes": nodos, "connections": conexiones, "settings": {}, "pinData": {}}


for archivo, wf in (("exlibris-tareas.json", tareas(GEMINI)), ("exlibris-agente.json", agente(GEMINI)),
                    ("exlibris-tareas-ollama.json", tareas(OLLAMA)), ("exlibris-agente-ollama.json", agente(OLLAMA))):
    if "ollama" in archivo:
        wf["name"] += " (Ollama)"
    (AQUI / archivo).write_text(json.dumps(wf, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Generado", archivo)
