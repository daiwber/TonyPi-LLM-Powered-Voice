#!/usr/bin/python3
# coding=utf8
import sys
sys.path.append('/home/pi/TonyPi/')
import time
import cv2
import threading
import hiwonder.Camera as Camera
from ActionGroupDict import *
import hiwonder.TTS as TTS
import hiwonder.ASR as ASR
import hiwonder.Board as Board
import hiwonder.ActionGroupControl as AGC
import hiwonder.yaml_handle as yaml_handle

# 人脸检测配置
conf_threshold = 0.6
modelFile = "/home/pi/TonyPi/models/res10_300x300_ssd_iter_140000_fp16.caffemodel"
configFile = "/home/pi/TonyPi/models/deploy.prototxt"
net = cv2.dnn.readNetFromCaffe(configFile, modelFile)

# 语音控制
servo_data = yaml_handle.get_yaml_data(yaml_handle.servo_file_path)

# 全局变量
__isRunning = False
servo2_pulse = servo_data['servo2']
d_pulse = 10
start_greet = False
action_finish = True
detect_color = 'None'

def initMove():
    Board.setPWMServoPulse(1, 1500, 500)
    Board.setPWMServoPulse(2, servo2_pulse, 500)

def reset():
    global d_pulse, start_greet, servo2_pulse, action_finish, detect_color
    d_pulse = 10
    start_greet = False
    action_finish = True
    servo2_pulse = servo_data['servo2']
    detect_color = 'None'
    initMove()
    
def face_detection_thread():
    global __isRunning, start_greet, action_finish, servo2_pulse, d_pulse
    
    # 初始化摄像头
    my_camera = Camera.Camera()
    my_camera.camera_open()
    
    try:
        cv2.namedWindow('Robot View', cv2.WINDOW_NORMAL)
        initMove()
        __isRunning = True
        
        while __isRunning:
            ret, img = my_camera.read()
            if not ret:
                continue
                
            cv2.imshow('Robot View', img)
            if cv2.waitKey(1) & 0xFF == 27:
                break
                
            # 人脸检测
            img_copy = img.copy()
            blob = cv2.dnn.blobFromImage(img_copy, 1, (150, 150), [104, 117, 123], False, False)
            net.setInput(blob)
            detections = net.forward()
            
            face_detected = False
            img_h, img_w = img.shape[:2]
            
            for i in range(detections.shape[2]):
                confidence = detections[0, 0, i, 2]
                if confidence > conf_threshold:
                    face_detected = True
                    x1 = int(detections[0, 0, i, 3] * img_w)
                    x2 = int(detections[0, 0, i, 5] * img_w)
                    if abs((x1 + x2)/2 - img_w/2) < img_w/4:
                        if action_finish:
                            start_greet = True
                            # 检测到有效人脸后立即停止转头
                            __isRunning = False
                            break
                    break
            
            if not face_detected and __isRunning:
                if servo2_pulse > 2000 or servo2_pulse < 1000:
                    d_pulse = -d_pulse
                servo2_pulse += d_pulse
                Board.setPWMServoPulse(2, servo2_pulse, 50)
            
            time.sleep(0.05)
            
    except Exception as e:
        print(f"人脸检测出错: {str(e)}")
    finally:
        cv2.destroyAllWindows()
        my_camera.camera_close()
        reset()
        AGC.runActionGroup('stand')
        tts.TTSModuleSpeak('', '请给我下一个指令')

def color_detection_thread():
    global __isRunning, detect_color
    
    # 加载颜色检测配置
    lab_data = yaml_handle.get_yaml_data(yaml_handle.lab_file_path)
    size = (320, 240)
    
    # 初始化摄像头
    my_camera = Camera.Camera()
    my_camera.camera_open()
    
    try:
        cv2.namedWindow('Color Detection', cv2.WINDOW_NORMAL)
        __isRunning = True
        
        color_dict = {'red': '红色', 'green': '绿色', 'blue': '蓝色'}
        color_list = []
        
        while __isRunning:
            ret, img = my_camera.read()
            if not ret:
                continue
                
            img_copy = img.copy()
            frame_resize = cv2.resize(img_copy, size, interpolation=cv2.INTER_NEAREST)
            frame_gb = cv2.GaussianBlur(frame_resize, (3, 3), 3)
            frame_lab = cv2.cvtColor(frame_gb, cv2.COLOR_BGR2LAB)
            
            max_area = 0
            color_area_max = None
            
            for color in lab_data:
                if color not in ['black', 'white']:
                    frame_mask = cv2.inRange(frame_lab,
                                           (lab_data[color]['min'][0],
                                            lab_data[color]['min'][1],
                                            lab_data[color]['min'][2]),
                                           (lab_data[color]['max'][0],
                                            lab_data[color]['max'][1],
                                            lab_data[color]['max'][2]))
                    eroded = cv2.erode(frame_mask, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)))
                    dilated = cv2.dilate(eroded, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)))
                    contours = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[-2]
                    
                    if contours:
                        max_contour = max(contours, key=cv2.contourArea)
                        area = cv2.contourArea(max_contour)
                        if area > max_area and area > 200:
                            max_area = area
                            color_area_max = color
            
            if color_area_max in color_dict:
                color_list.append(color_area_max)
                if len(color_list) >= 5:
                    # 取出现次数最多的颜色
                    detect_color = max(set(color_list), key=color_list.count)
                    color_list = []
            else:
                detect_color = 'None'
            
            cv2.imshow('Color Detection', img)
            if cv2.waitKey(1) & 0xFF == 27:
                break
            time.sleep(0.1)
            
    except Exception as e:
        print(f"颜色检测出错: {str(e)}")
    finally:
        cv2.destroyAllWindows()
        my_camera.camera_close()
        reset()
        AGC.runActionGroup('stand')

