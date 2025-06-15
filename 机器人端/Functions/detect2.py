#!/usr/bin/python3
# coding=utf8
import sys
import cv2
import math
import time
import threading
import numpy as np
import requests
import json
import socket
import hiwonder.Misc as Misc
import hiwonder.Board as Board
import hiwonder.Camera as Camera
import hiwonder.ActionGroupControl as AGC
import hiwonder.yaml_handle as yaml_handle
import re  # 导入正则表达式模块
import re
import time
import sys
sys.path.append('/home/pi/TonyPi/')
import time
from ActionGroupDict import *
import hiwonder.TTS as TTS
import hiwonder.Board as Board
import hiwonder.ActionGroupControl as AGC
import hiwonder.yaml_handle as yaml_handle

# 配置参数
SERVER_IP = '192.168.43.11'  # 替换为你的本机IP
SERVER_PORT = 5000
API_ENDPOINT = f'http://{SERVER_IP}:{SERVER_PORT}/detect'
CONFIDENCE_THRESHOLD = 0.5  # 置信度阈值

# 外部回调函数，用于通知检测结果
object_detected_callback = None

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
    print("ObjectDetect Init")
    reset()


__isRunning = False


# app开始玩法调用
def start():
    global __isRunning
    __isRunning = True
    print("ObjectDetect Start")


# app停止玩法调用
def stop():
    global __isRunning
    __isRunning = False
    reset()
    print("ObjectDetect Stop")


# app退出玩法调用
def exit():
    global __isRunning
    __isRunning = False
    AGC.runActionGroup('stand_slow')
    print("ObjectDetect Exit")


def move():
    global start_greet
    global action_finish
    global d_pulse, servo2_pulse

    while True:
        if __isRunning:
            if start_greet:
                start_greet = False
                action_finish = False
                # AGC.runActionGroup('wave')  # 识别到目标时执行的动作


                # 获取 YAML 数据
                servo_data = yaml_handle.get_yaml_data(yaml_handle.servo_file_path)

                tts = TTS.TTS()

                # 检查并执行语音文件
                voice_file_path = '/home/pi/TonyPi/OpenVINO/temp/res.txt'
                voice_executed = False

                # 检查语音文件是否已被执行
                try:
                    with open(voice_file_path, 'r', encoding='utf-8') as f:
                        ai_response = f.read()
                        # 检查文件中是否包含标志位
                        if "# 已播放" in ai_response:
                            print("语音文件已播放，跳过播放")
                            voice_executed = True
                except FileNotFoundError:
                    print("语音文件未找到")
                    ai_response = ""

                if not voice_executed:
                    # 按标点符号分隔
                    segments = re.split(r'([\。\!\?\，\、\；\：“”“”‘’（）「」『』【】〔〕])', ai_response)
                    filtered_segments = []
                    for segment in segments:
                        if segment.strip():
                            filtered_segments.append(segment.strip())

                    print("分段后的语音内容：")
                    for segment in filtered_segments:
                        print(segment)

                    # 执行语音合成和播放
                    print('TTS Start')
                    chars_per_minute = 200  # 假设每分钟播放 200 个字符
                    for segment in filtered_segments:
                        tts.TTSModuleSpeak('', segment)
                        estimated_time = len(segment) / chars_per_minute * 60
                        print(f"Estimated time for segment '{segment}': {estimated_time:.2f} seconds")
                        time.sleep(estimated_time)

                    # 在文件中添加标志位，表示已播放
                    with open(voice_file_path, 'a', encoding='utf-8') as f:
                        f.write("\n# 已播放")
                else:
                    print("跳过语音播放")

                # 检查并执行动作文件
                action_file_path = '/home/pi/TonyPi/OpenVINO/temp/plan.txt'
                action_executed = False

                # 检查动作文件是否已被执行
                try:
                    with open(action_file_path, 'r', encoding='utf-8') as f:
                        agent_plan = f.read()
                        # 检查文件中是否包含标志位
                        if "# 已执行" in agent_plan:
                            print("动作文件已执行，跳过执行")
                            action_executed = True
                except FileNotFoundError:
                    print("动作文件未找到")
                    agent_plan = ""

                if not action_executed:
                    try:
                        agent_plan = eval(agent_plan)
                    except:
                        print('动作为空，退出')
                        exit()

                    print('Agent Action List:', agent_plan)

                    # 依次执行每个动作
                    for action in agent_plan:
                        AGC.runActionGroup(action)
                    action_finish = True
                    time.sleep(0.5)

                    # 在文件中添加标志位，表示已执行
                    with open(action_file_path, 'a', encoding='utf-8') as f:
                        f.write("\n# 已执行")
                else:
                    print("跳过动作执行")


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

    # 发送图像到服务器进行检测
    _, img_encoded = cv2.imencode('.jpg', img_copy)
    try:
        response = requests.post(
            API_ENDPOINT,
            files={'image': ('image.jpg', img_encoded.tobytes(), 'image/jpeg')},
            timeout=1.0  # 设置超时时间
        )

        if response.status_code == 200:
            detections = response.json().get('detections', [])
            detected_objects = []

            data = response.json()
            if data.get('llm_available', False):
                # 保存 action_plan
                with open('/home/pi/TonyPi/OpenVINO/temp/plan.txt', 'w') as f:
                    f.write(str(data['action_plan']))  # 直接转为字符串写入

                # 保存 ai_response
                with open('/home/pi/TonyPi/OpenVINO/temp/res.txt', 'w', encoding='utf-8') as f:
                    f.write(data['ai_response'])
                print("已保存大模型结果到本地文件")

            for detection in detections:
                label = detection['label']
                confidence = detection['confidence']
                x1, y1, x2, y2 = detection['bbox']

                if confidence > CONFIDENCE_THRESHOLD:
                    # 绘制检测框和标签
                    cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(img, f"{label}: {confidence:.2f}",
                                (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX,
                                0.5, (0, 255, 0), 2)

                    detected_objects.append(label)

                    # 如果检测到人且在中心区域，触发动作
                    if abs((x1 + x2) / 2 - img_w / 2) < img_w / 4:
                        if action_finish:
                            start_greet = True

            # 触发外部回调函数（如果设置了）
            if detected_objects and callable(object_detected_callback):
                object_detected_callback(detected_objects)

    except (requests.exceptions.RequestException, socket.timeout) as e:
        print(f"Error connecting to detection server: {e}")

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
