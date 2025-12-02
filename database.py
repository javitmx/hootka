# database.py - ADAPTADO AL SQL DUMP PROPORCIONADO
# Se usa la tabla 'kahoots' como principal y 'kahoot_id' como enlace.

import mysql.connector
from mysql.connector import Error
import time

# ============================================
# CONFIGURACIÓN DE CONEXIÓN A MYSQL
# ============================================
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "kahoot_db",  # Debe coincidir con tu SQL dump
}


def get_db_connection():
    """Crea y devuelve una conexión a la base de datos."""
    connection = None
    try:
        connection = mysql.connector.connect(**db_config)
    except Error as e:
        print(f"Error conectando a MySQL: {e}")
    return connection


# ============================================
# FUNCIONES DE ACCESO A DATOS
# ============================================

# --- LECTURA DE DATOS ---


def obtener_partida_por_pin(pin):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM partidas WHERE pin = %s", (pin,))
            return cursor.fetchone()
        except Error as e:
            print(f"Error: {e}")
        finally:
            cursor.close()
            conn.close()
    return None


def obtener_preguntas_por_kahoot(kahoot_id):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        try:
            # SQL DUMP: La columna se llama 'kahoot_id'
            cursor.execute(
                "SELECT * FROM preguntas WHERE kahoot_id = %s ORDER BY orden ASC",
                (kahoot_id,),
            )
            return cursor.fetchall()
        except Error as e:
            print(f"Error: {e}")
        finally:
            cursor.close()
            conn.close()
    return []


def obtener_opciones_pregunta(pregunta_id):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        try:
            # SQL DUMP: La columna se llama 'pregunta_id'
            cursor.execute(
                "SELECT id, pregunta_id, texto as texto, es_correcta != 0 as es_correcta FROM opciones WHERE pregunta_id = %s",
                (pregunta_id,),
            )
            return cursor.fetchall()
        except Error as e:
            print(f"Error: {e}")
        finally:
            cursor.close()
            conn.close()
    return []


# --- JUGADORES Y RESPUESTAS ---


def registrar_jugador(partida_id, nombre, session_id):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        try:
            sql = "INSERT INTO jugadores_sesion (partida_id, nombre, session_id, puntaje) VALUES (%s, %s, %s, 0)"
            cursor.execute(sql, (partida_id, nombre, session_id))
            conn.commit()
            jugador_id = cursor.lastrowid
            cursor.execute(
                "SELECT * FROM jugadores_sesion WHERE id = %s", (jugador_id,)
            )
            return cursor.fetchone()
        except Error as e:
            print(f"Error: {e}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
    return None


def obtener_jugadores_partida(partida_id):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT * FROM jugadores_sesion WHERE partida_id = %s", (partida_id,)
            )
            return cursor.fetchall()
        except Error as e:
            print(f"Error: {e}")
        finally:
            cursor.close()
            conn.close()
    return []


def obtener_jugador_por_session(session_id):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT * FROM jugadores_sesion WHERE session_id = %s", (session_id,)
            )
            return cursor.fetchone()
        except Error as e:
            print(f"Error: {e}")
        finally:
            cursor.close()
            conn.close()
    return None


def registrar_respuesta(jugador_id, pregunta_id, opcion_id, tiempo_respuesta):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            sql = "INSERT INTO respuestas (jugador_id, pregunta_id, opcion_id, tiempo_respuesta) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql, (jugador_id, pregunta_id, opcion_id, tiempo_respuesta))
            conn.commit()
            return True
        except Error as e:
            print(f"Error: {e}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
    return False


def obtener_respuestas_pregunta(pregunta_id, partida_id):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        try:
            sql = """SELECT r.* FROM respuestas r JOIN jugadores_sesion js ON r.jugador_id = js.id WHERE r.pregunta_id = %s AND js.partida_id = %s"""
            cursor.execute(sql, (pregunta_id, partida_id))
            return cursor.fetchall()
        except Error as e:
            print(f"Error: {e}")
        finally:
            cursor.close()
            conn.close()
    return []


def actualizar_puntaje_jugador(jugador_id, nuevo_puntaje):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE jugadores_sesion SET puntaje = %s WHERE id = %s",
                (nuevo_puntaje, jugador_id),
            )
            conn.commit()
            return True
        except Error as e:
            print(f"Error: {e}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
    return False


def obtener_ranking(partida_id):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT * FROM jugadores_sesion WHERE partida_id = %s ORDER BY puntaje DESC",
                (partida_id,),
            )
            return cursor.fetchall()
        except Error as e:
            print(f"Error: {e}")
        finally:
            cursor.close()
            conn.close()
    return []


