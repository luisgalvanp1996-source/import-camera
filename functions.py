import os
import string
import ctypes
import hashlib
import tkinter as tk
from tkinter import filedialog, messagebox

from functions_get import mostrar_historial

from data import (
    VOLUME_LABEL,
    CARPETA_POR_ORGANIZAR
)

from db import (
    foto_existe,
    insertar_foto,
    insertar_archivo,
    actualizar_archivo,
    buscar_foto_sincronizada_por_hash
)

####################################################################################
def calcular_hash_sha256(ruta):
    """Calcula el SHA-256 de un archivo."""
    sha256 = hashlib.sha256()

    with open(ruta, "rb") as archivo:
        for bloque in iter(lambda: archivo.read(1024 * 1024), b""):
            sha256.update(bloque)

    return sha256.hexdigest()

def buscar_archivos_sincronizados(unidad):
    """
    Busca en la SD todos los archivos multimedia que ya
    fueron sincronizados correctamente.
    """

    carpeta_dcim = os.path.join(unidad, "DCIM")

    extensiones_multimedia = {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
        ".mp4",
        ".mov",
        ".avi"
    }

    archivos_sincronizados = []

    print("\n================================")
    print("BUSCANDO ARCHIVOS SINCRONIZADOS")
    print("================================")
    print(f"Unidad: {unidad}")

    if not os.path.exists(carpeta_dcim):
        print("No se encontró la carpeta DCIM.")
        return []

    for raiz, carpetas, archivos_encontrados in os.walk(
        carpeta_dcim
    ):

        for nombre_archivo in archivos_encontrados:

            extension = os.path.splitext(
                nombre_archivo
            )[1].lower()

            if extension not in extensiones_multimedia:
                continue

            ruta_completa = os.path.join(
                raiz,
                nombre_archivo
            )

            try:
                print("\n--------------------------------")
                print(f"Archivo: {nombre_archivo}")

                hash_sha256 = calcular_hash_sha256(
                    ruta_completa
                )

                print(f"SHA-256: {hash_sha256}")

                resultado = buscar_foto_sincronizada_por_hash(
                    hash_sha256
                )

                if resultado:

                    print("Estado: SINCRONIZADO")
                    print(
                        f"UUID: {resultado[0]}"
                    )

                    archivos_sincronizados.append(
                        ruta_completa
                    )

                else:

                    print("Estado: NO SINCRONIZADO")

            except Exception as error:

                print("\nERROR:")
                print(error)

    print("\n================================")
    print("BÚSQUEDA FINALIZADA")
    print("================================")

    print(
        f"Archivos sincronizados encontrados: "
        f"{len(archivos_sincronizados)}"
    )

    for archivo in archivos_sincronizados:
        print(f"  - {archivo}")

    print("================================\n")

    return archivos_sincronizados

