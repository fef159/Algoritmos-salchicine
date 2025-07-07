from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash
import sqlite3
from models.models import NodoPelicula, ListaCircularEnlazada
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from werkzeug.security import generate_password_hash, check_password_hash
from io import BytesIO
import os
import json
from flask import send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Establecer una clave secreta para las sesiones
app.secret_key = '123456'

# Conexión a la base de datos SQLite
DATABASE = 'database/salchichon.sqlite'


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Para obtener resultados como diccionarios
    return conn


@app.route('/')
def index():
    # Verificar si el usuario está logueado
    user_name = None
    if 'user_id' in session:
        # Obtener el nombre del usuario desde la sesión
        user_name = session['user_name']

    lista_peliculas = ListaCircularEnlazada()

    # Consulta de las películas en la base de datos
    conn = get_db()
    cursor = conn.cursor()
    # CAMBIO: Incluir el ID real de la película en la consulta
    cursor.execute("SELECT id, titulo, descripcion, imagen FROM Peliculas")
    peliculas = cursor.fetchall()
    conn.close()

    # Agregar las películas a la lista circular
    for pelicula in peliculas:
        lista_peliculas.agregar_pelicula(
            pelicula[1],    # titulo
            pelicula[2],    # descripcion
            pelicula[0],    # id real de la base de datos (NO el índice)
            pelicula[3],    # imagen
            None
        )

    # Obtener las tres películas
    pelicula_actual = lista_peliculas.obtener_primera_pelicula()
    pelicula_siguiente = lista_peliculas.obtener_siguiente(pelicula_actual)
    pelicula_tercera = lista_peliculas.obtener_siguiente(pelicula_siguiente)
    pelicula_anterior = lista_peliculas.obtener_anterior(pelicula_actual)
    pelicula_siguiente_siguiente = lista_peliculas.obtener_siguiente(
        pelicula_tercera)

    data = {
        'titulo': 'Peliculas en Estreno',
        'bienvenida': '¡Disfruta de nuestra selección de películas!',
        'pelicula_actual': pelicula_actual,
        'pelicula_siguiente': pelicula_siguiente,
        'pelicula_tercera': pelicula_tercera,
        'pelicula_anterior': pelicula_anterior,
        'pelicula_siguiente_siguiente': pelicula_siguiente_siguiente,
        'user_name': user_name  # Pasamos el nombre del usuario a la plantilla
    }

    return render_template('index.html', data=data)


@app.route('/pelicula/<int:indice>', methods=['GET'])
def ver_pelicula(indice):
    lista_peliculas = ListaCircularEnlazada()

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, titulo, descripcion, imagen FROM Peliculas")
    peliculas = cursor.fetchall()
    conn.close()

    # Agregar las películas a la lista circular usando el ID real como 'indice'
    for pelicula in peliculas:
        lista_peliculas.agregar_pelicula(
            pelicula[1], pelicula[2], pelicula[0], pelicula[3], None)

    # Obtener la película actual a partir del ID real
    pelicula_actual = lista_peliculas.obtener_primera_pelicula()
    while pelicula_actual:
        if pelicula_actual.indice == indice:
            break
        pelicula_actual = lista_peliculas.obtener_siguiente(pelicula_actual)

    # Obtener las siguientes y anteriores películas
    pelicula_anterior = lista_peliculas.obtener_anterior(pelicula_actual)
    pelicula_siguiente = lista_peliculas.obtener_siguiente(pelicula_actual)
    pelicula_siguiente_siguiente = lista_peliculas.obtener_siguiente(
        pelicula_siguiente)

    pelicula_tercera = pelicula_siguiente_siguiente

    user_name = session.get('user_name')

    data = {
        'titulo': 'Peliculas en Estreno',
        'bienvenida': '¡Disfruta de nuestra selección de películas!',
        'pelicula_actual': pelicula_actual,
        'pelicula_anterior': pelicula_anterior,
        'pelicula_siguiente': pelicula_siguiente,
        'pelicula_siguiente_siguiente': pelicula_siguiente_siguiente,
        'pelicula_tercera': pelicula_tercera,
        'user_name': user_name
    }

    return render_template('index.html', data=data)


