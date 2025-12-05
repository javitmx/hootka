# 💎 GAME LIVE — ¡Crea y Juega Cuestionarios Interactivos!

¡Bienvenido a **GAME LIVE**! Esta es una aplicación web divertida y visualmente impactante, perfecta para crear y dirigir tus propios cuestionarios interactivos, ¡al estilo de los famosos juegos de preguntas en vivo!

Imagina un profesor lanzando preguntas en una pantalla grande (el "Host") mientras sus estudiantes responden emocionados desde sus teléfonos (los "Jugadores"). Eso es GAME LIVE: una experiencia dinámica con una estética neón muy llamativa.

## ✨ ¿Qué puedes hacer con GAME LIVE?

* **👥 Gestionar Usuarios:** Los usuarios pueden registrarse e iniciar sesión de forma segura.
* **📚 Crear Cuestionarios:** Los "Hosts" pueden diseñar sus propios sets de preguntas para diferentes temas.
* **❓ Tipos de Preguntas:** Prepara preguntas de texto simple o preguntas con imágenes.
* **✔️ Tipos de Respuestas:** Desde opciones únicas o múltiples hasta respuestas abiertas donde los jugadores escriben.
* **🖥️ Panel del Host:** Una interfaz clara para que el administrador controle el juego, vea los temporizadores, las preguntas y la tabla de clasificación en vivo.
* **📱 Experiencia del Jugador:** Una vista optimizada para móviles donde los jugadores se unen con un código PIN y responden en tiempo real.
* **🏆 Podio y Puntuación:** El sistema calcula puntos automáticamente y muestra los ganadores al final de cada partida.
* **🎨 Diseño al Estilo Neón:** Disfruta de una interfaz moderna y vibrante inspirada en la estética cyberpunk.

<picture>
  <img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" alt="divider">
</picture>

## 🚀 ¡Manos a la Obra! ¿Cómo empezar?

Para que GAME LIVE funcione en tu computadora, necesitamos preparar algunas cosas. ¡No te asustes! Te guiaré paso a paso.

### 📝 Requisitos Esenciales

Asegúrate de tener estos dos programas instalados en tu computadora:

#### 🐍 1. Python (El cerebro de la aplicación)

Python es el lenguaje de programación con el que está hecha esta aplicación.

