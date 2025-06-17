#!/usr/bin/python3
# coding=utf8

import sys
import time

import hiwonder.Misc as Misc
import hiwonder.Board as Board
import hiwonder.yaml_handle as yaml_handle

if sys.version_info.major == 2:
    print('Please run this program with python3!')
    sys.exit(0)

# 加载舵机参数
servo_data = None
def load_config():
    global servo_data
    servo_data = yaml_handle.get_yaml_data(yaml_handle.servo_file_path)

load_config()

# 初始化机器人头部舵机位置
def initMove():
    Board.setPWMServoPulse(1, servo_data['servo1'], 500)
    Board.setPWMServoPulse(2, servo_data['servo2'], 500)

# 设置舵机的运动范围
SERVO1_MIN = servo_data['servo1'] - 1400  # 上下舵机最小值
SERVO1_MAX = servo_data['servo1'] + 1400  # 上下舵机最大值
SERVO2_MIN = servo_data['servo2'] - 1400  # 左右舵机最小值
SERVO2_MAX = servo_data['servo2'] + 1400  # 左右舵机最大值

# 当前舵机位置
servo1_pos = servo_data['servo1']
servo2_pos = servo_data['servo2']

# 头部运动控制函数
def headControl(key):
    global servo1_pos, servo2_pos
    step = 20  # 每次运动的步长
    
    if key == '1':  # 向上
        servo1_pos = max(SERVO1_MIN, servo1_pos - step)
        Board.setPWMServoPulse(1, servo1_pos, 30)
    elif key == '2':  # 向下
        servo1_pos = min(SERVO1_MAX, servo1_pos + step)
        Board.setPWMServoPulse(1, servo1_pos, 30)
    elif key == '3':  # 向左
        servo2_pos = max(SERVO2_MIN, servo2_pos - step)
        Board.setPWMServoPulse(2, servo2_pos, 30)
    elif key == '4':  # 向右
        servo2_pos = min(SERVO2_MAX, servo2_pos + step)
        Board.setPWMServoPulse(2, servo2_pos, 30)
    elif key == '5':  # 回到中间位置
        servo1_pos = servo_data['servo1']
        servo2_pos = servo_data['servo2']
        Board.setPWMServoPulse(1, servo1_pos, 30)
        Board.setPWMServoPulse(2, servo2_pos, 30)
    elif key == '6':  # 自定义位置（示例）
        servo1_pos = int(input("输入上下舵机位置: "))
        servo2_pos = int(input("输入左右舵机位置: "))
        servo1_pos = max(SERVO1_MIN, min(SERVO1_MAX, servo1_pos))
        servo2_pos = max(SERVO2_MIN, min(SERVO2_MAX, servo2_pos))
        Board.setPWMServoPulse(1, servo1_pos, 30)
        Board.setPWMServoPulse(2, servo2_pos, 30)
    elif key == '0':  # 退出
        return False
    return True

# 设置舵机位置的函数
def moveServos(servo1, servo2):
    # 确保舵机位置在安全范围内
    servo1 = max(SERVO1_MIN, min(SERVO1_MAX, servo1))
    servo2 = max(SERVO2_MIN, min(SERVO2_MAX, servo2))
    
    # 设置舵机位置
    Board.setPWMServoPulse(1, servo1, 30)
    Board.setPWMServoPulse(2, servo2, 30)

def main():
    initMove()  # 初始化舵机位置

    print("控制说明:")
    print("1: 向上")
    print("2: 向下")
    print("3: 向左")
    print("4: 向右")
    print("5: 回到中间位置")
    print("6: 自定义位置")
    print("0: 退出")

    while True:
        key = input("请输入控制指令: ")
        if not headControl(key):
            break

if __name__ == '__main__':
    main()