def jugador_ya_respondio(jugador_id, pregunta_id):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT COUNT(*) FROM respuestas WHERE jugador_id = %s AND pregunta_id = %s",
                (jugador_id, pregunta_id),
            )
            return cursor.fetchone()[0] > 0
        except Error as e:
            print(f"Error: {e}")
        finally:
            cursor.close()
            conn.close()
    return False


def actualizar_estado_partida(partida_id, nuevo_estado):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE partidas SET estado = %s WHERE id = %s",
                (nuevo_estado, partida_id),
            )
            conn.commit()
            return True
        except Error as e:
            print(f"Error: {e}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
    return False


def reiniciar_partida_db(partida_id):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "DELETE r FROM respuestas r INNER JOIN jugadores_sesion js ON r.jugador_id = js.id WHERE js.partida_id = %s",
                (partida_id,),
            )
            cursor.execute(
                "DELETE FROM jugadores_sesion WHERE partida_id = %s", (partida_id,)
            )
            cursor.execute(
                "UPDATE partidas SET estado = 'esperando' WHERE id = %s", (partida_id,)
            )
            conn.commit()
            return True
        except Error as e:
            print(f"Error: {e}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
    return False


# --- USUARIOS ---


def obtener_usuario_por_username(username_or_email):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT * FROM usuarios WHERE username = %s OR email = %s",
                (username_or_email, username_or_email),
            )
            return cursor.fetchone()
        except Error as e:
            print(f"Error: {e}")
        finally:
            cursor.close()
            conn.close()
    return None


# ============================================
# FUNCIÓN DE GUARDADO (ADAPTADA AL SQL DUMP)
# ============================================
def guardar_cuestionario_completo(usuario_nombre, datos_json):
    """
    Guarda en 'kahoots' y 'preguntas' según la estructura del SQL dump.
    Recibe el NOMBRE de usuario (texto), no el ID.
    """
    conn = get_db_connection()
    if not conn:
        return False, "Error de conexión"

    cursor = conn.cursor()
    try:
        conn.start_transaction()

        titulo = datos_json.get("titulo")

        # 1. Insertar en la tabla 'kahoots' (la que mandan las foreign keys)
        # SQL DUMP: usa columnas 'titulo' y 'creado_por' (texto)
        cursor.execute(
            "INSERT INTO kahoots (titulo, creado_por) VALUES (%s, %s)",
            (titulo, usuario_nombre),
        )
        kahoot_id = cursor.lastrowid  # Obtenemos el ID del nuevo kahoot

        # 2. Insertar Preguntas
        preguntas_lista = datos_json.get("preguntas", [])
        for i, p_data in enumerate(preguntas_lista):
            orden = i + 1
            # SQL DUMP: la columna de enlace es 'kahoot_id'
            cursor.execute(
                "INSERT INTO preguntas (kahoot_id, texto, tipo, tiempo_limite, imagen_url, orden) VALUES (%s, %s, %s, %s, %s, %s)",
                (
                    kahoot_id,
                    p_data["pregunta"],
                    p_data["tipo_pregunta"],
                    20,
                    p_data.get("imagen"),
                    orden,
                ),
            )
            pregunta_id = cursor.lastrowid

            # 3. Insertar Opciones
            if (
                p_data["tipo_pregunta"] != "abierta"
            ):  # Asumiendo que 'abierta' no tiene opciones
                opciones = p_data.get("opciones", [])
                correctas = p_data.get("correctas", [])
                for j, texto_op in enumerate(opciones):
                    es_correcta = (j + 1) in correctas
                    # SQL DUMP: la columna de enlace es 'pregunta_id', texto es 'texto'
                    cursor.execute(
                        "INSERT INTO opciones (pregunta_id, texto, es_correcta) VALUES (%s, %s, %s)",
                        (pregunta_id, texto_op, es_correcta),
                    )

        conn.commit()
        return True, kahoot_id

    except Exception as e:
        conn.rollback()
        print(f"Error SQL: {e}")
        return False, str(e)
    finally:
        cursor.close()
        conn.close()


