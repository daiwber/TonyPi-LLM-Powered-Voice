#!/usr/bin/python3
# coding=utf8
import sys
import cv2
import time
import math
import threading
import numpy as np
import hiwonder.PID as PID
import hiwonder.Misc as Misc
import hiwonder.Board as Board
import hiwonder.Camera as Camera
import hiwonder.ActionGroupControl as AGC
import hiwonder.yaml_handle as yaml_handle

if __name__ == '__main__':
    from CameraCalibration.CalibrationConfig import *
else:
    from Functions.CameraCalibration.CalibrationConfig import *

# 自动踢球
debug = False

if sys.version_info.major == 2:
    print('Please run this program with python3!')
    sys.exit(0)

#加载参数
param_data = np.load(calibration_param_path + '.npz')

#获取参数
mtx = param_data['mtx_array']
dist = param_data['dist_array']
newcameramtx, roi = cv2.getOptimalNewCameraMatrix(mtx, dist, (640, 480), 0, (640, 480))
mapx, mapy = cv2.initUndistortRectifyMap(mtx, dist, None, newcameramtx, (640, 480), 5)

range_rgb = {
    'red': (0, 0, 255),
    'blue': (255, 0, 0),
    'green': (0, 255, 0),
    'black': (0, 0, 0),
    'white': (255, 255, 255),
}

__target_color = ('red',)
# 设置检测颜色
def setBallTargetColor(target_color):
    global __target_color

    __target_color = target_color
    return (True, (), 'SetBallColor')

lab_data = None
servo_data = None
def load_config():
    global lab_data, servo_data
    
    lab_data = yaml_handle.get_yaml_data(yaml_handle.lab_file_path)
    servo_data = yaml_handle.get_yaml_data(yaml_handle.servo_file_path)

load_config()

# 初始位置
def initMove():
    Board.setPWMServoPulse(1, servo_data['servo1'], 500)
    Board.setPWMServoPulse(2, servo_data['servo2'], 500)

t1 = 0
d_x = 20
d_y = 20
step = 1
step_ = 1
x_dis = servo_data['servo2']
y_dis = servo_data['servo1']
last_status = ''
start_count = True
centerX, centerY = -2, -2
x_pid = PID.PID(P=0.4, I=0.01, D=0.02)#pid初始化
y_pid = PID.PID(P=0.35, I=0.01, D=0.02)
# 变量重置
def reset():
    global t1
    global d_x, d_y
    global last_status
    global start_count
    global step, step_
    global x_dis, y_dis
    global __target_color
    global centerX, centerY

    t1 = 0
    d_x = 20
    d_y = 20
    step = 1
    step_ = 1
    x_pid.clear()
    y_pid.clear()
    x_dis = servo_data['servo2']
    y_dis = servo_data['servo1']
    last_status = ''
    start_count = True
    __target_color = ()
    centerX, centerY = -2, -2
    
# app初始化调用
def init():
    print("KickBall Init")
    load_config()
    initMove()

__isRunning = False
# app开始玩法调用
def start():
    global __isRunning
    reset()
    __isRunning = True
    print("KickBall Start")

# app停止玩法调用
def stop():
    global __isRunning
    __isRunning = False
    print("KickBall Stop")

# app退出玩法调用
def exit():
    global __isRunning
    __isRunning = False
    AGC.runActionGroup('stand_slow')
    print("KickBall Exit")

# 找出面积最大的轮廓
# 参数为要比较的轮廓的列表
def getAreaMaxContour(contours):
    contour_area_temp = 0
    contour_area_max = 0
    area_max_contour = None

    for c in contours:  # 历遍所有轮廓
        contour_area_temp = math.fabs(cv2.contourArea(c))  # 计算轮廓面积
        if contour_area_temp > contour_area_max:
            contour_area_max = contour_area_temp
            if 1000 > contour_area_temp >= 2:  # 只有在面积大于设定值时，最大面积的轮廓才是有效的，以过滤干扰
                area_max_contour = c

    return area_max_contour, contour_area_max  # 返回最大的轮廓

