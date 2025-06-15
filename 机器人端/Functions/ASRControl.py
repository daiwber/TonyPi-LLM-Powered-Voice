#!/usr/bin/python3
# coding=utf8
import sys
sys.path.append('/home/pi/TonyPi/')
import time
from ActionGroupDict import *
import hiwonder.TTS as TTS
import hiwonder.ASR as ASR
import hiwonder.Board as Board
import hiwonder.ActionGroupControl as AGC
import hiwonder.yaml_handle as yaml_handle

# 语音控制
servo_data = yaml_handle.get_yaml_data(yaml_handle.servo_file_path)

try:
    asr = ASR.ASR()
    tts = TTS.TTS()

    asr.eraseWords()
    asr.setMode(2)
    asr.addWords(1, 'kai shi')
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

    data = asr.getResult()
    Board.setPWMServoPulse(1, 1500, 500)
    Board.setPWMServoPulse(2, servo_data['servo2'], 500)    
    AGC.runActionGroup('stand')
    action_finish = True
    tts.TTSModuleSpeak('[h0][v10][m3]', '准备就绪')
    print('''当前为口令模式，每次说指令前均需要说口令来激活
口令：开始
指令2：往前走
指令2：前进
指令2：直走
指令3：往后退
指令4：向左移
指令5：向右移
''')
    time.sleep(2)
except:
    print('传感器初始化出错')

while True:
    data = asr.getResult()
    if data:
        print('result:', data)
        tts.TTSModuleSpeak('', '收到')
        time.sleep(1)
        AGC.runActionGroup(action_group_dict[str(data - 1)], 1 ,True)
    time.sleep(0.01)
