# Integral · Calculadora de multivariado

Aplicación de escritorio en Python, con interfaz en español, para calcular
numéricamente integrales simples, dobles y triples. Permite escribir la función
y los límites manualmente, incluidos límites que dependen de otras variables.

## Iniciar en Windows

Instala Python 3.10 o superior con Tkinter y haz doble clic en **Iniciar.bat**.
El iniciador crea un entorno `.venv`, instala SciPy si hace falta y abre la
calculadora. La primera instalación necesita conexión a Internet.

También puedes ejecutarla desde PowerShell, en esta carpeta:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

No hace falta activar el entorno. Tkinter viene con la instalación habitual de
Python para Windows. En Linux puede requerir el paquete `python3-tk` del sistema.

## Ingresar una integral

Para calcular

\[
\int_0^1\int_0^x (x+y)\,dy\,dx
\]

elige **Doble · cartesianas**, escribe `x+y` y completa:

| Variable | Desde | Hasta |
|---|---|---|
| x | `0` | `1` |
| y | `0` | `x` |

Pulsa **Calcular integral** o **Ctrl+Enter**. El resultado es aproximadamente `0.5`.
El reporte incluye el planteamiento, la estimación de error, las evaluaciones y
el tiempo de cálculo; puedes copiarlo o guardarlo en un archivo de texto.

Los límites aparecen desde la integral exterior a la interior. Cada fila puede
depender de las variables de las filas anteriores. El orden de cada sistema es:

| Sistema | Filas, de exterior a interior | Diferenciales | Jacobiano |
|---|---|---|---|
| Simple | x | dx | 1 |
| Doble cartesiana | x, y | dy dx | 1 |
| Polar | theta, r | dr dtheta | r |
| Triple cartesiana | x, y, z | dz dy dx | 1 |
| Cilíndrica | theta, r, z | dz dr dtheta | r |
| Esférica | theta, phi, rho | drho dphi dtheta | rho² sin(phi) |

Para una integral con otro orden cartesiano, renombra las variables de forma
consistente en la función y en los límites. El programa no cambia el orden ni
deduce la región a partir de desigualdades. Si la región requiere varios
intervalos, calcula cada parte por separado y suma los resultados.

## Ejemplo parecido al tablero

En **Doble · polares**, escribe `x^2*(x^2+y^2)^3`, con `theta` entre `0` y `pi`
y `r` entre `0` y `1`. Mantén marcada **Incluir jacobiano: r**.
El programa sustituye `x=r*cos(theta)`, `y=r*sin(theta)` y multiplica por `r`.
El resultado esperado es `pi/20 ≈ 0.15707963267949`.

También puedes ingresar directamente `r^8*cos(theta)^2` con el jacobiano
activado. Si ingresas `r^9*cos(theta)^2`, desactívalo: esa expresión ya incluye
el factor `r`. La aplicación no detecta automáticamente si lo escribiste.

Los diez ejemplos de la pestaña **Ejemplos resueltos** se pueden cargar y editar.
Sus resultados de referencia son analíticos y solo se muestran para esos
ejercicios; el cálculo de entradas arbitrarias es numérico.

## Expresiones

- Potencias: `x^2` o `x**2`.
- Multiplicación explícita: `2*x`, `r*cos(theta)`.
- Decimales con punto: `0.5`.
- Constantes: `pi`, `e`, `inf`; también se admite `π`.
- Funciones: `sin`, `cos`, `tan`, `asin`, `acos`, `atan`, `atan2`, `sinh`,
  `cosh`, `tanh`, `sqrt`, `exp`, `ln`, `log`, `log10`, `abs`, `min`, `max`.
- `log(x)` y `ln(x)` son logaritmos naturales; `log(x, 10)` usa base 10.
- Ángulos en radianes. En esféricas, `theta` es el azimut y `phi` se mide desde
  el eje positivo z, entre `0` y `pi`. El radio es `rho`, siempre no negativo.
- En las funciones polares/cilíndricas se pueden usar `x` e `y`; en esféricas,
  `x`, `y` y `z`. Los límites usan solamente las coordenadas de las filas previas.

Las expresiones se interpretan con una lista permitida de nodos AST y
funciones matemáticas; no se usa `eval`, `exec` ni evaluación simbólica de texto.

## Método y alcance

El motor usa cuadratura adaptativa de SciPy/QUADPACK mediante
[`scipy.integrate.nquad`](https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.nquad.html).
La tolerancia absoluta y relativa se configura en cada nivel de integración
(por defecto `1e-7`; intervalo admitido: `1e-12` a `0.01`).

El error mostrado es **el máximo de las estimaciones de error de los distintos
niveles**. No es una cota rigurosa del error total de una integral múltiple.
Las advertencias de integración se conservan en el reporte. Un valor devuelto
no demuestra que una integral impropia converja; revisa analíticamente la
convergencia y divide regiones con singularidades o discontinuidades.

Se admiten límites infinitos para integrales convergentes y límites invertidos
con su signo correspondiente. El cálculo trabaja con números reales en punto
flotante. Cada cálculo tiene un tiempo máximo de 60 segundos y puede cancelarse.
Las integrales triples difíciles pueden necesitar dividirse en varias partes.

## Uso desde código o consola

```python
from integrales.motor import Problema, resolver

problema = Problema(
    sistema="cartesianas2",
    funcion="x+y",
    limites=(("0", "1"), ("0", "x")),
    tolerancia=1e-7,
)
resultado = resolver(problema)
print(resultado.valor)  # 0.5
```

```powershell
.\.venv\Scripts\python.exe main.py --listar
.\.venv\Scripts\python.exe main.py --ejemplo tablero
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

El núcleo está en `integrales/motor.py`, el intérprete en
`integrales/expresiones.py` y la interfaz en `integrales/interfaz.py`.
