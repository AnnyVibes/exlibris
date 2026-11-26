"""Genera la ilustración del login (panel izquierdo): un librero acogedor (lila/periwinkle) con dos gatos.

Uso (desde la raíz del proyecto):  python docs/generar_ilustracion.py
Los gatos son PNG con transparencia en docs/gatos/ y se incrustan en el SVG (un SVG usado como fondo
no puede cargar archivos externos).
"""
import base64
import io
import random
from pathlib import Path

from PIL import Image

GATOS = Path(__file__).resolve().parent / "gatos"

R = random.Random(7)
W, H = 760, 900
FONDO, FONDO2 = "#a9b1e6", "#9ea7df"
TABLA, TABLA_SOMBRA = "#dfe3fa", "#8d96d4"
LIBROS = ["#f4a7c0", "#ef8a6f", "#f7b267", "#3e8e6f", "#86cfae", "#8c6fd1", "#c7aef2",
          "#2f4b8f", "#e8607a", "#fbe3a1", "#f9f4ec", "#5aa9c9", "#f6c6d8"]
def suavizar(hexa, t=0.28, hacia=(201, 205, 239)):
    r, g, b = (int(hexa[i:i + 2], 16) for i in (1, 3, 5))
    return "#%02x%02x%02x" % tuple(round(c + (d - c) * t) for c, d in zip((r, g, b), hacia))


LIBROS = [suavizar(c, 0.12) for c in LIBROS]  # apenas suavizados: colores vivos pero armónicos
partes = []
add = partes.append


