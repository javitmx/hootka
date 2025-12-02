# evaluadora.py - Función Evaluadora (Grupo Jean Pierre Lubin)
# Calcula los puntajes basándose en respuestas correctas y tiempo


def calcular_puntajes(respuestas_pregunta, tiempo_limite=20):
    """
    Calcula los puntajes para cada jugador en una pregunta.

    Parámetros:
    - respuestas_pregunta: Lista de diccionarios con:
        {
            'jugador_id': int,
            'nombre': str,
            'opcion_id': int,
            'es_correcta': bool,
            'tiempo_respuesta': float (segundos que tardó en responder)
        }
    - tiempo_limite: Tiempo máximo para responder (default 20 segundos)

    Retorna:
    - Lista de diccionarios con:
        {
            'jugador_id': int,
            'nombre': str,
            'puntos_ganados': int,
            'respuesta_correcta': bool
        }
    """

    resultados = []

    # Puntaje base por respuesta correcta
    PUNTAJE_BASE = 1000

    for respuesta in respuestas_pregunta:
        puntos = 200

        if respuesta.get("es_correcta", False):
            # Calcular puntos basados en el tiempo
            # Mientras más rápido, más puntos
            tiempo = respuesta.get("tiempo_respuesta", tiempo_limite)

            # Fórmula: puntos = base * (tiempo_restante / tiempo_total)
            # Si respondió en 5 segundos de 20: 1000 * (15/20) = 750 puntos
            tiempo_restante = max(0, tiempo_limite - tiempo)
            factor_tiempo = tiempo_restante / tiempo_limite

            # Mínimo 500 puntos por respuesta correcta, máximo 1000
            puntos = int(PUNTAJE_BASE * (0.5 + 0.5 * factor_tiempo))

        resultados.append(
            {
                "jugador_id": respuesta["jugador_id"],
                "nombre": respuesta.get("nombre", "Anónimo"),
                "puntos_ganados": puntos,
                "respuesta_correcta": respuesta.get("es_correcta", False),
            }
        )

    return resultados


def actualizar_puntajes_totales(jugadores_actuales, resultados_pregunta):
    """
    Actualiza los puntajes totales de los jugadores.

    Parámetros:
    - jugadores_actuales: Lista de jugadores con sus puntajes actuales
        [{'id': 1, 'nombre': 'Juan', 'puntaje': 1500}, ...]
    - resultados_pregunta: Resultados de calcular_puntajes()

    Retorna:
    - Lista actualizada de jugadores con nuevos puntajes, ordenada por puntaje
    """

    # Crear diccionario para búsqueda rápida
    puntajes_nuevos = {
        r["jugador_id"]: r["puntos_ganados"] for r in resultados_pregunta
    }

    # Actualizar puntajes
    for jugador in jugadores_actuales:
        puntos_ganados = puntajes_nuevos.get(jugador["id"], 0)
        jugador["puntaje"] = jugador.get("puntaje", 0) + puntos_ganados
        jugador["puntos_ultima_pregunta"] = puntos_ganados

    # Ordenar por puntaje descendente
    jugadores_ordenados = sorted(
        jugadores_actuales, key=lambda x: x["puntaje"], reverse=True
    )

    # Asignar posiciones
    for i, jugador in enumerate(jugadores_ordenados):
        jugador["posicion"] = i + 1

    return jugadores_ordenados


def obtener_podio(jugadores):
    """
    Obtiene el top 3 para el podio.

    Parámetros:
    - jugadores: Lista de jugadores ordenada por puntaje

    Retorna:
    - Diccionario con primero, segundo y tercero
    """

    podio = {"primero": None, "segundo": None, "tercero": None}

    if len(jugadores) >= 1:
        podio["primero"] = {
            "nombre": jugadores[0]["nombre"],
            "puntaje": jugadores[0]["puntaje"],
        }

    if len(jugadores) >= 2:
        podio["segundo"] = {
            "nombre": jugadores[1]["nombre"],
            "puntaje": jugadores[1]["puntaje"],
        }

    if len(jugadores) >= 3:
        podio["tercero"] = {
            "nombre": jugadores[2]["nombre"],
            "puntaje": jugadores[2]["puntaje"],
        }

    return podio


def generar_estadisticas_pregunta(respuestas, opciones):
    """
    Genera estadísticas de una pregunta para mostrar en pantalla.

    Parámetros:
    - respuestas: Lista de respuestas de los jugadores
    - opciones: Lista de opciones de la pregunta

    Retorna:
    - Diccionario con estadísticas
    """

    total_respuestas = len(respuestas)
    correctas = sum(1 for r in respuestas if r.get("es_correcta", False))
    incorrectas = total_respuestas - correctas

    # Contar respuestas por opción
    conteo_opciones = {}
    for opcion in opciones:
        conteo_opciones[opcion["id"]] = {
            "texto": opcion["texto"],
            "cantidad": 0,
            "es_correcta": opcion["es_correcta"],
        }

    for respuesta in respuestas:
        opcion_id = respuesta.get("opcion_id")
        if opcion_id in conteo_opciones:
            conteo_opciones[opcion_id]["cantidad"] += 1

    return {
        "total_respuestas": total_respuestas,
        "correctas": correctas,
        "incorrectas": incorrectas,
        "porcentaje_acierto": round(
            (correctas / total_respuestas * 100) if total_respuestas > 0 else 0, 1
        ),
        "por_opcion": conteo_opciones,
    }
