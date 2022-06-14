from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QTimer, QDateTime, QCoreApplication, QThread
from PyQt5.QtWidgets import QApplication, QWidget, QMessageBox, QInputDialog


import cv2
import dlib
import imutils
from imutils import face_utils
from imutils.video import VideoStream

from scipy.spatial import distance as dist


from utils.GlobalVar import add_path_to_sys
rootdir = add_path_to_sys()


from utils.GlobalVar import CAMERA_ID



class BlinksDetectThread(QThread):
    trigger = QtCore.pyqtSignal()

    def __init__(self):
        """
        :rtype: object
        """
        super(BlinksDetectThread, self).__init__()

        
        self.shape_predictor_path = f"{rootdir}/model_blink_detection/shape_predictor_68_face_landmarks.dat"
        
        self.EYE_AR_THRESH = 0.20
        self.EYE_AR_CONSEC_FRAMES = 2

        
        self.COUNTER = 0
        self.TOTAL = 0

        
        self.A = 0
        self.B = 0
        self.C = 0
        self.leftEye = 0
        self.rightEye = 0
        self.leftEAR = 0
        self.rightEAR = 0
        self.ear = 0

        
        self.BlinksFlag = 1

    
    def eye_aspect_ratio(self, eye):
        
        self.A = dist.euclidean(eye[1], eye[5])
        self.B = dist.euclidean(eye[2], eye[4])
        
        self.C = dist.euclidean(eye[0], eye[3])
        
        ear = (self.A + self.B) / (2.0 * self.C)
        
        return ear

    def run(self):
        if self.BlinksFlag == 1:
            
            print("[INFO] loading facial landmark predictor...")
            detector = dlib.get_frontal_face_detector()
            predictor = dlib.shape_predictor(self.shape_predictor_path)
            
            (lStart, lEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
            (rStart, rEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]
            while self.BlinksFlag == 1:
                
                vs = VideoStream(src=CAMERA_ID).start()
                frame = vs.read()
                QApplication.processEvents()
                frame = imutils.resize(frame, width=900)
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                rects = detector(gray, 0)
                
                for rect in rects:
                    
                    shape = predictor(gray, rect)
                    shape = face_utils.shape_to_np(shape)
                    
                    self.leftEye = shape[lStart:lEnd]
                    self.rightEye = shape[rStart:rEnd]
                    self.leftEAR = self.eye_aspect_ratio(self.leftEye)
                    self.rightEAR = self.eye_aspect_ratio(self.rightEye)
                    
                    self.ear = (self.leftEAR + self.rightEAR) / 2.0

                    
                    if self.ear < self.EYE_AR_THRESH:
                        self.COUNTER += 1
                    else:
                        
                        if self.COUNTER >= self.EYE_AR_CONSEC_FRAMES:
                            self.TOTAL += 1
                        
                        self.COUNTER = 0

                self.trigger.emit()
                if self.TOTAL == 1:
                    print("[INFO] 活体！眨眼次数为: {}".format(self.TOTAL))
                    print("[INFO] 人眼纵横比：", self.ear)

    
    def terminate(self):
        self.BlinksFlag = 0
        if flag2 == 0:
            VideoStream(src=CAMERA_ID).stop()