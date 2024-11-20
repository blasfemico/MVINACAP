import time
import re
from datetime import datetime
from typing import List, Generator
import os
from flask import (
    Flask,
    render_template,
    Response,
    request,
    redirect,
    url_for,
    jsonify,
    send_from_directory,
    flash,
)
import cv2
import easyocr
import openpyxl
import requests
from openpyxl import load_workbook
import pytesseract


EXCEL_FILE = "registro_miembros.xlsx"
UPLOAD_FOLDER = "temp/"
ESP32_IP = "http://192.168.100.49/motor"
CAP = cv2.VideoCapture(1)
LATEST_FRAME = None
CAPTURING = False

app = Flask(__name__)
app.secret_key = os.urandom(24)

if os.name == "posix":
    pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"
elif os.name == "nt":
    pytesseract.pytesseract.tesseract_cmd = (
        "C:/Program Files (x86)/Tesseract-OCR/tesseract.exe"
    )

try:
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    print(f"Directorio '{UPLOAD_FOLDER}' creado o ya existe.")
except OSError as e:
    print(f"Error al crear el directorio '{UPLOAD_FOLDER}': {e}")

if not os.path.exists(EXCEL_FILE):
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.append(
        ["Nombre", "RUT", "Foto", "Patente", "Hora Entrada", "Hora Salida", "Vehiculo"]
    )
    workbook.save(EXCEL_FILE)


@app.route("/control_motor", methods=["POST"])
def control_motor():
    try:
        response = requests.get(ESP32_IP)
        response.raise_for_status()
        return jsonify({"message": "Motor controlado exitosamente"}), 200
    except requests.exceptions.ConnectionError:
        return (
            jsonify(
                {
                    "error": "No se pudo conectar al ESP32. Verifica la dirección IP y la conexión."
                }
            ),
            503,
        )
    except requests.exceptions.Timeout:
        return (
            jsonify(
                {"error": "La solicitud al ESP32 ha excedido el tiempo de espera."}
            ),
            504,
        )
    except requests.exceptions.RequestException as e:
        return (
            jsonify(
                {"error": f"Ocurrió un error al comunicarse con el ESP32: {str(e)}"}
            ),
            500,
        )


def detectar_matricula(imagen) -> List[str]:
    img = cv2.imread(imagen)
    if img is None:
        print(f"Error: No se pudo abrir la imagen en la ruta especificada: {imagen}")
        return []
    cv2.imwrite("output/image_original.jpg", img)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    cv2.imwrite("output/image_gray.jpg", gray)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    cv2.imwrite("output/image_blurred.jpg", blurred)
    edges = cv2.Canny(blurred, 50, 150)
    cv2.imwrite("output/image_edges.jpg", edges)
    contours, _ = cv2.findContours(
        edges.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    matriculas = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if area > 10000:
            peri = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.02 * peri, True)
            if len(approx) == 4:
                matriculas.append(approx)
                cv2.drawContours(img, [approx], -1, (0, 255, 0), 3)
    cv2.imwrite("output/image_contours.jpg", img)
    return matriculas


def guardar_matriculas(imagen, matriculas) -> List[str]:
    img = cv2.imread(imagen)
    rutas_matriculas = []
    for i, matricula in enumerate(matriculas):
        x, y, w, h = cv2.boundingRect(matricula)
        matricula_recortada = img[y : y + h, x : x + w]
        ruta = f"{UPLOAD_FOLDER}matricula_{i+1}.jpg"
        cv2.imwrite(ruta, matricula_recortada)
        rutas_matriculas.append(ruta)
    return rutas_matriculas


def leer_matricula(image_path) -> str:
    reader = easyocr.Reader(["en"])
    if not os.path.exists(image_path):
        print(f"Error: No se encontró la imagen en la ruta especificada: {image_path}")
        return ""
    image = cv2.imread(image_path)
    if image is None:
        print(
            f"Error: No se pudo abrir la imagen en la ruta especificada: {image_path}"
        )
        return ""
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    result = reader.readtext(image_rgb)
    matricula = ""
    for bbox, text, prob in result:
        print(f"Detectado: {text} con una probabilidad de {prob:.2f}")
        if matricula == "" or prob > 0.55:
            matricula = text
    print(f"Matrícula: {matricula}")
    return matricula


def limpiar_matricula(matricula) -> str:
    matricula_limpia = re.sub(r"[^A-Za-z0-9]", "", matricula)
    return matricula_limpia


def gen_frames() -> Generator[bytes, None, None]:
    global CAP, LATEST_FRAME, CAPTURING
    while True:
        while CAPTURING:
            time.sleep(0.1)

        if not CAP.isOpened():
            print("Reconectando a la cámara...")
            CAP.release()
            CAP.open(URL)

        success, frame = CAP.read()
        if not success:
            print("Error: No se pudo capturar la imagen.")
            time.sleep(2)
            continue

        LATEST_FRAME = frame

        _, buffer = cv2.imencode(".jpg", LATEST_FRAME)
        frame_bytes = buffer.tobytes()
        yield (
            b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
        )