def eliminar_archivos_sincronizados(unidad, ventana=None):
    """
    Busca archivos multimedia ya sincronizados y solicita
    confirmación antes de eliminarlos de la SD.
    """

    archivos_sincronizados = buscar_archivos_sincronizados(unidad)

    if not archivos_sincronizados:
        messagebox.showinfo(
            "Nada que eliminar",
            "No se encontraron archivos sincronizados "
            "que puedan eliminarse de la SD.",
            parent=ventana
        )
        return

    cantidad = len(archivos_sincronizados)

    # Mostrar lista de archivos que serán eliminados
    lista_archivos = "\n".join(
        os.path.basename(archivo)
        for archivo in archivos_sincronizados
    )

    confirmacion = messagebox.askyesno(
        "Confirmar eliminación",
        f"Se encontraron {cantidad} archivo(s) "
        "que ya fueron sincronizados correctamente.\n\n"
        "Estos archivos serán eliminados de la SD:\n\n"
        f"{lista_archivos}\n\n"
        "Esta acción no se puede deshacer.\n\n"
        "¿Deseas continuar?",
        parent=ventana
    )

    if not confirmacion:
        print("\nEliminación cancelada por el usuario.")
        return

    eliminados = []
    errores = []

    print("\n================================")
    print("ELIMINANDO ARCHIVOS SINCRONIZADOS")
    print("================================")

    for archivo in archivos_sincronizados:

        try:
            print(f"Eliminando: {archivo}")

            os.remove(archivo)

            eliminados.append(archivo)

            print("Resultado: ELIMINADO")

        except Exception as error:

            errores.append((archivo, error))

            print("ERROR:")
            print(error)

    print("\n================================")
    print("ELIMINACIÓN FINALIZADA")
    print("================================")

    print(f"Encontrados: {cantidad}")
    print(f"Eliminados:  {len(eliminados)}")
    print(f"Errores:     {len(errores)}")
    print("================================\n")

    if errores:

        detalle_errores = "\n".join(
            f"{os.path.basename(archivo)}: {error}"
            for archivo, error in errores
        )

        messagebox.showwarning(
            "Eliminación con errores",
            f"Se eliminaron {len(eliminados)} de "
            f"{cantidad} archivos.\n\n"
            f"Errores:\n{detalle_errores}",
            parent=ventana
            
        )

    else:

        messagebox.showinfo(
            "Eliminación completada",
            f"Se eliminaron correctamente "
            f"{len(eliminados)} archivo(s) de la SD.",
            parent=ventana
        )

def obtener_unidades():
    """Obtiene las unidades disponibles en Windows."""
    unidades = []

    for letra in string.ascii_uppercase:
        ruta = f"{letra}:\\"

        if os.path.exists(ruta):
            unidades.append(ruta)

    return unidades


def obtener_etiqueta(ruta):
    """Obtiene la etiqueta del volumen."""
    volumen = ctypes.create_unicode_buffer(261)
    sistema = ctypes.create_unicode_buffer(261)

    try:
        resultado = ctypes.windll.kernel32.GetVolumeInformationW(
            ctypes.c_wchar_p(ruta),
            volumen,
            len(volumen),
            None,
            None,
            None,
            sistema,
            len(sistema)
        )

        if resultado:
            return volumen.value

    except Exception:
        pass

    return None


def abrir_dcim(unidad, ventana):
    """Abre la carpeta DCIM de la unidad detectada."""

    ruta_dcim = os.path.join(unidad, "DCIM")

    if os.path.exists(ruta_dcim):
        # Ocultar nuestra ventana
        ventana.withdraw()

        # Abrir DCIM en el Explorador de Windows
        os.startfile(ruta_dcim)

    else:
        messagebox.showwarning(
            "Carpeta no encontrada",
            f"No se encontró la carpeta:\n\n{ruta_dcim}"
        )





