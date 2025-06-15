#!/usr/bin/python3
# coding=utf8
import sys
import cv2
import time
import math
import threading
import numpy as np

import hiwonder.TTS as TTS
import hiwonder.ASR as ASR
import hiwonder.Misc as Misc
import hiwonder.Board as Board
import hiwonder.Camera as Camera
import hiwonder.apriltag as apriltag
import hiwonder.ActionGroupControl as AGC
import hiwonder.yaml_handle as yaml_handle

if __name__ == '__main__':
    from CameraCalibration.CalibrationConfig import *
else:
    from Functions.CameraCalibration.CalibrationConfig import *

# 语音控制

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

# 搬运用到的动作组名称
go_forward = 'go_forward'
back = 'back_fast'
turn_left = 'turn_left_small_step'
turn_right = 'turn_right_small_step'
left_move = 'left_move'
right_move = 'right_move'
left_move_large = 'left_move_30'
right_move_large = 'right_move_30'

try:
    asr = ASR.ASR()
    tts = TTS.TTS()
except:
    print('传感器初始化出错')

range_rgb = {
    'red': (0, 0, 255),
    'blue': (255, 0, 0),
    'green': (0, 255, 0),
    'black': (0, 0, 0),
    'white': (255, 255, 255),
}

# 颜色对应的tag编号
color_tag = {'red': 1,
             'green': 2,
             'blue': 3
             }

lab_data = None
servo_data = None
def load_config():
    global lab_data, servo_data
    
    lab_data = yaml_handle.get_yaml_data(yaml_handle.lab_file_path)
    servo_data = yaml_handle.get_yaml_data(yaml_handle.servo_file_path)

# 初始位置
def initMove():
    Board.setPWMServoPulse(1, servo_data['servo1'], 500)
    Board.setPWMServoPulse(2, servo_data['servo2'], 500)

load_config()

d_x = 15
d_y = 15
step = 1
time_start = 0
x_dis = servo_data['servo2']
y_dis = servo_data['servo1']
last_status = ''
start_count = True
head_turn = 'left_right'
object_center_x, object_center_y, object_angle = -2, -2, 0
# 变量重置
def reset():
    global time_start
    global d_x, d_y
    global last_status
    global start_count
    global step, head_turn
    global x_dis, y_dis
    global object_center_x, object_center_y, object_angle

    d_x = 15
    d_y = 15
    step = 1
    time_start = 0
    x_dis = servo_data['servo2']
    y_dis = servo_data['servo1']
    last_status = ''
    start_count = True
    head_turn = 'left_right'
    object_center_x, object_center_y, object_angle = -2, -2, 0
    
# app初始化调用
def init():
    print("Transport Init")
    load_config()
    asr_init()
    initMove()

__isRunning = False
# app开始玩法调用
def start():
    global __isRunning
    reset()
    __isRunning = True
    print("Transport Start")

# app停止玩法调用
def stop():
    global __isRunning
    __isRunning = False
    print("Transport Stop")

# app退出玩法调用
def exit():
    global __isRunning
    __isRunning = False
    AGC.runActionGroup('stand_slow')
    print("Transport Exit")

# 找出面积最大的轮廓
# 参数为要比较的轮廓的列表
def getAreaMaxContour(contours):
    contour_area_max = 0
    area_max_contour = None

    for c in contours:  # 历遍所有轮廓
        contour_area_temp = math.fabs(cv2.contourArea(c))  # 计算轮廓面积
        if contour_area_temp > contour_area_max:
            contour_area_max = contour_area_temp
            if contour_area_temp >= 300:  # 只有在面积大于300时，最大面积的轮廓才是有效的，以过滤干扰
                area_max_contour = c

    return area_max_contour, contour_area_max  # 返回最大的轮廓

