import sqlite3
import cv2
import os

KNOWN_FACES_DIR = "rostros_registrados"
os.makedirs(KNOWN_FACES_DIR, exist_ok=True)

def registrar_usuario(nombre):
    # Capturar el rostro
    camara = cv2.VideoCapture(0)
    print(f"Registrando rostro para: {nombre}")
    while True:
        ret, frame = camara.read()
        cv2.imshow("Registrar rostro", frame)
        if cv2.waitKey(1) & 0xFF == ord('s'):  # Capturar imagen con 's'
            ruta_imagen = os.path.join(KNOWN_FACES_DIR, f"{nombre}.jpg")
            cv2.imwrite(ruta_imagen, frame)
            print(f"Rostro guardado en: {ruta_imagen}")
            guardar_en_base_datos(nombre, ruta_imagen)
            break
    camara.release()
    cv2.destroyAllWindows()

# Guardar datos en la base de datos
def guardar_en_base_datos(nombre, ruta_imagen):
    conexion = sqlite3.connect("database/base_datos.db")
    cursor = conexion.cursor()

    cursor.execute("INSERT INTO usuarios (nombre, ruta_imagen) VALUES (?, ?)", (nombre, ruta_imagen))
    conexion.commit()
    conexion.close()
    print(f"Usuario {nombre} registrado correctamente en la base de datos.")

if __name__ == "__main__":
    nombre = input("Ingrese el nombre del usuario: ")
    registrar_usuario(nombre)
