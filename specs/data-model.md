# Modelo de datos

```
User 1───0..1 PreferenciaLibrero
User 1───* Libro 1───0..1 Resena
              │ 1───* Anotacion
              └ 1───* Prestamo
```

| Modelo | Campos principales |
|---|---|
| Libro | propietario, isbn (13, opcional), titulo, autores, editorial, anio, paginas, portada (imagen subida), portada_url, descripcion, genero (lista cerrada), estado, pagina_actual |
| Resena | libro (único), calificacion (1–5), texto |
| Anotacion | libro, pagina (opcional), texto, creado |
| Prestamo | libro, persona, contacto, prestado_el, devolver_el, devuelto_el, notas |
| PreferenciaLibrero | usuario (único), estilo (repisas/mueble), color (lila, rosa, celeste, menta, madera, noche) |

Restricciones: `isbn_unico_por_usuario` (propietario + isbn cuando isbn no está vacío) y
`un_prestamo_activo_por_libro` (libro cuando devuelto_el es nulo).