@app.route('/peliculas', methods=['GET', 'POST'])
def peliculas():
    conn = get_db()  # Conexión a la base de datos SQLite
    cursor = conn.cursor()

    # Obtener géneros únicos sin duplicados
    cursor.execute(
        "SELECT id, nombre FROM Generos GROUP BY nombre ORDER BY nombre")
    generos_raw = cursor.fetchall()

    # Eliminar duplicados manualmente por si GROUP BY no es suficiente
    generos = []
    generos_vistos = set()
    for genero in generos_raw:
        if genero[1] not in generos_vistos:
            generos.append(genero)
            generos_vistos.add(genero[1])

    # Obtener todas las películas únicas (sin duplicados por título)
    cursor.execute(
        "SELECT id, titulo, descripcion, imagen, genero_id FROM Peliculas GROUP BY titulo ORDER BY titulo")
    peliculas_db = cursor.fetchall()

    # Crear diccionario de géneros para lookup rápido
    generos_dict = {g[0]: g[1] for g in generos}

    # Variables de estado
    tipo_busqueda = 'genero'
    busqueda_seleccionada = None
    resultados = []
    peliculas_desplegable = []

    # Procesar formulario POST
    if request.method == 'POST':
        tipo_busqueda = request.form.get('tipo_busqueda', 'genero')
        busqueda_seleccionada = request.form.get('busqueda', '')

        # Normalizar entrada vacía
        if busqueda_seleccionada in ['', 'Todas', None]:
            busqueda_seleccionada = None

    # Filtrar películas según el tipo de búsqueda
    if tipo_busqueda == 'genero':
        if busqueda_seleccionada:
            # Buscar por género específico
            cursor.execute("""
                SELECT p.id, p.titulo, p.descripcion, p.imagen, p.genero_id 
                FROM Peliculas p 
                JOIN Generos g ON p.genero_id = g.id 
                WHERE g.nombre = ?
                GROUP BY p.titulo
                ORDER BY p.titulo
            """, (busqueda_seleccionada,))
            peliculas_filtradas = cursor.fetchall()
        else:
            # Mostrar todas las películas únicas
            peliculas_filtradas = peliculas_db

        # Opciones para el desplegable (géneros)
        peliculas_desplegable = [{'nombre': g[1]} for g in generos]

    elif tipo_busqueda == 'nombre':
        if busqueda_seleccionada:
            # Buscar por nombre específico
            cursor.execute("""
                SELECT id, titulo, descripcion, imagen, genero_id 
                FROM Peliculas 
                WHERE titulo = ?
                GROUP BY titulo
                ORDER BY titulo
            """, (busqueda_seleccionada,))
            peliculas_filtradas = cursor.fetchall()
        else:
            # Mostrar todas las películas únicas
            peliculas_filtradas = peliculas_db

        # Opciones para el desplegable (títulos únicos)
        cursor.execute(
            "SELECT titulo FROM Peliculas GROUP BY titulo ORDER BY titulo")
        titulos_unicos = cursor.fetchall()
        peliculas_desplegable = [{'titulo': t[0]} for t in titulos_unicos]

    # Formatear resultados para la plantilla
    resultados = []
    for idx, pelicula in enumerate(peliculas_filtradas):
        pelicula_id, titulo, descripcion, imagen, genero_id = pelicula
        genero_nombre = generos_dict.get(genero_id, 'Sin género')

        resultados.append({
            'indice': idx,
            'id': pelicula_id,
            'titulo': titulo,
            'descripcion': descripcion or '',  # Manejar None
            'imagen': imagen or 'default.jpg',  # Imagen por defecto si es None
            'genero': genero_nombre,
        })

    # Cerrar conexión
    conn.close()

    # Datos para la plantilla
    data = {
        'titulo': 'Películas',
        'bienvenida': '¡Disfruta de nuestra selección de películas!',
        'user_name': session.get('user_name')
    }

    return render_template('peliculas.html',
                           generos=generos,
                           peliculas_desplegable=peliculas_desplegable,
                           resultados=resultados,
                           tipo_busqueda=tipo_busqueda,
                           busqueda_seleccionada=busqueda_seleccionada,
                           data=data)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email_or_user = request.form['email']
        contraseña = request.form['contraseña']

        conn = get_db()
        cursor = conn.cursor()

        # Buscar en Usuarios por email o nombre de usuario
        cursor.execute('SELECT * FROM Usuarios WHERE email = ? OR nombre = ?',
                       (email_or_user, email_or_user))
        usuario = cursor.fetchone()
        if usuario and check_password_hash(usuario['contraseña'], contraseña):
            session['user_id'] = usuario['id']
            session['user_name'] = usuario['nombre']
            return redirect(url_for('index'))

        # Buscar en Admin por email o usuario
        cursor.execute('SELECT * FROM Admin WHERE email = ? OR usuario = ?',
                       (email_or_user, email_or_user))
        admin = cursor.fetchone()
        if admin and (admin['contraseña'] == contraseña or (admin['contraseña'].startswith('pbkdf2:') and check_password_hash(admin['contraseña'], contraseña))):
            session['admin_id'] = admin['id']
            session['admin_name'] = admin['usuario']
            return redirect(url_for('dashboard_admin'))

        return render_template('login.html', error="Credenciales incorrectas.")

    return render_template('login.html')


