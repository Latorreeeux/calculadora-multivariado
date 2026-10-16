"""Interfaz de escritorio en español, construida con Tkinter."""

from __future__ import annotations

import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from .ejemplos import EJEMPLOS
from .motor import CalculoCancelado, Problema, SISTEMAS, describir, resolver, validar


FONDO = "#eef2f6"
TINTA = "#172b42"
MUTED = "#576b80"
AZUL = "#145e70"

AYUDA = """CÓMO ESCRIBIR UNA INTEGRAL

1. Elige el sistema de coordenadas.
2. Escribe la función que quieres integrar.
3. Completa los límites, desde la integral exterior a la interior.
4. Revisa el planteamiento y pulsa «Calcular integral».

Por ejemplo, para ∫[0,1] ∫[0,x] (x+y) dy dx:
  Sistema: Doble · cartesianas
  Función: x+y
  x: desde 0 hasta 1
  y: desde 0 hasta x
  Resultado aproximado: 0.5

EXPRESIONES ADMITIDAS

Potencias: x^2 o x**2. Multiplicación: 2*x, nunca 2x.
Decimales: 0.5 (usa punto, no coma).
Constantes: pi, e, inf. También puedes escribir π.
Funciones: sin, cos, tan, asin, acos, atan, atan2, sinh, cosh,
tanh, sqrt, exp, ln, log, log10, abs, min y max.
log(x) es el logaritmo natural; log(x, 10) usa base 10.
Todos los ángulos se expresan en radianes.
Escribe exp(x) o e^x para la exponencial.

LÍMITES DEPENDIENTES

Cada límite puede usar las variables de las filas anteriores.
En cartesianas dobles: x tiene límites constantes; y puede usar x.
En cartesianas triples: z puede usar x e y.
En polares: r puede depender de theta.
Los límites se escriben en las variables del sistema seleccionado.
inf y -inf se admiten en integrales impropias convergentes.
Los límites invertidos cambian el signo de la integral.
Una región que necesite varios intervalos debe dividirse en integrales.

COORDENADAS Y JACOBIANO

Polares: x = r*cos(theta), y = r*sin(theta); medida r dr dtheta.
Cilíndricas: las mismas x e y, con z; medida r dz dr dtheta.
Esféricas: x = rho*sin(phi)*cos(theta),
  y = rho*sin(phi)*sin(theta), z = rho*cos(phi).
  Medida rho^2*sin(phi) drho dphi dtheta.
theta es el azimut; phi se mide desde el eje +z, de 0 a pi.
Los radios r y rho deben ser no negativos.
Puedes escribir la función usando las coordenadas del sistema o x, y, z;
el programa calcula las equivalencias en cada punto.

La opción «Incluir jacobiano» agrega el factor de medida una sola vez.
Si ya escribiste el factor en la función, desmarca esa opción.
Ejemplo: exp(r^2) con la opción marcada equivale a
exp(r^2)*r con la opción desmarcada.
Para áreas o volúmenes por integrales dobles/triples, la función puede ser 1.
Para volumen bajo una superficie, escribe la altura de la superficie.

INTERPRETACIÓN DEL RESULTADO

Se usa cuadratura adaptativa de SciPy (QUADPACK).
La tolerancia se aplica como objetivo absoluto y relativo en cada nivel.
El error mostrado es el máximo de las estimaciones de error de los
niveles de integración; no es una cota garantizada del error total.
Las advertencias indican que el valor requiere revisión y no confirman
convergencia. Una integral divergente puede devolver un número engañoso.
Si hay singularidades o discontinuidades, divide la región en partes.
El programa trabaja con valores reales y precisión de punto flotante.
La evaluación se cancela al alcanzar 60 segundos o al pulsar «Cancelar».
"""


