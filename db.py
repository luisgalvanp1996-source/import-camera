import sqlite3
import os


# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "SONY.db")


# ============================================================
# CONEXIÓN
# ============================================================

def conectar():
    """Abre una conexión con la base de datos SQLite."""

    conexion = sqlite3.connect(DB_PATH)

    # Activar claves foráneas
    conexion.execute("PRAGMA foreign_keys = ON")

    return conexion


# ============================================================
# FOTOS
# ============================================================

def buscar_foto_por_hash(hash_sha256):
    """
    Busca una fotografía utilizando su SHA-256.

    Devuelve:
        - Los datos de la foto si existe.
        - None si no existe.
    """

    conexion = conectar()

    try:
        cursor = conexion.cursor()

        cursor.execute(
            """
            SELECT
                FotoID,
                HashSHA256,
                NombreOriginal,
                Extension,
                Formato,
                FechaCaptura,
                FechaImportacion
            FROM Fotos
            WHERE HashSHA256 = ?
            """,
            (hash_sha256,)
        )

        resultado = cursor.fetchone()

        return resultado

    finally:
        conexion.close()


def foto_existe(hash_sha256):
    """
    Comprueba si una fotografía ya existe en la base de datos.

    Devuelve:
        True  -> existe
        False -> no existe
    """

    conexion = conectar()

    try:
        cursor = conexion.cursor()

        cursor.execute(
            """
            SELECT 1
            FROM Fotos
            WHERE HashSHA256 = ?
            LIMIT 1
            """,
            (hash_sha256,)
        )

        return cursor.fetchone() is not None

    finally:
        conexion.close()


def insertar_foto(
    foto_id,
    hash_sha256,
    nombre_original,
    extension,
    formato=None,
    fecha_captura=None
):
    """
    Registra una fotografía nueva en la tabla Fotos.
    """

    conexion = conectar()

    try:
        cursor = conexion.cursor()

        cursor.execute(
            """
            INSERT INTO Fotos (
                FotoID,
                HashSHA256,
                NombreOriginal,
                Extension,
                Formato,
                FechaCaptura
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                foto_id,
                hash_sha256,
                nombre_original,
                extension,
                formato,
                fecha_captura
            )
        )

        conexion.commit()

    finally:
        conexion.close()


# ============================================================
# ARCHIVOS
# ============================================================

def insertar_archivo(
    foto_id,
    nombre_archivo,
    ruta_archivo,
    tamano_bytes,
    estado="PENDIENTE"
):
    """
    Registra la ubicación física de una fotografía.
    """

    conexion = conectar()

    try:
        cursor = conexion.cursor()

        cursor.execute(
            """
            INSERT INTO Archivos (
                FotoID,
                NombreArchivo,
                RutaArchivo,
                TamanoBytes,
                Estado
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                foto_id,
                nombre_archivo,
                ruta_archivo,
                tamano_bytes,
                estado
            )
        )

        conexion.commit()

    finally:
        conexion.close()


def actualizar_estado_archivo(foto_id, estado):
    """
    Actualiza el estado de un archivo.
    """

    conexion = conectar()

    try:
        cursor = conexion.cursor()

        cursor.execute(
            """
            UPDATE Archivos
            SET
                Estado = ?,
                FechaActualizacion = CURRENT_TIMESTAMP
            WHERE FotoID = ?
            """,
            (estado, foto_id)
        )

        conexion.commit()

    finally:
        conexion.close()


# ============================================================
# IMPORTACIONES
# ============================================================

def crear_importacion(etiqueta_sd, unidad):
    """
    Crea un registro para una nueva sesión de importación.

    Devuelve:
        ImportacionID
    """

    conexion = conectar()

    try:
        cursor = conexion.cursor()

        cursor.execute(
            """
            INSERT INTO Importaciones (
                EtiquetaSD,
                Unidad,
                Estado
            )
            VALUES (?, ?, 'EN_PROCESO')
            """,
            (
                etiqueta_sd,
                unidad
            )
        )

        conexion.commit()

        return cursor.lastrowid

    finally:
        conexion.close()


def finalizar_importacion(
    importacion_id,
    cantidad_fotos,
    cantidad_exitosas,
    cantidad_errores
):
    """
    Finaliza una sesión de importación.
    """

    conexion = conectar()

    try:
        cursor = conexion.cursor()

        estado = "COMPLETADA"

        if cantidad_errores > 0:
            estado = "COMPLETADA_CON_ERRORES"

        cursor.execute(
            """
            UPDATE Importaciones
            SET
                FechaFin = CURRENT_TIMESTAMP,
                CantidadFotos = ?,
                CantidadExitosas = ?,
                CantidadErrores = ?,
                Estado = ?
            WHERE ImportacionID = ?
            """,
            (
                cantidad_fotos,
                cantidad_exitosas,
                cantidad_errores,
                estado,
                importacion_id
            )
        )

        conexion.commit()

    finally:
        conexion.close()

