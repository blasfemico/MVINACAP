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
import numpy as np 
from pynput import keyboard
from typing import Tuple
import logging
import openpyxl
from CCTV.sistema_gestion import SistemaGestion

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()  
    ]
)


app = Flask(__name__, static_url_path='/CCTV')
app.secret_key = os.urandom(24)
sistema = SistemaGestion()
sistema.registrar_teclado()

@app.route("/video_feed/<int:cam_index>")
def video_feed(cam_index):
    if cam_index >= len(sistema.camaras):
        return "Cámara no disponible", 404
    return Response(sistema.video_feed(cam_index), mimetype="multipart/x-mixed-replace; boundary=frame")

@app.route("/eliminar_miembro/<rut>", methods=["POST"])
def eliminar_miembro(rut):
    workbook = load_workbook(sistema.excel_file)
    sheet = workbook.active
    encontrado = False
    for row in sheet.iter_rows(min_row=2):
        if row[1].value == rut:  
            sheet.delete_rows(row[0].row)
            encontrado = True
            break

    if encontrado:
        workbook.save(sistema.excel_file)
        flash(f"El miembro con RUT {rut} ha sido eliminado exitosamente.")
    else:
        flash(f"No se encontró un miembro con el RUT {rut}.")
    return redirect(url_for("index"))


@app.route("/agregar_miembro", methods=["POST"])
def agregar_miembro():
    nombre = request.form.get("name") 
    rut = request.form.get("rut") 
    patente_input = request.form.get("patente")  
    rol = request.form.get("rol") 
    foto = request.files["foto"]
    
    sistema.agregar_miembro(nombre, rut, foto, patente_input, rol)  
    return redirect(url_for("index"))


@app.route("/registrar_salida/<rut>")
def registrar_salida(rut):
    sistema.registrar_salida(rut)
    return redirect(url_for("index"))

@app.route("/capture/<int:cam_index>")
def capture(cam_index):
    filename = sistema.capturar_imagen(cam_index)
    if filename:
        return jsonify({"message": "Imagen capturada y procesada con éxito", "file": filename}), 200
    return jsonify({"error": "No se pudo capturar la imagen"}), 500

@app.route("/")
def index():
    registros = []
    workbook = load_workbook(sistema.excel_file)
    sheet = workbook.active
    for row in sheet.iter_rows(min_row=2, values_only=True):  
        registros.append(row)

    cantidad_camaras = len(sistema.camaras)
    registros_camaras = [cam is not None for cam in sistema.camaras]
    print(f"Cantidad de cámaras disponibles: {cantidad_camaras}")
    return render_template(
        "index.html",
        registros=registros,
        cantidad_camaras=cantidad_camaras,
        registros_camaras=registros_camaras
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
