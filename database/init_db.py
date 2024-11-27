import sqlite3

# Conexión e inicialización de la base de datos
def inicializar_base_datos():
    conexion = sqlite3.connect("database/base_datos.db")
    cursor = conexion.cursor()

    # Crear tabla de usuarios si no existe
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            ruta_imagen TEXT NOT NULL
        )
    ''')
    conexion.commit()
    conexion.close()
    print("Base de datos inicializada correctamente.")

if __name__ == "__main__":
    inicializar_base_datos()
