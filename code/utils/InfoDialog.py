from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QImage, QIcon, QPixmap
from PyQt5.QtCore import QCoreApplication, QThread
from PyQt5.QtWidgets import QApplication, QWidget, QMessageBox, QInputDialog

from ui import infoUI

import threading
import cv2
import imutils
import os
import sys
from datetime import datetime

from utils.GlobalVar import CAMERA_ID, COLLENCT_FACE_NUM_DEFAULT, LOOP_FRAME

from utils.GlobalVar import add_path_to_sys, statical_facedata_nums
rootdir = add_path_to_sys()


from utils.GlobalVar import connect_to_sql


class InfoDialog(QWidget):
    def __init__(self):
        
        super().__init__()

        self.Dialog = infoUI.Ui_Form()
        self.Dialog.setupUi(self)

        
        self.current_filename = os.path.basename(__file__)

        try:
            
            self.setWindowTitle('i')
            self.setWindowIcon(QIcon(f'{rootdir}/logo_imgs/fcb_logo.jpg'))
           
            pixmap = QPixmap(f'{rootdir}/logo_imgs/bkg2.png')
            self.Dialog.label_capture.setPixmap(pixmap)
        except FileNotFoundError as e:
            print("[ERROR] ii(source file: {})".format(self.current_filename), e)

        
        self.Dialog.bt_start_collect.clicked.connect(self.open_camera)
        
        self.Dialog.bt_take_photo.clicked.connect(self.take_photo)
        
        self.Dialog.bt_check_info.clicked.connect(self.check_info)
        
        self.Dialog.bt_change_info.clicked.connect(self.change_info)
        
        self.Dialog.bt_check_dirs_faces.clicked.connect(self.check_dir_faces_num)

        
        # self.cap = cv2.VideoCapture(0 + cv2.CAP_DSHOW)
        self.cap = cv2.VideoCapture()

        
        self.Dialog.spinBox_set_num.setValue(COLLENCT_FACE_NUM_DEFAULT)
        
        self.have_token_photos = 0

        
        self.dialog_text_id_past = None

        self.collect_photos = int(self.Dialog.spinBox_set_num.text())

    def handle_click(self):
        if not self.isVisible():
            self.show()

    def handle_close(self):
        self.close()

    def open_camera(self):
        
        if not self.cap.isOpened():
            
            self.dialog_text_id, ok = QInputDialog.getText(self, 'y', 'id:')
            if ok and self.dialog_text_id != '':

                
                if self.dialog_text_id != self.dialog_text_id_past:
                    self.have_token_photos = 0
                    self.Dialog.lcdNumber_collection_nums.display(0)

                self.Dialog.label_capture.clear()
                self.cap.open(CAMERA_ID)
                self.show_capture()
        else:
            self.cap.release()
            self.Dialog.label_capture.clear()
            self.Dialog.bt_start_collect.setText(u'ok')

    def show_capture(self):
        self.Dialog.bt_start_collect.setText(u'stop')
        self.Dialog.label_capture.clear()
        print("[INFO] starting video stream...")
        loop_num = 0

        
        while self.cap.isOpened():
            
            self.collect_photos = int(self.Dialog.spinBox_set_num.text())
           
            loop_num += 1

            ret, frame = self.cap.read()
            QApplication.processEvents()
            frame = imutils.resize(frame, width=500)
            # frame = cv2.putText(frame, "Have token {}/{} faces".format(self.have_token_photos,
            # self.Dialog.spinBox_set_num.text()), (50, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 100, 50), 2) 显示输出框架
            show_video = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  
            
            # QImage(uchar * data, int width, int height, int bytesPerLine, Format format)
            self.showImage = QImage(show_video.data,
                                    show_video.shape[1],
                                    show_video.shape[0],
                                    QImage.Format_RGB888)
            self.Dialog.label_capture.setPixmap(QPixmap.fromImage(self.showImage))
            
            is_auto_collect = self.Dialog.checkBox_auto_collect.isChecked()

            if is_auto_collect:
                
                if self.have_token_photos != self.collect_photos:
                    
                    if loop_num == LOOP_FRAME:
                        self.have_token_photos += 1
                        self.save_image()

                        loop_num = 0
                if self.have_token_photos == self.collect_photos:
                    QMessageBox.warning(self, "Warning", "max :{}".format(self.have_token_photos), QMessageBox.Ok)
                    self.cap.release()
                    self.Dialog.bt_start_collect.setText('ok')
                    break
            else:
                QMessageBox.information(self, "Tips", "exit")
                # self.cap.release()
                
                break

        
        self.dialog_text_id_past = self.dialog_text_id

        
        self.Dialog.label_capture.clear()

    def save_image(self, method='qt5'):
        self.filename = '{}/face_dataset/{}/'.format(rootdir, self.dialog_text_id)
        self.mk_folder(self.filename)
        if method == 'qt5':
            photo_save_path = os.path.join(os.path.dirname(os.path.abspath('__file__')), '{}'.format(self.filename))
            save_filename = datetime.now().strftime("%Y%m%d%H%M%S") + ".png"
            self.showImage.save(photo_save_path + save_filename)
        else:
            p = os.path.sep.join([output, "{}.png".format(str(total).zfill(5))])
            cv2.imwrite(p, self.showImage)

        self.Dialog.lcdNumber_collection_nums.display(self.have_token_photos)

    
    def mk_folder(self, path):
        
        path = path.strip()
        
        path = path.rstrip("\\")
        
        is_dir_exists = os.path.exists(path)
        
        if not is_dir_exists:
            
            os.makedirs(path)
            return True

    def take_photo(self):
        if self.cap.isOpened():
            self.collect_photos = int(self.Dialog.spinBox_set_num.text())
            # print('self.collect_photos: ', self.collect_photos, type(self.collect_photos))
            # print(self.have_token_photos, type(self.have_token_photos))
            if self.have_token_photos != self.collect_photos:
                self.have_token_photos += 1
                try:
                    self.save_image()
                except FileNotFoundError as e:
                    print("[ERROR] error(source file: {})".format(self.current_filename), e)

            else:
                QMessageBox.information(self, "Information", self.tr("max!"), QMessageBox.Ok)

        else:
            QMessageBox.information(self, "Information", self.tr("open camera"), QMessageBox.Ok)

    
    def check_info(self):
        
        self.input_id = self.Dialog.lineEdit_id.text()
        if self.input_id != '':
            
            lists = []
            
            try:
                db, cursor = connect_to_sql()
            except ConnectionRefusedError as e:
                print("[ERROR] mysql error", e)
            
            else:
                
                sql = "SELECT * FROM STUDENTS WHERE ID = {}".format(self.input_id)
                
                try:
                    cursor.execute(sql)
                    
                    results = cursor.fetchall()
                    for i in results:
                        lists.append(i[0])
                        lists.append(i[1])
                        lists.append(i[2])
                        lists.append(i[3])
                        lists.append(i[4])
                except ValueError as e:
                    print("[ERROR] cannot sql", e)
                    
                else:
                    
                    table_view_module = QtGui.QStandardItemModel(5, 1)
                   
                    table_view_module.setHorizontalHeaderLabels(['1', '2'])
                    rows_name = ['id', 'name', 'class', 'gen', 'bir']
                    

                    
                    lists[0] = self.input_id
                    if len(lists) == 0:
                        QMessageBox.warning(self, "warning", "21", QMessageBox.Ok)
                    else:
                        for row, content in enumerate(lists):
                            row_name = QtGui.QStandardItem(rows_name[row])
                            item = QtGui.QStandardItem(content)
                            
                            table_view_module.setItem(row, 0, row_name)
                            table_view_module.setItem(row, 1, item)

                        
                        self.Dialog.tableView.setModel(table_view_module)
                    
                    assert isinstance(db, object)
                    
            finally:
                cursor.close()
                db.close()

    
    def check_dir_faces_num(self):
        num_dict = statical_facedata_nums()
        keys = list(num_dict.keys())
        values = list(num_dict.values())
        # print(values)
        
        if len(keys) == 0:
            QMessageBox.warning(self, "Error", "121", QMessageBox.Ok)
        else:
            
            table_view_module = QtGui.QStandardItemModel(len(keys), 1)
            table_view_module.setHorizontalHeaderLabels(['ID', 'Number'])

            for row, key in enumerate(keys):
                print(key, values[row])
                id = QtGui.QStandardItem(key)
                num = QtGui.QStandardItem(str(values[row]))

                
                table_view_module.setItem(row, 0, id)
                table_view_module.setItem(row, 1, num)

            
            self.Dialog.tableView.setModel(table_view_module)

    
    def write_info(self):
        
        users = []
        
        is_info_full = False
        student_id = self.Dialog.lineEdit_id.text()
        name = self.Dialog.lineEdit_name.text()
        which_class = self.Dialog.lineEdit_class.text()
        sex = self.Dialog.lineEdit_sex.text()
        birth = self.Dialog.lineEdit_birth.text()
        users.append((student_id, name, which_class, sex, birth))
        
        if all([student_id, name, which_class, sex, birth]):
            is_info_full = True
        return is_info_full, users

    
    def change_info(self):
        
        try:
            db, cursor = connect_to_sql()
            
            insert_sql = "replace into students(ID, Name, Class, Sex, Birthday) values(%s, %s, %s, %s, %s)"

            flag, users = self.write_info()
            if flag:
                cursor.executemany(insert_sql, users)
                QMessageBox.warning(self, "Warning", "21", QMessageBox.Ok)
            else:
                QMessageBox.information(self, "Error", "21", QMessageBox.Ok)
        
        except Exception as e:
            print("[ERROR] sql execute failed!", e)
            
        finally:
            
            db.commit()
            
            cursor.close()
            
            db.close()
