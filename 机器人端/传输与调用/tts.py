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
with open('/home/pi/TonyPi/OpenVINO/output.txt', 'r', encoding='utf-8') as f:
    ai_response = f.read()
print(ai_response)

# ai_response = "生动地呈现出一个正在焦急等待工作录用通知或其他录取通知的状态。这张图很容易让人产生共鸣在求职求学等场景中人们满怀期待地提交申请"

# 去掉标点符号
ai_response_no_punctuation = re.sub(r'[\.\!\?\，\、\；\：“”“”‘’（）「」『』【】〔〕]', '', ai_response)
print("去掉标点后的语音内容：")
print(ai_response_no_punctuation)

# 每九个字切分成一段
segments = []
current_segment = ""
for i, char in enumerate(ai_response_no_punctuation):
    current_segment += char
    if (i + 1) % 11 == 0:  # 每九个字切分
        segments.append(current_segment)
        current_segment = ""
if current_segment:  # 添加剩余不足九个字的部分
    segments.append(current_segment)

print("切分后的语音内容：")
for segment in segments:
    print(segment)

# 执行语音合成和播放
print('TTS Start')
chars_per_minute = 300  # 假设每分钟播放 200 个字符，可以根据实际情况调整
for segment in segments:
    tts.TTSModuleSpeak('', segment)
    # 估算播放时间（秒）= 字符数 / 每分钟字符数 * 60
    estimated_time = len(segment) / chars_per_minute * 60
    print(f"Estimated time for segment '{segment}': {estimated_time:.2f} seconds")
    time.sleep(estimated_time)  # 等待语音播放完成
