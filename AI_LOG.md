# AI Development Log · Ex Libris

Registro de los usos de IA que afectaron el desarrollo (mismo formato que el Proyecto 1 y 2).

**Autora:** Anllelina Varcasia · **Herramientas:** Claude (Claude Code, plan Pro) como agente de desarrollo.
La IA generativa *dentro* de la app (fase 2) usará un LLM gratuito (Gemini u Ollama) vía n8n.

## Leyenda de decisión humana
- ✅ **Aceptada** · 🟡 **Modificada** · ❌ **Rechazada** · 🔴 **Incorrecta** · ⏳ **Pendiente de revisión**

## Registro

| # | Fecha | Actividad | Herramienta | Qué se solicitó | Resultado | Decisión humana |
|---|---|---|---|---|---|---|
| 1 | 2026-11-25 | Definición del tema | Claude Code | ¿Es viable una app para escanear libros, reseñas, anotaciones y préstamos? | Viable, pero sin IA no cumplía el objetivo del proyecto; propuso agregar clasificación, resúmenes, borradores de reseña y un agente. Revisó los repos de los labs y proyectos para alinear el stack (Django, n8n del Lab 14, ODD/SDD del Proyecto 2) | ✅ Se aceptó y se redactó el tema con alcance explícito |
| 2 | 2026-11-25 | Costos | Claude Code | ¿Puedo usar Claude dentro de la app? | Aclaró que Claude Pro no incluye la API (se paga aparte); recomendó Claude para desarrollar y Gemini (capa gratuita) u Ollama dentro de la app; n8n autoinstalado porque n8n Cloud es de pago | ✅ Decisión: costo $0 además de Claude Pro |
| 3 | 2026-11-25 | Diseño | Claude Code | Inspirarse en un diseño de Figma Sites y una imagen de Pinterest | El sitio de Figma no fue accesible desde el entorno de la IA; se usó solo la imagen de Pinterest (tres columnas, rosa pastel + verde, tarjetas redondeadas) y se dibujó una ilustración propia en SVG (estante en arco con flores y alas) | ⏳ Revisar si el diseño de Figma aporta algo más |
| 4 | 2026-11-25 | Fase 1 (código) | Claude Code | Crear el proyecto | Django con modelos Libro, Resena, Anotacion y Prestamo; servicios de ISBN, catálogo, préstamos y estadísticas; escáner con html5-qrcode; 11 vistas; diseño adaptable; comando `datos_demo`; 44 pruebas en verde; CI | ⏳ Pendiente de revisión y prueba manual en el celular |
| 5 | 2026-11-25 | Pruebas | Claude Code | (Dentro de la fase 1) ejecutar las pruebas | 1 de 44 falló: la prueba de búsqueda de anotaciones fallaba porque el panel lateral muestra la última anotación en todas las páginas. Era la prueba la que estaba mal; se cambió para revisar el contexto de la vista. También se corrigió que el buscador superior se rellenaba con la búsqueda de anotaciones | 🔴🟡 Error de la IA en la prueba, detectado por la propia ejecución |
| 6 | 2026-11-25 | QA visual | Claude Code | (Dentro de la fase 1) capturas de escritorio y celular con Playwright | Detectó 4 detalles: fondo blanco de las columnas cortado en páginas largas, 1 px de desbordamiento horizontal en el celular, lista de préstamos encimada con «Última anotación» y portada vacía en «Leyendo ahora». Corregidos | ✅ |
| 7 | 2026-11-25 | Limitación | Claude Code | Verificar Open Library y el CDN | El entorno de la IA no tiene salida a esos dominios: el catálogo se probó con respuestas simuladas y el escáner no se probó con cámara real | ⏳ Probar en local: escanear un libro real |
| 8 | 2026-11-25 | Rediseño | Claude Code | Cambiar la tipografía a una como la de una app de diario (sistema/Segoe UI), paleta blanco + lila con colores que combinen y estilo «librero» tomado de un dashboard de librería | Tipografía del sistema; paleta lila con acentos de lomo de libro (coral, azul, verde, mostaza); libros dibujados con páginas y cinta, estantes, categorías como libros, pila de libros en el banner; anotaciones como tarjetas de diario (título, texto, etiquetas, fecha); barra inferior móvil con el activo en lila. El archivo de Figma de la Comunidad no se pudo leer (hay que duplicarlo en Drafts); se usaron las capturas | ⏳ Pendiente de revisión |
| 9 | 2026-11-25 | QA visual | Claude Code | (Dentro del rediseño) capturas con Playwright | Detectó libros enormes en «Agregados recientemente», desbordamiento horizontal en el celular por títulos largos (columnas `1fr` sin `minmax(0, …)`) y estrellas sin color en la ficha. Corregidos. 44/44 pruebas en verde | ✅ |