@app.route('/registrarse', methods=['GET', 'POST'])
def registrarse():
    if request.method == 'POST':
        nombre = request.form['nombre']
        email = request.form['email']
        contraseña = request.form['contraseña']
        confirmar_contraseña = request.form['confirmar_contraseña']

        # Validar que las contraseñas coincidan
        if contraseña != confirmar_contraseña:
            return render_template('registrarse.html', error="Las contraseñas no coinciden.")

        # Hashear la contraseña antes de guardarla
        hashed_password = generate_password_hash(
            contraseña, method='pbkdf2:sha256')

        # Conexión a la base de datos
        conn = get_db()
        cursor = conn.cursor()

        # Verificar si el correo ya está registrado
        cursor.execute('SELECT * FROM Usuarios WHERE email = ?', (email,))
        if cursor.fetchone():
            return render_template('registrarse.html', error="El correo electrónico ya está registrado.")

        # Registrar al nuevo usuario con la contraseña hasheada
        cursor.execute(
            'INSERT INTO Usuarios (nombre, email, contraseña) VALUES (?, ?, ?)', (nombre, email, hashed_password))
        conn.commit()

        return redirect(url_for('login'))

    return render_template('registrarse.html')


@app.route('/usuarios')
def usuarios():
    # Aquí va la lógica para mostrar los usuarios
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM Usuarios')
    usuarios = cursor.fetchall()
    conn.close()

    return render_template('usuarios.html', usuarios=usuarios)


