#!/usr/bin/python3
# coding=utf8
import sys
import cv2
import math
import time
import threading
import numpy as np
import hiwonder.Board as Board
import hiwonder.Camera as Camera
from hiwonder import yaml_handle
# 人脸检测

# 阈值
conf_threshold = 0.6

# 模型位置
modelFile = "/home/pi/TonyPi/models/res10_300x300_ssd_iter_140000_fp16.caffemodel"
configFile = "/home/pi/TonyPi/models/deploy.prototxt"
net = cv2.dnn.readNetFromCaffe(configFile, modelFile)

di_once = True
detect_people = False
def buzzer():
    global di_once
    global detect_people
    
    while True:
        if detect_people and di_once:
            Board.setBuzzer(1) # 打开
            time.sleep(0.3) # 延时
            Board.setBuzzer(0) #关闭  
            di_once = False            
        else:
            time.sleep(0.01)
            
# 运行子线程
th = threading.Thread(target=buzzer)
th.setDaemon(True)
th.start()

count = 0
size = (320, 240)
def run(img):
    global count
    global di_once
    global detect_people
    
    img_copy = img.copy()
    img_h, img_w = img.shape[:2]

    blob = cv2.dnn.blobFromImage(img_copy, 0.5, (150, 150), [104, 117, 123], False, False)
    net.setInput(blob)
    detections = net.forward() #计算识别
    for i in range(detections.shape[2]):
        confidence = detections[0, 0, i, 2]
        if confidence > conf_threshold:
            #识别到的人了的各个坐标转换会未缩放前的坐标
            x1 = int(detections[0, 0, i, 3] * img_w)
            y1 = int(detections[0, 0, i, 4] * img_h)
            x2 = int(detections[0, 0, i, 5] * img_w)
            y2 = int(detections[0, 0, i, 6] * img_h)             
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2, 8) #将识别到的人脸框出
            detect_people = True
            count = 0
        else:
            count += 1
            if count > 200:
                count = 0
                di_once = True
                detect_people = False
    return img

if __name__ == '__main__':
    from CameraCalibration.CalibrationConfig import *
    
    #加载参数
    param_data = np.load(calibration_param_path + '.npz')

    #获取参数
    mtx = param_data['mtx_array']
    dist = param_data['dist_array']
    newcameramtx, roi = cv2.getOptimalNewCameraMatrix(mtx, dist, (640, 480), 0, (640, 480))
    mapx, mapy = cv2.initUndistortRectifyMap(mtx, dist, None, newcameramtx, (640, 480), 5)    
    
    open_once = yaml_handle.get_yaml_data('/boot/camera_setting.yaml')['open_once']
    if open_once:
        my_camera = cv2.VideoCapture('http://127.0.0.1:8080/?action=stream?dummy=param.mjpg')
    else:
        my_camera = Camera.Camera()
        my_camera.camera_open()
    
    print("Face_Detect Init")
    print("Face_Detect Start")
    
    while True:
        ret, img = my_camera.read()
        if img is not None:
            frame = img.copy()
#             frame = cv2.remap(frame, mapx, mapy, cv2.INTER_LINEAR)  # 畸变矫正
            Frame = run(frame)           
            cv2.imshow('Frame', Frame)
           
            key = cv2.waitKey(1)
            if key == 27:
                break
        else:
            time.sleep(0.01)
    my_camera.camera_close()
    cv2.destroyAllWindows()
