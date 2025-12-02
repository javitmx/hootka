# app.py - Servidor Flask Principal para Kahoot Live

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    jsonify,
    flash,
)
import os
import uuid
import time

# Importa las funciones de seguridad para contraseñas
from werkzeug.security import generate_password_hash, check_password_hash

# --- IMPORTACIONES DE BASE DE DATOS ---
# Asegúrate de que todas estas funciones existan en tu archivo database.py
from database import (
    get_db_connection,
    obtener_usuario_por_username,
    obtener_partida_por_pin,
    obtener_preguntas_por_kahoot,
    obtener_opciones_pregunta,
    registrar_jugador,
    obtener_jugadores_partida,
    obtener_jugador_por_session,
    registrar_respuesta,
    obtener_respuestas_pregunta,
    actualizar_puntaje_jugador,
    obtener_ranking,
    jugador_ya_respondio,
    actualizar_estado_partida,
    reiniciar_partida_db,
    guardar_cuestionario_completo,
    obtener_todos_kahoots,
    actualizar_kahoot_partida,
    verificar_si_es_correcta,
    registrar_respuesta_y_puntaje,
)

from evaluadora import (
    calcular_puntajes,
    obtener_podio,
    generar_estadisticas_pregunta,
    actualizar_puntajes_totales,
)

app = Flask(__name__)
app.secret_key = "kahoot_secreto_2024"  # Asegúrate de que esta sea la única secret_key

# Configura la carpeta de subida de imágenes si no la tienes
UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ALMACENAMIENTO EN MEMORIA (Estado del juego)

# Estructura: {pin: {estado, pregunta_actual, tiempo_inicio, preguntas, partida_id}}
partidas_activas = {}


def garantizar_estado_partida_en_memoria(pin, partida_db):
    """
    Asegura que la partida esté inicializada en el diccionario global 'partidas_activas'.
    Si no existe, carga las preguntas de la DB y crea la estructura inicial en memoria.
    """
    if pin not in partidas_activas:
        # print(f"⚡ Inicializando estado en memoria para PIN {pin}") # Debug opcional
        preguntas = obtener_preguntas_por_kahoot(partida_db["kahoot_id"])

        partidas_activas[pin] = {
            "estado": partida_db["estado"],  # Usamos el estado inicial de la DB
            "pregunta_actual": 0,
            "tiempo_inicio": 0,  # No ha empezado la primera pregunta
            "preguntas": preguntas,
            "partida_id": partida_db["id"],
        }
    # else:
    # print(f"ℹ️ El estado en memoria ya existía para PIN {pin}") # Debug opcional


@app.route("/")
def index():
    """Página principal - Redirige según estado de sesión"""
    # 1. Preguntamos: ¿El usuario ya inició sesión?
    if "user_id" in session:
        # SI YA ESTÁ LOGUEADO: Le mostramos la pantalla para unirse al juego.
        # Pasamos error=None por si la plantilla lo espera.
        return render_template("join.html", error=None)
    else:
        # SI NO ESTÁ LOGUEADO: Le mostramos la pantalla de Login.
        return render_template("login.html")


# ============================================
# RUTA TEMPORAL PARA CREAR EL PRIMER USUARIO
# ============================================
@app.route("/crear-admin")
def crear_admin_temporal():
    """Crea un usuario administrador para poder probar el login."""
    # --- CONFIGURA AQUÍ TUS DATOS ---
    MI_USUARIO = "prueba"
    MI_EMAIL = "user@gmail.com"
    MI_PASSWORD = "prueba123"  # ¡Cambia esto por una contraseña segura!
    # --------------------------------

    # 1. Generar el hash de la contraseña (encriptarla)
    password_hash = generate_password_hash(MI_PASSWORD)

    # 2. Guardar en la base de datos
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            sql = "INSERT INTO usuarios (username, email, password_hash) VALUES (%s, %s, %s)"
            cursor.execute(sql, (MI_USUARIO, MI_EMAIL, password_hash))
            conn.commit()
            return f"✅ Usuario '{MI_USUARIO}' creado con éxito. ¡Ahora puedes ir a /login!"
        except Exception as e:
            return f"❌ Error al crear usuario (¿quizás ya existe?): {e}"
        finally:
            cursor.close()
            conn.close()
    return "Error de conexión a la DB"