@app.route('/compra/<int:pelicula_id>', methods=['GET', 'POST'])
def compra(pelicula_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor()
    # Corregir la consulta para obtener todos los campos necesarios, incluyendo el id
    cursor.execute(
        "SELECT id, titulo, descripcion, imagen FROM Peliculas WHERE id = ?", (pelicula_id,))
    pelicula = cursor.fetchone()
    conn.close()

    # Verificar que la película existe
    if not pelicula:
        flash('La película solicitada no existe.', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        try:
            cantidad = int(request.form['cantidad'])

            # Validar que la cantidad sea válida
            if cantidad < 1 or cantidad > 10:
                flash('La cantidad debe estar entre 1 y 10.', 'error')
                return render_template('compra.html', pelicula=pelicula)

            conn = get_db()
            cursor = conn.cursor()

            # Insertar la compra en la base de datos
            cursor.execute('''
                INSERT INTO Compras (usuario_id, pelicula_id, cantidad)
                VALUES (?, ?, ?)
            ''', (session['user_id'], pelicula_id, cantidad))

            conn.commit()
            conn.close()

            return redirect(url_for('compra_confirmada', pelicula_id=pelicula_id, cantidad=cantidad))

        except ValueError:
            flash('Por favor, ingrese una cantidad válida.', 'error')
        except Exception as e:
            flash('Error al procesar la compra. Intente nuevamente.', 'error')
            print(f"Error en compra: {e}")  # Para debugging

    return render_template('compra.html', pelicula=pelicula)


@app.route('/compra_confirmada')
def compra_confirmada():
    pelicula_id = request.args.get('pelicula_id', type=int)
    cantidad = request.args.get('cantidad', type=int)

    # Validar que se recibieron los parámetros
    if not pelicula_id or not cantidad:
        flash('Error: Información de compra incompleta.', 'error')
        return redirect(url_for('index'))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, titulo, descripcion, imagen FROM Peliculas WHERE id = ?", (pelicula_id,))
    pelicula = cursor.fetchone()
    conn.close()

    # Verificar que la película existe
    if not pelicula:
        flash('Error: Película no encontrada.', 'error')
        return redirect(url_for('index'))

    # Calcular el total
    precio_unitario = 15.00
    total = precio_unitario * cantidad

    return render_template('compra_confirmada.html',
                           cantidad=cantidad,
                           pelicula=pelicula,
                           precio_unitario=precio_unitario,
                           total=total)


@app.route('/pelicula/detalles/<int:pelicula_id>', methods=['GET'])
def ver_detalles_pelicula(pelicula_id):
    # Conexión a la base de datos
    conn = get_db()
    cursor = conn.cursor()

    # Obtener los detalles completos de la película
    cursor.execute('''
        SELECT id, titulo, descripcion, duracion, hora_funcion, imagen, banner_pelicula 
        FROM Peliculas 
        WHERE id = ?
    ''', (pelicula_id,))
    pelicula = cursor.fetchone()
    conn.close()

    # Verificar si la película existe
    if pelicula:
        data = {
            'id': pelicula['id'],
            # ← AGREGADO: Para que funcione el botón de comprar
            'indice': pelicula['id'],
            'titulo': pelicula['titulo'],
            'descripcion': pelicula['descripcion'],
            'duracion': pelicula['duracion'],
            'hora_funcion': pelicula['hora_funcion'],
            'imagen': pelicula['imagen'],
            'banner_pelicula': pelicula['banner_pelicula'],
        }
        return render_template('detalle_pelicula.html', data=data)
    else:
        return redirect(url_for('index'))


@app.route('/logout')
def logout():
    # Verificar si el usuario es un admin
    if 'admin_id' in session:
        # Eliminar la clave 'admin_id' si es un admin
        session.pop('admin_id', None)
        # Eliminar la clave 'admin_name' si es un admin
        session.pop('admin_name', None)
    else:
        # Eliminar las claves de sesión para el usuario regular
        session.pop('user_id', None)
        session.pop('user_name', None)

    # Redirigir al usuario a la página de login o al inicio
    # Redirigir al login o a la página de inicio
    return redirect(url_for('login'))


@app.route('/mis_tickets', methods=['GET', 'POST'])
def mis_tickets():
    # Debugging: Verificar que el nombre del usuario esté en la sesión
    print(f"Nombre del usuario: {session.get('user_name')}")

    # Verificar si el usuario está logueado
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor()

    # Obtener los tickets comprados por el usuario (cine)
    cursor.execute('''
        SELECT c.id, p.titulo, c.cantidad, c.fecha_compra, p.id as pelicula_id
        FROM Compras c
        JOIN Peliculas p ON c.pelicula_id = p.id
        WHERE c.usuario_id = ?
        ORDER BY c.fecha_compra DESC
    ''', (session['user_id'],))
    tickets = cursor.fetchall()

    # Obtener las compras de dulcería
    cursor.execute('''
        SELECT id, productos, total, fecha_compra, pdf_path
        FROM ComprasDulceria
        WHERE usuario_id = ?
        ORDER BY fecha_compra DESC
    ''', (session['user_id'],))
    dulceria_raw = cursor.fetchall()
    dulceria = []
    for row in dulceria_raw:
        try:
            productos = json.loads(row[1])
        except Exception:
            productos = []
        dulceria.append((row[0], productos, row[2], row[3], row[4]))
    conn.close()

    # Crear el diccionario 'data' con el nombre del usuario
    data = {
        'titulo': 'Mis Tickets Comprados',
        'user_name': session.get('user_name')
    }

    # Opción de descarga de PDF (solo para cine)
    if request.args.get('download') == 'true':
        return descargar_tickets_pdf(tickets)

    # Pasar ambas listas a la plantilla
    return render_template('mis_tickets.html', tickets=tickets, dulceria=dulceria, data=data)


def descargar_tickets_pdf(tickets):
    # Crear un objeto BytesIO para almacenar el PDF en memoria
    buffer = BytesIO()

    # Crear un canvas para el PDF
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Título
    c.setFont("Helvetica-Bold", 16)
    c.drawString(30, height - 40, "Mis Tickets Comprados - CineDB")

    # Encabezados de la tabla
    c.setFont("Helvetica-Bold", 12)
    c.drawString(30, height - 70, "Película")
    c.drawString(250, height - 70, "Cantidad")
    c.drawString(350, height - 70, "Fecha de Compra")
    c.drawString(450, height - 70, "Total")

    # Línea separadora
    c.line(30, height - 75, 550, height - 75)

    # Insertar los datos de los tickets
    y_position = height - 95
    c.setFont("Helvetica", 10)
    precio_unitario = 15.00

    for ticket in tickets:
        # Verificar que no se salga de la página
        if y_position < 50:
            c.showPage()
            y_position = height - 50

        total_ticket = precio_unitario * ticket[2]

        # Título de la película (limitado a 30 chars)
        c.drawString(30, y_position, ticket[1][:30])
        c.drawString(250, y_position, str(ticket[2]))  # Cantidad
        # Fecha de compra (solo fecha)
        c.drawString(350, y_position, ticket[3][:10])
        c.drawString(450, y_position, f"S/. {total_ticket:.2f}")  # Total
        y_position -= 25  # Mover hacia abajo para el siguiente ticket

    # Finalizar el PDF
    c.showPage()
    c.save()

    # Volver al principio del buffer
    buffer.seek(0)

    # Enviar el archivo PDF al usuario para que lo descargue
    return send_file(buffer, as_attachment=True, download_name="mis_tickets.pdf", mimetype='application/pdf')


@app.route('/dashboard_admin')
def dashboard_admin():
    if 'admin_id' not in session:
        # Si no hay sesión de admin, redirigir al login
        return redirect(url_for('login'))

    # Obtener el nombre del administrador desde la sesión
    admin_name = session['admin_name']

    # Lógica para obtener estadísticas, como el número de películas, usuarios y compras
    conn = get_db()
    cursor = conn.cursor()

    # Obtener el número de películas registradas
    cursor.execute("SELECT COUNT(*) FROM Peliculas")
    num_peliculas = cursor.fetchone()[0]

    # Obtener el número de usuarios registrados
    cursor.execute("SELECT COUNT(*) FROM Usuarios")
    num_usuarios = cursor.fetchone()[0]

    # Obtener el número de compras realizadas
    cursor.execute("SELECT COUNT(*) FROM Compras")
    num_compras = cursor.fetchone()[0]

    conn.close()

    # Datos para la plantilla
    return render_template('admin/dashboard_admin.html', admin_name=admin_name,
                           num_peliculas=num_peliculas, num_usuarios=num_usuarios,
                           num_compras=num_compras)


@app.route('/compras')
def compras():
    if 'admin_id' not in session:
        # Redirigir al login si no hay sesión de admin
        return redirect(url_for('login'))

    # Obtener las compras de la base de datos
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT c.id, p.titulo, c.cantidad, c.fecha_compra, p.id as pelicula_id, u.nombre as usuario
        FROM Compras c
        JOIN Peliculas p ON c.pelicula_id = p.id
        JOIN Usuarios u ON c.usuario_id = u.id
        ORDER BY c.fecha_compra DESC
    ''')
    compras = cursor.fetchall()
    conn.close()

    return render_template('compras_admin.html', compras=compras)


@app.route('/cines')
def cines():
    # Lógica para mostrar cines y películas
    return render_template('cines.html')


@app.route('/dulceria', methods=['GET', 'POST'])
def dulceria():
    # Verificar si el usuario está logueado
    user_name = None
    if 'user_id' in session:
        # Obtener el nombre del usuario desde la sesión
        user_name = session['user_name']

    conn = get_db()
    cursor = conn.cursor()

    # Obtener todos los productos de la dulcería desde la base de datos
    cursor.execute('SELECT * FROM Dulceria')
    productos = cursor.fetchall()
    conn.close()

    # Si el usuario realiza una compra (POST)
    if request.method == 'POST':
        producto_id = request.form.get('producto_id')
        cantidad_str = request.form.get('cantidad')

        # Verificar si cantidad es válida
        if cantidad_str and cantidad_str.isdigit():  # Asegura que sea un número
            cantidad = int(cantidad_str)  # Convertir a entero

            # Obtener el producto para verificar
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute(
                'SELECT nombre, precio FROM Dulceria WHERE id = ?', (producto_id,))
            producto = cursor.fetchone()
            conn.close()

            if producto:
                # Aquí podrías procesar la compra directamente (sin carrito)
                flash(
                    f'{cantidad} unidades de {producto[0]} han sido compradas.', 'success')
            else:
                flash('Producto no encontrado.', 'error')
        else:
            flash('Por favor, ingresa una cantidad válida.', 'error')

        # Redirige a la misma página para seguir comprando
        return redirect(url_for('dulceria'))

    data = {
        'titulo': 'Dulcería',
        'productos': productos,
        'user_name': user_name  # Pasamos el nombre del usuario a la plantilla
    }

    return render_template('dulceria.html', data=data)


@app.route('/comprar_dulceria', methods=['POST'])
def comprar_dulceria():
    if 'user_id' not in session:
        return {'error': 'No autenticado'}, 401

    data = request.get_json()
    productos = data.get('productos', [])
    total = data.get('total', 0)
    usuario_id = session['user_id']

    if not productos or total <= 0:
        return {'error': 'Datos inválidos'}, 400

    # Guardar la compra en la base de datos
    conn = get_db()
    cursor = conn.cursor()
    productos_json = json.dumps(productos, ensure_ascii=False)
    cursor.execute('''
        INSERT INTO ComprasDulceria (usuario_id, productos, total)
        VALUES (?, ?, ?)
    ''', (usuario_id, productos_json, total))
    compra_id = cursor.lastrowid
    conn.commit()
    conn.close()

    # Generar el PDF y guardar la ruta
    pdf_filename = f'dulceria_ticket_{compra_id}.pdf'
    pdf_folder = os.path.join('static', 'tickets_dulceria')
    os.makedirs(pdf_folder, exist_ok=True)
    pdf_path = os.path.join(pdf_folder, pdf_filename)
    generar_pdf_dulceria(productos, total, pdf_path, compra_id)

    # Guardar la ruta del PDF en la base de datos
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE ComprasDulceria SET pdf_path = ? WHERE id = ?', (pdf_filename, compra_id))
    conn.commit()
    conn.close()

    return {'pdf_url': url_for('descargar_ticket_dulceria', compra_id=compra_id)}


def generar_pdf_dulceria(productos, total, pdf_path, compra_id):
    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter
    c.setFont("Helvetica-Bold", 16)
    c.drawString(30, height - 40, f"Ticket Dulcería #{compra_id}")
    c.setFont("Helvetica", 12)
    c.drawString(30, height - 70, "Producto")
    c.drawString(250, height - 70, "Cantidad")
    c.drawString(350, height - 70, "Precio Unitario")
    c.drawString(480, height - 70, "Subtotal")
    c.line(30, height - 75, 550, height - 75)
    y = height - 100
    for prod in productos:
        nombre = prod.get('name', '')
        cantidad = prod.get('quantity', 1)
        precio = prod.get('price', 0)
        subtotal = cantidad * precio
        c.drawString(30, y, nombre[:30])
        c.drawString(250, y, str(cantidad))
        c.drawString(350, y, f"S/. {precio:.2f}")
        c.drawString(480, y, f"S/. {subtotal:.2f}")
        y -= 25
        if y < 50:
            c.showPage()
            y = height - 50
    c.setFont("Helvetica-Bold", 13)
    c.drawString(30, y - 10, f"Total: S/. {total:.2f}")
    c.showPage()
    c.save()


@app.route('/dulceria/ticket/<int:compra_id>')
def descargar_ticket_dulceria(compra_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT pdf_path FROM ComprasDulceria WHERE id = ?', (compra_id,))
    row = cursor.fetchone()
    conn.close()
    if not row or not row[0]:
        return 'Ticket no encontrado', 404
    pdf_filename = row[0]
    pdf_folder = os.path.join('static', 'tickets_dulceria')
    return send_from_directory(pdf_folder, pdf_filename, as_attachment=True)


@app.route('/dulceria/compras', methods=['GET'])
def compras_dulceria_usuario():
    if 'user_id' not in session:
        return {'error': 'No autenticado'}, 401
    usuario_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, productos, total, fecha_compra, pdf_path
        FROM ComprasDulceria
        WHERE usuario_id = ?
        ORDER BY fecha_compra DESC
    ''', (usuario_id,))
    compras = cursor.fetchall()
    conn.close()
    compras_list = []
    for row in compras:
        compras_list.append({
            'id': row[0],
            'productos': json.loads(row[1]),
            'total': row[2],
            'fecha_compra': row[3],
            'pdf_url': url_for('descargar_ticket_dulceria', compra_id=row[0]) if row[4] else None
        })
    return {'compras': compras_list}


@app.route('/dulceria/tickets_pdf')
def descargar_todos_tickets_dulceria():
    if 'user_id' not in session:
        return {'error': 'No autenticado'}, 401
    usuario_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT productos, total, fecha_compra
        FROM ComprasDulceria
        WHERE usuario_id = ?
        ORDER BY fecha_compra DESC
    ''', (usuario_id,))
    compras = cursor.fetchall()
    conn.close()
    # Generar PDF en memoria
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    c.setFont("Helvetica-Bold", 16)
    c.drawString(30, height - 40, "Tickets de Dulcería - LaButaca")
    c.setFont("Helvetica-Bold", 12)
    c.drawString(30, height - 70, "Productos")
    c.drawString(300, height - 70, "Total")
    c.drawString(400, height - 70, "Fecha")
    c.line(30, height - 75, 550, height - 75)
    y = height - 100
    c.setFont("Helvetica", 10)
    for compra in compras:
        productos = []
        try:
            productos = json.loads(compra[0])
        except Exception:
            pass
        productos_str = ', '.join(
            [f"{p['name']} × {p['quantity']}" for p in productos])
        total = compra[1]
        fecha = compra[2][:19]
        if y < 60:
            c.showPage()
            y = height - 50
        c.drawString(30, y, productos_str[:60])
        c.drawString(300, y, f"S/. {total:.2f}")
        c.drawString(400, y, fecha)
        y -= 25
    c.showPage()
    c.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="tickets_dulceria.pdf", mimetype='application/pdf')


@app.route('/admin/peliculas')
def admin_peliculas():
    if 'admin_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''SELECT p.id, p.titulo, p.descripcion, p.duracion, g.nombre as genero, p.hora_funcion, p.imagen FROM Peliculas p LEFT JOIN Generos g ON p.genero_id = g.id ORDER BY p.id DESC''')
    peliculas = cursor.fetchall()
    conn.close()
    return render_template('admin/admin_peliculas.html', peliculas=peliculas)


