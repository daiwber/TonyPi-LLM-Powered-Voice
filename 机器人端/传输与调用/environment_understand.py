#!/usr/bin/python
# -*- coding: utf-8 -*-
from openai import OpenAI
import base64
import pyttsx3
from gtts import gTTS
import os

#!/usr/bin/python3
# coding=utf8
import cv2
import time
import hiwonder.Camera as Camera
import hiwonder.yaml_handle as yaml_handle

#!/usr/bin/python3
# coding=utf8
import cv2
import time
import hiwonder.Camera as Camera
import hiwonder.yaml_handle as yaml_handle
import os
import sys

def capture_frame(save_path):
    try:
        # 读取摄像头配置
        config = yaml_handle.get_yaml_data('/boot/camera_setting.yaml')
        open_once = config['open_once']
        print(f"摄像头配置: open_once={open_once}")
        
        if open_once:
            print("尝试通过MJPG流访问摄像头...")
            # 清理URL格式
            url = 'http://127.0.0.1:8080/?action=stream'
            my_camera = cv2.VideoCapture(url)
            if not my_camera.isOpened():
                print(f"无法打开MJPG流: {url}")
                return False
        else:
            print("尝试直接访问摄像头...")
            my_camera = Camera.Camera()
            try:
                my_camera.camera_open()
                print("摄像头直接访问成功")
            except Exception as e:
                print(f"摄像头直接访问失败: {e}")
                return False
        
        # 等待摄像头初始化
        print("摄像头预热中...")
        time.sleep(1.0)
        
        # 尝试读取多帧以确保获取有效图像
        for i in range(5):
            ret, frame = my_camera.read()
            if ret and frame is not None:
                print(f"成功捕获第{i+1}帧图像")
                break
            else:
                print(f"第{i+1}次尝试获取图像失败")
                time.sleep(0.2)
        else:
            print("多次尝试后仍无法获取图像帧")
            return False
        
        # 保存图像
        cv2.imwrite(save_path, frame)
        print(f"图像已保存至: {save_path}")
        
        return True
    
    except Exception as e:
        print(f"捕获图像过程中发生异常: {e}")
        return False
    finally:
        # 确保关闭摄像头
        try:
            if open_once:
                my_camera.release()
                print("MJPG流已释放")
            else:
                my_camera.camera_close()
                print("摄像头已关闭")
        except:
            pass


# 设置保存路径（根据需求修改）
save_path = "/home/pi/TonyPi/OpenVINO/kk.jpg"
    
# 捕获并保存图像
if capture_frame(save_path):
    print("图像捕获成功!")
else:
    print("图像捕获失败")




# 将字节串转换为字符串
def file_to_base64(file_path):
    with open(file_path, "rb") as file:
        file_content = file.read()
        base64_encoded = base64.b64encode(file_content)
        return base64_encoded.decode('utf-8')


base_url = 'https://api.mindcraft.com.cn/v1/'
api_key = 'MC-FC7Bxxxxxxxx'

client = OpenAI(base_url=base_url, api_key=api_key)

params = {
    "model": "Doubao-1.5-vision-pro-32k",
    "messages": [
        {
            "role": "user",
            "content": [
                # 使用 base64 编码传输
                {
                    'type': 'image',
                    'source': {
                        'data': file_to_base64(
                            r'/home/pi/TonyPi/OpenVINO/kk.jpg')
                    },
                },
                {
                    'type': 'text',
                    'text': '假设你是一个机器人，图片是你识别到的，请你介绍一下你所看到的场景',
                },
            ]
        }
    ],
    "temperature": 0.2,
    "max_tokens": 4000,
    "stream": True
}

response = client.chat.completions.create(
    model=params.get("model"),
    messages=params.get("messages"),
    temperature=params.get("temperature"),
    max_tokens=params.get("max_tokens"),
    stream=params.get("stream"),
)

# 收集所有 content 内容
full_content = ""
for i in response:
    content = i.choices[0].delta.content
    if not content:
        if i.usage:
            print('\n请求花销usage:', i.usage)
        continue
    # print(content, end='', flush=True)
    print(content)
    full_content += content

print(full_content)

# 指定要写入的文件路径
file_path = "/home/pi/TonyPi/OpenVINO/output.txt"

# 将内容写入文件
with open(file_path, "w", encoding="utf-8") as file:
    file.write(full_content)

print(f"内容已写入到 {file_path}")



terminal = 'python3 /home/pi/TonyPi/OpenVINO/tts_api.py'
print('terminal', terminal)
os.system(terminal)

