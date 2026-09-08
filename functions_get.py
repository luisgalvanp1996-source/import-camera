import os
import tkinter as tk
from tkinter import ttk, messagebox

from db import (
    obtener_historial_fotos,
    obtener_foto_por_id
)


def obtener_historial():
    """
    Obtiene el historial completo de fotografías.
    """

    return obtener_historial_fotos()


def obtener_detalle_foto(foto_id):
    """
    Obtiene los detalles de una fotografía por su UUID.
    """

    return obtener_foto_por_id(foto_id)


def mostrar_historial(ventana_principal):
    """
    Abre la ventana independiente del historial.
    """

    ventana = tk.Toplevel(ventana_principal)

    ventana.title("Historial - SONY Sync")
    ventana.geometry("950x550")
    ventana.minsize(800, 450)

    ventana.transient(ventana_principal)

    # Llevar la ventana al frente al abrirla
    ventana.lift()
    ventana.focus_force()

    # ---------------------------------------------------------
    # TÍTULO
    # ---------------------------------------------------------

    titulo = tk.Label(
        ventana,
        text="📋 Historial de fotografías",
        font=("Segoe UI", 16, "bold")
    )
    titulo.pack(
        anchor="w",
        padx=20,
        pady=(15, 5)
    )

    subtitulo = tk.Label(
        ventana,
        text="Archivos registrados en SONY.db",
        font=("Segoe UI", 10)
    )
    subtitulo.pack(
        anchor="w",
        padx=20,
        pady=(0, 10)
    )

    # ---------------------------------------------------------
    # CONTENEDOR DE TABLA
    # ---------------------------------------------------------

    marco_tabla = tk.Frame(ventana)
    marco_tabla.pack(
        fill="both",
        expand=True,
        padx=20,
        pady=5
    )

    columnas = (
        "nombre",
        "fecha",
        "formato",
        "tamano",
        "estado"
    )

    tabla = ttk.Treeview(
        marco_tabla,
        columns=columnas,
        show="headings",
        selectmode="browse"
    )

    tabla.heading(
        "nombre",
        text="Archivo original"
    )

    tabla.heading(
        "fecha",
        text="Fecha de importación"
    )

    tabla.heading(
        "formato",
        text="Formato"
    )

    tabla.heading(
        "tamano",
        text="Tamaño"
    )

    tabla.heading(
        "estado",
        text="Estado"
    )

    tabla.column(
        "nombre",
        width=250
    )

    tabla.column(
        "fecha",
        width=180
    )

    tabla.column(
        "formato",
        width=100,
        anchor="center"
    )

    tabla.column(
        "tamano",
        width=120,
        anchor="e"
    )

    tabla.column(
        "estado",
        width=150,
        anchor="center"
    )

    scrollbar_vertical = ttk.Scrollbar(
        marco_tabla,
        orient="vertical",
        command=tabla.yview
    )

    scrollbar_horizontal = ttk.Scrollbar(
        marco_tabla,
        orient="horizontal",
        command=tabla.xview
    )

    tabla.configure(
        yscrollcommand=scrollbar_vertical.set,
        xscrollcommand=scrollbar_horizontal.set
    )

    tabla.grid(
        row=0,
        column=0,
        sticky="nsew"
    )

    scrollbar_vertical.grid(
        row=0,
        column=1,
        sticky="ns"
    )

    scrollbar_horizontal.grid(
        row=1,
        column=0,
        sticky="ew"
    )

    marco_tabla.grid_rowconfigure(
        0,
        weight=1
    )

    marco_tabla.grid_columnconfigure(
        0,
        weight=1
    )

    # ---------------------------------------------------------
    # CARGAR DATOS
    # ---------------------------------------------------------

    historial = obtener_historial()

    for registro in historial:

        (
            foto_id,
            nombre_original,
            extension,
            formato,
            fecha_captura,
            fecha_importacion,
            nombre_archivo,
            ruta_archivo,
            tamano_bytes,
            estado,
            fecha_creacion,
            fecha_actualizacion
        ) = registro

        if tamano_bytes is not None:

            tamano_mb = tamano_bytes / (
                1024 * 1024
            )

            tamano_texto = f"{tamano_mb:.2f} MB"

        else:

            tamano_texto = "-"

        if estado == "SINCRONIZADO":
            estado_texto = "✅ Sincronizado"

        elif estado == "ERROR":
            estado_texto = "❌ Error"

        elif estado == "PENDIENTE":
            estado_texto = "⏳ Pendiente"

        else:
            estado_texto = estado or "-"

        tabla.insert(
            "",
            "end",
            iid=foto_id,
            values=(
                nombre_original,
                fecha_importacion,
                formato or "-",
                tamano_texto,
                estado_texto
            )
        )

    # ---------------------------------------------------------
    # INFORMACIÓN INFERIOR
    # ---------------------------------------------------------

    cantidad = len(historial)

    etiqueta_cantidad = tk.Label(
        ventana,
        text=f"{cantidad} archivo(s) registrado(s)",
        font=("Segoe UI", 10)
    )

    etiqueta_cantidad.pack(
        anchor="w",
        padx=20,
        pady=(5, 5)
    )

    # ---------------------------------------------------------
    # BOTONES
    # ---------------------------------------------------------

    marco_botones = tk.Frame(ventana)
    marco_botones.pack(
        fill="x",
        padx=20,
        pady=(5, 15)
    )

    def ver_detalle():

        seleccion = tabla.selection()

        if not seleccion:
            messagebox.showinfo(
                "Selecciona un archivo",
                "Selecciona una fotografía de la tabla.",
                parent=ventana
            )
            return

        foto_id = seleccion[0]

        mostrar_detalle_foto(
            ventana,
            foto_id
        )

    boton_detalle = tk.Button(
        marco_botones,
        text="🔎 Ver detalles",
        width=18,
        command=ver_detalle
    )

    boton_detalle.pack(
        side="left"
    )

    boton_cerrar = tk.Button(
        marco_botones,
        text="Cerrar",
        width=12,
        command=ventana.destroy
    )

    boton_cerrar.pack(
        side="right"
    )

    # ---------------------------------------------------------
    # DOBLE CLIC
    # ---------------------------------------------------------

    tabla.bind(
        "<Double-1>",
        lambda evento: ver_detalle()
    )

    return ventana