# ============================================
# RUTAS DE AUTENTICACIÓN (Login/Logout)
# ============================================

# ============================================
# EN app.py - RUTA LOGIN DEFINITIVA (PIN FIJO)
# ============================================


@app.route("/login", methods=["GET", "POST"])
def login():
    """Maneja el inicio de sesión de usuarios (profesores)"""

    # Si ya está logueado, redirigir al inicio
    if "user_id" in session:
        # Opcional: Si es el admin, podrías redirigirlo al host directamente también aquí.
        return redirect(url_for("index"))

    if request.method == "POST":
        username_input = request.form.get("username")
        password_input = request.form.get("password")

        # 1. Buscar el usuario en la DB
        user_db = obtener_usuario_por_username(username_input)

        # 2. Verificar si existe y si la contraseña es correcta
        if user_db and check_password_hash(user_db["password_hash"], password_input):
            # ¡Login exitoso!
            session["user_id"] = user_db["id"]
            session["username"] = user_db["username"]
            flash(f"¡Bienvenido de nuevo, {user_db['username']}!", "success")

            # --- LÓGICA DEL SUPERUSUARIO HOST CON PIN FIJO ---
            USUARIO_HOST_ESPECIAL = "prueba"  # Tu usuario admin
            PIN_FIJO_ADMIN = "42777"  # Tu PIN fijo

            if user_db["username"] == USUARIO_HOST_ESPECIAL:
                # Como el PIN siempre es el mismo, redirigimos directamente.
                # 'host' es el nombre de la función que maneja la ruta /host/<pin>
                return redirect(url_for("host", pin=PIN_FIJO_ADMIN))

            # Si NO es el usuario especial, lo mandamos al inicio normal
            return redirect(url_for("index"))
            # -------------------------------------------

        else:
            # Login fallido
            flash("Usuario o contraseña incorrectos.", "danger")

    # Si es GET o el login falló, mostramos el formulario
    return render_template("login.html")


# ============================================
# REGISTRO DE NUEVOS USUARIOS
# ============================================

# ============================================
# EN app.py - Función 'register' FINAL (Con campo de Email real)
# ============================================


@app.route("/register", methods=["GET", "POST"])
def register():
    """Maneja el registro de nuevos usuarios"""
    if request.method == "POST":
        # 1. Obtener datos del formulario
        usuario = request.form.get("usuario")
        email = request.form.get("email")  # <--- ¡AHORA RECIBIMOS EL EMAIL REAL!
        password = request.form.get("password")
        confirmar = request.form.get("confirmar")

        # 2. Validaciones básicas
        # Comprobamos que el email tampoco esté vacío
        if not usuario or not email or not password or not confirmar:
            flash("Todos los campos son obligatorios, incluido el email.", "danger")
            return render_template("register.html")

        if password != confirmar:
            flash("Las contraseñas no coinciden.", "danger")
            return render_template("register.html")

        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            try:
                # 3. Verificar si el usuario O el email ya existen
                # Es importante chequear ambos para evitar errores de duplicado en la BD
                sql_check = "SELECT * FROM usuarios WHERE username = %s OR email = %s"
                cursor.execute(sql_check, (usuario, email))
                usuario_existente = cursor.fetchone()

                if usuario_existente:
                    # Averiguamos qué fue lo que se repitió para dar un mensaje claro
                    if usuario_existente["username"] == usuario:
                        flash(
                            "El nombre de usuario ya está en uso. Elige otro.", "danger"
                        )
                    elif usuario_existente["email"] == email:
                        flash("Ese correo electrónico ya está registrado.", "danger")
                    return render_template("register.html")

                # 4. Encriptar la contraseña
                password_hash = generate_password_hash(password)

                # 5. Insertar el nuevo usuario
                # Ahora la variable 'email' tiene el dato real que introdujo el usuario
                sql_insert = "INSERT INTO usuarios (username, email, password_hash) VALUES (%s, %s, %s)"
                cursor.execute(sql_insert, (usuario, email, password_hash))
                conn.commit()

                flash(
                    "✅ ¡Cuenta creada con éxito! Ahora puedes iniciar sesión.",
                    "success",
                )
                return redirect(url_for("login"))

            except Exception as e:
                # Si pasa algo inesperado, lo registramos
                print(f"Error no controlado en registro: {e}")
                conn.rollback()
                flash("Ocurrió un error interno al crear la cuenta.", "danger")
            finally:
                cursor.close()
                conn.close()
        else:
            flash("Error de conexión a la base de datos.", "danger")

    # Si es GET o hubo error, mostramos el formulario
    return render_template("register.html")


