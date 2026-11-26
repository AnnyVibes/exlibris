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
| Éxito / confirmación | fucsia `#a21caf` (color de marca, a pedido de la autora) | ✓ |
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

## 7. Segunda ronda (comentarios de la autora)

- **Colores de acento**: el azul y el naranja del resumen no armonizaban con el violeta. Se usa una paleta **análoga**
  (colores vecinos en el círculo cromático): violeta `#7c3aed` (libros), rosa `#ec4899` (anotaciones) y fucsia
  `#c026d3` (préstamos). Se aplica también a las estadísticas y los gráficos.
- **Lenguaje**: «prestados ahora» → **«En préstamo»**, el término usado en bibliotecas, en el panel, el inicio, las
  insignias de las tapas y las estadísticas.
- **Menos ruido**: se quitó el saludo del inicio (no aportaba información) y el estado «Abandonado» (los libros que lo
  tenían pasan a «Por leer»).
- **Libro con portada**: tapa con esquinas redondeadas, bloque de páginas con contorno y cinta separadora, como en la
  referencia de librería. Si hay foto de portada, el cuerpo del libro usa la misma imagen difuminada, para que una tapa
  oscura no quede sobre una base de otro color.

## 8. Tercera ronda

- **Mensajes**: la confirmación usa fucsia (marca) y el error mantiene el rojo: el color de error es una convención que
  no conviene cambiar. Las confirmaciones se cierran solas a los 6 s y todas tienen botón «×»; los errores no se cierran
  solos para que dé tiempo a leerlos. Se respeta «reducir movimiento» del sistema.
- **Librero «Mueble»**: ancho máximo para conservar proporciones de mueble real. Los estantes vacíos muestran
  siluetas punteadas (indican qué va ahí) y una acción concreta en lugar de solo texto.
- **Géneros** pasa a ser una sección propia en la navegación lateral, con una tarjeta por género. En el celular se llega
  desde los filtros de Mi biblioteca (la barra inferior se mantiene en 5 accesos para no saturarla).

## 9. Cuarta ronda

- **Avisos**: en lugar de una barra arriba, una **ventana modal** centrada (ícono, título y botón «Aceptar»), porque la
  autora quiere que la persona confirme que vio el resultado. Se muestra solo cuando se **modifica** algo (guardar, editar,
  eliminar, compartir, devolver). Títulos claros según el caso: «¡Guardado con éxito!», «Eliminado con éxito» o
  «No se pudo completar». Se puede cerrar con teclado (Esc) y el foco va al botón.
- **Lenguaje**: «Compartidos» reemplaza a «Préstamos» en toda la app; los mensajes usan «Compartiste… con…».
- **Microcopy**: textos más cortos y directos: «Tu biblioteca» / «Escanea, anota y comparte tus libros.».
- **Login**: ilustración propia de librero (paleta lila/periwinkle) con una tarjeta translúcida para el lema; en el celular
  la ilustración queda como encabezado y el formulario debajo.
- **Consistencia**: los estados de lectura se ven como libros (igual que los géneros) y se quitaron las flechas «→» de los
  enlaces y el triángulo del enlace plegable.

## 10. Login: análisis de diseño gráfico

| Problema | Por qué molesta | Solución |
|---|---|---|
| 7 estantes llenos de libros | Patrón muy denso, la vista no descansa y compite con la tarjeta | 4 estantes, grupos cortos con espacio entre ellos |
| Todo igual de saturado | No hay punto focal; los gatos se pierden | Lomos suavizados hacia el lila del fondo; los gatos conservan su color y son el foco |
| Velo morado sobre todo el fondo | Apaga la ilustración y la vuelve turbia | Luz radial clara solo detrás de la tarjeta |
| Encabezado de vidrio difuminado | Manchas de color detrás del texto blanco → baja legibilidad | Tarjeta blanca sólida |
| Marca pequeña y a un lado | «Ex Libris» parecía una etiqueta, no el nombre del sitio | Marca centrada a 46 px, «Libris» con el degradado de marca y el subtítulo «Biblioteca personal» |
| Íconos en burbujas separadas | Más elementos sueltos, más ruido | Íconos dentro de los campos |