@app.route("/video_feed")
def video_feed() -> Response:
    return Response(gen_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/fotos/<filename>")
def fotos(filename) -> Response:
    return send_from_directory("fotos", filename)


@app.route("/")
def index() -> str:
    workbook = load_workbook(EXCEL_FILE)
    sheet = workbook.active
    registros = []
    for row in sheet.iter_rows(min_row=2, values_only=True):
        registros.append(row)
    return render_template("index.html", registros=registros)


@app.route("/agregar_miembro", methods=["POST"])
def agregar_miembro() -> str:
    nombre = request.form.get("name")
    rut = request.form.get("rut")
    patente_input = request.form.get("patente")
    vehiculo = request.form.get("vehiculo")
    foto = request.files["foto"]
    if nombre and rut and foto and patente_input and vehiculo:
        foto_filename = os.path.join("fotos/", f"{rut}_foto.jpg")
        foto.save(foto_filename)
        matriculas_detectadas = detectar_matricula(foto_filename)
        rutas_matriculas = guardar_matriculas(foto_filename, matriculas_detectadas)

        if rutas_matriculas:
            matricula = leer_matricula(rutas_matriculas[0])
            matricula_procesada = limpiar_matricula(matricula)
            if matricula_procesada == patente_input:
                hora_entrada = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                workbook = load_workbook(EXCEL_FILE)
                sheet = workbook.active
                sheet.append(
                    [
                        nombre,
                        rut,
                        foto_filename,
                        matricula_procesada,
                        hora_entrada,
                        None,
                        vehiculo,
                    ]
                )
                workbook.save(EXCEL_FILE)
                control_motor()
                print("Comando 'GIRO' enviado al Arduino.")
                flash("Datos agregados correctamente.", "success")
                return redirect(url_for("index"))
            else:
                flash("La matrícula detectada no coincide con la ingresada.", "error")
                return redirect(url_for("index"))
        else:
            flash("No se detectó ninguna matrícula en la imagen.", "error")
            return redirect(url_for("index"))
    else:
        if os.path.exists(foto_filename):
            os.remove(foto_filename)
            print(f"Archivo '{foto_filename}' eliminado.")
        else:
            print(f"El archivo '{foto_filename}' no existe.")
        flash("Faltan datos, por favor complete todos los campos.", "error")
        return redirect(url_for("index"))


@app.route("/editar_miembro/<rut>", methods=["GET", "POST"])
def editar_miembro(rut) -> str:
    print(f"Editando miembro con RUT: {rut}")
    workbook = load_workbook(EXCEL_FILE)
    sheet = workbook.active
    if request.method == "POST":
        nombre = request.form.get("name")
        patente = request.form.get("patente")
        vehiculo = request.form.get("vehiculo")
        print(
            f"Datos recibidos: nombre={nombre}, patente={patente}, vehiculo={vehiculo}"
        )
        for row in sheet.iter_rows(min_row=2):
            if row[1].value == rut:
                print(f"Modificando el miembro: {row[0].value} con RUT {rut}")
                row[0].value = nombre
                row[3].value = patente
                row[6].value = vehiculo
                workbook.save(EXCEL_FILE)
                return redirect(url_for("index"))
    else:
        miembro = None
        for row in sheet.iter_rows(min_row=2, values_only=True):
            if row[1] == rut:
                miembro = row
                break
        if miembro is None:
            print(f"No se encontró miembro con RUT: {rut}")
        return render_template("editar_miembro.html", miembro=miembro)


@app.route("/eliminar_miembro/<rut>", methods=["GET"])
def eliminar_miembro(rut) -> str:
    workbook = load_workbook(EXCEL_FILE)
    sheet = workbook.active
    ruta = f"fotos/{rut}_foto.jpg"
    for row in sheet.iter_rows(min_row=2):
        if row[1].value == rut:
            sheet.delete_rows(row[0].row)
            workbook.save(EXCEL_FILE)
            break
    if os.path.exists(ruta):
        os.remove(ruta)
        print(f"Archivo {ruta} eliminado.")
    else:
        print(f"El archivo {ruta} no existe.")
    return redirect(url_for("index"))


@app.route("/capture")
def capture() -> str:
    global CAPTURING, LATEST_FRAME
    CAPTURING = True
    time.sleep(1)
    if LATEST_FRAME is not None:
        cv2.imwrite(f"{UPLOAD_FOLDER}captura.jpg", LATEST_FRAME)
        print("Imagen capturada.")
    CAPTURING = False
    return "Imagen capturada."


@app.route("/close_camera")
def close_camera() -> str:
    CAP.release()
    print("Cámara cerrada.")
    return "Cámara cerrada."


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