@app.route("/logout")
def logout():
    """Cierra la sesión del usuario"""
    session.pop("user_id", None)
    session.pop("username", None)
    flash("Has cerrado sesión correctamente.", "info")
    return redirect(url_for("login"))


# ============================================
# RUTAS PARA JUGADORES
# ============================================


@app.route("/unirse", methods=["POST"])
def unirse():
    """Procesar solicitud de unirse a partida"""
    pin = request.form.get("pin", "").strip().replace(" ", "")
    nombre = request.form.get("nombre", "").strip()

    if not pin or not nombre:
        return render_template("join.html", error="Ingresa el PIN y tu nombre")

    # Verificar que existe la partida
    partida = obtener_partida_por_pin(pin)
    if not partida:
        return render_template("join.html", error="PIN no válido o partida finalizada")

    # Crear ID de sesión único para el jugador
    session_id = str(uuid.uuid4())
    session["session_id"] = session_id
    session["nombre"] = nombre
    # session["pin"] = pin # ELIMINADO: El jugador ya no guarda el PIN directamente

    # Registrar jugador en la base de datos
    registrar_jugador(partida["id"], nombre, session_id)

    return redirect(url_for("lobby_jugador"))


@app.route("/lobby")
def lobby_jugador():
    """Sala de espera del jugador"""
    if "session_id" not in session:
        return redirect(url_for("index"))

    jugador = obtener_jugador_por_session(session["session_id"])
    if not jugador:
        return redirect(url_for("index"))

    # Necesitamos el PIN para mostrarlo en el lobby, lo obtenemos de la DB
    partida_id = jugador["partida_id"]
    pin = None
    # Buscamos el PIN en las partidas activas en memoria
    for p_pin, p_estado in partidas_activas.items():
        if p_estado["partida_id"] == partida_id:
            pin = p_pin
            break

    # Si no está en memoria, es una partida "esperando", lo buscamos en la DB
    if pin is None:
        # Esta es una solución temporal, idealmente tendríamos una función obtener_partida_por_id
        # o partidas_activas se llenaría al crear la partida.
        # Por ahora, asumimos que el host ya visitó /host/<pin> y llenó partidas_activas si está jugando
        # Si está esperando, no hay problema si pin es None, la plantilla lo maneja.
        pass

    return render_template("lobby.html", jugador=jugador, pin=pin)


