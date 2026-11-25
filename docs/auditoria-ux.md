# Auditoría UX/UI · Ex Libris

Fecha: 2026-11-25 · Revisión del rediseño «librero» (blanco y lila) antes de seguir con la fase 2.

## 1. Contraste de colores (WCAG 2.1 AA)

Texto normal necesita **4.5:1**; texto grande y elementos gráficos (íconos, bordes), **3:1**.

| Elemento | Antes | Contraste | Después | Contraste |
|---|---|---|---|---|
| Botón principal (texto blanco) | degradado lila `#a78bfa → #c084fc` | **2.6–2.7 ❌** | violeta sólido `#7c3aed` (hover `#6d28d9`) | **5.7 / 7.1 ✅** |
| Botón «Buscar» y «Escanear» del menú | degradado arcoíris (termina en mostaza `#f4b942`) | **1.8 ❌** en el extremo amarillo | **Se mantiene el degradado** por decisión de la autora (es parte de la identidad visual) | ⚠️ riesgo aceptado |
| Botón «Escanear libro» / «Prestar» | coral `#f07167` | **2.9 ❌** | violeta sólido (una sola acción principal) | **5.7 ✅** |
| Autor del libro | coral `#f07167` sobre blanco | **2.9 ❌** | `#c2410c` | **5.2 ✅** |
| Estrellas | mostaza `#f4b942` | **1.8 ❌** (ícono) | ámbar `#d97706` | **3.2 ✅** |
| Botón suave (lila) | `#7e22ce` sobre `#f3e8ff` | 5.9 ✅ | `#6d28d9` sobre `#f3e8ff` | 6.0 ✅ |
| Texto secundario | `#6b7280` sobre `#f6f7ff` | 4.5 ✅ | sin cambio | 4.5 ✅ |

**Decisión de diseño:** el degradado arcoíris se conserva solo en esos dos botones como elemento de marca.
Son botones con una palabra corta, en negrita, en lugares fijos y con ícono (Escanear) o junto a una lupa (Buscar),
lo que reduce el impacto del menor contraste. El resto de botones usa el violeta sólido.

Los colores de lomo de libro (coral, azul, verde, rosa, mostaza) se mantienen **solo como decoración**
(tapas, íconos, ilustraciones), nunca como fondo de texto pequeño ni para comunicar información por sí solos.

## 2. Jerarquía de botones

Problema: casi todos los botones eran del mismo color llamativo (lila, coral o arcoíris), así que no se sabía cuál era la acción principal.

| Nivel | Uso | Estilo |
|---|---|---|
| Primario | **una** acción principal por pantalla o tarjeta (Guardar, Escanear, Prestar) | violeta sólido, texto blanco |
| Secundario | alternativa a la principal (Agregar a mano, Cancelar, Buscar ISBN, Editar) | blanco con borde lila |
| Suave | acciones de poco peso (Ver todo, Quitar filtros) | fondo lila claro |
| Peligro | acciones destructivas (Eliminar) | borde y texto rojo, siempre con confirmación |
| Éxito | confirmar algo positivo (Ya me lo devolvió) | verde suave |

Además: alto mínimo de **44 px** (36 px los compactos) para tocar cómodo en el celular, y **foco visible**
(anillo lila) al navegar con teclado.

## 3. Mensajes del sistema

Antes los mensajes solo se distinguían por el color de fondo. Ahora tienen **ícono + barra lateral de color + texto oscuro**,
así no dependen solo del color (útil para daltonismo):

| Tipo | Color | Ícono |
|---|---|---|
| Éxito | verde `#15803d` | ✓ |
| Error | rojo `#b42318` | ⓘ alerta |
| Aviso | ámbar `#92400e` | ⓘ |
| Información | violeta `#6d28d9` | ⓘ |

Se anuncian a lectores de pantalla con `role="status"`.

## 4. Arquitectura de la información: categorías

Problema: la página de inicio mostraba todos los géneros y estados como libros, mezclando navegación con resumen.

- **Inicio** queda como resumen: saludo, banner con las dos acciones clave, contadores, «Leyendo ahora» y los recientes.
- **Mi biblioteca** concentra los filtros, en dos bloques separados y combinables:
  - **Estado de lectura**: pestañas con contador (Todos, Por leer, Leyendo, Leído, Abandonado).
  - **Géneros**: estantes con los géneros que realmente tienes, con contador. Tocar uno activo lo quita.
- Los filtros se combinan con la búsqueda (p. ej. «Leído» + «Novela»).
- En el celular, cada bloque es una sola fila deslizable; con la biblioteca vacía no se muestran filtros.

## 5. Formularios

- **Género**: lista cerrada de 29 opciones en lugar de texto libre (evita «novela», «Novela», «novelas»…).
  Al escanear, la categoría del catálogo (en inglés) se traduce sola a la lista; si no se puede, queda para elegir.
- **Portada**: botón «Subir imagen» con vista previa inmediata, validación (JPG/PNG/WEBP, 5 MB) y reducción automática
  a 900 px. En el celular permite tomar una foto. El enlace de imagen queda como opción secundaria (plegada).

## 6. Estados vacíos

La cuenta demo empieza vacía, así que se cuidaron los estados vacíos: cada uno explica qué pasa y ofrece la acción para salir
de él (p. ej. «Tu estante está vacío» → **Escanear**).