@app.route('/admin/usuarios')
def admin_usuarios():
    if 'admin_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, nombre, email FROM Usuarios ORDER BY id DESC')
    usuarios = cursor.fetchall()
    conn.close()
    return render_template('admin/admin_usuarios.html', usuarios=usuarios)


@app.route('/admin/compras')
def admin_compras():
    if 'admin_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    cursor = conn.cursor()
    # Compras de entradas
    cursor.execute('''SELECT c.id, u.nombre as usuario, p.titulo as pelicula, c.cantidad, c.fecha_compra FROM Compras c JOIN Usuarios u ON c.usuario_id = u.id JOIN Peliculas p ON c.pelicula_id = p.id ORDER BY c.fecha_compra DESC''')
    compras_entradas = cursor.fetchall()
    # Compras de dulcería
    cursor.execute('''SELECT cd.id, u.nombre as usuario, cd.productos, cd.total, cd.fecha_compra FROM ComprasDulceria cd JOIN Usuarios u ON cd.usuario_id = u.id ORDER BY cd.fecha_compra DESC''')
    compras_dulceria = cursor.fetchall()
    # Decodificar productos JSON
    compras_dulceria_list = []
    for d in compras_dulceria:
        d = dict(d)
        try:
            d['productos'] = json.loads(
                d['productos']) if d['productos'] else []
        except Exception:
            d['productos'] = []
        compras_dulceria_list.append(d)
    conn.close()
    return render_template('admin/admin_compras.html', compras_entradas=compras_entradas, compras_dulceria=compras_dulceria_list)


