import os
import time
import re
from datetime import datetime
from typing import List, Generator
import cv2
import easyocr
import requests
from flask import Flask, render_template, Response, request, redirect, url_for, jsonify, flash
from openpyxl import Workbook, load_workbook
import pytesseract

class SistemaGestion:
    def __init__(self):
        self.excel_file = "registro_miembros.xlsx"
        self.upload_folder = "temp/"
        self.esp32_motor_url = "http://192.168.100.49/motor"
        self.camaras = []
        self.latest_frames = []
        self.capturing = []
        self.reader = easyocr.Reader(["en"])
        self.setup()

    
    def setup(self):
        if not os.path.exists(self.upload_folder):
            os.makedirs(self.upload_folder)
        if not os.path.exists(self.excel_file):
            workbook = Workbook()
            sheet = workbook.active
            sheet.append(["Nombre", "RUT", "Foto", "Patente", "Hora Entrada", "Hora Salida", "Vehiculo"])
            workbook.save(self.excel_file)
        pytesseract.pytesseract.tesseract_cmd = (
            "/usr/bin/tesseract" if os.name == "posix" else "C:/Program Files (x86)/Tesseract-OCR/tesseract.exe"
        )
        self.inicializar_camaras()

    def control_motor(self, motor_id):
        response = requests.get(f"{self.esp32_motor_url}/{motor_id}")
        response.raise_for_status()

    def capturar_frame(self, cam_index):
        if cam_index < len(self.camaras) and not self.capturing[cam_index]:
            success, frame = self.camaras[cam_index].read()
            if success:
                self.latest_frames[cam_index] = frame

    
    def video_feed(self, cam_index) -> Generator[bytes, None, None]:
        while True:
            if cam_index < len(self.camaras):
                self.capturar_frame(cam_index)
                if self.latest_frames[cam_index] is not None:
                    _, buffer = cv2.imencode(".jpg", self.latest_frames[cam_index])
                    yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n"
            else:
                yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n"
    
    def inicializar_camaras(self):
        for index in range(3):  
            cam = cv2.VideoCapture(index)
            if cam.isOpened():
                self.camaras.append(cam)
                self.latest_frames.append(None)
                self.capturing.append(False)
                print(f"Cámara {index} inicializada correctamente.")
            else:
                print(f"Advertencia: No se pudo inicializar la cámara {index}. Ignorando...")
        if not self.camaras:
            print("No se encontraron cámaras disponibles.")


    def detectar_matricula(self, imagen):
        img = cv2.imread(imagen)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        matriculas = [cv2.approxPolyDP(c, 0.02 * cv2.arcLength(c, True), True) for c in contours if cv2.contourArea(c) > 10000]
        return [m for m in matriculas if len(m) == 4]

    def guardar_matriculas(self, imagen, matriculas):
        img = cv2.imread(imagen)
        return [
            f"{self.upload_folder}matricula_{i + 1}.jpg" 
            for i, m in enumerate(matriculas)
            if cv2.imwrite(f"{self.upload_folder}matricula_{i + 1}.jpg", img[cv2.boundingRect(m)[1]:cv2.boundingRect(m)[1] + cv2.boundingRect(m)[3], cv2.boundingRect(m)[0]:cv2.boundingRect(m)[0] + cv2.boundingRect(m)[2]])
        ]

    def leer_matricula(self, image_path):
        if not os.path.exists(image_path):
            return ""
        result = self.reader.readtext(cv2.cvtColor(cv2.imread(image_path), cv2.COLOR_BGR2RGB))
        return next((re.sub(r"[^A-Za-z0-9]", "", text) for _, text, prob in result if prob > 0.55), "")

    def registrar_entrada(self, nombre, rut, foto, patente_input, vehiculo):
        foto_filename = os.path.join("fotos/", f"{rut}_foto.jpg")
        foto.save(foto_filename)
        matriculas = self.detectar_matricula(foto_filename)
        if matriculas:
            matricula_procesada = self.leer_matricula(self.guardar_matriculas(foto_filename, matriculas)[0])
            if matricula_procesada == patente_input:
                hora_entrada = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                workbook = load_workbook(self.excel_file)
                sheet = workbook.active
                sheet.append([nombre, rut, foto_filename, matricula_procesada, hora_entrada, None, vehiculo])
                workbook.save(self.excel_file)
                self.control_motor(1)

    def registrar_salida(self, rut):
        workbook = load_workbook(self.excel_file)
        sheet = workbook.active
        for row in sheet.iter_rows(min_row=2):
            if row[1].value == rut and not row[5].value:
                row[5].value = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                workbook.save(self.excel_file)
                self.control_motor(2)
                break

    def sensor_entrada(self):
        self.control_motor(3)

    def sensor_salida(self):
        self.control_motor(4)

    def obtener_registros(self):
        registros = []
        if os.path.exists(self.excel_file):
            workbook = load_workbook(self.excel_file)
            sheet = workbook.active
            for row in sheet.iter_rows(min_row=2, values_only=True):  
                registros.append(row)
        else:
            print("Advertencia: El archivo de registros no existe.")
        return registros
    
app = Flask(__name__)
app.secret_key = os.urandom(24)
sistema = SistemaGestion()

@app.route("/video_feed/<int:cam_index>")
def video_feed(cam_index):
    if cam_index >= len(sistema.camaras):
        return "Cámara no disponible", 404
    return Response(sistema.video_feed(cam_index), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/agregar_miembro", methods=["POST"])
def agregar_miembro():
    nombre = request.form.get("name")
    rut = request.form.get("rut")
    patente_input = request.form.get("patente")
    vehiculo = request.form.get("vehiculo")
    foto = request.files["foto"]
    sistema.registrar_entrada(nombre, rut, foto, patente_input, vehiculo)
    return redirect(url_for("index"))

@app.route("/sensor/entrada")
def sensor_entrada():
    sistema.sensor_entrada()
    return "Sensor de entrada activado"

@app.route("/sensor/salida")
def sensor_salida():
    sistema.sensor_salida()
    return "Sensor de salida activado"

@app.route("/registrar_salida/<rut>")
def registrar_salida(rut):
    sistema.registrar_salida(rut)
    return redirect(url_for("index"))

@app.route("/")
def index():
    registros = sistema.obtener_registros()  
    cantidad_camaras = len(sistema.camaras)  
    print(f"Cantidad de cámaras disponibles: {cantidad_camaras}")
    return render_template("index.html", registros=registros, cantidad_camaras=cantidad_camaras)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