# 红绿蓝颜色识别
size = (320, 240)
def colorDetect(img, _color_):
    img_h, img_w = img.shape[:2]
    
    frame_resize = cv2.resize(img, size, interpolation=cv2.INTER_NEAREST)
    frame_gb = cv2.GaussianBlur(frame_resize, (3, 3), 3)   
    frame_lab = cv2.cvtColor(frame_gb, cv2.COLOR_BGR2LAB)  # 将图像转换到LAB空间
    
    center_max_distance = pow(img_w/2, 2) + pow(img_h, 2)
    color, center_x, center_y, angle = 'None', -1, -1, 0
    for i in lab_data:
        if i == _color_:
            frame_mask = cv2.inRange(frame_lab,
                                     (lab_data[i]['min'][0],
                                      lab_data[i]['min'][1],
                                      lab_data[i]['min'][2]),
                                     (lab_data[i]['max'][0],
                                      lab_data[i]['max'][1],
                                      lab_data[i]['max'][2]))  #对原图像和掩模进行位运算 
            eroded = cv2.erode(frame_mask, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)))  #腐蚀
            dilated = cv2.dilate(eroded, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))) #膨胀
            contours = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[-2]  # 找出轮廓
            areaMaxContour, area_max = getAreaMaxContour(contours)  # 找出最大轮廓
            
            if area_max > 500:  # 有找到最大面积
                rect = cv2.minAreaRect(areaMaxContour)#最小外接矩形
                angle_ = rect[2]
        
                box = np.int0(cv2.boxPoints(rect))#最小外接矩形的四个顶点
                for j in range(4):
                    box[j, 0] = int(Misc.map(box[j, 0], 0, size[0], 0, img_w))
                    box[j, 1] = int(Misc.map(box[j, 1], 0, size[1], 0, img_h))

                cv2.drawContours(img, [box], -1, (0,255,255), 2)#画出四个点组成的矩形
            
                #获取矩形的对角点
                ptime_start_x, ptime_start_y = box[0, 0], box[0, 1]
                pt3_x, pt3_y = box[2, 0], box[2, 1]            
                center_x_, center_y_ = int((ptime_start_x + pt3_x) / 2), int((ptime_start_y + pt3_y) / 2)#中心点       
                cv2.circle(img, (center_x_, center_y_), 5, (0, 255, 255), -1)#画出中心点
                
                distance = pow(center_x_ - img_w/2, 2) + pow(center_y_ - img_h, 2)
                if distance < center_max_distance:  # 寻找距离最近的物体来搬运
                    center_max_distance = distance
                    color = i
                    center_x, center_y, angle = center_x_, center_y_, angle_
                    
    return color, center_x, center_y, angle

# 检测apriltag
detector = apriltag.Detector(searchpath=apriltag._get_demo_searchpath())
def apriltagDetect(img):   
    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
    detections = detector.detect(gray, return_image=False)
    tag_1 = [-1, -1, 0]
    tag_2 = [-1, -1, 0]
    tag_3 = [-1, -1, 0]

    if len(detections) != 0:
        for detection in detections:                       
            corners = np.rint(detection.corners)  # 获取四个角点
            cv2.drawContours(img, [np.array(corners, np.int)], -1, (0, 255, 255), 2)

            tag_family = str(detection.tag_family, encoding='utf-8')  # 获取tag_family
            tag_id = str(detection.tag_id)  # 获取tag_id

            object_center_x, object_center_y = int(detection.center[0]), int(detection.center[1])  # 中心点
            cv2.circle(frame, (object_center_x, object_center_y), 5, (0, 255, 255), -1)
            
            object_angle = int(math.degrees(math.atan2(corners[0][1] - corners[1][1], corners[0][0] - corners[1][0])))  # 计算旋转角
            
            if tag_family == 'tag36h11':
                if tag_id == '1':
                    tag_1 = [object_center_x, object_center_y, object_angle]
                elif tag_id == '2':
                    tag_2 = [object_center_x, object_center_y, object_angle]
                elif tag_id == '3':
                    tag_3 = [object_center_x, object_center_y, object_angle]
        
    return tag_1, tag_2, tag_3

# 通过其他apriltag判断目标apriltag位置
# apriltag摆放位置：红(tag36h11_1)，绿(tag36h11_2)，蓝(tag36h11_3)
def getTurn(tag_id, tag_data):
    tag_1 = tag_data[0]
    tag_2 = tag_data[1]
    tag_3 = tag_data[2]

    if tag_id == 1:  # 目标apriltag为1
        if tag_2[0] == -1:  # 没有检测到apriltag 2
            if tag_3[0] != -1:  # 检测到apriltag 3， 则apriltag 1在apriltag 3左边，所以左转
                return 'left'
        else:  # 检测到apriltag 2，则则apriltag 1在apriltag 2左边，所以左转
            return 'left'
    elif tag_id == 2:
        if tag_1[0] == -1:
            if tag_3[0] != -1:
                return 'left'
        else:
            return 'right'
    elif tag_id == 3:
        if tag_1[0] == -1:
            if tag_2[0] != -1:
                return 'right'
        else:
            return 'right'

    return 'None'