@app.route('/admin/dulceria')
def admin_dulceria():
    if 'admin_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT id, nombre, precio, descripcion, imagen FROM Dulceria ORDER BY id DESC')
    productos = cursor.fetchall()
    conn.close()
    return render_template('admin/admin_dulceria.html', productos=productos)


@app.route('/admin/dulceria/nuevo', methods=['GET', 'POST'])
def admin_dulceria_nuevo():
    if 'admin_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        precio = request.form.get('precio')
        descripcion = request.form.get('descripcion')
        imagen = request.files.get('imagen')
        if not nombre or not precio:
            error = 'El nombre y el precio son obligatorios.'
            return render_template('admin/admin_dulceria_form.html', error=error)
        imagen_filename = None
        if imagen and imagen.filename:
            imagen_filename = secure_filename(imagen.filename)
            imagen.save(os.path.join('static', 'images', imagen_filename))
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO Dulceria (nombre, precio, descripcion, imagen) VALUES (?, ?, ?, ?)',
                       (nombre, precio, descripcion, imagen_filename))
        conn.commit()
        conn.close()
        return redirect(url_for('admin_dulceria'))
    return render_template('admin/admin_dulceria_form.html')


@app.route('/admin/dulceria/editar/<int:producto_id>', methods=['GET', 'POST'])
def admin_dulceria_editar(producto_id):
    if 'admin_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM Dulceria WHERE id = ?', (producto_id,))
    producto = cursor.fetchone()
    if not producto:
        conn.close()
        return redirect(url_for('admin_dulceria'))
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        precio = request.form.get('precio')
        descripcion = request.form.get('descripcion')
        imagen = request.files.get('imagen')
        if not nombre or not precio:
            error = 'El nombre y el precio son obligatorios.'
            return render_template('admin/admin_dulceria_form.html', producto=producto, error=error)
        imagen_filename = producto['imagen']
        if imagen and imagen.filename:
            imagen_filename = secure_filename(imagen.filename)
            imagen.save(os.path.join('static', 'images', imagen_filename))
        cursor.execute('UPDATE Dulceria SET nombre=?, precio=?, descripcion=?, imagen=? WHERE id=?',
                       (nombre, precio, descripcion, imagen_filename, producto_id))
        conn.commit()
        conn.close()
        return redirect(url_for('admin_dulceria'))
    conn.close()
    return render_template('admin/admin_dulceria_form.html', producto=producto)


