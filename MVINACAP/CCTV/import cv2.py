import cv2

for index in range(10):  # Prueba con los primeros 10 índices
    cap = cv2.VideoCapture(index)
    if cap.isOpened():
        print(f"Cámara encontrada en el índice: {index}")
        cap.release()
    else:
        print(f"Índice {index} no disponible.")