@app.route("/jugar")
def jugar():
    """Pantalla de juego del jugador"""
    if "session_id" not in session:
        return redirect(url_for("index"))

    jugador = obtener_jugador_por_session(session["session_id"])
    if not jugador:
        return redirect(url_for("index"))

    partida_id = jugador["partida_id"]
    pin = None
    estado = None

    # Buscamos la partida activa en memoria usando el partida_id
    for p_pin, p_estado in partidas_activas.items():
        if p_estado["partida_id"] == partida_id:
            pin = p_pin
            estado = p_estado
            break

    # Verificar si hay partida activa
    if estado is None:
        return render_template(
            "lobby.html",
            jugador=jugador,
            pin=pin,  # Puede ser None aquí
            mensaje="Esperando que inicie el juego...",
        )

    if estado["estado"] == "finalizado":
        return redirect(url_for("podio_jugador"))

    if estado["estado"] == "mostrando_resultado":
        return render_template(
            "esperando.html", mensaje="Esperando siguiente pregunta..."
        )

    # Obtener pregunta actual
    pregunta_idx = estado["pregunta_actual"]
    preguntas = estado["preguntas"]

    if pregunta_idx >= len(preguntas):
        return redirect(url_for("podio_jugador"))

    pregunta = preguntas[pregunta_idx]
    opciones = obtener_opciones_pregunta(pregunta["id"])

    # Verificar si ya respondió
    ya_respondio = jugador_ya_respondio(jugador["id"], pregunta["id"])

    # Calcular tiempo restante
    tiempo_transcurrido = time.time() - estado["tiempo_inicio"]
    tiempo_restante = max(
        0, int(pregunta.get("tiempo_limite", 20) - tiempo_transcurrido)
    )

    return render_template(
        "question.html",
        pregunta=pregunta,
        opciones=opciones,
        tiempo_restante=tiempo_restante,
        numero_pregunta=pregunta_idx + 1,
        total_preguntas=len(preguntas),
        ya_respondio=ya_respondio,
        jugador=jugador,
    )


# ============================================
# EN app.py - REEMPLAZA TU FUNCIÓN 'responder' CON ESTA
# ============================================


@app.route("/responder", methods=["POST"])
def responder():
    """Registrar respuesta del jugador, verificarla y sumar puntos."""
    if "session_id" not in session:
        return jsonify({"error": "No autorizado"}), 401

    jugador = obtener_jugador_por_session(session["session_id"])
    if not jugador:
        return jsonify({"error": "Jugador no encontrado"}), 404

    # Obtener datos JSON (Mantenemos tu lógica de compatibilidad)
    data = request.get_json(silent=True)
    if not data:
        data = request.form.to_dict() if request.form else {}

    pregunta_id = data.get("pregunta_id")
    opcion_id = data.get("opcion_id")

    # Validación básica
    if not pregunta_id:
        return jsonify({"error": "pregunta_id no proporcionado"}), 400
    if not opcion_id:
        return jsonify({"error": "opcion_id no proporcionado"}), 400

    try:
        tiempo_respuesta = float(data.get("tiempo_respuesta", 20))
    except (TypeError, ValueError):
        tiempo_respuesta = 20

    # Verificar que no haya respondido ya
    if jugador_ya_respondio(jugador["id"], pregunta_id):
        return jsonify({"error": "Ya respondiste esta pregunta"}), 400

    # --- NUEVA LÓGICA DE PUNTOS ---
    puntos_ganados = 0
    es_correcta = False

    # 1. Verificamos si la opción elegida es la correcta en la BD
    #    (Usamos la nueva función que agregaste en el Paso 1 a database.py)
    if verificar_si_es_correcta(opcion_id):
        es_correcta = True
        puntos_ganados = 200  # Puntos fijos por acierto
    else:
        es_correcta = False
        puntos_ganados = 0  # 0 puntos si falla

    # 2. Registramos la respuesta y actualizamos el puntaje en la BD
    #    (Usamos la OTRA nueva función que agregaste en el Paso 1 a database.py)
    success = registrar_respuesta_y_puntaje(
        jugador["id"], pregunta_id, opcion_id, tiempo_respuesta, puntos_ganados
    )

    if success:
        # --- IMPORTANTE: Devolvemos al frontend si acertó o no ---
        return jsonify(
            {
                "success": True,
                "mensaje": "Respuesta registrada",
                "es_correcta": es_correcta,  # <-- NUEVO: Le dice al JS si acertó
                "puntos_ganados": puntos_ganados,  # <-- NUEVO: Cuántos puntos ganó
            }
        )
    else:
        return jsonify({"error": "Error al registrar respuesta"}), 500


