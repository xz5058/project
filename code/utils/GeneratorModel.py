from imutils import paths
import numpy as np
import imutils
import pickle
import cv2
import os
import sys
from sklearn.preprocessing import LabelEncoder
from sklearn.svm import SVC


from utils.GlobalVar import add_path_to_sys
rootdir = add_path_to_sys()


def Generator():
    
    global embedder
    face_data = f"{rootdir}/face_dataset"
    
    embeddings = f"{rootdir}/saved_weights/embeddings.pickle"
    
    detector_path = f"{rootdir}/model_face_detection/"

    embedding_model = f"{rootdir}/model_facenet/openface_nn4.small2.v1.t7"
    
    default_confidence = 0.5

    
    print("[INFO] loading face detector...")
    proto_path = os.path.sep.join([detector_path, "deploy.prototxt"])
    model_path = os.path.sep.join([detector_path, "res10_300x300_ssd_iter_140000.caffemodel"])
    detector = cv2.dnn.readNetFromCaffe(proto_path, model_path)

    try:
        
        print("[INFO] loading face recognizer...")
        embedder = cv2.dnn.readNetFromTorch(embedding_model)
    except IOError:
        print("[ERROR] Please check filepath!")

    
    print("[INFO] quantifying faces...")
    image_paths = list(paths.list_images(face_data))

    
    known_embeddings = []
    known_names = []

    
    total = 0

    for (i, imagePath) in enumerate(image_paths):
        
        print("[INFO] processing image {}/{}".format(i + 1, len(image_paths)))
        name = imagePath.split(os.path.sep)[-2]

        
        image = cv2.imread(imagePath)
        image = imutils.resize(image, width=600)
        (h, w) = image.shape[:2]

        
        image_blob = cv2.dnn.blobFromImage(
            cv2.resize(image, (300, 300)), 1.0, (300, 300),
            (104.0, 177.0, 123.0), swapRB=False, crop=False)

        
        detector.setInput(image_blob)
        detections = detector.forward()

        
        if len(detections) > 0:
            
            i = np.argmax(detections[0, 0, :, 2])
            confidence = detections[0, 0, i, 2]

            
            if confidence > default_confidence:
                
                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                (startX, startY, endX, endY) = box.astype("int")

                
                face = image[startY:endY, startX:endX]
                (fH, fW) = face.shape[:2]

                
                if fW < 20 or fH < 20:
                    continue

                
                face_blob = cv2.dnn.blobFromImage(face, 1.0 / 255,
                                                  (96, 96), (0, 0, 0), swapRB=True, crop=False)
                embedder.setInput(face_blob)
                vec = embedder.forward()

                
                known_names.append(name)
                known_embeddings.append(vec.flatten())
                total += 1

    
    print("[INFO] serializing {} encodings...".format(total))
    data = {"embeddings": known_embeddings, "names": known_names}
    f = open(embeddings, "wb")
    f.write(pickle.dumps(data))
    f.close()


def TrainModel():
    
    embeddings_path = f"{rootdir}/saved_weights/embeddings.pickle"
   
    recognizer_path = f"{rootdir}/saved_weights/recognizer.pickle"
    
    le_path = f"{rootdir}/saved_weights/le.pickle"

    
    print("[INFO] loading face embeddings...")
    data = pickle.loads(open(embeddings_path, "rb").read())

   
    print("[INFO] encoding labels...")
    le = LabelEncoder()
    labels = le.fit_transform(data["names"])

    
    print("[INFO] training model...")
    recognizer = SVC(C=1.0, kernel="linear", probability=True)
    recognizer.fit(data["embeddings"], labels)

    
    f = open(recognizer_path, "wb")
    f.write(pickle.dumps(recognizer))
    f.close()

   
    f = open(le_path, "wb")
    f.write(pickle.dumps(le))
    f.close()