def lomo(x, base, w, h, c):
    y = base - h
    claro = c in ("#fbe3a1", "#f9f4ec", "#f6c6d8", "#86cfae", "#c7aef2")
    deco = "#7b5aa6" if claro else "#fff7ee"
    add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="2" fill="{c}"/>')
    add(f'<rect x="{x}" y="{y+5}" width="{w}" height="2" fill="{deco}" opacity=".7"/>')
    add(f'<rect x="{x}" y="{base-8}" width="{w}" height="2" fill="{deco}" opacity=".7"/>')
    cx = x + w / 2
    tipo = R.choice(["enredadera", "puntos", "rombo", "liso"])
    if tipo == "enredadera":
        add(f'<path d="M{cx} {y+14} V{base-14}" stroke="{deco}" stroke-width="1" opacity=".75"/>')
        for yy in range(int(y) + 18, int(base) - 16, 9):
            lado = 1 if (yy // 9) % 2 else -1
            add(f'<ellipse cx="{cx+lado*2.6}" cy="{yy}" rx="2.4" ry="1.2" fill="{deco}" opacity=".8" transform="rotate({lado*35} {cx+lado*2.6} {yy})"/>')
    elif tipo == "puntos":
        for yy in range(int(y) + 16, int(base) - 14, 10):
            add(f'<circle cx="{cx}" cy="{yy}" r="1.4" fill="{deco}" opacity=".85"/>')
    elif tipo == "rombo":
        my = (y + base) / 2
        add(f'<path d="M{cx} {my-7}l4 7-4 7-4-7z" fill="{deco}" opacity=".85"/>')


def grupo_libros(x, base, n):
    for _ in range(n):
        w = R.randint(13, 20); h = R.randint(68, 98)
        lomo(x, base, w, h, R.choice(LIBROS)); x += w + 1
    return x + 6


def pila(x, base, n=3):
    yy = base
    for _ in range(n):
        w = R.randint(58, 70); c = R.choice(LIBROS)
        add(f'<rect x="{x}" y="{yy-13}" width="{w}" height="13" rx="2" fill="{c}"/>')
        add(f'<rect x="{x+4}" y="{yy-9}" width="{w-8}" height="1.6" fill="#fff7ee" opacity=".7"/>')
        yy -= 13
    return x + 74, yy


def jarron_margaritas(x, base):
    cx = x + 26
    for i, (dx, dy) in enumerate([(-16, -58), (-4, -70), (10, -62), (18, -48), (-20, -44), (2, -50)]):
        add(f'<path d="M{cx} {base-30} Q{cx+dx/2} {base-40} {cx+dx} {base+dy+6}" stroke="#4f9a6c" stroke-width="1.6" fill="none"/>')
        for a in range(0, 360, 40):
            add(f'<ellipse cx="{cx+dx}" cy="{base+dy-4}" rx="2.2" ry="5" fill="#fffdf6" transform="rotate({a} {cx+dx} {base+dy})"/>')
        add(f'<circle cx="{cx+dx}" cy="{base+dy}" r="2.6" fill="#f6b73c"/>')
    add(f'<path d="M{cx-14} {base-34}h28l-3 8c6 4 8 10 8 16 0 6-6 10-19 10s-19-4-19-10c0-6 2-12 8-16z" fill="#f4a7c0"/>')
    add(f'<path d="M{cx-12} {base-14}h24" stroke="#fff" stroke-width="1.5" opacity=".7"/><path d="M{cx-14} {base-8}h28" stroke="#fff" stroke-width="1.5" opacity=".7"/>')
    return x + 60


def maceta_planta(x, base):
    cx = x + 24
    for ang in (-50, -25, 0, 25, 50, -10, 15):
        add(f'<path d="M{cx} {base-26} q{ang/3} -18 {ang/2} -30" stroke="#3e8e6f" stroke-width="1.6" fill="none"/>')
        add(f'<circle cx="{cx+ang/2}" cy="{base-58+abs(ang)/5}" r="6.5" fill="{R.choice(["#3e8e6f", "#4fa57c", "#2f7a5c"])}"/>')
    add(f'<path d="M{cx-18} {base-26}h36l-4 26h-28z" fill="#ef8a6f"/>')
    for yy in (base - 20, base - 13, base - 6):
        add(f'<path d="M{cx-15} {yy}h30" stroke="#f9d3c6" stroke-width="2"/>')
    return x + 56


def cuadro(x, base):
    y = base - 62
    add(f'<rect x="{x}" y="{y}" width="46" height="58" fill="#d9b77a"/><rect x="{x+5}" y="{y+5}" width="36" height="48" fill="#fff8ec"/>')
    cx, cy = x + 23, y + 24
    add(f'<path d="M{cx} {cy+6} V{y+48}" stroke="#4f9a6c" stroke-width="1.4"/><ellipse cx="{cx-5}" cy="{cy+16}" rx="5" ry="2.2" fill="#4f9a6c" transform="rotate(-30 {cx-5} {cy+16})"/>')
    color = R.choice(["#e8607a", "#5aa9c9", "#f6b73c"])
    for a in range(0, 360, 60):
        add(f'<ellipse cx="{cx}" cy="{cy-4}" rx="3.2" ry="5.5" fill="{color}" transform="rotate({a} {cx} {cy})"/>')
    add(f'<circle cx="{cx}" cy="{cy}" r="2.6" fill="#f6b73c"/>')
    return x + 56


def lampara(x, base):
    cx = x + 24
    add(f'<path d="M{cx-18} {base-62}h36l8 26h-52z" fill="#fde7ef"/>')
    for i in range(-14, 16, 6):
        add(f'<path d="M{cx+i} {base-61} l{i/5} 24" stroke="#f4a7c0" stroke-width="1.2"/>')
    add(f'<circle cx="{cx}" cy="{base-20}" r="13" fill="#f6b73c"/><rect x="{cx-10}" y="{base-8}" width="20" height="8" rx="2" fill="#e09b24"/>')
    return x + 58


def taza_sobre_libros(x, base):
    nx, top = pila(x, base, 2)
    cx = x + 30
    add(f'<path d="M{cx-12} {top-20}h24v12c0 6-5 8-12 8s-12-2-12-8z" fill="#e8607a"/>')
    add(f'<path d="M{cx+12} {top-16}c7 0 7 9 0 9" stroke="#e8607a" stroke-width="3" fill="none"/>')
    add(f'<circle cx="{cx}" cy="{top-12}" r="3" fill="#fff" opacity=".8"/>')
    return nx


def tulipanes(x, base):
    cx = x + 24
    for dx, dy, c in ((-10, -64, "#f4a7c0"), (0, -74, "#e8607a"), (11, -66, "#f6c6d8")):
        add(f'<path d="M{cx} {base-30} Q{cx+dx/2} {base-46} {cx+dx} {base+dy+10}" stroke="#4f9a6c" stroke-width="1.8" fill="none"/>')
        add(f'<path d="M{cx+dx-6} {base+dy}c0 8 3 12 6 12s6-4 6-12l-3 4-3-6-3 6z" fill="{c}"/>')
    add(f'<ellipse cx="{cx-9}" cy="{base-42}" rx="3" ry="9" fill="#4f9a6c" transform="rotate(-25 {cx-9} {base-42})"/>')
    add(f'<path d="M{cx-11} {base-32}h22c0 4-3 6-3 8 4 3 6 8 6 13 0 7-6 11-14 11s-14-4-14-11c0-5 2-10 6-13 0-2-3-4-3-8z" fill="#9ad3bc"/>')
    add(f'<path d="M{cx-6} {base-14}c3 -4 9 -4 12 0" stroke="#fff" stroke-width="1.5" fill="none"/>')
    return x + 54


def gato(x, base):
    cx = x + 30
    add(f'<path d="M{cx+20} {base-6}c14 0 16 -20 6 -24" stroke="#2b2540" stroke-width="5" fill="none" stroke-linecap="round"/>')
    add(f'<ellipse cx="{cx}" cy="{base-20}" rx="22" ry="20" fill="#2b2540"/>')
    add(f'<circle cx="{cx-4}" cy="{base-46}" r="14" fill="#2b2540"/>')
    add(f'<path d="M{cx-17} {base-52}l3 -14 8 9z M{cx+3} {base-55}l6 -12 4 13z" fill="#2b2540"/>')
    add(f'<ellipse cx="{cx-9}" cy="{base-47}" rx="2.4" ry="3" fill="#f6d55c"/><ellipse cx="{cx+1}" cy="{base-47}" rx="2.4" ry="3" fill="#f6d55c"/>')
    add(f'<path d="M{cx-6} {base-41}l2 2 2 -2" stroke="#f4a7c0" stroke-width="1.4" fill="none"/>')
    return x + 70


encima = []


def gato_img(nombre, alto, apoyo=1.0):
    """Reserva espacio en el estante y dibuja el gato encima (apoyo = fracción de la altura que queda sobre la tabla)."""
    def dibujar(x, base):
        im = Image.open(GATOS / f"{nombre}.png")
        ancho = round(im.width * alto / im.height)
        im = im.resize((ancho * 2, alto * 2), Image.LANCZOS)
        buf = io.BytesIO(); im.save(buf, "WEBP", quality=82)
        datos = base64.b64encode(buf.getvalue()).decode()
        y = base - alto * apoyo + 2
        encima.append(f'<image href="data:image/webp;base64,{datos}" x="{x}" y="{y:.1f}" width="{ancho}" height="{alto}"/>')
        return x + ancho + 8
    return dibujar


DECOS = [jarron_margaritas, maceta_planta, cuadro, lampara, taza_sobre_libros, tulipanes]
add(f'<rect width="{W}" height="{H}" fill="{FONDO}"/>')
# (fondo liso: sin rayas verticales para reducir ruido visual)

filas = [165, 345, 525, 705, 885]
# Dos gatos como punto focal (naranja sentado arriba a la izquierda, blanco y negro acostado abajo a la derecha):
# la vista entra por uno, recorre los estantes en diagonal y termina en el otro.
# «libros:N» = N libros; «aire:N» = N px vacíos; «hasta:N» = grupos con algo de aire hasta la posición N.
plan = [
    ["libros:4", jarron_margaritas, "libros:5", "aire:10", lampara, "libros:4"],
    [maceta_planta, "libros:3", "aire:8", gato_img("a0", 112), "aire:10", "libros:4", cuadro, "libros:3"],
    ["pila", "libros:5", taza_sobre_libros, "libros:4", tulipanes],
    ["libros:4", cuadro, "libros:3", "aire:14", gato_img("a1", 84, .66), "aire:6", "libros:3"],
    [jarron_margaritas, "libros:5", "aire:10", maceta_planta, "libros:4"],
]
for base, fila in zip(filas, plan):
    x = 22
    for item in fila:
        if x > W - 40:
            break
        if isinstance(item, str) and item.startswith("hasta:"):
            meta = int(item.split(":")[1])
            while x < meta - 40:
                x = grupo_libros(x, base, max(1, min(R.randint(2, 4), int((meta - x) // 18)))) + R.randint(26, 56)
            continue
        if isinstance(item, str) and item.startswith("aire:"):
            x += int(item.split(":")[1])
            continue
        if isinstance(item, str) and item.startswith("libros:"):
            x = grupo_libros(x, base, int(item.split(":")[1]))
            continue
        if item == "libros":
            restante = W - 22 - x
            n = R.randint(4, 7)
            if restante < 140:
                n = max(2, restante // 19)
            x = grupo_libros(x, base, n)
        elif item == "pila":
            x, _ = pila(x, base, 3)
        else:
            x = item(x, base) + 4
    while x < W - 40:
        n = max(1, min(R.randint(3, 5), int((W - 22 - x) // 18)))
        x = grupo_libros(x, base, n) + R.randint(12, 26)
    add(f'<rect x="0" y="{base}" width="{W}" height="7" fill="{TABLA}"/>')
    add(f'<rect x="0" y="{base+7}" width="{W}" height="3" fill="{TABLA_SOMBRA}" opacity=".6"/>')

partes.extend(encima)
svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid slice" '
       f'role="img" aria-label="Librero con libros de colores, plantas, flores y gatos">' + "".join(partes) + "</svg>")
open(Path(__file__).resolve().parent.parent / "biblioteca/static/biblioteca/img/librero-login.svg", "w").write(svg)
print(len(svg) // 1024, "KB")