@app.route("/podio")
def podio_jugador():
    """Mostrar podio final al jugador"""
    if "session_id" not in session:
        return redirect(url_for("index"))

    jugador = obtener_jugador_por_session(session["session_id"])
    if not jugador:
        return redirect(url_for("index"))

    partida_id = jugador["partida_id"]

    ranking = obtener_ranking(partida_id)
    podio = obtener_podio(ranking)

    # Encontrar posición del jugador actual
    mi_posicion = next(
        (i + 1 for i, j in enumerate(ranking) if j["id"] == jugador["id"]), 0
    )

    return render_template(
        "podium.html",
        podio=podio,
        ranking=ranking,
        jugador=jugador,
        mi_posicion=mi_posicion,
    )


# ============================================
# RUTAS PARA EL HOST (Profesor)
# ============================================


@app.route("/host/<pin>")
def host(pin):
    """Panel de control del host (Con selección de cuestionario)"""

    # 1. Validación básica
    partida_db = obtener_partida_por_pin(pin)
    if not partida_db:
        return "Partida no encontrada", 404

    # 2. Lógica de Reinicio Automático (Si venía de 'finalizada')
    if partida_db["estado"] == "finalizada":
        print(f"🔄 Reiniciando partida finalizada PIN {pin}...")
        reiniciar_partida_db(partida_db["id"])
        partida_db["estado"] = "esperando"
        if pin in partidas_activas:
            del partidas_activas[pin]

    # 3. Asegurar memoria
    garantizar_estado_partida_en_memoria(pin, partida_db)
    estado_memoria = partidas_activas[pin]

    # 4. Obtener datos para la vista
    jugadores = obtener_jugadores_partida(partida_db["id"])
    total_preguntas = len(estado_memoria["preguntas"])

    # --- NUEVO: Obtener la lista de todos los cuestionarios disponibles ---
    lista_kahoots = obtener_todos_kahoots()

    # 5. Renderizar vista enviando la nueva lista
    return render_template(
        "host.html",
        pin=pin,
        partida=partida_db,  # Tiene el kahoot_id actual
        estado_actual=estado_memoria["estado"],
        jugadores=jugadores,
        total_preguntas=total_preguntas,
        kahoots_disponibles=lista_kahoots,  # <-- ENVIAMOS LA LISTA AQUÍ
    )


# ============================================
# NUEVA RUTA PARA CAMBIAR EL CUESTIONARIO
# ============================================
@app.route("/host/<pin>/seleccionar-kahoot", methods=["POST"])
def seleccionar_kahoot(pin):
    """API para que el host cambie el cuestionario de la partida actual"""
    partida = obtener_partida_por_pin(pin)
    if not partida:
        return jsonify({"error": "Partida no encontrada"}), 404

    data = request.get_json()
    nuevo_kahoot_id = data.get("kahoot_id")

    if not nuevo_kahoot_id:
        return jsonify({"error": "ID de cuestionario no proporcionado"}), 400

    # 1. Actualizar en Base de Datos
    exito = actualizar_kahoot_partida(partida["id"], nuevo_kahoot_id)

    if exito:
        # 2. IMPORTANTE: Borrar la memoria RAM para este PIN.
        #    Esto forzará a que, al recargar la página, se lean las NUEVAS preguntas de la DB.
        if pin in partidas_activas:
            del partidas_activas[pin]
            print(
                f"🧹 Memoria RAM limpiada para PIN {pin} tras cambio de cuestionario."
            )

        return jsonify({"success": True})
    else:
        return jsonify({"error": "Error al actualizar la base de datos"}), 500


# ============================================


@app.route("/host/<pin>/iniciar", methods=["POST"])
def iniciar_partida(pin):
    """Iniciar el juego"""
    partida = obtener_partida_por_pin(pin)
    if not partida:
        return jsonify({"error": "Partida no encontrada"}), 404

    if pin not in partidas_activas:
        preguntas = obtener_preguntas_por_kahoot(partida["kahoot_id"])
        partidas_activas[pin] = {
            "estado": "esperando",
            "pregunta_actual": 0,
            "tiempo_inicio": 0,
            "preguntas": preguntas,
            "partida_id": partida["id"],
        }

    # Actualizar estado en memoria
    partidas_activas[pin]["estado"] = "jugando"
    partidas_activas[pin]["tiempo_inicio"] = time.time()
    partidas_activas[pin]["pregunta_actual"] = 0

    # Actualizar estado en base de datos
    actualizar_estado_partida(partida["id"], "en_curso")

    return jsonify({"success": True})


