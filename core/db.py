import sqlite3
from datetime import datetime

def get_connection():
    return sqlite3.connect("omnidesk.db")

def init_db():
    """Inicializa las tablas de la base de datos."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Tabla de tickets
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            username TEXT,
            descripcion TEXT NOT NULL,
            categoria TEXT,
            urgencia TEXT,
            estado TEXT DEFAULT 'Abierto',
            fecha TEXT NOT NULL
        )
    ''')
    
    # Tabla de telemetría IoT
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS iot_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            servidor TEXT NOT NULL,
            temperatura REAL NOT NULL,
            alerta BOOLEAN NOT NULL,
            fecha TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ticket_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER NOT NULL,
            sender TEXT NOT NULL,
            contenido TEXT NOT NULL,
            fecha TEXT NOT NULL,
            FOREIGN KEY (ticket_id) REFERENCES tickets(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bot_user_state (
            user_id TEXT PRIMARY KEY,
            requires_start INTEGER NOT NULL DEFAULT 0
        )
    ''')

    # Usuarios cuyo ticket más reciente ya estaba cerrado antes de esta función.
    cursor.execute('''
        INSERT OR IGNORE INTO bot_user_state (user_id, requires_start)
        SELECT t.user_id, 1
        FROM tickets t
        WHERE t.id = (SELECT MAX(t2.id) FROM tickets t2 WHERE t2.user_id = t.user_id)
          AND t.estado = 'Resuelto'
    ''')
    
    conn.commit()
    conn.close()

def crear_ticket(user_id, username, descripcion, categoria, urgencia, estado='Abierto'):
    conn = get_connection()
    cursor = conn.cursor()
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO tickets (user_id, username, descripcion, categoria, urgencia, estado, fecha)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, username, descripcion, categoria, urgencia, estado, fecha_actual))
    conn.commit()
    ticket_id = cursor.lastrowid
    conn.close()
    return ticket_id

def obtener_ticket_activo(user_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT id, estado, descripcion FROM tickets WHERE user_id = ? AND estado IN ('Esperando decisión', 'Esperando detalles', 'Abierto', 'Esperando técnico', 'En atención') ORDER BY id DESC LIMIT 1",
        (str(user_id),)
    ).fetchone()
    conn.close()
    return row

def obtener_historial_tickets(user_id, limite=10):
    """Devuelve los tickets recientes pertenecientes al ID de Telegram indicado."""
    conn = get_connection()
    rows = conn.execute(
        '''SELECT id, descripcion, categoria, urgencia, estado, fecha
           FROM tickets
           WHERE user_id = ?
           ORDER BY id DESC
           LIMIT ?''',
        (str(user_id), limite)
    ).fetchall()
    conn.close()
    return rows

def guardar_mensaje(ticket_id, sender, contenido):
    conn = get_connection()
    conn.execute(
        'INSERT INTO ticket_messages (ticket_id, sender, contenido, fecha) VALUES (?, ?, ?, ?)',
        (ticket_id, sender, contenido, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    conn.commit()
    conn.close()

def actualizar_estado_ticket(ticket_id, estado):
    conn = get_connection()
    conn.execute('UPDATE tickets SET estado = ? WHERE id = ?', (estado, ticket_id))
    conn.commit()
    conn.close()

def actualizar_detalles_ticket(ticket_id, descripcion, categoria, urgencia, estado):
    conn = get_connection()
    conn.execute(
        'UPDATE tickets SET descripcion = ?, categoria = ?, urgencia = ?, estado = ? WHERE id = ?',
        (descripcion, categoria, urgencia, estado, ticket_id)
    )
    conn.commit()
    conn.close()

def actualizar_nombre_tickets_activos(user_id, username):
    conn = get_connection()
    conn.execute(
        "UPDATE tickets SET username = ? WHERE user_id = ? AND estado IN ('Esperando decisión', 'Esperando detalles', 'Abierto', 'Esperando técnico', 'En atención')",
        (username, str(user_id))
    )
    conn.commit()
    conn.close()

def marcar_requiere_start(user_id):
    conn = get_connection()
    conn.execute(
        'INSERT INTO bot_user_state (user_id, requires_start) VALUES (?, 1) '
        'ON CONFLICT(user_id) DO UPDATE SET requires_start = 1',
        (str(user_id),)
    )
    conn.commit()
    conn.close()

def confirmar_inicio_bot(user_id):
    conn = get_connection()
    conn.execute(
        'INSERT INTO bot_user_state (user_id, requires_start) VALUES (?, 0) '
        'ON CONFLICT(user_id) DO UPDATE SET requires_start = 0',
        (str(user_id),)
    )
    conn.commit()
    conn.close()

def usuario_requiere_start(user_id):
    conn = get_connection()
    row = conn.execute(
        'SELECT requires_start FROM bot_user_state WHERE user_id = ?',
        (str(user_id),)
    ).fetchone()
    conn.close()
    return bool(row and row[0])

def registrar_metrica_iot(servidor, temperatura, alerta):
    conn = get_connection()
    cursor = conn.cursor()
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO iot_metrics (servidor, temperatura, alerta, fecha)
        VALUES (?, ?, ?, ?)
    ''', (servidor, temperatura, alerta, fecha_actual))
    conn.commit()
    conn.close()
