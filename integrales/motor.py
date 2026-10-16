"""Cuadratura adaptativa con SciPy y límites dependientes de otras variables."""

from __future__ import annotations

import math
import threading
import time
import warnings
from dataclasses import dataclass

from scipy.integrate import IntegrationWarning, nquad

from .expresiones import ErrorExpresion, Expresion


@dataclass(frozen=True)
class Sistema:
    nombre: str
    variables: tuple[str, ...]  # Desde la integral exterior a la interior.
    jacobiano: str
    descripcion: str


SISTEMAS = {
    "simple": Sistema("Simple · x", ("x",), "1", "Una variable: f(x)."),
    "cartesianas2": Sistema("Doble · cartesianas", ("x", "y"), "1", "Orden: dy dx. Los límites de y pueden depender de x."),
    "polares": Sistema("Doble · polares", ("theta", "r"), "r", "x = r cos(theta), y = r sin(theta). Ángulos en radianes."),
    "cartesianas3": Sistema("Triple · cartesianas", ("x", "y", "z"), "1", "Orden: dz dy dx. Los límites de z pueden depender de x e y."),
    "cilindricas": Sistema("Triple · cilíndricas", ("theta", "r", "z"), "r", "x = r cos(theta), y = r sin(theta); z conserva su valor."),
    "esfericas": Sistema("Triple · esféricas", ("theta", "phi", "rho"), "rho^2*sin(phi)", "theta: azimut [0, 2*pi]; phi: ángulo desde +z [0, pi]; rho: radio."),
}


@dataclass(frozen=True)
class Problema:
    sistema: str
    funcion: str
    limites: tuple[tuple[str, str], ...]
    jacobiano: bool = True
    tolerancia: float = 1e-7


@dataclass(frozen=True)
class Resultado:
    valor: float
    error_estimado: float
    evaluaciones: int
    segundos: float
    advertencias: tuple[str, ...]


class CalculoCancelado(Exception):
    pass


def variables_funcion(sistema: Sistema) -> tuple[str, ...]:
    if sistema is SISTEMAS["polares"]:
        return ("theta", "r", "x", "y")
    if sistema is SISTEMAS["cilindricas"]:
        return ("theta", "r", "z", "x", "y")
    if sistema is SISTEMAS["esfericas"]:
        return ("theta", "phi", "rho", "x", "y", "z")
    return sistema.variables


def validar(problema: Problema) -> tuple[Sistema, Expresion, list]:
    if problema.sistema not in SISTEMAS:
        raise ValueError("Sistema de coordenadas desconocido.")
    sistema = SISTEMAS[problema.sistema]
    if len(problema.limites) != len(sistema.variables):
        raise ValueError("Faltan límites de integración.")
    if not math.isfinite(problema.tolerancia) or not 1e-12 <= problema.tolerancia <= 1e-2:
        raise ValueError("La tolerancia debe estar entre 1e-12 y 0.01.")
    funcion = Expresion(problema.funcion, variables_funcion(sistema))
    limites = []
    for indice, (inferior, superior) in enumerate(problema.limites):
        anteriores = sistema.variables[:indice]
        try:
            limites.append((Expresion(inferior, anteriores), Expresion(superior, anteriores)))
        except ErrorExpresion as exc:
            raise ErrorExpresion(f"Límites de {sistema.variables[indice]}: {exc}") from exc
    return sistema, funcion, limites


def resolver(problema: Problema, cancelar: threading.Event | None = None,
             tiempo_maximo: float = 60.0) -> Resultado:
    sistema, funcion, limites = validar(problema)
    inicio = time.perf_counter()
    orden = tuple(reversed(sistema.variables))
    jacobiano = Expresion(sistema.jacobiano, sistema.variables)
    evaluaciones = 0

    def comprobar():
        if cancelar is not None and cancelar.is_set():
            raise CalculoCancelado("Cálculo cancelado.")
        if time.perf_counter() - inicio > tiempo_maximo:
            raise CalculoCancelado("Se alcanzó el tiempo máximo de cálculo (60 s por defecto). Simplifica la región o cambia la tolerancia.")

    def rango(indice):
        def evaluar(*externas):
            comprobar()
            valores = dict(zip(reversed(sistema.variables[:indice]), externas))
            inferior, superior = (exp.calcular(valores) for exp in limites[indice])
            nombre = sistema.variables[indice]
            if inferior == superior and not math.isfinite(inferior):
                raise ValueError(f"Los dos límites de {nombre} no pueden ser el mismo infinito.")
            # Los radios y el ángulo polar describen las coordenadas habituales.
            if nombre in ("r", "rho") and min(inferior, superior) < 0:
                raise ValueError(f"El radio {nombre} no puede tener límites negativos.")
            if problema.sistema == "esfericas" and nombre == "phi":
                if min(inferior, superior) < 0 or max(inferior, superior) > math.pi:
                    raise ValueError("En esféricas, phi debe estar entre 0 y pi.")
            return inferior, superior
        return evaluar

    def integrando(*argumentos):
        nonlocal evaluaciones
        comprobar()
        evaluaciones += 1
        valores = dict(zip(orden, argumentos))
        if problema.sistema in ("polares", "cilindricas"):
            valores["x"] = valores["r"] * math.cos(valores["theta"])
            valores["y"] = valores["r"] * math.sin(valores["theta"])
        elif problema.sistema == "esfericas":
            radio = valores["rho"]
            seno = math.sin(valores["phi"])
            valores["x"] = radio * seno * math.cos(valores["theta"])
            valores["y"] = radio * seno * math.sin(valores["theta"])
            valores["z"] = radio * math.cos(valores["phi"])
        valor = funcion.calcular(valores)
        if problema.jacobiano:
            valor *= jacobiano.calcular(valores)
        if not math.isfinite(valor):
            raise ErrorExpresion("El integrando produjo un valor no finito dentro de la región.")
        return valor

    rangos = [rango(i) for i in reversed(range(len(sistema.variables)))]
    with warnings.catch_warnings(record=True) as avisos:
        warnings.simplefilter("always", IntegrationWarning)
        # full_output=False conserva las advertencias de QUADPACK. Con True,
        # quad las entrega como mensajes que nquad no propaga al resultado.
        valor, error = nquad(
            integrando, rangos,
            opts={"epsabs": problema.tolerancia, "epsrel": problema.tolerancia, "limit": 100},
            full_output=False,
        )
    if not math.isfinite(valor) or not math.isfinite(error):
        raise ValueError("No se obtuvo un resultado finito. Revisa la convergencia y los límites.")
    mensajes = tuple(dict.fromkeys(str(aviso.message) for aviso in avisos))
    if error > max(problema.tolerancia, problema.tolerancia * abs(valor)):
        mensajes += ("La estimación de error supera la tolerancia solicitada.",)
    return Resultado(valor, error, evaluaciones, time.perf_counter() - inicio, mensajes)


def describir(problema: Problema) -> str:
    sistema = SISTEMAS[problema.sistema]
    lineas = [f"Sistema: {sistema.nombre}", "Límites, desde la integral exterior a la interior:"]
    for variable, (inferior, superior) in zip(sistema.variables, problema.limites):
        lineas.append(f"  {inferior} ≤ {variable} ≤ {superior}")
    factor = sistema.jacobiano if problema.jacobiano else "1"
    diferenciales = " ".join(f"d{v}" for v in reversed(sistema.variables))
    lineas += [f"Integrando: {problema.funcion}", f"Factor de medida: {factor}",
               f"Orden de integración: {diferenciales}", f"Tolerancia absoluta y relativa: {problema.tolerancia:g}"]
    return "\n".join(lineas)
