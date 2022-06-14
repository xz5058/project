import os
import re
import sys
import pymysql


CAMERA_ID = 1

COLLENCT_FACE_NUM_DEFAULT = 100


LOOP_FRAME = 20


COURSE_TIME = 95  # minutes

LATE_SPAN = 30


FR_LOOP_NUM = 20


def add_path_to_sys():
    rootdir = "C:/Users/ziyun/Desktop/code/code/"
    # rootdir = os.getcwd()
    sys.path.append(rootdir)

    return rootdir


def connect_to_sql():
    db = pymysql.connect(host="localhost", user="root", password="123456", database="facerecognition")
    
    cursor = db.cursor()

    return db, cursor


def statical_facedata_nums():
    
    files_dir = "E:/work/face_pyqt/Face-Recognition-Class-Attendance-System/face_dataset/"
    # print(os.listdir(files_dir))

    dirs = os.listdir(files_dir)
    
    files_num_dict = dict(zip(dirs, [0] * len(dirs)))

    for dir in dirs:
        for file in os.listdir(files_dir + dir):
            
            # if re.match(r'.*\.jpg$', file) or re.match(r'.*\.png$', file):
            if file.endswith('.jpg') or file.endswith('.png'):
                files_num_dict[dir] += 1

    return files_num_dict


print(os.path.basename(__file__))

if __name__ == '__main__':
    files = statical_facedata_nums()
    print(files)