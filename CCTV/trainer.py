import cv2
import numpy as np
from PIL import Image
import os
path = 'datasets'
recognizer = cv2.face.LBPHFaceRecognizer_create()
detector = cv2.CascadeClassifier("CCTV/Cascades/haarcascade_frontalface_default.xml");


# function to get the images and label data
def getImagesAndLabels(path):
    folder_paths = [os.path.join(path,folder) for folder in os.listdir(path)]
    imagePaths = []
    for image_path in folder_paths:
        imagePaths.append([os.path.join(path,os.path.basename(image).split('_foto')[0].replace('.',''), image) for image in os.listdir(image_path)])

    face_Samples=[]
    ids = []
    for folder in imagePaths:
        for c, imagePath in enumerate(folder):
            PIL_img = Image.open(imagePath).convert('L') # grayscale
            img_numpy = np.array(PIL_img,'uint8')
            #img_numpy = cv2.resize(img_numpy, (100, 100))
            id = int(os.path.basename(imagePath).split('_foto')[0].replace('.', '').replace('-', ''))
            #id = c
            print(id)
            faces = detector.detectMultiScale(img_numpy)
            for (x,y,w,h) in faces:
                #rint(x,y,w,h)
                face_Samples.append(img_numpy[y:y+h,x:x+w])
                ids.append(id)
        
    return face_Samples,ids