def mostrar_detalle_foto(ventana_padre, foto_id):
    """
    Muestra los detalles completos de una fotografía.
    """

    registro = obtener_detalle_foto(foto_id)

    if not registro:
        messagebox.showerror(
            "Error",
            "No se encontró la fotografía.",
            parent=ventana_padre
        )
        return

    (
        foto_id,
        hash_sha256,
        nombre_original,
        extension,
        formato,
        fecha_captura,
        fecha_importacion,
        nombre_archivo,
        ruta_archivo,
        tamano_bytes,
        estado,
        fecha_creacion,
        fecha_actualizacion
    ) = registro

    ventana = tk.Toplevel(ventana_padre)

    ventana.title("Detalles de fotografía")
    ventana.geometry("650x500")
    ventana.resizable(False, False)

    ventana.transient(ventana_padre)

    ventana.lift()
    ventana.focus_force()

    titulo = tk.Label(
        ventana,
        text="🔎 Detalles de fotografía",
        font=("Segoe UI", 15, "bold")
    )

    titulo.pack(
        anchor="w",
        padx=20,
        pady=(20, 15)
    )

    marco = tk.Frame(ventana)
    marco.pack(
        fill="both",
        expand=True,
        padx=20
    )

    datos = [
        ("Nombre original", nombre_original),
        ("UUID", foto_id),
        ("SHA-256", hash_sha256),
        ("Extensión", extension),
        ("Formato", formato or "-"),
        ("Fecha de captura", fecha_captura or "No disponible"),
        ("Fecha de importación", fecha_importacion or "-"),
        ("Nombre destino", nombre_archivo or "-"),
        ("Ruta destino", ruta_archivo or "-"),
        ("Tamaño", (
            f"{tamano_bytes / (1024 * 1024):.2f} MB"
            if tamano_bytes is not None
            else "-"
        )),
        ("Estado", estado or "-"),
        ("Fecha de actualización", fecha_actualizacion or "-")
    ]

    for fila, (nombre, valor) in enumerate(datos):

        etiqueta = tk.Label(
            marco,
            text=f"{nombre}:",
            font=("Segoe UI", 9, "bold"),
            anchor="w"
        )

        etiqueta.grid(
            row=fila,
            column=0,
            sticky="nw",
            padx=(0, 15),
            pady=4
        )

        valor_label = tk.Label(
            marco,
            text=str(valor),
            font=("Segoe UI", 9),
            anchor="w",
            justify="left",
            wraplength=480
        )

        valor_label.grid(
            row=fila,
            column=1,
            sticky="nw",
            pady=4
        )

    marco.columnconfigure(
        1,
        weight=1
    )

    boton_cerrar = tk.Button(
        ventana,
        text="Cerrar",
        width=15,
        command=ventana.destroy
    )

    boton_cerrar.pack(
        pady=15
    )