class Aplicacion(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Integral · Calculadora de multivariado")
        ancho = min(1140, self.winfo_screenwidth() - 80)
        alto = min(800, self.winfo_screenheight() - 90)
        self.geometry(f"{ancho}x{alto}")
        self.minsize(940, 620)
        self.configure(bg=FONDO)
        self._estilos()
        self.cola = queue.Queue()
        self.cancelacion = threading.Event()
        self.ocupado = False
        self.ultimo_reporte = ""
        self.problema_activo = None
        self.sistema_var = tk.StringVar(value=SISTEMAS["polares"].nombre)
        self.funcion_var = tk.StringVar()
        self.jacobiano_var = tk.BooleanVar(value=True)
        self.tolerancia_var = tk.StringVar(value="1e-7")
        self.estado_var = tk.StringVar(value="Listo para calcular")
        self.variables_limites = []
        self._construir()
        self.cargar_ejemplo(EJEMPLOS[3])
        self.after(120, self._recibir)
        self.protocol("WM_DELETE_WINDOW", self._cerrar)
        self.bind("<Control-Return>", lambda _: self.calcular())

    def _estilos(self):
        estilo = ttk.Style(self)
        estilo.theme_use("clam")
        estilo.configure(".", font=("Segoe UI", 10), foreground=TINTA)
        estilo.configure("TFrame", background=FONDO)
        estilo.configure("Card.TFrame", background="white")
        estilo.configure("TLabel", background=FONDO)
        estilo.configure("Card.TLabel", background="white")
        estilo.configure("Muted.TLabel", background="white", foreground=MUTED)
        estilo.configure("Title.TLabel", background="white", font=("Segoe UI Semibold", 13))
        estilo.configure("TButton", padding=(12, 8))
        estilo.configure("Primary.TButton", background=AZUL, foreground="white", font=("Segoe UI Semibold", 10))
        estilo.map("Primary.TButton", background=[("active", "#1d788a"), ("disabled", "#96a9b1")])
        estilo.configure("TEntry", padding=7, fieldbackground="white")
        estilo.configure("TCombobox", padding=7, fieldbackground="white")
        estilo.configure("TCheckbutton", background="white")
        estilo.configure("TNotebook", background=FONDO, borderwidth=0)
        estilo.configure("TNotebook.Tab", padding=(20, 10))

    def _construir(self):
        cabecera = tk.Frame(self, bg=TINTA, padx=24, pady=14)
        cabecera.pack(fill="x")
        tk.Label(cabecera, text="∫  Integral", bg=TINTA, fg="white", font=("Segoe UI Semibold", 23)).pack(anchor="w")
        tk.Label(cabecera, text="Calculadora numérica de cálculo multivariado", bg=TINTA, fg="#b9cddd", font=("Segoe UI", 10)).pack(anchor="w")
        self.pestanas = ttk.Notebook(self)
        self.pestanas.pack(fill="both", expand=True, padx=16, pady=(12, 6))
        calculadora = ttk.Frame(self.pestanas, padding=10)
        ejemplos = ttk.Frame(self.pestanas, padding=16)
        ayuda = ttk.Frame(self.pestanas, padding=12)
        self.pestanas.add(calculadora, text="Calculadora")
        self.pestanas.add(ejemplos, text="Ejemplos resueltos")
        self.pestanas.add(ayuda, text="Cómo usarla")
        calculadora.columnconfigure(0, weight=3)
        calculadora.columnconfigure(1, weight=2)
        calculadora.rowconfigure(0, weight=1)
        contenedor = ttk.Frame(calculadora, style="Card.TFrame")
        contenedor.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        contenedor.columnconfigure(0, weight=1)
        contenedor.rowconfigure(0, weight=1)
        self.canvas_formulario = tk.Canvas(contenedor, bg="white", highlightthickness=0, width=540, height=350)
        self.canvas_formulario.grid(row=0, column=0, sticky="nsew")
        barra_formulario = ttk.Scrollbar(contenedor, command=self.canvas_formulario.yview)
        barra_formulario.grid(row=0, column=1, sticky="ns")
        self.canvas_formulario.configure(yscrollcommand=barra_formulario.set)
        formulario = ttk.Frame(self.canvas_formulario, style="Card.TFrame", padding=18)
        ventana_formulario = self.canvas_formulario.create_window((0, 0), window=formulario, anchor="nw")
        formulario.bind("<Configure>", lambda _: self.canvas_formulario.configure(scrollregion=self.canvas_formulario.bbox("all")))
        self.canvas_formulario.bind("<Configure>", lambda evento: self.canvas_formulario.itemconfigure(ventana_formulario, width=evento.width))

        def rueda_formulario(evento):
            widget = evento.widget
            while widget is not None:
                if widget is contenedor:
                    if formulario.winfo_reqheight() > self.canvas_formulario.winfo_height():
                        self.canvas_formulario.yview_scroll(-int(evento.delta / 120), "units")
                    break
                widget = getattr(widget, "master", None)
        self.bind("<MouseWheel>", rueda_formulario, add=True)
        formulario.columnconfigure(0, weight=1)
        ttk.Label(formulario, text="Plantea tu integral", style="Title.TLabel").grid(row=0, sticky="w", pady=(0, 10))
        ttk.Label(formulario, text="Sistema de coordenadas", style="Card.TLabel").grid(row=1, sticky="w")
        self.selector_sistema = ttk.Combobox(formulario, textvariable=self.sistema_var, values=[s.nombre for s in SISTEMAS.values()], state="readonly")
        self.selector_sistema.grid(row=2, sticky="ew", pady=(4, 8))
        self.selector_sistema.bind("<<ComboboxSelected>>", lambda _: self.cambiar_sistema())
        self.descripcion = ttk.Label(formulario, style="Muted.TLabel", wraplength=480)
        self.descripcion.grid(row=3, sticky="w", pady=(0, 10))
        ttk.Label(formulario, text="Función a integrar", style="Card.TLabel").grid(row=4, sticky="w")
        self.entrada_funcion = ttk.Entry(formulario, textvariable=self.funcion_var, font=("Consolas", 12))
        self.entrada_funcion.grid(row=5, sticky="ew", pady=(4, 3))
        self.pista_funcion = ttk.Label(formulario, style="Muted.TLabel", wraplength=480)
        self.pista_funcion.grid(row=6, sticky="w", pady=(0, 10))
        self.marco_limites = ttk.Frame(formulario, style="Card.TFrame")
        self.marco_limites.grid(row=7, sticky="ew")
        self.casilla_jacobiano = ttk.Checkbutton(formulario, variable=self.jacobiano_var, command=self.actualizar_preview)
        self.casilla_jacobiano.grid(row=8, sticky="w", pady=(9, 7))
        precision = ttk.Frame(formulario, style="Card.TFrame")
        precision.grid(row=9, sticky="ew", pady=(0, 10))
        ttk.Label(precision, text="Tolerancia", style="Card.TLabel").pack(side="left", padx=(0, 10))
        ttk.Entry(precision, textvariable=self.tolerancia_var, width=12).pack(side="left")
        ttk.Label(precision, text="1e-7 = 0.0000001", style="Muted.TLabel").pack(side="left", padx=10)
        botones = ttk.Frame(formulario, style="Card.TFrame")
        botones.grid(row=10, sticky="ew")
        self.boton_calcular = ttk.Button(botones, text="Calcular integral", style="Primary.TButton", command=self.calcular)
        self.boton_calcular.pack(side="left", fill="x", expand=True)
        self.boton_cancelar = ttk.Button(botones, text="Cancelar", command=self.cancelar, state="disabled")
        self.boton_cancelar.pack(side="left", padx=(8, 0))
        self.progreso = ttk.Progressbar(formulario, mode="indeterminate")
        self.progreso.grid(row=11, sticky="ew", pady=(10, 0))

        resultados = ttk.Frame(calculadora, style="Card.TFrame", padding=18)
        resultados.grid(row=0, column=1, sticky="nsew")
        resultados.columnconfigure(0, weight=1)
        resultados.rowconfigure(4, weight=1)
        ttk.Label(resultados, text="Resultado numérico", style="Title.TLabel").grid(row=0, sticky="w")
        self.valor_label = tk.Label(resultados, text="—", bg="white", fg=AZUL, font=("Segoe UI Semibold", 24), anchor="w")
        self.valor_label.grid(row=1, sticky="ew", pady=(14, 4))
        self.detalle_label = ttk.Label(resultados, text="Carga un ejemplo o escribe tu integral.", style="Muted.TLabel", wraplength=330)
        self.detalle_label.grid(row=2, sticky="w", pady=(0, 14))
        ttk.Label(resultados, text="Planteamiento y observaciones", style="Card.TLabel").grid(row=3, sticky="w", pady=(0, 6))
        self.reporte = tk.Text(resultados, wrap="word", font=("Consolas", 10), bg="#f5f8fa", fg=TINTA, relief="flat", padx=12, pady=12, width=34, height=12)
        self.reporte.grid(row=4, sticky="nsew")
        self.reporte.configure(state="disabled")
        acciones = ttk.Frame(resultados, style="Card.TFrame")
        acciones.grid(row=5, sticky="ew", pady=(12, 0))
        self.boton_copiar = ttk.Button(acciones, text="Copiar", command=self.copiar, state="disabled")
        self.boton_copiar.pack(side="left")
        self.boton_guardar = ttk.Button(acciones, text="Guardar .txt", command=self.guardar, state="disabled")
        self.boton_guardar.pack(side="left", padx=8)

        ejemplos.columnconfigure(0, weight=1)
        ejemplos.rowconfigure(1, weight=1)
        ttk.Label(ejemplos, text="Selecciona un ejercicio y pulsa «Cargar ejemplo». Puedes editarlo después.").grid(row=0, sticky="w", pady=(0, 12))
        self.lista_ejemplos = tk.Listbox(ejemplos, font=("Segoe UI", 12), bg="white", fg=TINTA, relief="flat", selectbackground=AZUL, activestyle="none", exportselection=False)
        self.lista_ejemplos.grid(row=1, sticky="nsew")
        for ejemplo in EJEMPLOS:
            self.lista_ejemplos.insert("end", ejemplo.nombre)
        self.lista_ejemplos.bind("<<ListboxSelect>>", lambda _: self._describir_ejemplo())
        self.lista_ejemplos.bind("<Double-Button-1>", lambda _: self._cargar_seleccion())
        self.detalle_ejemplo = ttk.Label(ejemplos, wraplength=850)
        self.detalle_ejemplo.grid(row=2, sticky="w", pady=12)
        ttk.Button(ejemplos, text="Cargar ejemplo", style="Primary.TButton", command=self._cargar_seleccion).grid(row=3, sticky="w")
        ayuda.rowconfigure(0, weight=1)
        ayuda.columnconfigure(0, weight=1)
        texto_ayuda = tk.Text(ayuda, wrap="word", bg="white", fg=TINTA, font=("Segoe UI", 11), relief="flat", padx=20, pady=16)
        texto_ayuda.grid(row=0, column=0, sticky="nsew")
        barra = ttk.Scrollbar(ayuda, command=texto_ayuda.yview)
        barra.grid(row=0, column=1, sticky="ns")
        texto_ayuda.configure(yscrollcommand=barra.set)
        texto_ayuda.insert("1.0", AYUDA)
        texto_ayuda.configure(state="disabled")
        ttk.Label(self, textvariable=self.estado_var, foreground=MUTED).pack(anchor="w", padx=26, pady=(0, 8))
        self.funcion_var.trace_add("write", lambda *_: self.actualizar_preview())
        self.tolerancia_var.trace_add("write", lambda *_: self.actualizar_preview())

    def clave_sistema(self):
        return next(clave for clave, sistema in SISTEMAS.items() if sistema.nombre == self.sistema_var.get())

    def cambiar_sistema(self):
        sistema = SISTEMAS[self.clave_sistema()]
        self.descripcion.configure(text=sistema.descripcion)
        self.pista_funcion.configure(text="Usa ^ para potencias, * para multiplicar y pi para π.")
        for widget in self.marco_limites.winfo_children():
            widget.destroy()
        self.variables_limites = []
        for col, texto in enumerate(("Variable", "Desde", "Hasta")):
            ttk.Label(self.marco_limites, text=texto, style="Muted.TLabel").grid(row=0, column=col, sticky="w", pady=(0, 4))
        self.marco_limites.columnconfigure(1, weight=1)
        self.marco_limites.columnconfigure(2, weight=1)
        for indice, variable in enumerate(sistema.variables):
            inferior = tk.StringVar(value="0")
            superior = tk.StringVar(value="2*pi" if variable == "theta" else "pi" if variable == "phi" else "1")
            ttk.Label(self.marco_limites, text=variable, style="Card.TLabel", width=8).grid(row=indice+1, column=0, sticky="w")
            ttk.Entry(self.marco_limites, textvariable=inferior, width=14).grid(row=indice+1, column=1, sticky="ew", padx=(0, 8), pady=3)
            ttk.Entry(self.marco_limites, textvariable=superior, width=14).grid(row=indice+1, column=2, sticky="ew", pady=3)
            self.variables_limites.append((inferior, superior))
            inferior.trace_add("write", lambda *_: self.actualizar_preview())
            superior.trace_add("write", lambda *_: self.actualizar_preview())
        self.jacobiano_var.set(True)
        self.casilla_jacobiano.configure(text=f"Incluir jacobiano: {sistema.jacobiano}")
        self.actualizar_preview()

    def leer_problema(self):
        try:
            tolerancia = float(self.tolerancia_var.get())
        except ValueError as exc:
            raise ValueError("Escribe una tolerancia numérica, por ejemplo 1e-7.") from exc
        return Problema(self.clave_sistema(), self.funcion_var.get(),
                        tuple((a.get(), b.get()) for a, b in self.variables_limites),
                        self.jacobiano_var.get(), tolerancia)

    def escribir_reporte(self, texto):
        self.reporte.configure(state="normal")
        self.reporte.delete("1.0", "end")
        self.reporte.insert("1.0", texto)
        self.reporte.configure(state="disabled")

    def actualizar_preview(self):
        if self.ocupado:
            return
        self.ultimo_reporte = ""
        self.valor_label.configure(text="—")
        self.detalle_label.configure(text="Pulsa Calcular para evaluar este planteamiento.")
        self.boton_copiar.configure(state="disabled")
        self.boton_guardar.configure(state="disabled")
        try:
            self.escribir_reporte(describir(self.leer_problema()))
        except ValueError:
            self.escribir_reporte("Completa la función, los límites y la tolerancia.")

    def cargar_ejemplo(self, ejemplo):
        if self.ocupado:
            self.estado_var.set("Cancela el cálculo actual antes de cargar otro ejemplo.")
            return
        problema = ejemplo.problema
        self.sistema_var.set(SISTEMAS[problema.sistema].nombre)
        self.cambiar_sistema()
        self.funcion_var.set(problema.funcion)
        for variables, valores in zip(self.variables_limites, problema.limites):
            variables[0].set(valores[0])
            variables[1].set(valores[1])
        self.jacobiano_var.set(problema.jacobiano)
        self.tolerancia_var.set(f"{problema.tolerancia:g}")
        self.pestanas.select(0)
        self.estado_var.set(f"Ejemplo cargado: {ejemplo.nombre}")

    def _describir_ejemplo(self):
        seleccion = self.lista_ejemplos.curselection()
        if seleccion:
            ejemplo = EJEMPLOS[seleccion[0]]
            self.detalle_ejemplo.configure(text=f"{ejemplo.descripcion}\nReferencia analítica: {ejemplo.exacto} ≈ {ejemplo.referencia:.12g}")

    def _cargar_seleccion(self):
        seleccion = self.lista_ejemplos.curselection()
        if seleccion:
            self.cargar_ejemplo(EJEMPLOS[seleccion[0]])

    def calcular(self):
        if self.ocupado:
            return
        try:
            problema = self.leer_problema()
            validar(problema)
        except ValueError as exc:
            messagebox.showerror("Revisa la integral", str(exc), parent=self)
            return
        self.problema_activo = problema
        self.ultimo_reporte = ""
        self.ocupado = True
        self.cancelacion.clear()
        self.boton_calcular.configure(state="disabled")
        self.boton_cancelar.configure(state="normal")
        self.boton_copiar.configure(state="disabled")
        self.boton_guardar.configure(state="disabled")
        # Conserva el formulario que corresponde al resultado en curso.
        self._habilitar_formulario(False)
        self.valor_label.configure(text="Calculando…")
        self.detalle_label.configure(text="Cuadratura adaptativa en curso.")
        self.escribir_reporte(describir(problema))
        self.estado_var.set("Calculando… Puedes cancelar. Tiempo máximo: 60 segundos.")
        self.progreso.start(12)

        def trabajo():
            try:
                self.cola.put((True, resolver(problema, self.cancelacion)))
            except Exception as exc:
                self.cola.put((False, exc))
        threading.Thread(target=trabajo, daemon=True).start()

    def _habilitar_formulario(self, habilitar):
        def recorrer(widget):
            for hijo in widget.winfo_children():
                if isinstance(hijo, (ttk.Entry, ttk.Checkbutton)):
                    hijo.configure(state="normal" if habilitar else "disabled")
                recorrer(hijo)
        recorrer(self.entrada_funcion.master)
        self.selector_sistema.configure(state="readonly" if habilitar else "disabled")

    def cancelar(self):
        if self.ocupado:
            self.cancelacion.set()
            self.estado_var.set("Cancelando cálculo…")

    def _recibir(self):
        try:
            exito, contenido = self.cola.get_nowait()
        except queue.Empty:
            self.after(120, self._recibir)
            return
        self.ocupado = False
        self.progreso.stop()
        self._habilitar_formulario(True)
        self.boton_calcular.configure(state="normal")
        self.boton_cancelar.configure(state="disabled")
        if exito:
            resultado = contenido
            self.valor_label.configure(text=f"{resultado.valor:.12g}")
            self.detalle_label.configure(text=f"Error estimado: {resultado.error_estimado:.3g}\n{resultado.evaluaciones:,} evaluaciones · {resultado.segundos:.3f} s")
            reporte = describir(self.problema_activo)
            reporte += f"\n\nResultado ≈ {resultado.valor:.15g}\nError estimado: {resultado.error_estimado:.6g}"
            reporte += f"\nEvaluaciones: {resultado.evaluaciones}\nTiempo: {resultado.segundos:.3f} s"
            reporte += "\n\nEl error es el máximo de las estimaciones de los niveles; no es una cota garantizada del error total."
            if resultado.advertencias:
                reporte += "\n\nADVERTENCIAS\nEl resultado requiere revisión.\n" + "\n".join(resultado.advertencias)
            self.ultimo_reporte = reporte
            self.escribir_reporte(reporte)
            self.boton_copiar.configure(state="normal")
            self.boton_guardar.configure(state="normal")
            self.estado_var.set("Cálculo terminado con advertencias: revisa el reporte." if resultado.advertencias else "Cálculo terminado · Ctrl+Enter para calcular de nuevo")
        else:
            self.valor_label.configure(text="—")
            self.detalle_label.configure(text="Cálculo cancelado." if isinstance(contenido, CalculoCancelado) else "Revisa la función y los límites.")
            self.escribir_reporte(describir(self.problema_activo) + f"\n\n{contenido}")
            self.estado_var.set(str(contenido))
        self.after(120, self._recibir)

    def copiar(self):
        if self.ultimo_reporte:
            self.clipboard_clear()
            self.clipboard_append(self.ultimo_reporte)
            self.estado_var.set("Reporte copiado al portapapeles.")

    def guardar(self):
        if not self.ultimo_reporte:
            return
        ruta = filedialog.asksaveasfilename(parent=self, title="Guardar resultado", defaultextension=".txt", initialfile="resultado_integral.txt", filetypes=[("Texto", "*.txt")])
        if ruta:
            try:
                with open(ruta, "w", encoding="utf-8") as archivo:
                    archivo.write(self.ultimo_reporte + "\n")
                self.estado_var.set(f"Resultado guardado: {ruta}")
            except OSError as exc:
                messagebox.showerror("No se pudo guardar", str(exc), parent=self)

    def _cerrar(self):
        self.cancelacion.set()
        self.destroy()


def iniciar():
    Aplicacion().mainloop()
