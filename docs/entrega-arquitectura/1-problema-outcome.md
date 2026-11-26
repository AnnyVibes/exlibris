# Ex Libris · Biblioteca personal con IA

**Proyecto final · Tópicos Especiales II** — Anllelina Varcasia

## 1. ¿Qué resultado queremos conseguir para el usuario?

### Problema

Las personas que tienen muchos libros en papel no llevan un control de su biblioteca:

- **No recuerdan qué libros tienen**, y a veces compran uno que ya tenían.
- **Registrar un libro a mano es lento**: hay que copiar título, autor, editorial, páginas…
- **Las ideas que surgen al leer se pierden** en papelitos, márgenes o notas del celular sin orden.
- **Olvidan qué opinaron** de cada libro y cuáles ya terminaron.
- **Los libros que comparten no vuelven**: no saben a quién se los dieron ni desde cuándo.

### Usuario

Una **persona lectora** que quiere organizar su biblioteca personal desde el **celular** (para escanear los libros) o la **computadora**, sin pagar ni instalar una aplicación.

### Outcome (resultado esperado)

> Que la persona tenga **su biblioteca organizada en un solo lugar**, pueda **registrar un libro en segundos escaneando su código de barras**, **guarde y encuentre sus ideas y reseñas**, **sepa siempre quién tiene sus libros**, y que la **IA le ahorre trabajo** clasificando, resumiendo y respondiendo preguntas sobre su biblioteca.

### Resultados medibles

| ID | Resultado para el usuario | Cómo se mide |
|---|---|---|
| OC-01 | Registrar un libro toma **menos de 15 segundos** escaneando su código ISBN con la cámara | Tiempo desde abrir el escáner hasta guardar el libro |
| OC-02 | Los datos del libro (título, autor, portada, páginas, género) **se completan solos** | % de libros escaneados que no necesitan escribir datos a mano |
| OC-03 | Las ideas que surgen al leer quedan **guardadas por libro, contadas y se pueden buscar** | Conteo de anotaciones por libro y búsqueda |
| OC-04 | Cada libro leído tiene **reseña y calificación** | Libros leídos con reseña / total de leídos |
| OC-05 | La persona sabe **en todo momento qué libros compartió, con quién, desde hace cuántos días** y cuáles debían volver | Página «Compartidos» con conteo de días y fecha de devolución |
| OC-06 | La IA **ahorra trabajo**: clasifica el género, resume las anotaciones, propone un borrador de reseña y responde preguntas como «¿a quién le presté Rayuela?» | Tareas resueltas por la IA sin intervención manual (fase 2) |
| OC-07 | Se usa **desde el celular o la PC, sin costo** | Funciona en el navegador del celular; costo $0 (herramientas libres y capas gratuitas) |

### Alcance

**Incluye:** escaneo de ISBN con la cámara e ingreso manual, datos automáticos desde catálogos públicos, biblioteca con librero personalizable, filtros por estado y género, progreso de lectura, reseñas, anotaciones con conteo, libros compartidos con conteo de días, estadísticas e IA generativa (n8n + LLM gratuito).

**No incluye:** aplicación nativa publicada en tiendas, funciones sociales (seguir o compartir con otras cuentas) ni compra o venta de libros.