def actualizar_puntajes_totales(jugadores_actualizados):
    conn = get_db_connection()
    if not conn:
        return jugadores_actualizados
    cursor = conn.cursor()
    try:
        sql = "UPDATE jugadores_sesion SET puntaje = %s WHERE id = %s"
        datos = [(j["puntaje"], j["id"]) for j in jugadores_actualizados]
        cursor.executemany(sql, datos)
        conn.commit()
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
    return jugadores_actualizados


# ============================================
# NUEVAS FUNCIONES PARA SELECCIÓN DE CUESTIONARIO
# ============================================


def obtener_todos_kahoots():
    """Devuelve una lista de todos los cuestionarios (kahoots) disponibles (ID y Título)."""
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        try:
            # Ordenamos por ID descendente para que los más nuevos salgan primero
            sql = "SELECT id, titulo FROM kahoots ORDER BY id DESC"
            cursor.execute(sql)
            return cursor.fetchall()
        except Error as e:
            print(f"Error al obtener lista de kahoots: {e}")
        finally:
            cursor.close()
            conn.close()
    return []


def actualizar_kahoot_partida(partida_id, nuevo_kahoot_id):
    """
    Actualiza una partida para que use un cuestionario (kahoot_id) diferente.
    IMPORTANTE: También debe reiniciar el estado de la partida a 'esperando'.
    """
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            # 1. Actualizamos el kahoot_id y forzamos el estado a 'esperando'
            sql = (
                "UPDATE partidas SET kahoot_id = %s, estado = 'esperando' WHERE id = %s"
            )
            cursor.execute(sql, (nuevo_kahoot_id, partida_id))

            # 2. Por seguridad, limpiamos jugadores y respuestas anteriores si se cambia el cuestionario
            #    (Reutilizamos la lógica de reinicio que ya tenías, pero sin la parte de UPDATE partida)
            cursor.execute(
                "DELETE r FROM respuestas r INNER JOIN jugadores_sesion js ON r.jugador_id = js.id WHERE js.partida_id = %s",
                (partida_id,),
            )
            cursor.execute(
                "DELETE FROM jugadores_sesion WHERE partida_id = %s", (partida_id,)
            )

            conn.commit()
            return True
        except Error as e:
            print(f"Error al actualizar kahoot de la partida: {e}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
    return False


# ============================================
# EN database.py
# ============================================


def verificar_si_es_correcta(opcion_id):
    """Verifica en la BD si una opción ID específica es la respuesta correcta."""
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            # MySQL devuelve 1 para true, 0 para false
            sql = "SELECT es_correcta FROM opciones WHERE id = %s"
            cursor.execute(sql, (opcion_id,))
            resultado = cursor.fetchone()
            if resultado:
                # Devolvemos True si es 1, False si es 0
                return resultado[0] == 1
        except Error as e:
            print(f"Error verificando opción: {e}")
        finally:
            cursor.close()
            conn.close()
    return False


def registrar_respuesta_y_puntaje(
    jugador_id, pregunta_id, opcion_id, tiempo, puntos_a_sumar
):
    """Guarda la respuesta y ACTUALIZA el puntaje del jugador en una sola operación."""
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            # 1. Insertar la respuesta en el historial
            sql_resp = "INSERT INTO respuestas (jugador_id, pregunta_id, opcion_id, tiempo_respuesta) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql_resp, (jugador_id, pregunta_id, opcion_id, tiempo))

            # 2. Si hay puntos que sumar (porque fue correcta), actualizar al jugador
            if puntos_a_sumar > 0:
                # Sumamos los puntos nuevos al puntaje que ya tenía
                sql_update = (
                    "UPDATE jugadores_sesion SET puntaje = puntaje + %s WHERE id = %s"
                )
                cursor.execute(sql_update, (puntos_a_sumar, jugador_id))

            conn.commit()
            return True
        except Error as e:
            print(f"Error registrando respuesta y puntaje: {e}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
    return False
