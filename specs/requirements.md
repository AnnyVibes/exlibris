# Requisitos

Versión 0.1. Estado: ✅ implementado en la fase 1 · ⏳ pendiente.

## Funcionales
| ID | Requisito | Estado |
|---|---|---|
| RF-01 | Registro, inicio y cierre de sesión. Cada persona ve solo su biblioteca. | ✅ |
| RF-02 | Escanear el código de barras (EAN-13/ISBN) con la cámara del celular desde el navegador. | ✅ |
| RF-03 | Escribir el ISBN a mano (ISBN-10 o ISBN-13, con o sin guiones). | ✅ |
| RF-04 | Con el ISBN, buscar título, autores, editorial, año, páginas, portada, descripción y género en Open Library y, para lo que falte, Google Books. | ✅ |
| RF-05 | Agregar un libro sin ISBN o que no esté en el catálogo, completando los datos a mano. El género se elige de una lista. | ✅ |
| RF-06 | Ver la biblioteca como estante, buscar por título/autor/ISBN y filtrar por estado y por género (combinables). | ✅ |
| RF-06b | Subir una imagen propia como portada (o usar un enlace), con vista previa. | ✅ |
| RF-06d | Sección «Géneros» con una tarjeta por género (cantidad, leídos y portadas) que lleva a la biblioteca filtrada. | ✅ |
| RF-06c | Ver la biblioteca como librero (estantes por estado) o como lista; personalizar el diseño (repisas o mueble) y el color, guardado en la cuenta. | ✅ |
| RF-07 | Estado de lectura (por leer, leyendo, leído) y página actual con porcentaje. | ✅ |
| RF-08 | Una reseña por libro con calificación de 1 a 5 estrellas. | ✅ |
| RF-09 | Anotaciones por libro (texto y página opcional), con conteo por libro y búsqueda global. | ✅ |
| RF-10 | Compartidos (préstamos): con quién, contacto, fecha, fecha acordada, devolución e historial. | ✅ |
| RF-11 | Panel de inicio y estadísticas (totales, por estado, por género, páginas leídas, calificación media, libros con más anotaciones). | ✅ |
| RF-12 | IA: sugerir el género (de la lista) y etiquetas de un libro. | ✅ |
| RF-13 | IA: resumir las anotaciones de un libro (se guarda con fecha). | ✅ |
| RF-14 | IA: borrador de reseña a partir de las anotaciones y la calificación (editable antes de guardar). | ✅ |
| RF-16 | IA: el asistente agrega un libro a partir del título y el autor, buscando su ISBN y datos en los catálogos. | ✅ |
| RF-15 | IA: agente que responde preguntas en lenguaje natural sobre la biblioteca y los compartidos, con herramientas que consultan la API. | ✅ |

## No funcionales
| ID | Requisito |
|---|---|
| RNF-01 | Costo $0: software libre, APIs públicas sin key y LLM gratuito (Gemini, capa gratuita, u Ollama local). |
| RNF-02 | Usable desde el celular (diseño adaptable, navegación inferior, sin desbordamiento horizontal). |
| RNF-03 | La cámara requiere HTTPS: en el celular se usa un túnel (Cloudflare Tunnel) sobre el servidor local. |
| RNF-04 | Toda vista con datos exige sesión y filtra por propietario (404 si el recurso es de otra persona). |
| RNF-05 | Pruebas automatizadas en CI (GitHub Actions) antes de integrar. |
| RNF-06 | Accesibilidad: contraste WCAG AA en texto y botones, foco visible, objetivos táctiles de 44 px (ver `docs/auditoria-ux.md`). |

## Fuera de alcance
App nativa en tiendas, funciones sociales (compartir, seguir), compra/venta de libros.