* **Versión recomendada:** 3.10 o superior.
* **¿Dónde descargarlo?** Visita [https://www.python.org/downloads/](https://www.python.org/downloads/)
* **¡Un truco importante durante la instalación en Windows!** Asegúrate de marcar la opción **“Add Python to PATH”**. Esto le permite a tu computadora encontrar Python fácilmente.
* **¿Cómo saber si está instalado?** Abre una ventana de "Símbolo del sistema" (CMD) o "PowerShell" y escribe:
    ```bash
    python --version
    ```
    Si ves un número de versión (ej. `Python 3.10.0`), ¡listo!

#### 🧱 2. XAMPP (Tu servidor de base de datos)

XAMPP es un programa que te da un servidor web y de base de datos MySQL en tu propia computadora. Lo necesitamos para guardar todos los cuestionarios y usuarios.

* **¿Dónde descargarlo?** Ve a [https://www.apachefriends.org/es/index.html](https://www.apachefriends.org/es/index.html)
* **Instala XAMPP** y asegúrate de seleccionar los componentes:
    * ✅ **Apache** (el servidor web)
    * ✅ **MySQL** (el gestor de base de datos)
* **¡Inícialos!** Abre el "Panel de Control de XAMPP" y haz clic en "Start" junto a **Apache** y **MySQL**. Cuando estén activos, sus nombres se pondrán en verde.

<picture>
  <img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" alt="divider">
</picture>

## 🗄️ Configuración de la Base de Datos (Dónde se guarda todo)

Vamos a crear el espacio en tu base de datos para GAME LIVE.

1.  Abre tu navegador web y ve a **phpMyAdmin**: [http://localhost/phpmyadmin](http://localhost/phpmyadmin)
2.  Haz clic en la pestaña **"SQL"** en la parte superior.
3.  Copia y pega el siguiente código completo en el cuadro de texto de SQL. Este código crea la base de datos y todas las tablas necesarias para tu aplicación:

    ```sql
    -- Crear la base de datos (si no existe) y seleccionarla
    CREATE DATABASE IF NOT EXISTS kahoot_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    USE kahoot_db;

    -- Tabla de Usuarios: Guarda la información de quienes usan la aplicación (Hosts/Administradores)
    CREATE TABLE IF NOT EXISTS usuarios (
      id INT AUTO_INCREMENT PRIMARY KEY,
      username VARCHAR(50) NOT NULL UNIQUE,
      email VARCHAR(100) NOT NULL UNIQUE,
      password_hash VARCHAR(255) NOT NULL, -- La contraseña se guarda codificada por seguridad
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    -- Tabla de Cuestionarios: Cada fila es un cuestionario que un usuario ha creado
    CREATE TABLE IF NOT EXISTS cuestionarios (
      id INT AUTO_INCREMENT PRIMARY KEY,
      usuario_id INT NOT NULL, -- Quién es el dueño del cuestionario
      titulo VARCHAR(255) NOT NULL,
      fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
    );

    -- Tabla de Preguntas: Guarda los detalles de cada pregunta de un cuestionario
    CREATE TABLE IF NOT EXISTS preguntas (
      id INT AUTO_INCREMENT PRIMARY KEY,
      cuestionario_id INT NOT NULL, -- A qué cuestionario pertenece esta pregunta
      tipo_pregunta ENUM('texto', 'imagen') NOT NULL, -- ¿Es solo texto o tiene una imagen?
      tipo_respuesta ENUM('abierta', 'unica', 'multiple') NOT NULL, -- ¿Cómo se responde?
      texto_pregunta TEXT NOT NULL,
      imagen_url VARCHAR(255) DEFAULT NULL, -- Enlace a la imagen si es una pregunta con imagen
      tiempo_limite INT DEFAULT 30, -- Segundos para responder
      orden INT DEFAULT 0, -- Orden de la pregunta en el cuestionario
      FOREIGN KEY (cuestionario_id) REFERENCES cuestionarios(id) ON DELETE CASCADE
    );

    -- Tabla de Opciones de Respuesta: Las posibles respuestas para cada pregunta (A, B, C, D...)
    CREATE TABLE IF NOT EXISTS opciones (
        id INT AUTO_INCREMENT PRIMARY KEY,
        pregunta_id INT NOT NULL, -- A qué pregunta pertenece esta opción
        texto_opcion VARCHAR(255) NOT NULL,
        es_correcta BOOLEAN DEFAULT FALSE, -- ¿Es la respuesta correcta? (Sí/No)
        FOREIGN KEY (pregunta_id) REFERENCES preguntas(id) ON DELETE CASCADE
    );

    -- Tabla de Partidas: Controla cada sesión de juego en vivo
    CREATE TABLE IF NOT EXISTS partidas (
        id INT AUTO_INCREMENT PRIMARY KEY,
        pin VARCHAR(10) NOT NULL UNIQUE, -- El código único para unirse a la partida
        usuario_id INT NOT NULL, -- Quién es el Host (administrador) de la partida
        cuestionario_id INT NOT NULL, -- Qué cuestionario se está jugando
        estado ENUM('esperando', 'en_progreso', 'finalizada') DEFAULT 'esperando',
        pregunta_actual_indice INT DEFAULT 0, -- Qué pregunta se está mostrando ahora
        fecha_inicio DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
        FOREIGN KEY (cuestionario_id) REFERENCES cuestionarios(id)
    );

    -- Tabla de Jugadores en Sesión: Quiénes están conectados y jugando en una partida
    CREATE TABLE IF NOT EXISTS jugadores_sesion (
        id INT AUTO_INCREMENT PRIMARY KEY,
        partida_id INT NOT NULL, -- A qué partida están conectados
        nombre_jugador VARCHAR(50) NOT NULL,
        puntaje_total INT DEFAULT 0,
        FOREIGN KEY (partida_id) REFERENCES partidas(id) ON DELETE CASCADE
    );

    -- Tabla de Respuestas de Jugadores: Guarda qué respondió cada jugador a cada pregunta
    CREATE TABLE IF NOT EXISTS respuestas_jugadores (
        id INT AUTO_INCREMENT PRIMARY KEY,
        jugador_id INT NOT NULL,
        pregunta_id INT NOT NULL,
        opcion_id INT DEFAULT NULL, -- Si eligió una opción, cuál fue (NULL si es respuesta abierta)
        texto_respuesta TEXT DEFAULT NULL, -- Para respuestas abiertas de texto
        es_correcta BOOLEAN DEFAULT FALSE,
        puntos_ganados INT DEFAULT 0,
        tiempo_respuesta FLOAT, -- Cuánto tardó en responder
        FOREIGN KEY (jugador_id) REFERENCES jugadores_sesion(id) ON DELETE CASCADE,
        FOREIGN KEY (pregunta_id) REFERENCES preguntas(id) ON DELETE CASCADE
    );
    ```

4.  Haz clic en el botón "Continuar" o "Ejecutar" (dependiendo de tu phpMyAdmin).

### 🔐 Datos de Conexión a MySQL (XAMPP)

Así es como tu aplicación se conectará a la base de datos en tu computadora (esto ya está configurado en el código, ¡es solo para tu información!):

* **Host:** `localhost`
* **Usuario:** `root`
* **Contraseña:** (vacía por defecto)
* **Puerto:** `3306`

<picture>
  <img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" alt="divider">
</picture>

## 📂 Estructura del Proyecto (¿Qué hay dentro?)

Aquí te muestro cómo está organizado el proyecto GAME LIVE. Cada carpeta y archivo tiene una función importante:

```
game-live/                 <-- Carpeta principal del proyecto
├── static/                <-- Archivos para la "belleza" de la web: estilos, scripts y fotos
│   ├── css/
│   │   └── style.css      <-- Tus estilos personalizados con efecto neón
│   └── uploads/           <-- Aquí se guardan las imágenes que subas para las preguntas
├── templates/             <-- Las "plantillas" de las páginas web (el diseño HTML)
│   ├── base.html          <-- El esqueleto base para todas las páginas
│   ├── login.html         <-- Página para iniciar sesión
│   ├── register.html      <-- Página para crear una nueva cuenta
│   ├── index.html         <-- Página principal (donde los jugadores meten el PIN)
│   ├── crear_cuestionario.html <-- Página para que el Host cree sus preguntas
│   ├── host.html          <-- Panel de control para el Host durante la partida
│   ├── lobby.html         <-- Sala de espera para jugadores antes de empezar
│   ├── question.html      <-- Vista de la pregunta para los jugadores
│   ├── podium.html        <-- Muestra los resultados finales
│   └── ...                <-- Otros archivos de plantillas
├── app.py                 <-- ¡El corazón del proyecto! Aquí está la lógica principal y las páginas
├── database.py            <-- Se encarga de conectar con la base de datos MySQL
├── evaluadora.py          <-- Lógica para calcular puntuaciones y evaluar respuestas
├── requirements.txt       <-- Una lista de todos los "ingredientes" de Python que la app necesita
└── README.md              <-- Este mismo archivo que estás leyendo :)
```

<picture>
  <img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" alt="divider">
</picture>

## 📦 ¡Instala y Corre la Aplicación!

¡Ya casi estás listo para ver GAME LIVE en acción!

1.  **Abre tu Terminal/Consola:**
    En la carpeta de tu proyecto `game-live` (donde está `app.py`), haz clic derecho en un espacio vacío y selecciona **"Open Git Bash Here"** (o usa el Símbolo del sistema de Windows).

2.  **Activa el Entorno Virtual:**
    Es una "burbuja" de Python para este proyecto. Así no hay conflictos con otros programas.

    ```bash
    source venv/Scripts/activate
    ```
    *(Verás `(venv)` al principio de la línea de tu terminal, ¡eso significa que funciona!)*

3.  **Instala los "ingredientes" (dependencias):**
    Este comando lee el archivo `requirements.txt` y descarga todo lo que necesita la aplicación.

    ```bash
    pip install -r requirements.txt
    ```

4.  **¡Lanza la Aplicación!**
    Asegúrate de que MySQL esté funcionando en tu Panel de Control de XAMPP. Luego, en la terminal:

    ```bash
    python app.py
    ```
    Si todo va bien, verás un mensaje como este:
    ```
    * Running on http://127.0.0.1:5000
    * Press CTRL+C to quit
    ```

<picture>
  <img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" alt="divider">
</picture>

## 🌐 ¡A Jugar! (Verificar el funcionamiento)

1.  Abre tu navegador web y ve a la dirección que te dio la terminal:
    👉 **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

2.  **Regístrate:** Ve a `http://127.0.0.1:5000/register` y crea una nueva cuenta de usuario. ¡Conviértete en el Host!

3.  **Crea un Cuestionario:** Inicia sesión con tu nueva cuenta. Busca la opción para crear un cuestionario y añade algunas preguntas de prueba (con opciones, imágenes, etc.).

4.  **Inicia una Partida:** Desde el panel de Host, inicia uno de tus cuestionarios. Te dará un **PIN**.

5.  **Únete como Jugador:** Abre otra pestaña en tu navegador (o usa tu móvil) y ve de nuevo a `http://127.0.0.1:5000`. Introduce el **PIN** que te dio el Host para unirte a la partida.

6.  **¡Juega!** Desde el panel del Host, avanza las preguntas. Desde la vista del Jugador, responde. Observa cómo el podio se actualiza en tiempo real.

7.  **Cierra Sesión:** Cuando termines, no olvides cerrar tu sesión.

<picture>
  <img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" alt="divider">
</picture>

## 🌟 ¡Disfruta de tu creación!

¡Felicidades por completar este proyecto! Espero que GAME LIVE te sea muy útil para tus sesiones de preguntas. Si tienes alguna duda o sugerencia, no dudes en contactar.

<picture>
  <img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" alt="divider">
</picture>

**Desarrollado por:** JaviTMX
**Versión:** 1.0.0
**Licencia:** Free-Code
````http://googleusercontent.com/image_generation_content/6````
<picture>
  <img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" alt="divider">
</picture>

# 🌐 Jugar Online con Amigos (Usando ngrok)

Por defecto, cuando ejecutas la aplicación (`python app.py`), solo funciona en **tu propia computadora** (eso significa `localhost` o `127.0.0.1`).

**¿Pero qué pasa si quieres que tus amigos se unan desde sus casas con sus celulares?**

Para eso usamos una herramienta llamada **ngrok**. Ngrok crea un "túnel" seguro desde tu computadora hacia internet, dándote una dirección web pública temporal que puedes compartir con quien quieras.

### Pasos para configurar ngrok

#### 1. Descarga y Configura ngrok
Si aún no lo tienes:
* Ve a [https://ngrok.com/download](https://ngrok.com/download) y descárgalo para tu sistema operativo.
* Regístrate gratis en su web.
* Sigue las instrucciones que te dan para conectar tu cuenta (usualmente es un comando que copias y pegas en la terminal una sola vez, algo como `ngrok config add-authtoken TU_TOKEN`).

#### 2. Inicia tu Aplicación GAME LIVE (Terminal 1)
Como siempre, abre tu primera terminal, activa el entorno virtual y ejecuta la app:
```bash
python app.py
```
### 3. Inicia el Túnel ngrok (Terminal 2)
Sin cerrar la primera terminal, abre una SEGUNDA ventana de terminal (Git Bash, CMD o PowerShell).
En esta nueva ventana, escribe el siguiente comando para decirle a ngrok que exponga el puerto 5000 (donde corre tu Flask):

```bash
ngrok http 5000
```
### 4.¡Obtén tu Enlace Público!
Verás que la terminal de ngrok cambia y te muestra una pantalla con varios datos. Busca la línea que dice Forwarding.

Verás una dirección web que termina en .ngrok-free.app. ¡Ese es tu enlace mágico!

Se verá algo parecido a esto (el tuyo será diferente): Forwarding https://1a2b-3c4d-5e6f.ngrok-free.app -> http://localhost:5000

👉 Copia la dirección HTTPS completa (ej. https://1a2b-3c4d-5e6f.ngrok-free.app).

### 5. Comparte y Juega
* Tú (como Host): Usa esa dirección HTTPS en tu navegador para entrar, iniciar sesión y lanzar la partida.
* Tus Amigos (Jugadores): Envíales esa dirección HTTPS por WhatsApp, Discord, etc. Ellos deberán abrirla en el navegador de sus celulares para ver la pantalla de inicio e ingresar el PIN.

## ⚠️ Importante sobre ngrok:
* No cierres la terminal de ngrok mientras estén jugando, o el enlace dejará de funcionar.
* En la versión gratuita, el enlace cambia cada vez que cierras y vuelves a abrir ngrok. Asegúrate de enviar siempre el enlace nuevo antes de empezar a jugar.
