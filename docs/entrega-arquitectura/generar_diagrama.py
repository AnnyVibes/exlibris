"""Genera el diagrama de arquitectura de alto nivel de Ex Libris en dos formatos:

- arquitectura.drawio  → se abre y edita en https://app.diagrams.net
- arquitectura.svg     → se convierte a PNG para entregar

Uso:  python docs/entrega-arquitectura/generar_diagrama.py
"""

from html import escape
from pathlib import Path

AQUI = Path(__file__).resolve().parent
W, H = 1600, 1030

# Paleta del proyecto
COL = {
    "usuario": ("#ede9fe", "#7c3aed"),
    "acceso": ("#f5f3ff", "#8b5cf6"),
    "django": ("#ffffff", "#7c3aed"),
    "capa": ("#faf5ff", "#a78bfa"),
    "servicio": ("#f3e8ff", "#a855f7"),
    "datos": ("#fdf4ff", "#c026d3"),
    "externo": ("#fef3c7", "#d97706"),
    "ia": ("#fce7f3", "#db2777"),
    "dev": ("#ecfdf5", "#059669"),
}

# id: (x, y, w, h, texto (primera línea en negrita), estilo, discontinuo)
CONTENEDORES = {
    "g_usuario": (30, 110, 230, 430, "Usuario", "usuario", False),
    "g_acceso": (290, 110, 230, 430, "Acceso (HTTPS)", "acceso", False),
    "g_django": (550, 110, 560, 610, "Ex Libris · Django 5.2 (Python)", "django", False),
    "g_apis": (1150, 110, 420, 200, "APIs públicas de libros (gratis, sin key)", "externo", False),
    "g_ia": (1150, 340, 420, 380, "IA generativa · fase 2 (n8n)", "ia", False),
    "g_dev": (30, 760, 1540, 190, "Ciclo de desarrollo asistido por IA", "dev", False),
}
NODOS = {
    "persona": (50, 160, 190, 70, "Persona lectora\nsu biblioteca personal", "usuario", False),
    "celular": (50, 260, 190, 90, "Celular\ncámara: escanea el ISBN", "usuario", False),
    "pc": (50, 380, 190, 90, "Computadora\nnavegador web", "usuario", False),
    "tunel": (310, 170, 190, 100, "Cloudflare Tunnel\nHTTPS para usar la\ncámara del celular", "acceso", False),
    "deploy": (310, 300, 190, 90, "PythonAnywhere\ndespliegue final", "acceso", True),
    "local": (310, 420, 190, 80, "Servidor local\n127.0.0.1:8000", "acceso", False),
    "ui": (570, 150, 520, 80, "Interfaz web (adaptable a celular)\nPlantillas Django · CSS propio · html5-qrcode (escáner) · Chart.js", "capa", False),
    "vistas": (570, 250, 520, 70, "Vistas y URLs\nInicio de sesión · CSRF · cada persona ve solo sus libros", "capa", False),
    "s_isbn": (570, 345, 96, 75, "ISBN\nvalidar", "servicio", False),
    "s_comp": (676, 345, 96, 75, "Compartidos\ndías", "servicio", False),
    "s_est": (782, 345, 96, 75, "Estadísticas", "servicio", False),
    "s_ia": (888, 345, 96, 75, "Cliente IA\nvalida JSON", "servicio", False),
    "s_cat": (994, 345, 96, 75, "Catálogo\nISBN → datos", "servicio", False),
    "modelos": (570, 445, 520, 70, "Modelos (ORM de Django)\nLibro · Reseña · Anotación · Compartido · Perfil · Librero", "capa", False),
    "sqlite": (570, 610, 160, 85, "SQLite\nbase de datos", "datos", False),
    "media": (750, 610, 160, 85, "Media\nportadas subidas\n(Pillow)", "datos", False),
    "api": (930, 610, 160, 85, "API /api/ia/\ntoken firmado · consulta\ny agregar libro", "datos", False),
    "openlib": (1170, 170, 180, 90, "Open Library\ndatos y portada", "externo", False),
    "gbooks": (1370, 170, 180, 90, "Google Books\nrespaldo", "externo", False),
    "n8n": (1170, 385, 380, 66, "n8n en Docker (gratis)\n2 webhooks: tareas y agente", "ia", False),
    "ia_agente": (1170, 468, 120, 58, "Agente\nchat + agregar", "ia", False),
    "ia_clas": (1300, 468, 120, 58, "Clasificar\ngénero + etiquetas", "ia", False),
    "ia_comp": (1430, 468, 120, 58, "Completar\ndatos del libro", "ia", False),
    "ia_res": (1170, 534, 120, 58, "Resumir\nanotaciones", "ia", False),
    "ia_borr": (1300, 534, 120, 58, "Borrador\nde reseña", "ia", False),
    "ia_sin": (1430, 534, 120, 58, "Sinopsis\nsin spoilers", "ia", False),
    "llm": (1170, 615, 380, 90, "LLM gratuito\nGoogle Gemini 3.5 Flash (capa gratuita)\no Ollama (modelo local)", "ia", False),
    "spec": (60, 815, 220, 100, "Especificación\nODD / SDD (specs/)\nrequisitos y reglas", "dev", False),
    "claude": (370, 815, 220, 100, "Claude Code\nagente de desarrollo\n(plan Pro)", "dev", False),
    "github": (680, 815, 220, 100, "GitHub\nrepositorio exlibris", "dev", False),
    "ci": (990, 815, 220, 100, "GitHub Actions\nCI: 165 pruebas\nen cada push", "dev", False),
    "log": (1300, 815, 240, 100, "AI_LOG.md\nrevisión humana: qué se\naceptó, modificó o rechazó", "dev", False),
}
# (origen, destino, etiqueta, puntos de la línea en el SVG, discontinua)
FLECHAS = [
    ("celular", "tunel", "HTTPS", [(240, 305), (270, 305), (270, 220), (310, 220)], False),
    ("pc", "local", "", [(240, 440), (275, 440), (275, 460), (310, 460)], False),
    ("pc", "deploy", "", [(240, 410), (285, 410), (285, 345), (310, 345)], True),
    ("tunel", "ui", "", [(500, 220), (530, 220), (530, 190), (570, 190)], False),
    ("local", "ui", "", [(500, 460), (535, 460), (535, 200), (570, 200)], False),
    ("deploy", "ui", "", [(500, 345), (540, 345), (540, 210), (570, 210)], True),
    ("ui", "vistas", "", [(830, 230), (830, 250)], False),
    ("vistas", "s_est", "", [(830, 320), (830, 345)], False),
    ("s_est", "modelos", "", [(830, 420), (830, 445)], False),
    ("modelos", "sqlite", "", [(650, 515), (650, 610)], False),
    ("modelos", "media", "", [(830, 515), (830, 610)], False),
    ("s_cat", "g_apis", "HTTPS · JSON por ISBN", [(1090, 382), (1115, 382), (1115, 215), (1150, 215)], False),
    ("vistas", "n8n", "webhook", [(1090, 285), (1135, 285), (1135, 425), (1170, 425)], False),
    ("n8n", "ia_clas", "", [(1360, 451), (1360, 468)], False),
    ("ia_borr", "llm", "prompt / respuesta", [(1360, 592), (1360, 615)], False),
    ("ia_agente", "api", "herramientas HTTP", [(1170, 497), (1130, 497), (1130, 652), (1090, 652)], False),
    ("spec", "claude", "guía", [(280, 865), (370, 865)], False),
    ("claude", "github", "commits", [(590, 865), (680, 865)], False),
    ("github", "ci", "push", [(900, 865), (990, 865)], False),
    ("ci", "log", "evidencia", [(1210, 865), (1300, 865)], False),
    ("github", "g_django", "código", [(790, 815), (790, 720)], False),
]


