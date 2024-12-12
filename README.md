# Documentación del Proyecto MVINACAP

## Introducción
Este proyecto integra procesamiento de imágenes, reconocimiento facial, escaneo de códigos QR, OCR (Reconocimiento Óptico de Caracteres) y una aplicación web construida con Flask. Su principal objetivo es automatizar el control de entrada y salida de vehículos, además de gestionar información de miembros.

El sistema incluye:
- Detección y reconocimiento facial.
- Verificación de matrículas y códigos QR.
- Activación automática de motores de entrada/salida según validaciones exitosas.
- Gestión de datos mediante una interfaz web y archivos Excel.

## Requisitos

1. **Sistema operativo**: Linux, Windows o macOS.
2. **Python**: Versión 3.8 o superior.
3. **Dependencias**: Listadas en `requirements.txt`.
4. **Software adicional**:
   - `Tesseract OCR` (debe estar instalado y configurado).
   - `ZBar` (para escaneo de códigos QR).

### Instalación de ZBar

#### En sistemas Linux (Ubuntu/Debian):
```bash
sudo apt-get update
sudo apt-get install libzbar0
```

#### En macOS:
```bash
brew install zbar
```

#### En Windows:
1. Descargue ZBar desde [ZBar project](http://zbar.sourceforge.net/download.html).
2. Asegúrese de que el archivo descargado esté accesible desde las variables de entorno del sistema.

## Instalación

### Paso 1: Clonar el repositorio
Extraiga los archivos del proyecto o clone el repositorio en su entorno local.

### Paso 2: Crear un entorno virtual
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### Paso 3: Instalar dependencias
```bash
pip install -r requirements.txt
```

### Paso 4: Configurar Tesseract OCR
Asegúrese de que `Tesseract` esté instalado y su ruta configurada en el sistema. Puede descargarlo desde:
[Tesseract OCR](https://github.com/tesseract-ocr/tesseract)

### Paso 5: Revisar configuraciones
- Verifique que los directorios mencionados en el código, como `CCTV/fotos`, existen y contienen los datos necesarios.
- Configure el archivo Excel `registro_miembros.xlsx` según las necesidades iniciales del sistema.

## Estructura del Proyecto

- **main.py**: Archivo principal del programa.
- **CCTV/**: Contiene scripts relacionados con el reconocimiento facial y procesamiento de imágenes.
- **registro_miembros.xlsx**: Archivo Excel para la gestión de datos de miembros.
- **templates/**: Archivos HTML para la interfaz web.
- **requirements.txt**: Lista de dependencias necesarias.

## Uso

### 1. Iniciar el servidor Flask
Ejecute el siguiente comando:
```bash
python main.py
```

El servidor se ejecutará en `http://127.0.0.1:5000/` por defecto.

### 2. Rutas Principales

- **`/`**: Página principal del sistema.
- **`/registrar`**: Registro de nuevos miembros, incluyendo vehículos, matrículas y datos personales.
- **`/reconocer`**: Verificación de matrícula, rostro y código QR para activar el motor.
- **`/ocr`**: Subir una imagen para extraer texto mediante OCR.
- **`/descargar_excel`**: Descarga del archivo Excel con los datos registrados.

### 3. Probar funcionalidades

#### Reconocimiento facial y códigos QR
1. Acceda a la ruta `/reconocer` desde el navegador.
2. Coloque el rostro frente a la cámara o muestre un código QR.
3. Verifique en pantalla que la detección se realice correctamente:
   - Si se detecta rostro, código QR y matrícula que coincidan con los datos registrados, el motor se activará y se mostrará un mensaje de éxito.

#### Registro de datos
1. Acceda a la ruta `/registrar`.
2. Complete el formulario con:
   - Nombre completo del propietario.
   - RUT.
   - Matrícula del vehículo.
   - Datos adicionales requeridos.
3. Guarde la información.
4. Verifique que los datos se reflejan en el archivo Excel descargable desde `/descargar_excel` y en la interfaz web.

#### Captura de matrículas
1. En la interfaz principal, seleccione el botón **"Capturar Frame"**.
2. Espere a que el sistema guarde la matrícula detectada en la base de datos.
3. Verifique que la matrícula esté registrada correctamente en la lista de vehículos.

#### OCR
1. Suba una imagen con texto legible desde la ruta `/ocr`.
2. Verifique que el texto extraído sea correcto y se muestre en la interfaz.

## Pruebas

### Paso 1: Verificar dependencias
Ejecute:
```bash
python -m pip check
```
Asegúrese de que no haya conflictos en las dependencias.

### Paso 2: Probar entrenamiento de reconocimiento facial
Ejecute:
```python
train(cv2.face.LBPHFaceRecognizer_create())
```
Confirme que se crea el archivo `trainer.yml` y que los rostros registrados se reconocen correctamente en `/reconocer`.

### Paso 3: Validar flujo completo de entrada
1. Registre un miembro en `/registrar`.
2. Capture un frame de la matrícula y guarde la información.
3. Verifique que el motor se active en `/reconocer` cuando los datos coincidan.

### Paso 4: Probar exportación de datos
1. Acceda a la ruta `/descargar_excel`.
2. Asegúrese de que el archivo descargado contiene los datos registrados correctamente.

## Notas finales
- Asegúrese de manejar adecuadamente los errores y excepciones.
- Actualice el archivo `requirements.txt` si se agregan nuevas dependencias.
- Mantenga respaldos de los datos de `registro_miembros.xlsx` para evitar pérdidas.

Este documento puede ser ampliado según nuevas funcionalidades o necesidades.


