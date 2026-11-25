# Reglas de negocio

| ID | Regla | Dónde se aplica | Pruebas |
|---|---|---|---|
| BR-01 | El ISBN se guarda siempre como ISBN-13 válido; un ISBN-10 se convierte. Un EAN que no empiece con 978/979 no es ISBN. | `services/isbn.py`, `LibroForm` | `test_isbn.py`, `test_libros.py` |
| BR-02 | Un ISBN no se repite en la biblioteca de una persona (sí en la de otra). Escanear un libro que ya tengo abre su ficha. | Restricción `isbn_unico_por_usuario`, `LibroForm`, `libro_nuevo` | `test_libros.py` |
| BR-03 | Un libro tiene como máximo un préstamo sin devolver. | Restricción `un_prestamo_activo_por_libro`, `services/prestamos.py` | `test_prestamos.py` |
| BR-04 | La fecha acordada de devolución no puede estar en el pasado al prestar; un préstamo está vencido si pasó esa fecha sin devolverse. | `prestar`, `Prestamo.vencido` | `test_prestamos.py` |
| BR-05 | La página actual no puede superar las páginas del libro; al marcarlo leído, el progreso es 100 %. | `ProgresoForm`, `progreso_actualizar` | `test_libros.py` |
| BR-06 | Una sola reseña por libro, calificación de 1 a 5. Volver a guardar la edita. | `Resena` (OneToOne), `ResenaForm` | `test_resenas_anotaciones.py` |
| BR-07 | Nadie ve, edita ni borra libros, anotaciones o préstamos de otra persona. | Consultas filtradas por propietario en todas las vistas | `test_libros.py`, `test_resenas_anotaciones.py`, `test_prestamos.py` |
| BR-08 | Si el catálogo no responde o no conoce el ISBN, el libro se puede completar a mano. | `services/catalogo.py`, `libro_nuevo` | `test_catalogo.py`, `test_libros.py` |
