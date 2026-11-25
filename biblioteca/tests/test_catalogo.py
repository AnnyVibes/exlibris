from unittest.mock import patch

from django.test import SimpleTestCase

from biblioteca.services import catalogo

ISBN = "9780307474728"
OPEN_LIBRARY = {
    f"ISBN:{ISBN}": {
        "title": "Cien años de soledad",
        "authors": [{"name": "Gabriel García Márquez"}],
        "publishers": [{"name": "Vintage Español"}],
        "publish_date": "2009",
        "number_of_pages": 417,
        "cover": {"medium": "http://covers.openlibrary.org/b/id/1-M.jpg"},
        "subjects": [{"name": "Fiction"}],
    }
}
GOOGLE = {"items": [{"volumeInfo": {
    "title": "Cien años de soledad", "authors": ["Gabriel García Márquez"],
    "description": "La historia de los Buendía.", "categories": ["Fiction"], "pageCount": 400,
}}]}


def falso(respuestas):
    def _get(url):
        for clave, valor in respuestas.items():
            if clave in url:
                return valor
        return None
    return _get


class CatalogoTests(SimpleTestCase):
    def test_combina_open_library_y_google(self):
        """Open Library manda; Google Books solo rellena lo que falta (la descripción)."""
        with patch.object(catalogo, "_get_json", side_effect=falso({"openlibrary": OPEN_LIBRARY, "googleapis": GOOGLE})):
            datos = catalogo.buscar_por_isbn(ISBN)
        self.assertEqual(datos["titulo"], "Cien años de soledad")
        self.assertEqual(datos["autores"], "Gabriel García Márquez")
        self.assertEqual(datos["paginas"], 417)
        self.assertEqual(datos["anio"], 2009)
        self.assertEqual(datos["descripcion"], "La historia de los Buendía.")
        self.assertTrue(datos["portada_url"].startswith("https://"))
        self.assertEqual(datos["isbn"], ISBN)
        self.assertEqual(datos["genero"], "Novela")  # «Fiction» se traduce a la lista de géneros

    def test_solo_google(self):
        with patch.object(catalogo, "_get_json", side_effect=falso({"googleapis": GOOGLE})):
            datos = catalogo.buscar_por_isbn(ISBN)
        self.assertEqual(datos["paginas"], 400)

    def test_no_encontrado(self):
        with patch.object(catalogo, "_get_json", return_value=None):
            self.assertEqual(catalogo.buscar_por_isbn(ISBN), {})