def seleccionar_fotos():
    """Selecciona fotografías/videos, los registra en SQLite y los sincroniza."""

    archivos = filedialog.askopenfilenames(
        title="Seleccionar fotos y videos",
        filetypes=[
            ("Fotos y videos", "*.jpg *.jpeg *.png *.webp *.mp4 *.mov *.avi"),
            ("Imágenes", "*.jpg *.jpeg *.png *.webp"),
            ("Videos", "*.mp4 *.mov *.avi"),
            ("JPEG", "*.jpg *.jpeg"),
            ("PNG", "*.png"),
            ("Todos los archivos", "*.*")
        ]
    )

    if not archivos:
        return []

    # Comprobar que la carpeta de destino esté disponible
    if not os.path.exists(CARPETA_POR_ORGANIZAR):
        messagebox.showerror(
            "Destino no disponible",
            "No se puede acceder a la carpeta de destino:\n\n"
            f"{CARPETA_POR_ORGANIZAR}\n\n"
            "Verifica que la unidad de red esté conectada."
        )

        print("\nERROR: carpeta de destino no disponible.")
        print(CARPETA_POR_ORGANIZAR)

        return []

    fotos_nuevas = []
    fotos_existentes = []
    fotos_sincronizadas = []
    fotos_error = []

    print("\n================================")
    print("INICIANDO SINCRONIZACIÓN")
    print("================================")
    print(f"Destino: {CARPETA_POR_ORGANIZAR}")

    for archivo in archivos:

        foto_id = None
        ruta_destino = None
        ruta_temporal = None
        copia_iniciada = False

        try:
            nombre_original = os.path.basename(archivo)
            extension = os.path.splitext(nombre_original)[1].lower()

            # -----------------------------------------
            # 1. Calcular SHA-256 del archivo original
            # -----------------------------------------

            hash_sha256 = calcular_hash_sha256(archivo)

            print("\n--------------------------------")
            print(f"Archivo: {nombre_original}")
            print(f"SHA-256: {hash_sha256}")

            # -----------------------------------------
            # 2. Comprobar si ya existe por SHA-256
            # -----------------------------------------

            if foto_existe(hash_sha256):
                fotos_existentes.append(archivo)

                print("Resultado: YA EXISTE")
                print("Acción: OMITIDA")

                continue

            # -----------------------------------------
            # 3. Archivo nuevo
            # -----------------------------------------

            fotos_nuevas.append(archivo)

            import uuid
            import shutil

            foto_id = str(uuid.uuid4())

            tamano_bytes = os.path.getsize(archivo)
            formato = extension.replace(".", "").upper()

            print("Resultado: NUEVA")
            print(f"UUID: {foto_id}")
            print(f"Tamaño: {tamano_bytes} bytes")

            # -----------------------------------------
            # 4. Registrar foto en SQLite
            # -----------------------------------------

            insertar_foto(
                foto_id=foto_id,
                hash_sha256=hash_sha256,
                nombre_original=nombre_original,
                extension=extension,
                formato=formato,
                fecha_captura=None
            )

            # -----------------------------------------
            # 5. Crear nombre físico usando UUID
            # -----------------------------------------
            #
            # Ejemplo:
            #
            # DSC00001.JPG
            #
            # se convierte en:
            #
            # 8f5a3c2e-1234-4567-89ab-cdef12345678.JPG
            #
            # Esto evita colisiones cuando la cámara
            # vuelve a generar DSC00001.JPG.
            # -----------------------------------------

            nombre_destino = f"{foto_id}{extension}"

            ruta_destino = os.path.join(
                CARPETA_POR_ORGANIZAR,
                nombre_destino
            )

            # Archivo temporal utilizado durante la copia
            ruta_temporal = ruta_destino + ".tmp"

            # -----------------------------------------
            # 6. Comprobar que el destino final no exista
            # -----------------------------------------

            if os.path.exists(ruta_destino):
                raise FileExistsError(
                    f"Ya existe un archivo con el UUID:\n"
                    f"{ruta_destino}"
                )

            # -----------------------------------------
            # 7. Registrar ubicación como PENDIENTE
            # -----------------------------------------

            insertar_archivo(
                foto_id=foto_id,
                nombre_archivo=nombre_destino,
                ruta_archivo=ruta_destino,
                tamano_bytes=tamano_bytes,
                estado="PENDIENTE"
            )

            print("SQLite: REGISTRADA")
            print("Estado: PENDIENTE")
            print(f"Nombre original: {nombre_original}")
            print(f"Nombre destino: {nombre_destino}")
            print(f"Destino: {ruta_destino}")

            # -----------------------------------------
            # 8. Copiar a archivo temporal
            # -----------------------------------------

            print("Copiando archivo...")

            copia_iniciada = True

            shutil.copy2(
                archivo,
                ruta_temporal
            )

            print("Copia temporal terminada.")

            # -----------------------------------------
            # 9. Verificar tamaño
            # -----------------------------------------

            tamano_temporal = os.path.getsize(ruta_temporal)

            if tamano_temporal != tamano_bytes:
                raise IOError(
                    "El tamaño del archivo copiado no coincide."
                )

            print("Verificación de tamaño: OK")

            # -----------------------------------------
            # 10. Verificar SHA-256
            # -----------------------------------------

            hash_temporal = calcular_hash_sha256(
                ruta_temporal
            )

            print(f"SHA-256 temporal: {hash_temporal}")

            if hash_temporal != hash_sha256:
                raise IOError(
                    "El SHA-256 del archivo copiado no coincide."
                )

            print("Verificación SHA-256: OK")

            # -----------------------------------------
            # 11. Mover archivo temporal al definitivo
            # -----------------------------------------

            if os.path.exists(ruta_destino):
                raise FileExistsError(
                    f"El archivo destino apareció durante la copia:\n"
                    f"{ruta_destino}"
                )

            os.replace(
                ruta_temporal,
                ruta_destino
            )

            ruta_temporal = None

            print("Archivo definitivo creado.")
            print(f"Ruta final: {ruta_destino}")

            # -----------------------------------------
            # 12. Marcar como SINCRONIZADO
            # -----------------------------------------

            actualizar_archivo(
                foto_id=foto_id,
                nombre_archivo=nombre_destino,
                ruta_archivo=ruta_destino,
                estado="SINCRONIZADO"
            )

            fotos_sincronizadas.append(archivo)

            print("Estado: SINCRONIZADO")
            print("Sincronización correcta.")

        except Exception as error:

            fotos_error.append(archivo)

            print("\nERROR:")
            print(error)

            # -----------------------------------------
            # Marcar registro como ERROR
            # -----------------------------------------

            if foto_id is not None:
                try:
                    actualizar_archivo(
                        foto_id=foto_id,
                        estado="ERROR"
                    )
                except Exception as error_db:
                    print(
                        f"Error actualizando SQLite: {error_db}"
                    )

            # -----------------------------------------
            # Eliminar SOLO el archivo temporal
            # -----------------------------------------
            #
            # Importante:
            # Nunca eliminamos un archivo existente del
            # destino por accidente.
            # -----------------------------------------

            if ruta_temporal and os.path.exists(ruta_temporal):
                try:
                    os.remove(ruta_temporal)
                    print("Archivo temporal eliminado.")
                except Exception as error_borrado:
                    print(
                        f"No se pudo eliminar el archivo temporal: "
                        f"{error_borrado}"
                    )

            # -----------------------------------------
            # Si la copia terminó pero ocurrió un error
            # antes de mover el temporal, no tocamos
            # ningún archivo definitivo.
            # -----------------------------------------

            if (
                copia_iniciada
                and ruta_destino
                and os.path.exists(ruta_destino)
            ):
                print(
                    "El archivo definitivo existe y NO será eliminado "
                    "automáticamente."
                )

    # -----------------------------------------
    # RESUMEN
    # -----------------------------------------

    print("\n================================")
    print("SINCRONIZACIÓN FINALIZADA")
    print("================================")
    print(f"Total seleccionadas: {len(archivos)}")
    print(f"Ya existentes:       {len(fotos_existentes)}")
    print(f"Nuevas:              {len(fotos_nuevas)}")
    print(f"Sincronizadas:       {len(fotos_sincronizadas)}")
    print(f"Errores:             {len(fotos_error)}")
    print("================================\n")

    messagebox.showinfo(
        "Sincronización finalizada",
        f"Fotos/videos seleccionados: {len(archivos)}\n\n"
        f"Ya existentes: {len(fotos_existentes)}\n"
        f"Nuevos: {len(fotos_nuevas)}\n"
        f"Sincronizados: {len(fotos_sincronizadas)}\n"
        f"Errores: {len(fotos_error)}"
    )

    return fotos_sincronizadas


