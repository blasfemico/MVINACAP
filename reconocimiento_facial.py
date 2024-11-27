import cv2
import face_recognition
import sqlite3

# Cargar rostros registrados desde la base de datos
def cargar_rostros_registrados():
    conexion = sqlite3.connect("database/base_datos.db")
    cursor = conexion.cursor()

    cursor.execute("SELECT nombre, ruta_imagen FROM usuarios")
    usuarios = cursor.fetchall()
    conexion.close()

    known_face_encodings = []
    known_face_names = []

    for nombre, ruta_imagen in usuarios:
        imagen = face_recognition.load_image_file(ruta_imagen)
        encoding = face_recognition.face_encodings(imagen)[0]
        known_face_encodings.append(encoding)
        known_face_names.append(nombre)
    
    return known_face_encodings, known_face_names

# Reconocimiento facial en tiempo real
def reconocimiento_facial():
    known_face_encodings, known_face_names = cargar_rostros_registrados()
    camara = cv2.VideoCapture(0)
    print("Iniciando reconocimiento facial...")

    while True:
        ret, frame = camara.read()
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = small_frame[:, :, ::-1]

        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            name = "Desconocido"

            if True in matches:
                match_index = matches.index(True)
                name = known_face_names[match_index]

            print(f"Rostro detectado: {name}")

            if name != "Desconocido":
                print("Acceso permitido.")
                # Aquí puedes activar la puerta o enviar un comando.
            else:
                print("Acceso denegado.")

        cv2.imshow("Reconocimiento facial", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):  # Salir con 'q'
            break

    camara.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    reconocimiento_facial()