@app.route('/admin/dulceria/eliminar/<int:producto_id>', methods=['POST'])
def admin_dulceria_eliminar(producto_id):
    if 'admin_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM Dulceria WHERE id = ?', (producto_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_dulceria'))


@app.route('/admin/peliculas/nueva', methods=['GET', 'POST'])
def admin_pelicula_nueva():
    if 'admin_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, nombre FROM Generos ORDER BY nombre')
    generos = cursor.fetchall()
    if request.method == 'POST':
        titulo = request.form.get('titulo')
        descripcion = request.form.get('descripcion')
        duracion = request.form.get('duracion')
        genero_id = request.form.get('genero_id') or None
        hora_funcion = request.form.get('hora_funcion') or None
        imagen = request.files.get('imagen')
        banner_pelicula = request.form.get('banner_pelicula') or None

        if not titulo or not duracion:
            error = 'El título y la duración son obligatorios.'
            return render_template('admin/admin_pelicula_form.html', generos=generos, error=error)

        imagen_filename = None
        if imagen and imagen.filename:
            imagen_filename = secure_filename(imagen.filename)
            imagen.save(os.path.join('static', 'images', imagen_filename))

        cursor.execute('''INSERT INTO Peliculas (titulo, descripcion, duracion, genero_id, hora_funcion, imagen, banner_pelicula) VALUES (?, ?, ?, ?, ?, ?, ?)''',
                       (titulo, descripcion, duracion, genero_id, hora_funcion, imagen_filename, banner_pelicula))
        conn.commit()
        conn.close()
        return redirect(url_for('admin_peliculas'))
    conn.close()
    return render_template('admin/admin_pelicula_form.html', generos=generos)


