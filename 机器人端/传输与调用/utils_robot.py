# -*- coding: utf-8 -*-



# 导入工具包
import os
import hiwonder.ActionGroupControl as AGC
import threading
import time

import pygame


music_file1 = "/home/pi/TonyPi/OpenVINO/xiao.mp3"
music_file2 = "/home/pi/TonyPi/OpenVINO/hajimi.mp3"

# 初始化 pygame 混音器
pygame.mixer.init()

    
# 田径运动：巡线、跨栏、上下台阶
def athletics():
    os.system('python /home/pi/TonyPi/Extend/athletics_course/athletics_perform_only.py')


    


import threading
import time
import pygame


# 模拟音乐播放函数
def play_music(action, stop_flag):
    try:
        # 加载音乐文件
        if action == 'apple_dance':
            pygame.mixer.music.load(music_file1)
        else:
            pygame.mixer.music.load(music_file2)
        print(f"加载音乐文件")
        
        # 播放音乐
        pygame.mixer.music.play()
        print("开始播放音乐")
        
        # 等待音乐播放完成或直到被停止
        while pygame.mixer.music.get_busy():
            if stop_flag.is_set():
                print("停止音乐播放")
                pygame.mixer.music.stop()
                break
            time.sleep(0.1)  # 减少CPU占用
        
        print("音乐线程结束")
    except Exception as e:
        print(f"播放音乐时出错：{e}")

# 模拟舞蹈函数
def dance(action, stop_flag):
    try:
        # 执行舞蹈动作
        if action == 'wave':
            AGC.runActionGroup(action, times = 5)
        else:
            AGC.runActionGroup(action)
        
        print("舞蹈线程结束")
    except Exception as e:
        print(f"执行舞蹈动作时出错：{e}")

print('Actions Step-by-Step')

with open('/home/pi/TonyPi/OpenVINO/temp/agent_plan.txt', 'r', encoding='utf-8') as f:
    agent_plan = f.read()
try:
    agent_plan = eval(agent_plan)
except:
    print('动作为空，退出')
    exit()

print('Agent Action List:', agent_plan)

# 依次执行每个动作
for action in agent_plan:
    print('Action:', action)
    if action == 'apple_dance' or action == 'wave':
        
        # 创建共享的停止标志
        stop_flag = threading.Event()
        
        # 创建线程
        music_thread = threading.Thread(target=play_music, args=(action, stop_flag))
        dance_thread = threading.Thread(target=dance, args=(action, stop_flag))
        
        # 启动线程
        music_thread.start()
        dance_thread.start()
        
        # 等待任一线程完成
        while music_thread.is_alive() and dance_thread.is_alive():
            time.sleep(0.1)  # 避免100% CPU占用
            
        # 设置停止标志
        stop_flag.set()
        
        # 等待两个线程都结束
        music_thread.join()
        dance_thread.join()
    elif action == 'face_detect':
        terminal = 'python3 /home/pi/TonyPi/Functions/FaceDetect.py'
        print('terminal', terminal)
        os.system(terminal)
    elif action == 'intellectual_vision_recognition':
        terminal = 'python3 /home/pi/TonyPi/Functions/Detect.py'
        print('terminal', terminal)
        os.system(terminal)
    elif action == 'ColorDetect':
        terminal = 'python3 /home/pi/TonyPi/Functions/ColorDetect.py'
        print('terminal', terminal)
        os.system(terminal)
    elif action == 'ApriltagDetect':
        terminal = 'python3 /home/pi/TonyPi/Functions/ApriltagDetect.py'
        print('terminal', terminal)
        os.system(terminal)
    elif action == 'VisualPatrol':
        terminal = 'python3 /home/pi/TonyPi/Functions/VisualPatrol.py'
        print('terminal', terminal)
        os.system(terminal)
    elif action == 'KickBall':
        terminal = 'python3 /home/pi/TonyPi/Functions/KickBall.py'
        print('terminal', terminal)
        os.system(terminal)
    elif action == 'Transport':
        terminal = 'python3 /home/pi/TonyPi/Functions/Transport.py'
        print('terminal', terminal)
        os.system(terminal)
    elif action == 'environment_understand':
        terminal = 'python3 /home/pi/TonyPi/OpenVINO/environment_understand.py'
        print('terminal', terminal)
        os.system(terminal)
    else:   
        AGC.runActionGroup(action)