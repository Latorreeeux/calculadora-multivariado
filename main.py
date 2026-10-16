"""Ejecuta la interfaz o un ejemplo numérico desde la consola."""

import argparse
import sys


def main():
    # Las consolas de Windows pueden usar una página de códigos sin símbolos
    # matemáticos. UTF-8 también permite redirigir el reporte a un archivo.
    for flujo in (sys.stdout, sys.stderr):
        if hasattr(flujo, "reconfigure"):
            flujo.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Calculadora de integrales multivariadas")
    parser.add_argument("--ejemplo", help="Calcula un ejemplo por su clave; usa --listar para verlas.")
    parser.add_argument("--listar", action="store_true", help="Lista los ejemplos disponibles.")
    argumentos = parser.parse_args()
    try:
        from integrales.ejemplos import EJEMPLOS
        from integrales.motor import CalculoCancelado, describir, resolver
    except ModuleNotFoundError as exc:
        if exc.name in ("scipy", "numpy"):
            print("Faltan dependencias. Ejecuta: python -m pip install -r requirements.txt", file=sys.stderr)
            return 1
        raise
    if argumentos.listar:
        for ejemplo in EJEMPLOS:
            print(f"{ejemplo.clave:14} {ejemplo.nombre}")
        return 0
    if argumentos.ejemplo:
        ejemplo = next((e for e in EJEMPLOS if e.clave == argumentos.ejemplo), None)
        if ejemplo is None:
            parser.error("Ejemplo desconocido. Usa --listar.")
        try:
            resultado = resolver(ejemplo.problema)
        except (ValueError, RuntimeError, CalculoCancelado) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        print(describir(ejemplo.problema))
        print(f"\nResultado aproximado: {resultado.valor:.15g}")
        print(f"Error estimado entre niveles: {resultado.error_estimado:.6g}")
        print(f"Referencia analítica del ejemplo: {ejemplo.exacto} = {ejemplo.referencia:.15g}")
        print(f"Evaluaciones: {resultado.evaluaciones} | Tiempo: {resultado.segundos:.3f} s")
        for aviso in resultado.advertencias:
            print(f"Advertencia: {aviso}")
        return 0
    from integrales.interfaz import iniciar
    iniciar()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
