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
    
    conn.commit()
    conn.close()

def crear_ticket(user_id, username, descripcion, categoria, urgencia):
    conn = get_connection()
    cursor = conn.cursor()
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO tickets (user_id, username, descripcion, categoria, urgencia, estado, fecha)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, username, descripcion, categoria, urgencia, 'Abierto', fecha_actual))
    conn.commit()
    ticket_id = cursor.lastrowid
    conn.close()
    return ticket_id

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