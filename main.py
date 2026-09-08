import tkinter as tk

import os
from dotenv import load_dotenv

from functions import (
    obtener_unidades,
    obtener_etiqueta,
    mostrar_aviso
)

load_dotenv()
volume_label = os.getenv("VOLUME_LABEL")

class Aplicacion:
    def __init__(self, root):
        self.root = root

        self.root.withdraw()

        self.unidades_actuales = set()

        self.detectar_sd()

    def detectar_sd(self):
        unidades = obtener_unidades()

        for unidad in unidades:

            if unidad in self.unidades_actuales:
                continue

            etiqueta = obtener_etiqueta(unidad)

            if etiqueta and etiqueta.upper() == volume_label.upper():

                print(f"SD detectada: {unidad}")
                print(f"Etiqueta: {etiqueta}")

                mostrar_aviso(unidad, etiqueta)

        self.unidades_actuales = set(unidades)

        # Volver a revisar en 2 segundos
        self.root.after(2000, self.detectar_sd)


if __name__ == "__main__":
    root = tk.Tk()

    app = Aplicacion(root)

    root.mainloop()