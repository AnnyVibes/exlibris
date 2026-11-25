from django.test import SimpleTestCase

from biblioteca.services.isbn import ISBNInvalido, normalizar


class ISBNTests(SimpleTestCase):
    def test_isbn13_valido_se_mantiene(self):
        """Un ISBN-13 válido (el del código de barras) se devuelve igual."""
        self.assertEqual(normalizar("9780307474728"), "9780307474728")

    def test_quita_guiones_y_espacios(self):
        self.assertEqual(normalizar("978-0-307-47472-8"), "9780307474728")
        self.assertEqual(normalizar(" 978 0307474728 "), "9780307474728")

    def test_isbn10_se_convierte_a_13(self):
        self.assertEqual(normalizar("0307474720"), "9780307474728")

    def test_isbn10_con_x(self):
        self.assertEqual(normalizar("080442957X"), "9780804429573")

    def test_digito_de_control_incorrecto(self):
        with self.assertRaises(ISBNInvalido):
            normalizar("9780307474729")

    def test_ean_que_no_es_libro(self):
        """Un EAN-13 de un producto que no empieza con 978/979 no es ISBN."""
        with self.assertRaises(ISBNInvalido):
            normalizar("7501055363278")

    def test_vacio_o_letras(self):
        for valor in ("", "abc", "12345"):
            with self.assertRaises(ISBNInvalido):
                normalizar(valor)