def actualizar_archivo(
    foto_id,
    nombre_archivo=None,
    ruta_archivo=None,
    estado=None,
    mensaje_error=None
):
    """
    Actualiza los datos físicos de una fotografía en la tabla Archivos.

    Solo modifica los valores que se proporcionen.
    """

    conexion = conectar()

    try:
        cursor = conexion.cursor()

        campos = []
        valores = []

        if nombre_archivo is not None:
            campos.append("NombreArchivo = ?")
            valores.append(nombre_archivo)

        if ruta_archivo is not None:
            campos.append("RutaArchivo = ?")
            valores.append(ruta_archivo)

        if estado is not None:
            campos.append("Estado = ?")
            valores.append(estado)

        if mensaje_error is not None:
            campos.append("MensajeError = ?")
            valores.append(mensaje_error)

        if not campos:
            return

        campos.append("FechaActualizacion = CURRENT_TIMESTAMP")

        valores.append(foto_id)

        consulta = f"""
            UPDATE Archivos
            SET {", ".join(campos)}
            WHERE FotoID = ?
        """

        cursor.execute(consulta, valores)
        conexion.commit()

    finally:
        conexion.close()


def buscar_foto_sincronizada_por_hash(hash_sha256):
    conexion = conectar()
    try:
        cursor = conexion.cursor()
        cursor.execute(
            """
            SELECT
                Fotos.FotoID,
                Fotos.HashSHA256,
                Archivos.NombreArchivo,
                Archivos.RutaArchivo,
                Archivos.Estado
            FROM Fotos
            INNER JOIN Archivos
                ON Fotos.FotoID = Archivos.FotoID
            WHERE Fotos.HashSHA256 = ?
                AND Archivos.Estado = 'SINCRONIZADO'
            LIMIT 1
            """,
            (hash_sha256,)
        )

        return cursor.fetchone()

    finally:
        conexion.close()

def obtener_historial_fotos():
    """
    Obtiene todas las fotografías registradas en la base de datos,
    junto con su información física y estado.
    """

    conexion = conectar()

    try:
        cursor = conexion.cursor()

        cursor.execute(
            """
            SELECT
                Fotos.FotoID,
                Fotos.NombreOriginal,
                Fotos.Extension,
                Fotos.Formato,
                Fotos.FechaCaptura,
                Fotos.FechaImportacion,
                Archivos.NombreArchivo,
                Archivos.RutaArchivo,
                Archivos.TamanoBytes,
                Archivos.Estado,
                Archivos.FechaCreacion,
                Archivos.FechaActualizacion
            FROM Fotos
            LEFT JOIN Archivos
                ON Fotos.FotoID = Archivos.FotoID
            ORDER BY Fotos.FechaImportacion DESC
            """
        )

        return cursor.fetchall()

    finally:
        conexion.close()

def obtener_foto_por_id(foto_id):
    """
    Obtiene toda la información de una fotografía específica.
    """

    conexion = conectar()

    try:
        cursor = conexion.cursor()

        cursor.execute(
            """
            SELECT
                Fotos.FotoID,
                Fotos.HashSHA256,
                Fotos.NombreOriginal,
                Fotos.Extension,
                Fotos.Formato,
                Fotos.FechaCaptura,
                Fotos.FechaImportacion,
                Archivos.NombreArchivo,
                Archivos.RutaArchivo,
                Archivos.TamanoBytes,
                Archivos.Estado,
                Archivos.FechaCreacion,
                Archivos.FechaActualizacion
            FROM Fotos
            LEFT JOIN Archivos
                ON Fotos.FotoID = Archivos.FotoID
            WHERE Fotos.FotoID = ?
            """,
            (foto_id,)
        )

        return cursor.fetchone()

    finally:
        conexion.close()

def eliminar_foto(foto_id):
    """
    Elimina una fotografía de Fotos.

    ON DELETE CASCADE elimina también
    el registro relacionado en Archivos.
    """

    conexion = conectar()

    try:
        cursor = conexion.cursor()

        cursor.execute(
            """
            DELETE FROM Fotos
            WHERE FotoID = ?
            """,
            (foto_id,)
        )

        conexion.commit()

    finally:
        conexion.close()