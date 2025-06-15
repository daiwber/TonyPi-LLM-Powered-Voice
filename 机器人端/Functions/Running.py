#!/usr/bin/python3
# coding=utf8
import sys
import time
import threading
import Functions.KickBall as KickBall
import Functions.Transport as Transport
import Functions.ColorTrack as ColorTrack
import Functions.FaceDetect as FaceDetect
import Functions.lab_adjust as lab_adjust
import Functions.ColorDetect as ColorDetect
import Functions.VisualPatrol as VisualPatrol
import Functions.RemoteControl as RemoteControl
import Functions.ApriltagDetect as ApriltagDetect

RunningFunc = 0
LastHeartbeat = 0
cam = None
open_once = False

FUNCTIONS = {
    1: RemoteControl, # 机体控制
    2: KickBall,      # 自动踢球
    3: ColorDetect,   # 颜色识别
    4: VisualPatrol,  # 智能巡线 
    5: ColorTrack,    # 云台跟踪
    6: FaceDetect,    # 人脸识别
    7: ApriltagDetect,# 标签识别
    8: Transport,     # 智能搬运
    9: lab_adjust     # lab阈值调节
}

def doHeartbeat(tmp=()):
    global LastHeartbeat
    LastHeartbeat = time.time() + 7
    return (True, ())

def CurrentEXE():
    global RunningFunc
    return FUNCTIONS[RunningFunc]

def loadFunc(newf):
    global RunningFunc
    new_func = newf[0]

    doHeartbeat()

    if new_func < 1 or new_func > 9:
        return (False,  sys._getframe().f_code.co_name + ": Invalid argument")
    else:
        try:
            if RunningFunc > 1:
                FUNCTIONS[RunningFunc].exit()
            RunningFunc = newf[0]
            if not open_once:
                cam.camera_close()
                cam.camera_open()
            FUNCTIONS[RunningFunc].init()
        except Exception as e:
            print(e)
    return (True, (RunningFunc,))

def unloadFunc(tmp = ()):
    global RunningFunc
    if RunningFunc != 0:
        FUNCTIONS[RunningFunc].exit()
        RunningFunc = 0
    if not open_once:
        cam.camera_close()
    return (True, (0,))

def getLoadedFunc(newf):
    global RunningFunc
    return (True, (RunningFunc,))

def startFunc(tmp):
    global RunningFunc
    FUNCTIONS[RunningFunc].start()
    return (True, (RunningFunc,))

def stopFunc(tmp):
    global RunningFunc
    FUNCTIONS[RunningFunc].stop()
    return (True, (RunningFunc,))

def heartbeatTask():
    global LastHeartbeat
    global RunningFunc
    while True:
        try:
            if LastHeartbeat < time.time():
                if RunningFunc != 0:
                    unloadFunc()
            time.sleep(0.1)
        except Exception as e:
            print(e)

        except KeyboardInterrupt:
            break

threading.Thread(target=heartbeatTask, daemon=True).start()