@app.route("/host/<pin>/siguiente", methods=["POST"])
def siguiente_pregunta(pin):
    """Pasar a la siguiente pregunta (Versión Limpia - SIN CALCULAR PUNTOS)"""
    if pin not in partidas_activas:
        return jsonify({"error": "Partida no iniciada"}), 400

    estado = partidas_activas[pin]

    # ==================================================================
    # [ELIMINADO] LÓGICA ANTIGUA DE CÁLCULO DE PUNTAJES
    # Los puntos ahora se calculan y suman en tiempo real en la ruta /responder.
    # Aquí ya no se debe tocar el puntaje.
    # ==================================================================

    # Avanzar a la siguiente pregunta
    estado["pregunta_actual"] += 1
    estado["tiempo_inicio"] = time.time()
    estado["estado"] = "jugando"

    # Verificar si se terminó el juego
    if estado["pregunta_actual"] >= len(estado["preguntas"]):
        estado["estado"] = "finalizado"
        actualizar_estado_partida(estado["partida_id"], "finalizada")
        return jsonify({"success": True, "finalizado": True})

    return jsonify(
        {
            "success": True,
            "pregunta_numero": estado["pregunta_actual"] + 1,
            "total": len(estado["preguntas"]),
        }
    )


@app.route("/host/<pin>/mostrar-resultado", methods=["POST"])
def mostrar_resultado(pin):
    """Mostrar resultado de la pregunta actual"""
    if pin not in partidas_activas:
        return jsonify({"error": "Partida no iniciada"}), 400

    estado = partidas_activas[pin]
    estado["estado"] = "mostrando_resultado"

    pregunta = estado["preguntas"][estado["pregunta_actual"]]
    opciones = obtener_opciones_pregunta(pregunta["id"])
    respuestas = obtener_respuestas_pregunta(pregunta["id"], estado["partida_id"])

    stats = generar_estadisticas_pregunta(respuestas, opciones)
    ranking = obtener_ranking(estado["partida_id"])[:5]  # Top 5

    return jsonify(
        {
            "success": True,
            "estadisticas": stats,
            "ranking": ranking,
        }
    )


@app.route("/host/<pin>/estado")
def estado_partida(pin):
    """Obtener estado actual de la partida (para polling)"""
    partida = obtener_partida_por_pin(pin)
    if not partida:
        return jsonify({"error": "Partida no encontrada"}), 404

    jugadores = obtener_jugadores_partida(partida["id"])
    estado_memoria = partidas_activas.get(pin)

    estado_actual_str = (
        estado_memoria["estado"] if estado_memoria else partida["estado"]
    )
    pregunta_actual_idx = estado_memoria["pregunta_actual"] if estado_memoria else 0

    tiempo_restante = 0
    if (
        estado_actual_str == "jugando"
        and estado_memoria
        and "tiempo_inicio" in estado_memoria
    ):
        pregunta = estado_memoria["preguntas"][pregunta_actual_idx]
        tiempo_transcurrido = time.time() - estado_memoria["tiempo_inicio"]
        tiempo_restante = max(
            0, int(pregunta.get("tiempo_limite", 20) - tiempo_transcurrido)
        )

    return jsonify(
        {
            "jugadores": jugadores,
            "total_jugadores": len(jugadores),
            "estado": estado_actual_str,
            "pregunta_actual": pregunta_actual_idx,
            "tiempo_restante": tiempo_restante,
        }
    )


# ============================================
# API PARA POLLING (Actualización automática)
# ============================================


