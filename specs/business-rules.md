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
| BR-09 | El género pertenece a una lista cerrada; la categoría del catálogo se traduce a esa lista o queda vacía. | `services/generos.py`, `Libro.genero` (choices), migración 0002 | `test_generos.py`, `test_catalogo.py` |
| BR-10 | La portada subida debe ser JPG, PNG o WEBP de hasta 5 MB; se reduce a 900 px y tiene prioridad sobre el enlace. Al cambiarla, quitarla o borrar el libro se elimina el archivo anterior. | `LibroForm.clean_portada`, `libro_editar`, `libro_eliminar` | `test_portadas.py` |
| BR-11 | La IA solo sugiere: el género sugerido debe pertenecer a la lista y la persona lo confirma; el borrador de reseña no se guarda sin pulsar «Guardar». | `services/ia.py`, `ia_clasificar`, `ia_resena` | `test_ia.py` |
| BR-12 | El agente solo lee la biblioteca de quien pregunta, con un token firmado que caduca en 15 minutos; la API es de solo lectura. | `api_ia.py`, `services/ia.token_para` | `test_ia.py` |
| BR-13 | Si n8n o el LLM no responden, la app sigue funcionando y lo informa; un resumen anterior no se borra. | `services/ia._llamar`, `ia_resumir` | `test_ia.py` |
