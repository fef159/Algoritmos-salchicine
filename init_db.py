import sqlite3


def init_db():
    # Conexión a la base de datos SQLite (se creará si no existe)
    conn = sqlite3.connect('database/salchichon.sqlite')
    c = conn.cursor()

    # Eliminar la tabla Dulcería si ya existe (esto es para evitar el error)
    c.execute('DROP TABLE IF EXISTS Dulceria')

    # Crear las tablas
    c.execute(''' 
    CREATE TABLE IF NOT EXISTS Usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        contraseña TEXT NOT NULL
    );
    ''')

    c.execute(''' 
    CREATE TABLE IF NOT EXISTS Admin (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT NOT NULL UNIQUE,
        contraseña TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE
    );
    ''')

    c.execute(''' 
    CREATE TABLE IF NOT EXISTS Generos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL
    );
    ''')

    c.execute(''' 
    CREATE TABLE IF NOT EXISTS Peliculas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titulo TEXT NOT NULL,
        descripcion TEXT,
        duracion INTEGER NOT NULL,
        genero_id INTEGER,
        hora_funcion TIME,
        imagen TEXT,
        banner_pelicula TEXT,
        FOREIGN KEY (genero_id) REFERENCES Generos(id)
    );
    ''')

    c.execute(''' 
    CREATE TABLE IF NOT EXISTS Salas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        capacidad INTEGER NOT NULL
    );
    ''')

    c.execute(''' 
    CREATE TABLE IF NOT EXISTS Asientos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sala_id INTEGER,
        fila TEXT NOT NULL,
        numero_asiento INTEGER NOT NULL,
        estado TEXT DEFAULT 'disponible',
        FOREIGN KEY (sala_id) REFERENCES Salas(id),
        UNIQUE (sala_id, fila, numero_asiento)
    );
    ''')

    c.execute(''' 
    CREATE TABLE IF NOT EXISTS Compras (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER,
        pelicula_id INTEGER,
        cantidad INTEGER,
        fecha_compra TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (usuario_id) REFERENCES Usuarios(id),
        FOREIGN KEY (pelicula_id) REFERENCES Peliculas(id)
    );
    ''')

    # Crear la tabla Dulcería
    c.execute(''' 
    CREATE TABLE IF NOT EXISTS Dulceria (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        precio REAL NOT NULL,
        descripcion TEXT,
        imagen TEXT  -- Columna para la ruta de la imagen
    );
    ''')

    # Crear la tabla ComprasDulceria para compras de dulcería
    c.execute(''' 
    CREATE TABLE IF NOT EXISTS ComprasDulceria (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER,
        productos TEXT, -- JSON con los productos y cantidades
        total REAL,
        fecha_compra TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        pdf_path TEXT,
        FOREIGN KEY (usuario_id) REFERENCES Usuarios(id)
    );
    ''')

    # Insertar datos de ejemplo para géneros
    c.executemany(''' 
    INSERT INTO Generos (nombre) VALUES (?);
    ''', [('Acción',), ('Comedia',), ('Drama',), ('Terror',)])

    # Insertar datos de ejemplo para películas
    peliculas_data = [
        ('Avengers: Endgame', 'Los Vengadores deben enfrentarse a Thanos para salvar el universo.',
         181, 1, '20:00:00', 'avengers_endgame.jpg', 'banner_1'),
        ('The Hangover', 'Un grupo de amigos intenta recordar lo que ocurrió durante su despedida de soltero en Las Vegas.',
         100, 2, '22:00:00', 'hangover.jpg', 'banner_2'),
        ('The Pursuit of Happyness', 'La historia de un hombre que lucha por salir de la pobreza.',
         117, 3, '18:00:00', 'happyness.jpg', 'banner_3'),
        ('The Conjuring', 'Una pareja de investigadores paranormales enfrenta una entidad maligna.',
         112, 4, '23:00:00', 'conjuring.jpg', 'banner_4'),
        ('Inception', 'Un ladrón especializado en robar secretos a través del sueño es desafiado con una tarea aparentemente imposible.',
         148, 1, '21:00:00', 'inception.jpg', 'banner_5'),
        ('The Shawshank Redemption', 'La historia de un hombre que es injustamente condenado y su lucha por la libertad en prisión.',
         142, 3, '19:00:00', 'shawshank_redemption.jpg', 'banner_6'),
        ('The Dark Knight', 'Batman enfrenta a un criminal psicópata conocido como el Joker, que amenaza con destruir Gotham City.',
         152, 1, '20:30:00', 'dark_knight.jpg', 'banner_7'),
        ('Spider-Man: No Way Home', 'Peter Parker se enfrenta a las consecuencias de su identidad secreta siendo revelada.',
         148, 1, '21:30:00', 'spiderman_no_way_home.jpg', 'banner_8'),
        ('Deadpool', 'Un ex-soldado que se convierte en un anti-héroe tras una transformación en su cuerpo y mente.',
         108, 1, '20:45:00', 'deadpool.jpg', 'banner_9'),
        ('The Hangover Part II', 'Los amigos de Doug intentan recordar lo sucedido en su viaje a Tailandia.',
         102, 2, '23:15:00', 'hangover_part_ii.jpg', 'banner_10'),
        ('Jumanji: Welcome to the Jungle', 'Cuatro adolescentes son transportados a un peligroso videojuego en el que deben completar misiones.',
         119, 2, '20:00:00', 'jumanji_welcome.jpg', 'banner_11'),
        ('The Lion King', 'El joven Simba lucha por reclamar su lugar como rey después de la muerte de su padre.',
         88, 3, '18:30:00', 'lion_king.jpg', 'banner_12'),
        ('It', 'Un grupo de niños enfrenta a un monstruo sobrenatural que se disfraza de payaso.',
         135, 4, '22:15:00', 'it.jpg', 'banner_13'),
        ('Shutter Island', 'Dos detectives investigan la desaparición de una paciente en un hospital psiquiátrico aislado.',
         138, 3, '19:45:00', 'shutter_island.jpg', 'banner_14'),
        ('Guardians of the Galaxy', 'Un grupo de inadaptados se une para salvar la galaxia de una amenaza universal.',
         121, 1, '20:00:00', 'guardians_of_galaxy.jpg', 'banner_15'),
        ('The Exorcist', 'Un sacerdote intenta salvar a una niña poseída por un demonio en un caso de exorcismo real.',
         122, 4, '23:00:00', 'exorcist.jpg', 'banner_16')
    ]

    c.executemany(''' 
    INSERT INTO Peliculas (titulo, descripcion, duracion, genero_id, hora_funcion, imagen, banner_pelicula) VALUES (?, ?, ?, ?, ?, ?, ?);
    ''', peliculas_data)

    # Insertar datos de ejemplo para salas
    c.executemany(''' 
    INSERT INTO Salas (nombre, capacidad) VALUES (?, ?);
    ''', [('Sala 1', 66), ('Sala 2', 66), ('Sala 3', 66)])

    # Insertar productos de ejemplo en Dulcería con imágenes
    c.executemany('''
    INSERT INTO Dulceria (nombre, precio, descripcion, imagen) VALUES (?, ?, ?, ?);
    ''', [
        ('Palomitas Grandes', 15.00,
         'Palomitas grandes con mantequilla', 'palomitas_grandes.jpg'),
        ('Palomitas Medianas', 10.00,
         'Palomitas medianas con mantequilla', 'palomitas_medianas.jpg'),
        ('Refresco', 5.00, 'Refresco en lata o botella', 'refresco.jpg'),
        ('Agua Mineral', 3.00, 'Botella de agua mineral', 'agua_mineral.jpg'),
        ('Crispetas de Caramelo', 8.00,
         'Crispetas dulces cubiertas con caramelo', 'crispetas_caramelo.jpg'),
        ('Nachos con Queso', 12.00,
         'Nachos acompañados con salsa de queso', 'nachos_con_queso.jpg')
    ])

    # Crear un admin por defecto si no existe
    c.execute(
        "SELECT COUNT(*) FROM Admin WHERE usuario = 'admin' OR email = 'admin@admin.com'")
    if c.fetchone()[0] == 0:
        c.execute("""
        INSERT INTO Admin (usuario, contraseña, email)
        VALUES ('admin', 'admin123', 'admin@admin.com')
        """)
    conn.commit()

    # Confirmar los cambios y cerrar la conexión
    conn.commit()
    conn.close()


# --- Script para agregar la columna trailer_url si no existe ---
def add_trailer_column():
    conn = sqlite3.connect('database/salchichon.sqlite')
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(Peliculas)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'trailer_url' not in columns:
        cursor.execute("ALTER TABLE Peliculas ADD COLUMN trailer_url TEXT")
        print("Columna 'trailer_url' agregada correctamente.")
    else:
        print("La columna 'trailer_url' ya existe.")
    conn.commit()
    conn.close()


if __name__ == '__main__':
    init_db()
    print("Base de datos y tablas creadas correctamente.")
    # BLOQUE TEMPORAL PARA VERIFICAR ADMIN
    conn = sqlite3.connect('database/salchichon.sqlite')
    c = conn.cursor()
    c.execute('SELECT * FROM Admin')
    admins = c.fetchall()
    print('Contenido de la tabla Admin:')
    for admin in admins:
        print(admin)
    conn.close()
    # Ejecutar el script para agregar la columna trailer_url
    add_trailer_column()