@app.route("/api/estado-juego")
def api_estado_juego():
    """API para que los jugadores consulten el estado"""
    if "session_id" not in session:
        return jsonify({"error": "No autorizado"}), 401

    jugador = obtener_jugador_por_session(session["session_id"])
    if not jugador:
        return jsonify({"error": "Jugador no encontrado"}), 404

    partida_id = jugador["partida_id"]
    pin = None
    estado = None

    for p_pin, p_estado in partidas_activas.items():
        if p_estado["partida_id"] == partida_id:
            pin = p_pin
            estado = p_estado
            break

    if estado is None:
        from database import get_db_connection

        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT estado FROM partidas WHERE id = %s", (partida_id,))
            partida_db = cursor.fetchone()
            cursor.close()
            conn.close()
            if partida_db and partida_db["estado"] == "esperando":
                return jsonify(
                    {
                        "estado": "esperando",
                        "mensaje": "Esperando que el host inicie la partida...",
                    }
                )
        return jsonify(
            {"estado": "esperando", "mensaje": "Esperando conexión con la partida..."}
        )

    if estado["estado"] == "finalizado":
        return jsonify({"estado": "finalizado", "redirect": "/podio"})

    tiempo_restante = 0
    if estado["estado"] == "jugando":
        if estado["pregunta_actual"] < len(estado["preguntas"]):
            pregunta = estado["preguntas"][estado["pregunta_actual"]]
            tiempo_transcurrido = time.time() - estado["tiempo_inicio"]
            tiempo_restante = max(
                0, int(pregunta.get("tiempo_limite", 20) - tiempo_transcurrido)
            )
        else:
            return jsonify({"estado": "finalizado", "redirect": "/podio"})

    return jsonify(
        {
            "estado": estado["estado"],
            "pregunta_actual": estado["pregunta_actual"],
            "tiempo_restante": tiempo_restante,
            "mi_puntaje": jugador["puntaje"],
        }
    )


# ============================================
# NUEVAS RUTAS PARA CREAR CUESTIONARIOS
# ============================================


@app.route("/crear_cuestionario")
def vista_crear_cuestionario():
    """Muestra la página HTML para crear cuestionarios"""
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("crear_cuestionario.html")


# --- EN TU ARCHIVO app.py ---


@app.route("/api/guardar-cuestionario", methods=["POST"])
def api_guardar_cuestionario():
    """Recibe JSON desde el frontend y lo guarda en la DB"""
    # 🔒 Protección API
    if "user_id" not in session:
        return jsonify({"success": False, "error": "No autorizado"}), 401

    try:
        # Obtener los datos JSON enviados por JavaScript
        datos_json = request.get_json()
        if not datos_json:
            return (
                jsonify({"success": False, "error": "No se recibieron datos JSON"}),
                400,
            )

        # --- MODIFICACIÓN IMPORTANTE ---
        # Tu tabla 'kahoots' usa 'creado_por' (texto), no 'usuario_id' (número).
        # Pasamos el nombre de usuario que guardamos en la sesión al hacer login.
        usuario_nombre = session["username"]

        # Llamamos a la función de base de datos con el NOMBRE, no el ID.
        exito, resultado = guardar_cuestionario_completo(usuario_nombre, datos_json)

        if exito:
            flash("¡Cuestionario creado exitosamente!", "success")
            # Redirigir a la página principal (o a un futuro dashboard)
            return jsonify({"success": True, "redirect_url": url_for("index")})
        else:
            return (
                jsonify({"success": False, "error": f"Error de BD: {resultado}"}),
                500,
            )

    except Exception as e:
        print(f"Error en API: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================
# INICIAR SERVIDOR
# ============================================

if __name__ == "__main__":
    print("=" * 50)
    print("🎮 KAHOOT LIVE - Servidor iniciado")
    print("=" * 50)
    print("📍 Jugadores: http://localhost:5000")
    # Asegúrate de usar un PIN válido que exista en tu DB
    print("📍 Host: http://localhost:5000/host/42777")
    print("=" * 50)
    # debug=True permite que el servidor se reinicie al guardar cambios
    app.run(debug=True, host="0.0.0.0", port=5000)
