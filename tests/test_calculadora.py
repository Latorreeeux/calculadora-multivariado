"""Contrastes analíticos y validación de las entradas del usuario."""

import math
import threading
import unittest

from integrales.ejemplos import EJEMPLOS
from integrales.expresiones import ErrorExpresion, Expresion
from integrales.motor import CalculoCancelado, Problema, resolver


class PruebasExpresiones(unittest.TestCase):
    def test_notacion_matematica(self):
        self.assertAlmostEqual(Expresion("sin(π/2) + 2^3 + ln(e)").calcular(), 10)
        self.assertEqual(Expresion("-x^2", ("x",)).calcular({"x": 3}), -9)
        self.assertAlmostEqual(Expresion("log(100, 10)").calcular(), 2)

    def test_rechaza_codigo_y_acceso_a_objetos(self):
        for texto in ("__import__('os')", "x.__class__", "[x][0]", "(lambda: 1)()", "open('archivo')", "[x for x in (1,)]", "True", "sin(x=1)"):
            with self.subTest(texto=texto), self.assertRaises(ErrorExpresion):
                Expresion(texto, ("x",))

    def test_variable_desconocida(self):
        with self.assertRaisesRegex(ErrorExpresion, "Nombre desconocido"):
            Expresion("y+1", ("x",))

    def test_dominios_reales(self):
        for texto in ("sqrt(-1)", "1/0", "(-1)^0.5", "exp(1000)"):
            with self.subTest(texto=texto), self.assertRaises(ErrorExpresion):
                Expresion(texto).calcular()


class PruebasIntegracion(unittest.TestCase):
    def test_ejemplos_contra_referencias_analiticas(self):
        for ejemplo in EJEMPLOS:
            with self.subTest(ejemplo=ejemplo.clave):
                resultado = resolver(ejemplo.problema)
                self.assertAlmostEqual(resultado.valor, ejemplo.referencia, delta=1e-7 * max(1, abs(ejemplo.referencia)))
                self.assertFalse(resultado.advertencias)
                self.assertGreater(resultado.evaluaciones, 0)

    def test_limites_anidados_con_tres_variables(self):
        # Integral de x+2y+3z sobre 0<x<1, 0<y<x, 0<z<y.
        resultado = resolver(Problema("cartesianas3", "x+2*y+3*z", (("0", "1"), ("0", "x"), ("0", "y"))))
        self.assertAlmostEqual(resultado.valor, 5/12, places=10)

    def test_jacobiano_se_puede_ingresar_manualmente(self):
        automatico = resolver(Problema("polares", "exp(r^2)", (("0", "pi"), ("0", "1"))))
        manual = resolver(Problema("polares", "exp(r^2)*r", (("0", "pi"), ("0", "1")), jacobiano=False))
        self.assertAlmostEqual(automatico.valor, manual.valor, places=12)

    def test_radio_dependiente_del_angulo(self):
        resultado = resolver(Problema("polares", "1", (("0", "pi/2"), ("0", "cos(theta)"))))
        self.assertAlmostEqual(resultado.valor, math.pi/8, places=10)

    def test_coordenadas_cartesianas_en_esfericas(self):
        resultado = resolver(Problema("esfericas", "x^2+y^2+z^2", (("0", "2*pi"), ("0", "pi"), ("0", "1"))))
        self.assertAlmostEqual(resultado.valor, 4*math.pi/5, places=10)

    def test_coordenadas_cartesianas_en_cilindricas(self):
        resultado = resolver(Problema("cilindricas", "x^2+y^2+z", (("0", "2*pi"), ("0", "1"), ("0", "2"))))
        self.assertAlmostEqual(resultado.valor, 3*math.pi, places=10)

    def test_limites_invertidos_y_nulos(self):
        self.assertAlmostEqual(resolver(Problema("simple", "x", (("1", "0"),))).valor, -0.5)
        self.assertEqual(resolver(Problema("simple", "x", (("1", "1"),))).valor, 0)

    def test_integral_gaussiana_impropia(self):
        resultado = resolver(Problema("simple", "exp(-x^2)", (("-inf", "inf"),)))
        self.assertAlmostEqual(resultado.valor, math.sqrt(math.pi), places=9)

    def test_limite_no_puede_usar_variable_interior(self):
        with self.assertRaisesRegex(ErrorExpresion, "Límites de x"):
            resolver(Problema("cartesianas2", "1", (("0", "y"), ("0", "1"))))

    def test_rechaza_radios_negativos_y_phi_fuera_de_rango(self):
        for problema in (
            Problema("polares", "1", (("0", "pi"), ("-1", "1"))),
            Problema("esfericas", "1", (("0", "pi"), ("0", "2*pi"), ("0", "1"))),
        ):
            with self.subTest(problema=problema), self.assertRaises(ValueError):
                resolver(problema)

    def test_rechaza_tolerancias_invalidas(self):
        for tolerancia in (0, -1, float("nan"), float("inf"), 1e-16):
            with self.subTest(tolerancia=tolerancia), self.assertRaises(ValueError):
                resolver(Problema("simple", "x", (("0", "1"),), tolerancia=tolerancia))

    def test_cancelacion_y_limite_de_tiempo(self):
        evento = threading.Event()
        evento.set()
        problema = Problema("simple", "x", (("0", "1"),))
        with self.assertRaises(CalculoCancelado):
            resolver(problema, evento)
        with self.assertRaises(CalculoCancelado):
            resolver(problema, tiempo_maximo=0)

    def test_preserva_advertencia_de_integral_divergente(self):
        resultado = resolver(Problema("simple", "1/x", (("1", "inf"),)))
        self.assertTrue(resultado.advertencias)


if __name__ == "__main__":
    unittest.main()