CENTER_X = 350
#执行动作组
def move():
    global t1
    global d_x
    global d_y
    global step
    global step_
    global x_dis
    global y_dis
    global last_status
    global start_count
    
    while True:
        if debug:
            return
        if __isRunning:
            #print('x', centerX)
            if centerX >= 0:
                step_ = 1
                d_x, d_y = 20, 20
                start_count = True
                #print('STEP', step)
                if step == 1:                    
                    if x_dis - servo_data['servo2'] > 150:#不在中心，根据方向让机器人转向一步
                        AGC.runActionGroup('turn_left_small_step')
                    elif x_dis - servo_data['servo2'] < -150:
                        AGC.runActionGroup('turn_right_small_step')
                    else:
                        step = 2
                elif step == 2:
                    if y_dis == servo_data['servo1']:
                        if x_dis == servo_data['servo2'] - 400:
                            AGC.runActionGroup('turn_right',2)
                        elif x_dis == servo_data['servo2'] + 400:
                            AGC.runActionGroup('turn_left',2)
                        elif 350 < centerY <= 380:
                            AGC.runActionGroup('go_forward_one_step')
                            last_status = 'go'
                            step = 1
                        elif 120 < centerY <= 350:
                            AGC.runActionGroup('go_forward')
                            last_status = 'go'
                            step = 1
                        elif 0 <= centerY <= 120 and abs(x_dis - servo_data['servo2']) <= 200:
                            AGC.runActionGroup('go_forward_fast')
                            last_status = 'go'
                            step = 1
                        else:
                            step = 3
                    else:
                        if x_dis == servo_data['servo2'] - 400:
                            AGC.runActionGroup('turn_right',2)
                        elif x_dis == servo_data['servo2'] + 400:
                            AGC.runActionGroup('turn_left',2)
                        else:
                            AGC.runActionGroup('go_forward_fast')
                            last_status = 'go'
                elif step == 3:
                    if y_dis == servo_data['servo1']:
                        if abs(centerX - CENTER_X) <= 40:#不在中心，根据方向让机器人转向一步
                            AGC.runActionGroup('left_move')
                        elif 0 < centerX < CENTER_X - 50 - 40:
                            AGC.runActionGroup('left_move_fast')
                            time.sleep(0.2)
                        elif CENTER_X + 50 + 40 < centerX:                      
                            AGC.runActionGroup('right_move_fast')
                            time.sleep(0.2)
                        else:
                            step = 4 
                    else:
                        if 270 <= x_dis - servo_data['servo2'] < 480:#不在中心，根据方向让机器人转向一步
                            AGC.runActionGroup('left_move_fast')
                            time.sleep(0.2)
                        elif abs(x_dis - servo_data['servo2']) < 170:
                            AGC.runActionGroup('left_move')
                        elif -480 < x_dis - servo_data['servo2'] <= -270:                      
                            AGC.runActionGroup('right_move_fast')
                            time.sleep(0.2)
                        else:
                            step = 4                   
                elif step == 4:
                    if y_dis == servo_data['servo1']:
                        if 380 < centerY <= 440:
                            AGC.runActionGroup('go_forward_one_step')
                            last_status = 'go'
                        elif 0 <= centerY <= 380:
                            AGC.runActionGroup('go_forward')
                            last_status = 'go'
                        else:
                            if centerX < CENTER_X:
                                AGC.runActionGroup('left_shot_fast')
                            else:
                                AGC.runActionGroup('right_shot_fast')
                            step = 1
                    else:
                        step = 1
            elif centerX == -1:
                if last_status == 'go':
                    last_status = ''
                    AGC.runActionGroup('back_fast', with_stand=True)                   
                elif start_count:
                    start_count = False
                    t1 = time.time()
                else:
                    if time.time() - t1 > 0.5:
                        #print(x_dis, y_dis, d_x)
                        #print(step_, servo_data['servo2'])
                        if step_ == 5:
                            x_dis += d_x
                            if abs(x_dis - servo_data['servo2']) <= abs(d_x):
                                AGC.runActionGroup('turn_right')
                                step_ = 1
                        if step_ == 1 or step_ == 3:
                            x_dis += d_x            
                            if x_dis > servo_data['servo2'] + 400:
                                if step_ == 1:
                                    step_ = 2
                                d_x = -d_x
                            elif x_dis < servo_data['servo2'] - 400:
                                if step_ == 3:
                                    step_ = 4
                                d_x = -d_x
                        elif step_ == 2 or step_ == 4:
                            y_dis += d_y
                            if y_dis > 1200:
                                if step_ == 2:
                                    step_ = 3
                                d_y = -d_y
                            elif y_dis < servo_data['servo1']:
                                if step_ == 4:                                
                                    step_ = 5
                                d_y = -d_y
                        Board.setPWMServoPulse(1, y_dis, 20)
                        Board.setPWMServoPulse(2, x_dis, 20)
                        time.sleep(0.02)
            else:
                time.sleep(0.01)
        else:
            time.sleep(0.01)

#启动动作的线程
th = threading.Thread(target=move)
th.setDaemon(True)
th.start()

