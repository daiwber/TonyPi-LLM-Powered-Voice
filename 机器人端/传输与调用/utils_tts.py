import os
import pyttsx3
import re  # 导入正则表达式模块

import sys
sys.path.append('/home/pi/TonyPi/')
import time
from ActionGroupDict import *
import hiwonder.TTS as TTS
import hiwonder.ASR as ASR
import hiwonder.Board as Board
import hiwonder.ActionGroupControl as AGC
import hiwonder.yaml_handle as yaml_handle
import pygame


# 语音控制
servo_data = yaml_handle.get_yaml_data(yaml_handle.servo_file_path)


tts = TTS.TTS()


# 获取语音识别结果
with open('/home/pi/TonyPi/OpenVINO/temp/ai_response.txt', 'r', encoding='utf-8') as f:
    ai_response = f.read()
print(ai_response)

# 按中英文标点符号分隔
segments = re.split(r'([\。\!\?\，\、\；\：“”“”‘’（）「」『』【】〔〕])', ai_response)
# 去除空字符串并合并分割的标点符号到前一个段落
filtered_segments = []
current_segment = ""
for segment in segments:
    if segment.strip():  # 去除空字符串
        filtered_segments.append(segment.strip())

print("分段后的语音内容：")
for segment in filtered_segments:
    print(segment)

# 执行语音合成和播放
print('TTS Start')
chars_per_minute = 200 # 假设每分钟播放 150 个字符，可以根据实际情况调整
for segment in filtered_segments:
    tts.TTSModuleSpeak('', segment)
    # 估算播放时间（秒）= 字符数 / 每分钟字符数 * 60
    estimated_time = len(segment) / chars_per_minute * 60
    print(f"Estimated time for segment '{segment}': {estimated_time:.2f} seconds")
    time.sleep(estimated_time)  # 等待语音播放完成