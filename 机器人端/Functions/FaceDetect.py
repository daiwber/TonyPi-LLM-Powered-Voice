#!/usr/bin/python3
# coding=utf8
import sys
import cv2
import math
import time
import threading
import numpy as np

import hiwonder.Misc as Misc
import hiwonder.Board as Board
import hiwonder.Camera as Camera
import hiwonder.ActionGroupControl as AGC
import hiwonder.yaml_handle as yaml_handle

# 人脸检测

if sys.version_info.major == 2:
    print('Please run this program with python3!')
    sys.exit(0)

# 阈值
conf_threshold = 0.6

# 模型位置
modelFile = "/home/pi/TonyPi/models/res10_300x300_ssd_iter_140000_fp16.caffemodel"
configFile = "/home/pi/TonyPi/models/deploy.prototxt"
net = cv2.dnn.readNetFromCaffe(configFile, modelFile)

# 外部回调函数，用于通知检测结果
face_detected_callback = None

servo_data = None
def load_config():
    global servo_data
    
    servo_data = yaml_handle.get_yaml_data(yaml_handle.servo_file_path)

load_config()

servo2_pulse = servo_data['servo2']
# 初始位置
def initMove():
    Board.setPWMServoPulse(1, 1800, 500)
    Board.setPWMServoPulse(2, servo2_pulse, 500)

d_pulse = 10
start_greet = False
action_finish = True
# 变量重置
def reset():
    global d_pulse
    global start_greet
    global servo2_pulse    
    global action_finish

    d_pulse = 10
    start_greet = False
    action_finish = True
    servo2_pulse = servo_data['servo2']    
    initMove()  
    
# app初始化调用
def init():
    print("FaceDetect Init")
    reset()

__isRunning = False
# app开始玩法调用
def start():
    global __isRunning
    __isRunning = True
    print("FaceDetect Start")

# app停止玩法调用
def stop():
    global __isRunning
    __isRunning = False
    reset()
    print("FaceDetect Stop")

# app退出玩法调用
def exit():
    global __isRunning
    __isRunning = False
    AGC.runActionGroup('stand_slow')
    print("FaceDetect Exit")

def move():
    global start_greet
    global action_finish
    global d_pulse, servo2_pulse    
    
    while True:
        if __isRunning:
            if start_greet:
                start_greet = False
                action_finish = False
                AGC.runActionGroup('wave') # 识别到人脸时执行的动作
                action_finish = True
                time.sleep(0.5)
            else:
                if servo2_pulse > 2000 or servo2_pulse < 1000:
                    d_pulse = -d_pulse
            
                servo2_pulse += d_pulse       
                Board.setPWMServoPulse(2, servo2_pulse, 50)
                time.sleep(0.05)
        else:
            time.sleep(0.01)
            
# 运行子线程
th = threading.Thread(target=move)
th.setDaemon(True)
th.start()

size = (320, 240)
def run(img):
    global start_greet
    global action_finish
       
    img_copy = img.copy()
    img_h, img_w = img.shape[:2]

    if not __isRunning:
        return img

    face_detected = False  # 初始化人脸检测状态
    blob = cv2.dnn.blobFromImage(img_copy, 1, (150, 150), [104, 117, 123], False, False)
    net.setInput(blob)
    detections = net.forward()  # 计算识别
    
    for i in range(detections.shape[2]):
        confidence = detections[0, 0, i, 2]
        if confidence > conf_threshold:
            # 识别到的人脸的各个坐标转换回未缩放前的坐标
            x1 = int(detections[0, 0, i, 3] * img_w)
            y1 = int(detections[0, 0, i, 4] * img_h)
            x2 = int(detections[0, 0, i, 5] * img_w)
            y2 = int(detections[0, 0, i, 6] * img_h)             
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2, 8)  # 将识别到的人脸框出
            
            # 只要检测到人脸就标记状态（无论位置）
            face_detected = True
            
            # 仅当人脸位于中心区域时才触发招手动作
            if abs((x1 + x2)/2 - img_w/2) < img_w/4:
                if action_finish:
                    start_greet = True
    
    # 触发外部回调函数（如果设置了）
    if face_detected and callable(face_detected_callback):
        face_detected_callback()
    
    return img

if __name__ == '__main__':
    from CameraCalibration.CalibrationConfig import *
    
    # 加载参数
    param_data = np.load(calibration_param_path + '.npz')

    # 获取参数
    mtx = param_data['mtx_array']
    dist = param_data['dist_array']
    newcameramtx, roi = cv2.getOptimalNewCameraMatrix(mtx, dist, (640, 480), 0, (640, 480))
    mapx, mapy = cv2.initUndistortRectifyMap(mtx, dist, None, newcameramtx, (640, 480), 5)
    
    max_runtime = 15  # 例如，设置为60秒
    start_time = time.time()  # 记录程序开始时间
    
    init()
    start()
    open_once = yaml_handle.get_yaml_data('/boot/camera_setting.yaml')['open_once']
    if open_once:
        my_camera = cv2.VideoCapture('http://127.0.0.1:8080/?action=stream?dummy=param.mjpg')
    else:
        my_camera = Camera.Camera()
        my_camera.camera_open()        
    AGC.runActionGroup('stand')
    while True:
        
        current_time = time.time()  # 获取当前时间
        if current_time - start_time > max_runtime:
            print("Program has run for the specified time, exiting...")
            break  # 退出循环
        
        ret, img = my_camera.read()
        if ret:
            frame = img.copy()
            frame = cv2.remap(frame, mapx, mapy, cv2.INTER_LINEAR)  # 畸变矫正
            Frame = run(frame)           
            cv2.imshow('Frame', Frame)
            key = cv2.waitKey(1)
            if key == 27:
                break
        else:
            time.sleep(0.01)
    my_camera.camera_close()
    cv2.destroyAllWindows()