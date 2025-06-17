#!/usr/bin/python3
# coding=utf8
import sys
import hiwonder.Board as Board
import hiwonder.ActionGroupControl as AGC

if sys.version_info.major == 2:
    print('Please run this program with python3!')
    sys.exit(0)

# 初始位置
def initMove():
    Board.setPWMServoPulse(1, 1500, 500)
    Board.setPWMServoPulse(2, 1500, 500)
    AGC.runActionGroup('stand_slow')

def reset():
    return None

def init():
    initMove()
    print("RemoteControl Init")
    return None

def start():
    print("RemoteControl Start")
    return None

def stop():
    print("RemoteControl Stop")
    return None

def exit():
    print("RemoteControl Exit")
    return None

def run(img):
    return img
