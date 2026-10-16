"""Ejercicios precargados con resultados de referencia analíticos."""

import math
from dataclasses import dataclass

from .motor import Problema


@dataclass(frozen=True)
class Ejemplo:
    clave: str
    nombre: str
    descripcion: str
    problema: Problema
    referencia: float
    exacto: str


EJEMPLOS = (
    Ejemplo("simple", "01 · Integral de x²", "Una integral simple para empezar.",
            Problema("simple", "x^2", (("0", "1"),)), 1/3, "1/3"),
    Ejemplo("triangulo", "02 · Región triangular", "Límites dependientes: 0 ≤ y ≤ x, con 0 ≤ x ≤ 1.",
            Problema("cartesianas2", "x+y", (("0", "1"), ("0", "x"))), 0.5, "1/2"),
    Ejemplo("semicirculo", "03 · Semicírculo en cartesianas", "Área del semicírculo superior unitario, integrando la función 1.",
            Problema("cartesianas2", "1", (("-1", "1"), ("0", "sqrt(1-x^2)"))), math.pi/2, "pi/2"),
    Ejemplo("tablero", "04 · Polinomio en semicírculo", "Ejercicio similar al tablero: x²(x²+y²)³ sobre el semicírculo superior unitario.",
            Problema("polares", "x^2*(x^2+y^2)^3", (("0", "pi"), ("0", "1"))), math.pi/20, "pi/20"),
    Ejemplo("exponencial", "05 · Exponencial en disco", "Integral de exp(x²+y²) sobre el disco unitario. El programa agrega r.",
            Problema("polares", "exp(r^2)", (("0", "2*pi"), ("0", "1"))), math.pi*(math.e-1), "pi*(e-1)"),
    Ejemplo("esfera", "06 · Volumen de esfera, radio 5", "Dos hemisferios: altura 2*sqrt(25-r²) sobre el disco de radio 5.",
            Problema("polares", "2*sqrt(25-r^2)", (("0", "2*pi"), ("0", "5"))), 500*math.pi/3, "500*pi/3"),
    Ejemplo("cilindro", "07 · Volumen de cilindro", "Cilindro de radio 2 y altura 3, usando una integral triple.",
            Problema("cilindricas", "1", (("0", "2*pi"), ("0", "2"), ("0", "3"))), 12*math.pi, "12*pi"),
    Ejemplo("esfericas", "08 · Esfera en esféricas", "Esfera unitaria; el programa agrega rho²*sin(phi).",
            Problema("esfericas", "1", (("0", "2*pi"), ("0", "pi"), ("0", "1"))), 4*math.pi/3, "4*pi/3"),
    Ejemplo("tetraedro", "09 · Tetraedro en cartesianas", "Volumen limitado por los planos coordenados y x+y+z=1.",
            Problema("cartesianas3", "1", (("0", "1"), ("0", "1-x"), ("0", "1-x-y"))), 1/6, "1/6"),
    Ejemplo("impropia", "10 · Integral impropia", "Integral convergente de exp(-x) entre cero e infinito.",
            Problema("simple", "exp(-x)", (("0", "inf"),)), 1, "1"),
)