size = (320, 240)
def run(img):
    global x_dis, y_dis
    global centerX, centerY
    
    img_copy = img.copy()
    img_h, img_w = img.shape[:2]

    if not __isRunning or __target_color == ():
        if debug:
            cv2.line(img, (0, 450), (img_w, 450), (0, 255, 255), 2)
            cv2.line(img, (0, 380), (img_w, 380), (0, 255, 255), 2)
            cv2.line(img, (0, 300), (img_w, 300), (0, 255, 255), 2)
        return img
    
    frame_resize = cv2.resize(img_copy, size, interpolation=cv2.INTER_NEAREST)
    frame_gb = cv2.GaussianBlur(frame_resize, (3, 3), 3)   
    frame_lab = cv2.cvtColor(frame_gb, cv2.COLOR_BGR2LAB)  # 将图像转换到LAB空间
    
    area_max = 0
    areaMaxContour = 0
    for i in lab_data:
        if i in __target_color:
            detect_color = i
            frame_mask = cv2.inRange(frame_lab,
                                         (lab_data[i]['min'][0],
                                          lab_data[i]['min'][1],
                                          lab_data[i]['min'][2]),
                                         (lab_data[i]['max'][0],
                                          lab_data[i]['max'][1],
                                          lab_data[i]['max'][2]))  #对原图像和掩模进行位运算
            eroded = cv2.erode(frame_mask, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)))  #腐蚀
            dilated = cv2.dilate(eroded, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))) #膨胀
            if debug:
                cv2.imshow(i, dilated)
            contours = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[-2]  # 找出轮廓
            areaMaxContour, area_max = getAreaMaxContour(contours)  # 找出最大轮廓
    if area_max:  # 有找到最大面积    
        try:
            (centerX, centerY), radius = cv2.minEnclosingCircle(areaMaxContour) #获取最小外接圆
        except:
            img = cv2.remap(img, mapx, mapy, cv2.INTER_LINEAR)  # 畸变矫正
            return img
        centerX = int(Misc.map(centerX, 0, size[0], 0, img_w))
        centerY = int(Misc.map(centerY, 0, size[1], 0, img_h))
        radius = int(Misc.map(radius, 0, size[0], 0, img_w))
        
        use_time = 0       
        
        if y_dis == servo_data['servo1'] and abs(x_dis - servo_data['servo2']) < 150:
            x_dis = servo_data['servo2']
        else:
            x_pid.SetPoint = img_w/2 #设定           
            x_pid.update(centerX) #当前
            dx = int(x_pid.output)
            if dx > 0:
                last_status = 'left'
            else:
                last_status = 'right'
            use_time = abs(dx*0.00025)
            x_dis += dx #输出           
            
            x_dis = servo_data['servo2'] - 400 if x_dis < servo_data['servo2'] - 400 else x_dis          
            x_dis = servo_data['servo2'] + 400 if x_dis > servo_data['servo2'] + 400 else x_dis
            
        y_pid.SetPoint = img_h/2
        y_pid.update(centerY)
        dy = int(y_pid.output)
        use_time = round(max(use_time, abs(dy*0.00025)), 5)
        y_dis += dy
        
        y_dis = servo_data['servo1'] if y_dis < servo_data['servo1'] else y_dis
        y_dis = 1200 if y_dis > 1200 else y_dis    
        
        Board.setPWMServoPulse(1, y_dis, use_time*1000)
        Board.setPWMServoPulse(2, x_dis, use_time*1000)
        time.sleep(use_time)
        
        cv2.circle(img, (centerX, centerY), radius, range_rgb[detect_color], 2)
        cv2.line(img, (int(centerX - radius/2), centerY), (int(centerX + radius/2), centerY), range_rgb[detect_color], 2)
        cv2.line(img, (centerX, int(centerY - radius/2)), (centerX, int(centerY + radius/2)), range_rgb[detect_color], 2)
    else:
        centerX, centerY = -1, -1
   
    #print(centerX, centerY)

    #img = cv2.remap(img, mapx, mapy, cv2.INTER_LINEAR)  # 畸变矫正

    if debug:
        cv2.putText(img, "x_dis: " + str(x_dis), (10, img.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.65, range_rgb[detect_color], 2)
        cv2.line(img, (0, 450), (img_w, 450), (0, 255, 255), 2)
        cv2.line(img, (0, 380), (img_w, 380), (0, 255, 255), 2)
        cv2.line(img, (0, 300), (img_w, 300), (0, 255, 255), 2) 

    return img

if __name__ == '__main__':
    debug = False
    if debug:
        print('Debug Mode')
    
    init()
    start()
    __target_color = ('red',)
    open_once = yaml_handle.get_yaml_data('/boot/camera_setting.yaml')['open_once']
    if open_once:
        my_camera = cv2.VideoCapture('http://127.0.0.1:8080/?action=stream?dummy=param.mjpg')
    else:
        my_camera = Camera.Camera()
        my_camera.camera_open()        
    AGC.runActionGroup('stand')
    while True:
        ret, img = my_camera.read()
        if ret:
            frame = img.copy()
            Frame = run(frame)           
            cv2.imshow('Frame', Frame)
            key = cv2.waitKey(1)
            if key == 27:
                break
        else:
            time.sleep(0.01)
    my_camera.camera_close()
    cv2.destroyAllWindows()
