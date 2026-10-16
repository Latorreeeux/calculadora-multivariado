"""Intérprete de expresiones matemáticas; no ejecuta código Python del usuario."""

from __future__ import annotations

import ast
import math
import operator
from collections.abc import Callable, Mapping


class ErrorExpresion(ValueError):
    """Una entrada no representa una expresión matemática admitida."""


FUNCIONES = {
    "sin": (math.sin, 1, 1), "cos": (math.cos, 1, 1),
    "tan": (math.tan, 1, 1), "asin": (math.asin, 1, 1),
    "acos": (math.acos, 1, 1), "atan": (math.atan, 1, 1),
    "atan2": (math.atan2, 2, 2), "sinh": (math.sinh, 1, 1),
    "cosh": (math.cosh, 1, 1), "tanh": (math.tanh, 1, 1),
    "sqrt": (math.sqrt, 1, 1), "exp": (math.exp, 1, 1),
    "ln": (math.log, 1, 1), "log": (math.log, 1, 2),
    "log10": (math.log10, 1, 1), "abs": (abs, 1, 1),
    "min": (min, 2, 8), "max": (max, 2, 8),
}
CONSTANTES = {"pi": math.pi, "e": math.e, "inf": math.inf}
OPERACIONES = {
    ast.Add: operator.add, ast.Sub: operator.sub,
    ast.Mult: operator.mul, ast.Div: operator.truediv,
    ast.Pow: math.pow,
}


class Expresion:
    """Valida un AST y construye funciones exclusivamente aritméticas."""

    def __init__(self, texto: str, variables: tuple[str, ...] = ()):
        self.texto = texto.strip()
        if not self.texto:
            raise ErrorExpresion("La expresión está vacía.")
        if len(self.texto) > 600:
            raise ErrorExpresion("La expresión debe tener como máximo 600 caracteres.")
        normalizado = self.texto.replace("^", "**").replace("π", "pi")
        normalizado = normalizado.replace("θ", "theta").replace("φ", "phi").replace("ρ", "rho")
        normalizado = normalizado.replace("−", "-").replace("×", "*").replace("·", "*")
        try:
            arbol = ast.parse(normalizado, mode="eval")
        except (SyntaxError, RecursionError) as exc:
            raise ErrorExpresion("Sintaxis inválida. Usa, por ejemplo, sqrt(1-x^2) y escribe 2*x.") from exc
        if sum(1 for _ in ast.walk(arbol)) > 160:
            raise ErrorExpresion("La expresión es demasiado compleja.")
        self.variables = variables
        self._funcion = self._construir(arbol.body)

    def _construir(self, nodo: ast.AST) -> Callable:
        if isinstance(nodo, ast.Constant) and type(nodo.value) in (int, float):
            try:
                numero = float(nodo.value)
            except (OverflowError, ValueError) as exc:
                raise ErrorExpresion("La constante numérica es demasiado grande.") from exc
            if not math.isfinite(numero):
                raise ErrorExpresion("Usa inf para expresar un límite infinito.")
            return lambda valores: numero
        if isinstance(nodo, ast.Name):
            if nodo.id in CONSTANTES:
                numero = CONSTANTES[nodo.id]
                return lambda valores: numero
            if nodo.id in self.variables:
                nombre = nodo.id
                return lambda valores: valores[nombre]
            disponibles = ", ".join(self.variables) or "ninguna (el límite debe ser constante)"
            raise ErrorExpresion(f"Nombre desconocido: {nodo.id}. Variables permitidas: {disponibles}.")
        if isinstance(nodo, ast.UnaryOp) and isinstance(nodo.op, (ast.UAdd, ast.USub)):
            operando = self._construir(nodo.operand)
            signo = -1 if isinstance(nodo.op, ast.USub) else 1
            return lambda valores: signo * operando(valores)
        if isinstance(nodo, ast.BinOp) and type(nodo.op) in OPERACIONES:
            izquierda = self._construir(nodo.left)
            derecha = self._construir(nodo.right)
            operacion = OPERACIONES[type(nodo.op)]
            return lambda valores: operacion(izquierda(valores), derecha(valores))
        if isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Name):
            if nodo.func.id not in FUNCIONES:
                raise ErrorExpresion(f"Función no admitida: {nodo.func.id}.")
            funcion, minimo, maximo = FUNCIONES[nodo.func.id]
            if nodo.keywords or not minimo <= len(nodo.args) <= maximo:
                raise ErrorExpresion(f"Revisa los argumentos de {nodo.func.id}.")
            argumentos = [self._construir(arg) for arg in nodo.args]
            return lambda valores: funcion(*(arg(valores) for arg in argumentos))
        raise ErrorExpresion("Usa solamente números, variables, operaciones y funciones matemáticas.")

    def calcular(self, valores: Mapping[str, float] | None = None) -> float:
        try:
            resultado = float(self._funcion(valores or {}))
        except (ArithmeticError, ValueError, TypeError, KeyError) as exc:
            raise ErrorExpresion(f"No se puede evaluar «{self.texto}»: {exc}") from exc
        if math.isnan(resultado):
            raise ErrorExpresion(f"«{self.texto}» produjo un valor indefinido.")
        return resultado