POS_ETIQUETA = {
    "HTTPS": (270, 262),
    "HTTPS · JSON por ISBN": (1360, 290),
    "webhook": (1236, 326),
    "herramientas HTTP": (1072, 585),
    "prompt / respuesta": (1452, 609),
}


def lineas(texto):
    return texto.split("\n")


# ------------------------------------------------------------------ SVG
def svg():
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         'font-family="Segoe UI, system-ui, -apple-system, Roboto, Arial, sans-serif">',
         '<defs><marker id="f" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
         '<path d="M0 0 10 5 0 10z" fill="#5b4a8a"/></marker></defs>',
         f'<rect width="{W}" height="{H}" fill="#fbfaff"/>',
         '<text x="30" y="52" font-size="30" font-weight="800" fill="#3b2a63">Ex Libris · Arquitectura de alto nivel</text>',
         '<text x="30" y="82" font-size="16" fill="#6b7280">Biblioteca personal con IA — escanea, anota y comparte tus libros</text>']
    for _, (x, y, w, h, t, est, disc) in CONTENEDORES.items():
        fondo, borde = COL[est]
        guion = ' stroke-dasharray="8 6"' if disc else ""
        p.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="18" fill="{fondo}" fill-opacity=".55" stroke="{borde}" stroke-width="2"{guion}/>')
        p.append(f'<text x="{x + 16}" y="{y + 26}" font-size="16" font-weight="700" fill="{borde}">{escape(t)}</text>')
    for _, (x, y, w, h, t, est, disc) in NODOS.items():
        fondo, borde = COL[est]
        guion = ' stroke-dasharray="6 5"' if disc else ""
        p.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{fondo}" stroke="{borde}" stroke-width="1.6"{guion}/>')
        ls = lineas(t)
        alto = 20 + (len(ls) - 1) * 17
        y0 = y + h / 2 - alto / 2 + 14
        for i, linea in enumerate(ls):
            if i == 0:
                p.append(f'<text x="{x + w / 2}" y="{y0}" font-size="15" font-weight="700" fill="#1f2937" text-anchor="middle">{escape(linea)}</text>')
            else:
                p.append(f'<text x="{x + w / 2}" y="{y0 + 4 + i * 17}" font-size="12.5" fill="#4b5563" text-anchor="middle">{escape(linea)}</text>')
    etiquetas = []
    for o, d, et, pts, disc in FLECHAS:
        guion = ' stroke-dasharray="7 5"' if disc else ""
        camino = " ".join(f"{x},{y}" for x, y in pts)
        p.append(f'<polyline points="{camino}" fill="none" stroke="#5b4a8a" stroke-width="2"{guion} marker-end="url(#f)"/>')
        if et in POS_ETIQUETA:
            ex, ey = POS_ETIQUETA[et]
            ancho = len(et) * 7 + 12
            etiquetas.append(f'<rect x="{ex - ancho / 2}" y="{ey - 14}" width="{ancho}" height="20" rx="6" fill="#fff" stroke="#e9e3fb"/>')
            etiquetas.append(f'<text x="{ex}" y="{ey + 1}" font-size="12" fill="#3b2a63" text-anchor="middle">{escape(et)}</text>')
        elif et:
            (x1, y1), (x2, y2) = pts[len(pts) // 2 - 1], pts[len(pts) // 2]
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            ancho = len(et) * 7 + 12
            if x1 == x2:  # tramo vertical: etiqueta a la derecha
                etiquetas.append(f'<rect x="{mx + 6}" y="{my - 11}" width="{ancho}" height="20" rx="6" fill="#fff" stroke="#e9e3fb"/>')
                etiquetas.append(f'<text x="{mx + 12}" y="{my + 4}" font-size="12" fill="#3b2a63">{escape(et)}</text>')
            else:
                etiquetas.append(f'<rect x="{mx - ancho / 2}" y="{my - 22}" width="{ancho}" height="20" rx="6" fill="#fff" stroke="#e9e3fb"/>')
                etiquetas.append(f'<text x="{mx}" y="{my - 7}" font-size="12" fill="#3b2a63" text-anchor="middle">{escape(et)}</text>')
    p.extend(etiquetas)
    # Leyenda
    ly = 985
    p.append(f'<line x1="30" y1="{ly}" x2="80" y2="{ly}" stroke="#5b4a8a" stroke-width="2" marker-end="url(#f)"/>')
    p.append(f'<text x="90" y="{ly + 5}" font-size="14" fill="#374151">Implementado</text>')
    p.append(f'<line x1="270" y1="{ly}" x2="320" y2="{ly}" stroke="#5b4a8a" stroke-width="2" stroke-dasharray="7 5" marker-end="url(#f)"/>')
    p.append(f'<text x="330" y="{ly + 5}" font-size="14" fill="#374151">Planificado (despliegue)</text>')
    p.append(f'<text x="{W - 30}" y="{ly + 5}" font-size="14" fill="#6b7280" text-anchor="end">Costo total: $0 · software libre y capas gratuitas</text>')
    p.append("</svg>")
    return "\n".join(p)


# ------------------------------------------------------------------ draw.io
def drawio():
    celdas = ['<mxCell id="0"/>', '<mxCell id="1" parent="0"/>']

    def valor(t):
        ls = lineas(t)
        html = f"<b>{escape(ls[0])}</b>" + "".join(f"<br><font style='font-size:11px'>{escape(l)}</font>" for l in ls[1:])
        return escape(html, quote=True)

    for cid, (x, y, w, h, t, est, disc) in CONTENEDORES.items():
        fondo, borde = COL[est]
        estilo = (f"rounded=1;arcSize=6;whiteSpace=wrap;html=1;fillColor={fondo};strokeColor={borde};strokeWidth=2;"
                  f"verticalAlign=top;align=left;spacingLeft=12;spacingTop=6;fontStyle=1;fontColor={borde};fontSize=14;"
                  + ("dashed=1;" if disc else ""))
        celdas.append(f'<mxCell id="{cid}" value="{escape(t, quote=True)}" style="{estilo}" vertex="1" parent="1">'
                      f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')
    for cid, (x, y, w, h, t, est, disc) in NODOS.items():
        fondo, borde = COL[est]
        forma = "shape=cylinder3;boundedLbl=1;size=10;" if cid == "sqlite" else "rounded=1;"
        estilo = (f"{forma}whiteSpace=wrap;html=1;fillColor={fondo};strokeColor={borde};fontColor=#1f2937;fontSize=13;"
                  + ("dashed=1;" if disc else ""))
        celdas.append(f'<mxCell id="{cid}" value="{valor(t)}" style="{estilo}" vertex="1" parent="1">'
                      f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')
    for i, (o, d, et, pts, disc) in enumerate(FLECHAS):
        estilo = ("edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;strokeColor=#5b4a8a;strokeWidth=2;endArrow=block;"
                  "endFill=1;fontSize=11;labelBackgroundColor=#ffffff;" + ("dashed=1;" if disc else ""))
        puntos = "".join(f'<mxPoint x="{x}" y="{y}"/>' for x, y in pts[1:-1])
        celdas.append(f'<mxCell id="e{i}" value="{escape(et, quote=True)}" style="{estilo}" edge="1" parent="1" source="{o}" target="{d}">'
                      f'<mxGeometry relative="1" as="geometry"><Array as="points">{puntos}</Array></mxGeometry></mxCell>')
    celdas.append('<mxCell id="titulo" value="&lt;b style=&quot;font-size:24px&quot;&gt;Ex Libris · Arquitectura de alto nivel&lt;/b&gt;&lt;br&gt;Biblioteca personal con IA" '
                  'style="text;html=1;align=left;verticalAlign=top;fontColor=#3b2a63;" vertex="1" parent="1">'
                  '<mxGeometry x="30" y="25" width="700" height="70" as="geometry"/></mxCell>')
    celdas.append('<mxCell id="leyenda" value="Línea continua: implementado · Línea discontinua: planificado (despliegue) · Costo total: $0" '
                  'style="text;html=1;align=left;fontColor=#374151;fontSize=13;" vertex="1" parent="1">'
                  '<mxGeometry x="30" y="970" width="900" height="30" as="geometry"/></mxCell>')
    modelo = (f'<mxGraphModel dx="1600" dy="1030" grid="1" gridSize="10" page="1" pageWidth="{W}" pageHeight="{H}" background="#fbfaff">'
              f'<root>{"".join(celdas)}</root></mxGraphModel>')
    return f'<mxfile host="app.diagrams.net"><diagram name="Arquitectura Ex Libris" id="exlibris">{modelo}</diagram></mxfile>'


(AQUI / "arquitectura.svg").write_text(svg(), encoding="utf-8")
(AQUI / "arquitectura.drawio").write_text(drawio(), encoding="utf-8")
print("Generados arquitectura.svg y arquitectura.drawio")