def sincronizar_archivos(archivos, ventana=None):
    """Sincroniza una lista de archivos multimedia."""

    import uuid
    import shutil

    fotos_nuevas = []
    fotos_existentes = []
    fotos_sincronizadas = []
    fotos_error = []

    print("\n================================")
    print("INICIANDO PROCESAMIENTO")
    print("================================")
    print(f"Archivos a procesar: {len(archivos)}")
    print(f"Destino: {CARPETA_POR_ORGANIZAR}")

    for archivo in archivos:

        foto_id = None
        ruta_destino = None
        ruta_temporal = None

        try:
            # -----------------------------------------
            # 1. Información del archivo
            # -----------------------------------------

            nombre_original = os.path.basename(archivo)
            extension = os.path.splitext(nombre_original)[1].lower()

            print("\n--------------------------------")
            print(f"Archivo: {nombre_original}")

            # -----------------------------------------
            # 2. Calcular SHA-256
            # -----------------------------------------

            hash_sha256 = calcular_hash_sha256(archivo)

            print(f"SHA-256: {hash_sha256}")

            # -----------------------------------------
            # 3. Comprobar si ya existe
            # -----------------------------------------

            if foto_existe(hash_sha256):

                fotos_existentes.append(archivo)

                print("Resultado: YA EXISTE")
                print("Acción: OMITIDA")

                continue

            # -----------------------------------------
            # 4. Archivo nuevo
            # -----------------------------------------

            fotos_nuevas.append(archivo)

            foto_id = str(uuid.uuid4())

            tamano_bytes = os.path.getsize(archivo)
            formato = extension.replace(".", "").upper()

            print("Resultado: NUEVO")
            print(f"UUID: {foto_id}")
            print(f"Tamaño: {tamano_bytes} bytes")

            # -----------------------------------------
            # 5. Registrar en Fotos
            # -----------------------------------------

            insertar_foto(
                foto_id=foto_id,
                hash_sha256=hash_sha256,
                nombre_original=nombre_original,
                extension=extension,
                formato=formato,
                fecha_captura=None
            )

            # -----------------------------------------
            # 6. Crear nombre físico
            # -----------------------------------------

            nombre_destino = f"{foto_id}{extension}"

            ruta_destino = os.path.join(
                CARPETA_POR_ORGANIZAR,
                nombre_destino
            )

            ruta_temporal = ruta_destino + ".tmp"

            print(f"Nombre destino: {nombre_destino}")
            print(f"Destino: {ruta_destino}")

            # -----------------------------------------
            # 7. Comprobar que UUID no exista
            # -----------------------------------------

            if os.path.exists(ruta_destino):
                raise FileExistsError(
                    f"Ya existe un archivo con ese UUID:\n"
                    f"{ruta_destino}"
                )

            # -----------------------------------------
            # 8. Registrar archivo como PENDIENTE
            # -----------------------------------------

            insertar_archivo(
                foto_id=foto_id,
                nombre_archivo=nombre_destino,
                ruta_archivo=ruta_destino,
                tamano_bytes=tamano_bytes,
                estado="PENDIENTE"
            )

            print("SQLite: REGISTRADA")
            print("Estado: PENDIENTE")

            # -----------------------------------------
            # 9. Copiar a archivo temporal
            # -----------------------------------------

            print("Copiando archivo...")

            shutil.copy2(
                archivo,
                ruta_temporal
            )

            print("Copia temporal terminada.")

            # -----------------------------------------
            # 10. Verificar tamaño
            # -----------------------------------------

            tamano_temporal = os.path.getsize(
                ruta_temporal
            )

            if tamano_temporal != tamano_bytes:
                raise IOError(
                    "El tamaño del archivo copiado no coincide."
                )

            print("Verificación de tamaño: OK")

            # -----------------------------------------
            # 11. Verificar SHA-256
            # -----------------------------------------

            hash_temporal = calcular_hash_sha256(
                ruta_temporal
            )

            print(f"SHA-256 temporal: {hash_temporal}")

            if hash_temporal != hash_sha256:
                raise IOError(
                    "El SHA-256 del archivo copiado no coincide."
                )

            print("Verificación SHA-256: OK")

            # -----------------------------------------
            # 12. Crear archivo definitivo
            # -----------------------------------------

            os.replace(
                ruta_temporal,
                ruta_destino
            )

            ruta_temporal = None

            print("Archivo definitivo creado.")

            # -----------------------------------------
            # 13. Marcar como SINCRONIZADO
            # -----------------------------------------

            actualizar_archivo(
                foto_id=foto_id,
                nombre_archivo=nombre_destino,
                ruta_archivo=ruta_destino,
                estado="SINCRONIZADO"
            )

            fotos_sincronizadas.append(archivo)

            print("Estado: SINCRONIZADO")
            print("Sincronización correcta.")

        except Exception as error:

            fotos_error.append(archivo)

            print("\nERROR:")
            print(error)

            # -----------------------------------------
            # Marcar como ERROR en SQLite
            # -----------------------------------------

            if foto_id is not None:

                try:
                    actualizar_archivo(
                        foto_id=foto_id,
                        estado="ERROR"
                    )

                except Exception as error_db:

                    print(
                        f"Error actualizando SQLite: {error_db}"
                    )

            # -----------------------------------------
            # Eliminar SOLO archivo temporal
            # -----------------------------------------

            if ruta_temporal and os.path.exists(ruta_temporal):

                try:
                    os.remove(ruta_temporal)

                    print(
                        "Archivo temporal eliminado."
                    )

                except Exception as error_borrado:

                    print(
                        "No se pudo eliminar el archivo "
                        f"temporal: {error_borrado}"
                    )

    # -----------------------------------------
    # RESUMEN
    # -----------------------------------------

    print("\n================================")
    print("PROCESAMIENTO FINALIZADO")
    print("================================")

    print(f"Total:           {len(archivos)}")
    print(f"Ya existentes:   {len(fotos_existentes)}")
    print(f"Nuevos:          {len(fotos_nuevas)}")
    print(f"Sincronizados:   {len(fotos_sincronizadas)}")
    print(f"Errores:         {len(fotos_error)}")

    print("================================\n")

    messagebox.showinfo(
        "Sincronización finalizada",
        f"Archivos procesados: {len(archivos)}\n\n"
        f"Ya existentes: {len(fotos_existentes)}\n"
        f"Nuevos: {len(fotos_nuevas)}\n"
        f"Sincronizados: {len(fotos_sincronizadas)}\n"
        f"Errores: {len(fotos_error)}",
        parent=ventana
    )

    return fotos_sincronizadas