turn = 'None'
CENTER_X = 350
find_box = True
go_step = 3
lock_servos = ''
stop_detect = False
object_color = None
haved_find_tag = False
head_turn = 'left_right'
color_list = ['red', 'green', 'blue']
color_center_x, color_center_y = -1, -1
LOCK_SERVOS = {'6': 650, '7': 850, '8': 0, '14': 350, '15': 150, '16': 1000}
#执行动作组
def move(): 
    global d_x
    global d_y
    global step
    global turn
    global x_dis
    global y_dis
    global go_step
    global lock_servos
    global start_count
    global find_box
    global head_turn
    global time_start
    global color_list
    global stop_detect
    global haved_find_tag    
    global object_color

    while True:
        if __isRunning:
            if object_center_x == -3:  # -3表示放置阶段，且没有找到目标apriltag，但是找到其他apriltag
                # 根据其他arpiltag的相对位置来判断转向
                if turn == 'left':
                    AGC.runActionGroup(turn_left, lock_servos=lock_servos)
                elif turn == 'right':
                    AGC.runActionGroup(turn_right, lock_servos=lock_servos)
            elif haved_find_tag and object_center_x == -1:  # 如果转头过程找到了apriltag，且头回中时apriltag不在视野中
                # 根据头转向来判断apriltag位置
                if x_dis > servo_data['servo2']:                    
                    AGC.runActionGroup(turn_left, lock_servos=lock_servos)
                elif x_dis < servo_data['servo2']:
                    AGC.runActionGroup(turn_right, lock_servos=lock_servos)
                else:
                    haved_find_tag = False
            elif object_center_x >= 0:  # 如果找到目标
                if not find_box:  # 如果是放置阶段
                    if color_center_y > 350:  # 搬运过程中，当太靠近其他物体时，需要绕开
                        if (color_center_x - CENTER_X) > 80:
                            AGC.runActionGroup(go_forward, lock_servos=lock_servos)
                        elif (color_center_x > CENTER_X and object_center_x >= CENTER_X) or (color_center_x <= CENTER_X and object_center_x >= CENTER_X):
                            AGC.runActionGroup(right_move_large, lock_servos=lock_servos)
                            #time.sleep(0.2)
                        elif (color_center_x > CENTER_X and object_center_x < CENTER_X) or (color_center_x <= CENTER_X and object_center_x < CENTER_X):
                            AGC.runActionGroup(left_move_large, lock_servos=lock_servos)
                            #time.sleep(0.2)

                # 如果是转头阶段找到物体， 头回中
                if x_dis != servo_data['servo2'] and not haved_find_tag:
                    # 重置转头寻找的相关变量
                    head_turn == 'left_right'
                    start_count = True
                    d_x, d_y = 15, 15
                    haved_find_tag = True
                    
                    # 头回中
                    Board.setPWMServoPulse(1, servo_data['servo1'], 500)
                    Board.setPWMServoPulse(2, servo_data['servo2'], 500)
                    time.sleep(0.6)
                elif step == 1:  # 左右调整，保持在正中
                    x_dis = servo_data['servo2']
                    y_dis = servo_data['servo1']                   
                    turn = ''
                    haved_find_tag = False
                    
                    if (object_center_x - CENTER_X) > 170 and object_center_y > 330:
                        AGC.runActionGroup(back, lock_servos=lock_servos)   
                    elif object_center_x - CENTER_X > 80:  # 不在中心，根据方向让机器人转向一步
                        AGC.runActionGroup(turn_right, lock_servos=lock_servos)
                    elif object_center_x - CENTER_X < -80:
                        AGC.runActionGroup(turn_left, lock_servos=lock_servos)                        
                    elif 0 < object_center_y <= 250:
                        AGC.runActionGroup(go_forward, lock_servos=lock_servos)
                    else:
                        step = 2
                elif step == 2:  # 接近物体
                    if 330 < object_center_y:
                        AGC.runActionGroup(back, lock_servos=lock_servos)
                    if find_box:
                        if object_center_x - CENTER_X > 150:  # 不在中心，根据方向让机器人转向一步
                            AGC.runActionGroup(right_move_large, lock_servos=lock_servos)
                        elif object_center_x - CENTER_X < -150:
                            AGC.runActionGroup(left_move_large, lock_servos=lock_servos)                        
                        elif -10 > object_angle > -45:
                            AGC.runActionGroup(turn_left, lock_servos=lock_servos)
                        elif -80 < object_angle <= -45:
                            AGC.runActionGroup(turn_right, lock_servos=lock_servos)
                        elif object_center_x - CENTER_X > 40:  # 不在中心，根据方向让机器人转向一步
                            AGC.runActionGroup(right_move_large, lock_servos=lock_servos)
                        elif object_center_x - CENTER_X < -40:
                            AGC.runActionGroup(left_move_large, lock_servos=lock_servos)
                        else:
                            step = 3
                    else:                        
                        if object_center_x - CENTER_X > 150:  # 不在中心，根据方向让机器人转向一步
                            AGC.runActionGroup(right_move_large, lock_servos=lock_servos)
                        elif object_center_x - CENTER_X < -150:
                            AGC.runActionGroup(left_move_large, lock_servos=lock_servos)                        
                        elif object_angle < -5:
                            AGC.runActionGroup(turn_left, lock_servos=lock_servos)
                        elif 5 < object_angle:
                            AGC.runActionGroup(turn_right, lock_servos=lock_servos)
                        elif object_center_x - CENTER_X > 40:  # 不在中心，根据方向让机器人转向一步
                            AGC.runActionGroup(right_move_large, lock_servos=lock_servos)
                        elif object_center_x - CENTER_X < -40:
                            AGC.runActionGroup(left_move_large, lock_servos=lock_servos)
                        else:
                            step = 3
                elif step == 3:
                    if 340 < object_center_y:
                        AGC.runActionGroup(back, lock_servos=lock_servos)
                    elif 0 < object_center_y <= 250:
                        AGC.runActionGroup(go_forward, lock_servos=lock_servos)
                    elif object_center_x - CENTER_X >= 40:  # 不在中心，根据方向让机器人转向一步
                        AGC.runActionGroup(right_move_large, lock_servos=lock_servos)
                    elif object_center_x - CENTER_X <= -40:
                        AGC.runActionGroup(left_move_large, lock_servos=lock_servos) 
                    elif 20 <= object_center_x - CENTER_X < 40:  # 不在中心，根据方向让机器人转向一步
                        AGC.runActionGroup(right_move, lock_servos=lock_servos)
                    elif -40 < object_center_x - CENTER_X < -20:                      
                        AGC.runActionGroup(left_move, lock_servos=lock_servos)
                    else:
                        step = 4 
                elif step == 4:  #靠近物体
                    if 300 < object_center_y <= 340:
                        AGC.runActionGroup('go_forward_one_step', lock_servos=lock_servos)
                        time.sleep(0.2)
                    elif 0 <= object_center_y <= 300:
                        AGC.runActionGroup(go_forward, lock_servos=lock_servos)
                    else:
                        if object_center_y >= 370:
                            go_step = 2
                        else:
                            go_step = 3
                        if abs(object_center_x - CENTER_X) <= 20:
                            stop_detect = True
                            step = 5
                        else:
                            step = 3
                elif step == 5:  # 拿起或者放下物体
                    if find_box:
                        AGC.runActionGroup('go_forward_one_step', times=3)
                        AGC.runActionGroup('stand', lock_servos=lock_servos)
                        AGC.runActionGroup('move_up')
                        lock_servos = LOCK_SERVOS
                        step = 6    
                    else:
                        AGC.runActionGroup('go_forward_one_step', times=go_step, lock_servos=lock_servos)
                        AGC.runActionGroup('stand', lock_servos=lock_servos)
                        AGC.runActionGroup('put_down')
                        AGC.runActionGroup(back, times=5, with_stand=True)
                        tts.TTSModuleSpeak('', '搬运完成')
                        lock_servos = ''
                        step = 6
                        object_color = None
            elif object_center_x == -1:  # 找不到目标时，转头，转身子来寻找                 
                if start_count:
                    start_count = False
                    time_start = time.time()
                else:
                    if time.time() - time_start > 0.5:
                        if 0 < servo_data['servo2'] - x_dis <= abs(d_x) and d_y > 0:
                            x_dis = servo_data['servo2']
                            y_dis = servo_data['servo1']
                            Board.setPWMServoPulse(1, y_dis, 20)
                            Board.setPWMServoPulse(2, x_dis, 20)
                            
                            AGC.runActionGroup(turn_right, times=5, lock_servos=lock_servos)
                        elif head_turn == 'left_right':
                            x_dis += d_x            
                            if x_dis > servo_data['servo2'] + 400 or x_dis < servo_data['servo2'] - 400:
                                if head_turn == 'left_right':
                                    head_turn = 'up_down'
                                d_x = -d_x
                        elif head_turn == 'up_down':
                            y_dis += d_y
                            if y_dis > servo_data['servo1'] + 300 or y_dis < servo_data['servo1']:
                                if head_turn == 'up_down':
                                    head_turn = 'left_right'
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

