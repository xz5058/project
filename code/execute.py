import os
import pickle
import sys
import threading
from datetime import datetime
from copy import deepcopy
import cv2
import imutils
import numpy as np

import pymysql

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QTimer, QDateTime, QCoreApplication, QThread
from PyQt5.QtGui import QImage, QIcon, QPixmap
from PyQt5.QtWidgets import QApplication, QWidget, QMessageBox, QInputDialog

from imutils import face_utils
from imutils.video import VideoStream

from scipy.spatial import distance as dist


from ui import mainwindow as MainWindowUI


from utils import PutChineseText

from utils import GeneratorModel

from utils.BlinksDetectionThread import BlinksDetectThread

from utils.InfoDialog import InfoDialog

from utils.RandomCheck import RCDialog

from utils.GlobalVar import connect_to_sql


from utils.AttendanceCheck import attendance_check
from utils.GlobalVar import FR_LOOP_NUM, statical_facedata_nums


# import importlib
# importlib.reload(GeneratorModel)

import sys
import os


sys.path.append(os.getcwd())


from utils.GlobalVar import CAMERA_ID


class MainWindow(QtWidgets.QMainWindow):
   
    def __init__(self):
        
        super().__init__()
        # self.ui = MainUI.Ui_Form()
        self.ui = MainWindowUI.Ui_MainWindow()
        self.ui.setupUi(self)

        
        self.bkg_pixmap = QPixmap('./logo_imgs/bkg1.png')
        
        self.logo = QIcon('./logo_imgs/fcb_logo.jpg')
        
        self.info_icon = QIcon('./logo_imgs/info_icon.jpg')
        
        self.detector_path = "./model_face_detection"
        
        self.embedding_model = "./model_facenet/openface_nn4.small2.v1.t7"
       
        self.recognizer_path = "./saved_weights/recognizer.pickle"
        
        self.le_path = "./saved_weights/le.pickle"

        
        self.setWindowTitle('Face System')
        self.setWindowIcon(self.logo)
        
        self.ui.label_camera.setPixmap(self.bkg_pixmap)
       
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.show_time_text)
      
        self.timer.start()

      
        self.url = 1
        self.cap = cv2.VideoCapture()
        # self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 500)
        # self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 400)
        # self.cap.set(cv2.CAP_PROP_FPS, 20)

        
        self.ui.bt_open_camera.clicked.connect(self.open_camera)
        
        self.ui.bt_start_check.clicked.connect(self.auto_control)
       
        self.ui.bt_blinks.clicked.connect(self.blinks_thread)
     
        self.ui.bt_exit.clicked.connect(self.quit_window)
        
        self.ui.bt_gathering.clicked.connect(self.open_info_dialog)
        
        self.switch_bt = 0

        
        self.record_name = []
        
        self.ui.bt_generator.clicked.connect(self.train_model)
        
        self.ui.bt_check.clicked.connect(self.check_nums)
       
        self.ui.bt_leave.clicked.connect(self.leave_button)
        
        self.ui.bt_supplement.clicked.connect(self.supplyment_button)
        
        self.ui.lineEdit_leave.setClearButtonEnabled(True)
        self.ui.lineEdit_supplement.setClearButtonEnabled(True)
        
        self.ui.bt_view.clicked.connect(self.show_late_absence)
       
        self.ui.bt_check_variation.clicked.connect(self.check_variation_db)

        
        self.check_time_set = '08:00:00'

        
        self.ui.spinBox_time_hour.setRange(0, 23)
        self.ui.spinBox_time_minute.setRange(0, 59)

    
    def show_time_text(self):
        
        self.ui.label_time.setFixedWidth(200)
       
        self.ui.label_time.setStyleSheet(
           
            "QLabel{color:rgb(0, 0, 0); font-size:14px; font-weight:bold; font-family:宋体;}"
            "QLabel{font-size:14px; font-weight:bold; font-family:宋体;}")

        current_datetime = QDateTime.currentDateTime().toString()
        self.ui.label_time.setText("" + current_datetime)

        
        self.ui.label_title.setFixedWidth(400)
        self.ui.label_title.setStyleSheet("QLabel{font-size:26px; font-weight:bold; font-family:宋体;}")
        self.ui.label_title.setText("Face Recognition Attendance System")

    def open_camera(self):
        
        if not self.cap.isOpened():
            self.ui.label_logo.clear()
            
            self.cap.open(self.url)
            self.show_camera()
        else:
            self.cap.release()
            self.ui.label_logo.clear()
            self.ui.label_camera.clear()
            self.ui.bt_open_camera.setText(u'open camera')

    
    def auto_control(self):
        self.check_time_set = self.format_check_time_set()
        if self.check_time_set == '':
            QMessageBox.warning(self, "Warning", "please set time(eg 08:00)！", QMessageBox.Ok)
        else:
            if self.cap.isOpened():
                if self.switch_bt == 0:
                    self.switch_bt = 1
                    QMessageBox.information(self, "Tips", f"the time is{self.check_time_set}", QMessageBox.Ok)
                    self.ui.bt_start_check.setText(u'exit')
                    self.show_camera()
                elif self.switch_bt == 1:
                    self.switch_bt = 0
                    self.ui.bt_start_check.setText(u'begain')
                    self.show_camera()
                else:
                    print("[Error] The value of self.switch_bt must be zero or one!")
            else:
                QMessageBox.information(self, "Tips", "please open camera first", QMessageBox.Ok)

    def blinks_thread(self):
        bt_text = self.ui.bt_blinks.text()
        if self.cap.isOpened():
            if bt_text == 'live dect':
                
                self.startThread = BlinksDetectThread()
                self.startThread.start()  
                self.ui.bt_blinks.setText('stop')
            else:
                self.ui.bt_blinks.setText('live dect')
                
        else:
            QMessageBox.information(self, "Tips", "please open camera", QMessageBox.Ok)

    def show_camera(self):
        
        global embedded, le, recognizer
        if self.switch_bt == 0:
            self.ui.label_logo.clear()
            self.ui.bt_open_camera.setText(u'close camera')
            while self.cap.isOpened():
                
                ret, self.image = self.cap.read()
                
                QApplication.processEvents()
                
                show = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)  
                
                self.showImage = QImage(show.data, show.shape[1], show.shape[0], QImage.Format_RGB888)
                self.ui.label_camera.setPixmap(QPixmap.fromImage(self.showImage))
            
            self.ui.label_camera.clear()
            self.ui.bt_open_camera.setText(u'open camera')
            
            self.ui.label_camera.setPixmap(self.bkg_pixmap)

        elif self.switch_bt == 1:
            self.ui.label_logo.clear()
            self.ui.bt_start_check.setText(u'exit')

            
            confidence_default = 0.5
            
            proto_path = os.path.sep.join([self.detector_path, "deploy.prototxt"])
            model_path = os.path.sep.join([self.detector_path, "res10_300x300_ssd_iter_140000.caffemodel"])
            detector = cv2.dnn.readNetFromCaffe(proto_path, model_path)
            
            try:
                self.ui.textBrowser_log.append("[INFO] loading face recognizer...")
                
                embedded = cv2.dnn.readNetFromTorch(self.embedding_model)
            except FileNotFoundError as e:
                self.ui.textBrowser_log.append("path is not correct", e)

            
            try:
                recognizer = pickle.loads(open(self.recognizer_path, "rb").read())
                le = pickle.loads(open(self.le_path, "rb").read())
            except FileNotFoundError as e:
                self.ui.textBrowser_log.append("model path error", e)

            
            self.face_name_dict = dict(zip(le.classes_, len(le.classes_) * [0]))
            
            loop_num = 0
            
            while self.cap.isOpened():
                loop_num += 1
               
                ret, frame = self.cap.read()
                QApplication.processEvents()
                if ret:
                  
                    frame = imutils.resize(frame, width=900)
                    (h, w) = frame.shape[:2]
                    
                    image_blob = cv2.dnn.blobFromImage(
                        cv2.resize(frame, (300, 300)), 1.0, (300, 300),
                        (104.0, 177.0, 123.0), swapRB=False, crop=False)
                   
                    detector.setInput(image_blob)
                    
                    detections = detector.forward()

                   
                    face_names = []

                    
                    for i in np.arange(0, detections.shape[2]):
                        
                        confidence = detections[0, 0, i, 2]

                        
                        if not self.cap.isOpened():
                            self.ui.bt_open_camera.setText(u'open camera')
                        else:
                            self.ui.bt_open_camera.setText(u'close camera')

                        
                        if confidence > confidence_default:
                            
                            box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                            (startX, startY, endX, endY) = box.astype("int")

                            
                            face = frame[startY:endY, startX:endX]
                            (fH, fW) = face.shape[:2]

                            
                            if fW < 100 or fH < 100:
                                continue

                            
                            face_blob = cv2.dnn.blobFromImage(face, 1.0 / 255,
                                                              (96, 96), 
                                                              (0, 0, 0), swapRB=True, crop=False)
                            
                            embedded.setInput(face_blob)
                            
                            vec = embedded.forward()
                            
                            prediction = recognizer.predict_proba(vec)[0]
                           
                            j = np.argmax(prediction)
                            
                            probability = prediction[j]
                            
                            name = le.classes_[j]

                            
                            self.face_name_dict[name] += 1

                           
                            text = "{}: {:.2f}%".format(name, probability * 100)
                            
                            print("name",name)
                            y = startY - 10 if startY - 10 > 10 else startY + 10
                            cv2.rectangle(frame, (startX, startY), (endX, endY), (0, 0, 255), 2)
                            frame = cv2.putText(frame, text, (startX, y), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255),
                                                2)
                            face_names.append(name)

                    bt_liveness = self.ui.bt_blinks.text()
                    if bt_liveness == 'stop':
                        ChineseText = PutChineseText.put_chinese_text('./utils/microsoft.ttf')
                        frame = ChineseText.draw_text(frame, (330, 80), ' blink ', 25, (55, 255, 55))

                    
                    show_video = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  
                   
                    # QImage(uchar * data, int width, int height, int bytesPerLine, Format format)
                    self.showImage = QImage(show_video.data, show_video.shape[1], show_video.shape[0],
                                            QImage.Format_RGB888)
                    self.ui.label_camera.setPixmap(QPixmap.fromImage(self.showImage))

                    if loop_num == FR_LOOP_NUM:
                        print(self.face_name_dict)
                        print(face_names)
                        
                        most_id_in_dict = \
                            sorted(self.face_name_dict.items(), key=lambda kv: (kv[1], kv[0]), reverse=True)[0][0]
                        
                        self.set_name = set()
                        self.set_name.add(most_id_in_dict)
                        # self.set_name = set(face_names)
                        self.set_names = tuple(self.set_name)
                        print("11",self.set_name, self.set_names)

                        self.record_names()
                        self.face_name_dict = dict(zip(le.classes_, len(le.classes_) * [0]))
                        
                        loop_num = 0
                    else:
                        pass
                else:
                    self.cap.release()

            
            self.ui.label_camera.clear()

    def record_names(self):
        
        if self.set_name.issubset(self.record_name):
            pass  
        else:
            
            self.different_name = self.set_name.difference(self.record_name)
            
            self.record_name = self.set_name.union(self.record_name)
            
            self.write_data = tuple(self.different_name)
            names_num = len(self.write_data)
            
            self.ui.lcd_2.display(len(self.record_name))

            if names_num > 0:
               
                self.line_text_info = []
                try:
                    
                    db, cursor = connect_to_sql()
                except ConnectionError as e:
                    print("[Error] mysql errror")
                else:
                    
                    current_time = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    results2 = self.use_id_get_info(self.write_data[0])

                    
                    self.now = datetime.now()
                    self.attendance_state = attendance_check(self.check_time_set)
                    self.line_text_info.append((results2[0], results2[1], results2[2],
                                                current_time,
                                                self.attendance_state))
                    print(self.line_text_info)

               
                try:
                    
                    insert_sql2 = "replace into checkin(Name, ID, Class, Time, Description) values(%s, %s, %s, %s, %s)"
                    users2 = self.line_text_info
                    cursor.executemany(insert_sql2, users2)
                except ConnectionAbortedError as e:
                    self.ui.textBrowser_log.append("[INFO] SQL execute failed!")
                else:
                    self.ui.textBrowser_log.append("[INFO] SQL execute success!")
                    
                finally:
                    
                    db.commit()
                    cursor.close()
                    db.close()

    
    def check_nums(self):
        
        global db
        input_class = self.ui.comboBox_class.currentText()
        
        if input_class != '':
            try:
                
                db, cursor = connect_to_sql()
            except ValueError:
                self.ui.textBrowser_log.append("[ERROR] mysql error 1")
            else:
                self.ui.textBrowser_log.append("[INFO] mysql conectiing...")
                
                sql = "select * from studentnums where class = {}".format(input_class)
                cursor.execute(sql)
                
                results = cursor.fetchall()
                self.nums = []
                for i in results:
                    self.nums.append(i[1])

                
                sql2 = "select * from checkin where class = {}".format(input_class)
                cursor.execute(sql2)

                
                results2 = cursor.fetchall()
                self.ui.textBrowser_log.append("[INFO] query ok")

               
                self.check_time_set = self.format_check_time_set()

                if self.check_time_set != '':
                    

                    have_checked_id = self.process_check_log(results2)
                    self.nums2 = len(np.unique(have_checked_id))
                    # print(self.nums2)

                else:
                    QMessageBox.warning(self, "Warning", "please set time (eg 08:00)！", QMessageBox.Ok)

            finally:
                
                self.ui.lcd_1.display(self.nums[0])
                self.ui.lcd_2.display(self.nums2)
                
                db.close()

    
    def format_check_time_set(self):
        
       
        now = datetime.now()
        
        judg_time = now
        now_y = judg_time.year
        now_m = judg_time.month
        now_d = judg_time.day

        original_hour = str(self.ui.spinBox_time_hour.text())
        original_minute = str(self.ui.spinBox_time_minute.text())
        condition_hour = int(self.ui.spinBox_time_hour.text())
        condition_minute = int(self.ui.spinBox_time_minute.text())

        if condition_hour < 10 and condition_minute < 10:
            check_time_set = "0" + original_hour + ":" + "0" + original_minute + ":" + "00"
        elif condition_hour < 10 and condition_minute >= 10:
            check_time_set = "0" + original_hour + ":" + original_minute + ":" + "00"
        elif condition_hour >= 10 and condition_minute < 10:
            check_time_set = original_hour + ":" + "0" + original_minute + ":" + "00"
        elif condition_hour >= 10 and condition_minute >= 10:
            check_time_set = original_hour + ":" + original_minute + ":" + "00"
        else:
            check_time_set = "08:00:00"

        
        att_time = datetime.strptime(f'{now_y}-{now_m}-{now_d} {check_time_set}', '%Y-%m-%d %H:%M:%S')

        return att_time

    
    def process_check_log(self, results):
        
        have_checked_id = []
        for item in results:
            
            if (abs((item[3] - self.check_time_set).seconds) < 60 * 60) or (item[3] - self.check_time_set).seconds > 0:
                have_checked_id.append(int(item[1]))
        return have_checked_id

    
    def leave_button(self):
        self.leave_students(1)

    def supplyment_button(self):
        self.leave_students(2)

    def leave_students(self, button):
        global results
        self.lineTextInfo = []
        
        if self.ui.lineEdit_leave.isModified() or self.ui.lineEdit_supplement.isModified():
            
            db, cursor = connect_to_sql()
            
            currentTime = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            if button == 1:
                self.ui.textBrowser_log.append("[INFO] om...")
                self.description = "qingjia"
                self.lineText_leave_id = self.ui.lineEdit_leave.text()
                results = self.use_id_get_info(self.lineText_leave_id)
            elif button == 2:
                self.ui.textBrowser_log.append("[INFO] ok1...")
                self.description = "dd"
                self.lineText_leave_id = self.ui.lineEdit_supplement.text()
                results = self.use_id_get_info(self.lineText_leave_id)
            else:
                print("[Error] The value of button must be one or two!")

            if len(results) != 0:
                try:
                    self.ui.textBrowser_log.append("[INFO] mysql get...")
                    print(results[0], results[1], results[2], currentTime, self.description)
                except ConnectionAbortedError as e:
                    self.ui.textBrowser_log.append("[INFO] mysql error", e)
                
                try:
                    
                    insert_sql = "replace into checkin(Name, ID, Class, Time, Description) values(%s, %s, %s, %s, %s)"
                    users = self.lineTextInfo
                    cursor.executemany(insert_sql, users)
                except ValueError as e:
                    self.ui.textBrowser_log.append("[INFO] mysql write error", e)
                else:
                    self.ui.textBrowser_log.append("[INFO] mysql ok")
                    QMessageBox.warning(self, "Warning", "{} {}oko".format(self.lineText_leave_id,
                                                                                    self.description), QMessageBox.Ok)
                finally:
                   
                    db.commit()
                    cursor.close()
                    db.close()
            else:
                QMessageBox.critical(self, "Error", f"input id {self.lineText_leave_id} not exit")
        else:
            QMessageBox.critical(self, "Error", "not empty", QMessageBox.Ok)  # (QMessageBox.Yes | QMessageBox.No)
       
        self.ui.lineEdit_leave.clear()
        self.ui.lineEdit_supplement.clear()

    
    def set_rest_absenteeism(self):
        pass

    
    def check_variation_db(self):
        try:
            db, cursor = connect_to_sql()
        except ConnectionAbortedError as e:
            self.ui.textBrowser_log.append('[INFO] mysql error')
        else:
            sql = "select id, name from students"
            
            cursor.execute(sql)
            results = cursor.fetchall()
            self.student_ids = []
            self.student_names = []
            for item in results:
                self.student_ids.append(item[0])
                self.student_names.append(item[1])
            
            # self.random_check_names = deepcopy(self.student_names)
            # self.random_check_ids = deepcopy(self.student_ids)
            print('[INFO] include', self.student_ids, self.student_names)
            
            num_dict = statical_facedata_nums()
            # ID
            self.keys = []
            for key in list(num_dict.keys()):
                self.keys.append(int(key))
            # print(set(self.student_ids))
            # print(set(self.keys))
            self.check_variation_set_operate()
        finally:
            db.commit()
            cursor.close()
            db.close()

    def check_variation_set_operate(self):
       
        union_set = set(self.student_ids).union(set(self.keys))
        
        inter_set = set(self.student_ids).intersection(set(self.keys))
        
        two_diff_set = set(self.student_ids).difference(set(self.keys))
        
        local_diff_set = union_set - set(self.student_ids)
        
        db_diff_set = union_set - set(self.keys)

        if len(union_set) == 0:
            QMessageBox.critical(self, "Error", "luru", QMessageBox.Ok)
            print('[Error] union_set:', union_set)
        elif len(inter_set) == 0 and len(union_set) != 0:
            QMessageBox.critical(self, "Error", "11", QMessageBox.Ok)
            print('[Error] inter_set:', inter_set)
        elif len(two_diff_set) == 0 and len(union_set) != 0:
            QMessageBox.information(self, "Success", "11", QMessageBox.Ok)
            print('[Success] two_diff_set:', two_diff_set)

        elif len(local_diff_set) != 0:
            QMessageBox.warning(self, "Warning", "11", QMessageBox.Ok)
            print('[Warning] local_diff_set:', local_diff_set)
        elif len(db_diff_set) != 0:
            QMessageBox.warning(self, "Warning", "11", QMessageBox.Ok)
            print('[Warning] db_diff_set:', db_diff_set)

    
    def use_id_get_info(self, ID):
        global cursor, db
        if ID != '':
            try:
               
                db, cursor = connect_to_sql()
                
                sql = "select * from students where ID = {}".format(ID)
                
                cursor.execute(sql)
                
                results = cursor.fetchall()
                self.check_info = []
                for i in results:
                    self.check_info.append(i[1])
                    self.check_info.append(i[0])
                    self.check_info.append(i[2])
                return self.check_info
            except ConnectionAbortedError as e:
                self.ui.textBrowser_log.append("[ERROR] 2")
            finally:
                cursor.close()
                db.close()

    
    def show_late_absence(self):
        db, cursor = connect_to_sql()
        
        sql1 = "select name from checkin where Description = '{}'".format('22')
        sql2 = "select name from students"
        try:
            cursor.execute(sql1)
            results = cursor.fetchall()
            self.late_students = []
            for x in results:
                self.late_students.append(x[0])
            self.late_students.sort()
            # self.ui.textBrowser_log.append(self.late_students)
        except ConnectionAbortedError as e:
            self.ui.textBrowser_log.append('[INFO] 21', e)

        try:
            cursor.execute(sql2)
            results2 = cursor.fetchall()
            self.students_id = []
            for i in results2:
                self.students_id.append(i[0])
            self.students_id.sort()
            print(self.students_id)
        except ConnectionAbortedError as e:
            self.ui.textBrowser_log.append('[INFO] 121', e)

        finally:
            db.commit()
            cursor.close()
            db.close()

        
        self.absence_nums = set(set(self.students_id) - set(self.late_students))
        self.absence_nums = list(self.absence_nums)
        self.absence_nums.sort()

        
        n_row_late = len(self.late_students)
        n_row_absence= len(self.absence_nums)
        model1 = QtGui.QStandardItemModel(n_row_late, 0)
        
        model1.setHorizontalHeaderLabels(['name'])
        
        for row in range(n_row_late):
            item = QtGui.QStandardItem(self.late_students[row])
            
            model1.setItem(row, 0, item)
        
        table_view1 = self.ui.tableView_escape
        table_view1.setModel(model1)

        
        module2 = QtGui.QStandardItemModel(rowAbsentee, 0)
        
        module2.setHorizontalHeaderLabels(['name'])
       
        for row in range(rowAbsentee):
            item = QtGui.QStandardItem(self.absence_nums[row])
           
            module2.setItem(row, 0, item)
        
        table_view2 = self.ui.tableView_late
        table_view2.setModel(module2)

    
    # @staticmethod
    def train_model(self):
        q_message = QMessageBox.information(self, "Tips", "train again", QMessageBox.Yes | QMessageBox.No)
        if QMessageBox.Yes == q_message:
            GeneratorModel.Generator()
            GeneratorModel.TrainModel()
            self.ui.textBrowser_log.append('[INFO] Model has been trained!')
        else:
            self.ui.textBrowser_log.append('[INFO] Cancel train process!')

    def open_info_dialog(self):
        if self.cap.isOpened():
            QMessageBox.warning(self, "Warning", "close canera", QMessageBox.Ok)
            self.cap.release()

    def quit_window(self):
        if self.cap.isOpened():
            self.cap.release()
        QCoreApplication.quit()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    mainWindow = MainWindow()
    infoWindow = InfoDialog()
    rcWindow = RCDialog()
    mainWindow.ui.bt_gathering.clicked.connect(infoWindow.handle_click)
    mainWindow.ui.bt_random_check.clicked.connect(rcWindow.handle_click)
    mainWindow.show()
    sys.exit(app.exec_())