def iniciar_sincronizacion(unidad, ventana=None):
    """Busca y sincroniza automáticamente todo el contenido multimedia."""

    print("\n================================")
    print("INICIANDO SINCRONIZACIÓN")
    print("================================")
    print(f"Unidad: {unidad}")

    # -----------------------------------------
    # 1. Localizar carpeta DCIM
    # -----------------------------------------

    carpeta_dcim = os.path.join(unidad, "DCIM")

    if not os.path.exists(carpeta_dcim):

        print("\nERROR:")
        print("No se encontró la carpeta DCIM:")
        print(carpeta_dcim)

        messagebox.showerror(
            "DCIM no encontrada",
            f"No se encontró la carpeta DCIM en:\n\n"
            f"{carpeta_dcim}"
        )

        return []

    print(f"DCIM encontrada: {carpeta_dcim}")

    # -----------------------------------------
    # 2. Extensiones multimedia
    # -----------------------------------------

    extensiones_multimedia = {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
        ".mp4",
        ".mov",
        ".avi"
    }

    archivos = []

    # -----------------------------------------
    # 3. Buscar archivos recursivamente
    # -----------------------------------------

    print("\nBuscando archivos multimedia...")

    for raiz, carpetas, archivos_encontrados in os.walk(
        carpeta_dcim
    ):

        for nombre_archivo in archivos_encontrados:

            extension = os.path.splitext(
                nombre_archivo
            )[1].lower()

            if extension in extensiones_multimedia:

                ruta_completa = os.path.join(
                    raiz,
                    nombre_archivo
                )

                archivos.append(ruta_completa)

    # -----------------------------------------
    # 4. Mostrar archivos encontrados
    # -----------------------------------------

    print("\n================================")
    print("BÚSQUEDA FINALIZADA")
    print("================================")

    print(
        f"Archivos multimedia encontrados: "
        f"{len(archivos)}"
    )

    for archivo in archivos:
        print(f"  - {archivo}")

    print("================================\n")

    # -----------------------------------------
    # 5. No hay archivos
    # -----------------------------------------

    if not archivos:

        messagebox.showinfo(
            "Sin archivos",
            "No se encontraron fotografías o videos "
            "en la carpeta DCIM."
        )

        return []

    # -----------------------------------------
    # 6. Iniciar sincronización real
    # -----------------------------------------

    return sincronizar_archivos(archivos)