@app.route('/admin/peliculas/editar/<int:pelicula_id>', methods=['GET', 'POST'])
def admin_pelicula_editar(pelicula_id):
    if 'admin_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, nombre FROM Generos ORDER BY nombre')
    generos = cursor.fetchall()
    cursor.execute('SELECT * FROM Peliculas WHERE id = ?', (pelicula_id,))
    pelicula = cursor.fetchone()
    if not pelicula:
        conn.close()
        return redirect(url_for('admin_peliculas'))
    if request.method == 'POST':
        titulo = request.form.get('titulo')
        descripcion = request.form.get('descripcion')
        duracion = request.form.get('duracion')
        genero_id = request.form.get('genero_id') or None
        hora_funcion = request.form.get('hora_funcion') or None
        imagen = request.files.get('imagen')
        banner_pelicula = request.form.get('banner_pelicula') or None

        if not titulo or not duracion:
            error = 'El título y la duración son obligatorios.'
            return render_template('admin/admin_pelicula_form.html', generos=generos, pelicula=pelicula, error=error)

        imagen_filename = pelicula['imagen']
        if imagen and imagen.filename:
            imagen_filename = secure_filename(imagen.filename)
            imagen.save(os.path.join('static', 'images', imagen_filename))

        cursor.execute('''UPDATE Peliculas SET titulo=?, descripcion=?, duracion=?, genero_id=?, hora_funcion=?, imagen=?, banner_pelicula=? WHERE id=?''',
                       (titulo, descripcion, duracion, genero_id, hora_funcion, imagen_filename, banner_pelicula, pelicula_id))
        conn.commit()
        conn.close()
        return redirect(url_for('admin_peliculas'))
    conn.close()
    return render_template('admin/admin_pelicula_form.html', generos=generos, pelicula=pelicula)


@app.route('/admin/peliculas/eliminar/<int:pelicula_id>', methods=['POST'])
def admin_pelicula_eliminar(pelicula_id):
    if 'admin_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM Peliculas WHERE id = ?', (pelicula_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_peliculas'))


@app.route('/admin/usuarios/eliminar/<int:usuario_id>', methods=['POST'])
def admin_usuario_eliminar(usuario_id):
    if 'admin_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM Usuarios WHERE id = ?', (usuario_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_usuarios'))


if __name__ == '__main__':
    app.run(debug=True)