def run(img):
    global step 
    global turn
    global stop_detect, find_box
    global color, color_center_x, color_center_y, color_angle
    global object_color, object_center_x, object_center_y, object_angle

    if not __isRunning or stop_detect:
        if step == 5:
            object_center_x = 0
        elif step == 6:
            find_box = not find_box
            object_center_x = -2
            step = 1
            stop_detect = False
        #img = cv2.remap(img, mapx, mapy, cv2.INTER_LINEAR)

        return img
    
    data = asr.getResult()
    if data == 2:
       object_color = 'red'
       tts.TTSModuleSpeak('', '收到, 开始寻找红色')
    elif data == 3:
        object_color = 'green'
        tts.TTSModuleSpeak('', '好的，开始寻找绿色')
    elif data == 4:
        object_color = 'blue'
        tts.TTSModuleSpeak('', 'ok， 开始寻找蓝色')
    
    if object_color is None:
        object_center_x = -4
        return img
    
    color, color_center_x, color_center_y, color_angle = colorDetect(img, object_color)  # 颜色检测，返回颜色，中心坐标，角度
    
    # 如果是搬运阶段
    if find_box:
        object_center_x, object_center_y, object_angle = color_center_x, color_center_y, color_angle
    else:
        tag_data = apriltagDetect(img) # apriltag检测
        
        if object_color is None:
            return img
        if tag_data[color_tag[object_color] - 1][0] != -1:  # 如果检测到目标arpiltag
            object_center_x, object_center_y, object_angle = tag_data[color_tag[object_color] - 1]
        else:  # 如果没有检测到目标arpiltag，就通过其他arpiltag来判断相对位置
            turn = getTurn(color_tag[object_color], tag_data)
            if turn == 'None':
                object_center_x, object_center_y, object_angle = -1, -1, 0
            else:  # 完全没有检测到apriltag
                object_center_x, object_center_y, object_angle = -3, -1, 0
    
    #print(object_center_x, object_center_y, object_angle)
    
    #img = cv2.remap(img, mapx, mapy, cv2.INTER_LINEAR)  # 畸变矫正
    
    return img

def asr_init():
    asr.eraseWords()
    asr.setMode(2)
    asr.addWords(1, 'kai shi')
    asr.addWords(2, 'ban yun hong se')
    asr.addWords(3, 'ban yun lv se')
    asr.addWords(4, 'ban yun lan se')
    
    tts.TTSModuleSpeak('[h0][v10][m3]', '准备就绪')
    time.sleep(1)
    asr.getResult()

if __name__ == '__main__':
    init()
    start()
    open_once = yaml_handle.get_yaml_data('/boot/camera_setting.yaml')['open_once']
    if open_once:
        my_camera = cv2.VideoCapture('http://127.0.0.1:8080/?action=stream?dummy=param.mjpg')
    else:
        my_camera = Camera.Camera()
        my_camera.camera_open()        
    AGC.runActionGroup('stand_slow')

    try:
        asr_init()
        print('''当前为口令模式，每次说指令前均需要说口令来激活
口令：开始
指令2：搬运红色
指令3：搬运绿色
指令4：搬运蓝色
    ''')
    except:
        print('传感器初始化出错')
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