def mostrar_aviso(unidad, etiqueta):
    """Muestra la ventana de opciones cuando se detecta la SD."""

    ventana = tk.Toplevel()
    ventana.title("Sincronizador de fotos")
    ventana.geometry("430x330")
    ventana.resizable(False, False)

    # Centrar ventana
    ventana.update_idletasks()

    ancho = 430
    alto = 430

    x = (ventana.winfo_screenwidth() // 2) - (ancho // 2)
    y = (ventana.winfo_screenheight() // 2) - (alto // 2)

    ventana.geometry(f"{ancho}x{alto}+{x}+{y}")

    # Mantener encima de otras ventanas
    ventana.attributes("-topmost", True)

    # Título
    titulo = tk.Label(
        ventana,
        text="📷 Cámara / SD detectada",
        font=("Segoe UI", 16, "bold")
    )
    titulo.pack(pady=(20, 10))

    # Información
    informacion = tk.Label(
        ventana,
        text=f"Etiqueta: {etiqueta}\nUnidad: {unidad}",
        font=("Segoe UI", 11)
    )
    informacion.pack(pady=(0, 15))

    # Botón sincronizar
    boton_sincronizar = tk.Button(
        ventana,
        text="🔄  Iniciar sincronización en segundo plano",
        width=40,
        height=2,
        command=lambda: iniciar_sincronizacion(unidad, ventana)
    )
    boton_sincronizar.pack(pady=5)

    #boton eliminar sincronizados
    boton_eliminar = tk.Button(
        ventana,
        text="🗑️  Eliminar fotos sincronizadas",
        width=40,
        height=2,
        command=lambda: eliminar_archivos_sincronizados(unidad, ventana)
    )
    boton_eliminar.pack(pady=5)

    # Botón seleccionar fotos
    boton_seleccionar = tk.Button(
        ventana,
        text="🖼️  Seleccionar fotos a sincronizar",
        width=40,
        height=2,
        command=seleccionar_fotos
    )
    boton_seleccionar.pack(pady=5)

    # Botón abrir DCIM
    boton_dcim = tk.Button(
        ventana,
        text="📁  Abrir ruta DCIM",
        width=40,
        height=2,
        command=lambda: abrir_dcim(unidad, ventana)
    )
    boton_dcim.pack(pady=5)

    # Botón mostrar historial
    boton_historial = tk.Button(
        ventana,
        text="📜  Mostrar historial de sincronización",
        width=40,
        height=2,
        command=lambda: mostrar_historial(ventana)
    )
    boton_historial.pack(pady=5)

    # Botón cerrar
    boton_cerrar = tk.Button(
        ventana,
        text="✕  Cerrar",
        width=20,
        command=ventana.destroy
    )
    boton_cerrar.pack(pady=(10, 5))

    # El usuario puede cerrar con la X
    ventana.protocol("WM_DELETE_WINDOW", ventana.destroy)