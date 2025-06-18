
import pygame

import threading

import dashscope
from dashscope import SpeechSynthesizer
import pygame
import time

# 设置API Key
dashscope.api_key = "sk-6964cxxxxx"
file_path = '/home/pi/TonyPi/OpenVINO/output.txt'

# 读取文件内容到变量
with open(file_path, 'r', encoding='utf-8') as file:
    text_content = file.read()

# 新版调用方式：参数在 .call() 中传递，而非构造函数
synthesizer = SpeechSynthesizer()  # 无参初始化
response = synthesizer.call(
    model="sambert-zhichu-v1",  # 模型名
    voice="longcheng",       # 发音人
    text=text_content
)


audio = response.get_audio_data()

with open('/home/pi/TonyPi/OpenVINO/skt.wav', 'wb') as f:
    f.write(audio)
    
music_file = "/home/pi/TonyPi/OpenVINO/skt.wav"

pygame.mixer.init()
try:
    pygame.mixer.music.load(music_file)  # 使用绝对路径
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        time.sleep(0.1)
except Exception as e:
    print("播放失败:", str(e))


#import subprocess
#subprocess.run(["mpg123", "/home/pi/TonyPi/OpenVINO/skt.wav"])