# 主程序初始化
try:
    asr = ASR.ASR()
    tts = TTS.TTS()

    # 添加指令
    asr.addWords(1, 'ben dan')
    asr.addWords(2, 'wang qian zou')
    asr.addWords(2, 'qian jin')
    asr.addWords(2, 'zhi zou')
    asr.addWords(3, 'wang hou tui')
    asr.addWords(4, 'xiang zuo yi')
    asr.addWords(5, 'xiang you yi')
    asr.addWords(6, 'fu wo cheng')
    asr.addWords(7, 'yang wo qi zuo')
    asr.addWords(8, 'zuo zhuan')
    asr.addWords(9, 'you zhuan')
    asr.addWords(17, 'zuo gou quan')
    asr.addWords(18, 'you gou quan')
    asr.addWords(16, 'yong chun')
    asr.addWords(100, 'xiao ping guo')
    asr.addWords(101, '跟随红色方块走')
    asr.addWords(102, '跟随蓝色方块走')
    asr.addWords(103, '跟随绿色方块走')
    asr.addWords(104, 'ni kan')
    asr.addWords(104, 'kan qian mian')
    asr.addWords(104, 'kan')
    asr.addWords(105, 'you sha yan se')
    asr.addWords(105, 'cai se')
    asr.addWords(105, 'shi bie yan se')

    reset()
    AGC.runActionGroup('stand')
    tts.TTSModuleSpeak('[h0][v10][m3]', '准备就绪')
    print('''当前为口令模式，每次说指令前均需要说口令来激活
口令：春竹
指令2：往前走
指令2：前进
指令2：直走
指令3：往后退
指令4：向左移
指令5：向右移
指令101：跟随红色方块
指令102：跟随蓝色方块
指令103：跟随绿色方块
指令104：看附近有人吗
指令105：你面前有什么颜色
''')
except Exception as e:
    print(f'初始化出错: {str(e)}')
    sys.exit(1)

# 招手动作线程
def wave_thread():
    global start_greet, action_finish
    while True:
        if start_greet:
            start_greet = False
            action_finish = False
            AGC.runActionGroup('wave')
            action_finish = True
            time.sleep(0.5)
        else:
            time.sleep(0.1)

# 启动招手动作线程
wave_th = threading.Thread(target=wave_thread)
wave_th.daemon = True
wave_th.start()

# 主循环
while True:
    try:
        data = asr.getResult()
        if data:
            print('result:', data)
            tts.TTSModuleSpeak('', '收到')
            time.sleep(1)
            
            if data == 104:  # 执行104指令
                if not __isRunning:
                    reset()
                    detection_thread = threading.Thread(target=face_detection_thread)
                    detection_thread.daemon = True
                    detection_thread.start()
            elif data == 105:  # 执行105指令
                if not __isRunning:
                    reset()
                    detect_color = 'None'
                    color_thread = threading.Thread(target=color_detection_thread)
                    color_thread.daemon = True
                    color_thread.start()
                    # 等待颜色检测结果
                    time.sleep(2)
                    if detect_color != 'None':
                        color_dict = {'red': '红色', 'green': '绿色', 'blue': '蓝色'}
                        tts.TTSModuleSpeak('', f'前面是{color_dict[detect_color]}')
                    else:
                        tts.TTSModuleSpeak('', '没有检测到颜色')
                    __isRunning = False
            else:  # 其他指令
                AGC.runActionGroup(action_group_dict[str(data - 1)], 1, True)
                tts.TTSModuleSpeak('', '请给我下一个指令')
                
        time.sleep(0.1)
    except KeyboardInterrupt:
        __isRunning = False
        break
    except Exception as e:
        print(f'主循环出错: {str(e)}')
        time.sleep(1)

# 退出清理
reset()
AGC.runActionGroup('stand')
sys.exit(0)