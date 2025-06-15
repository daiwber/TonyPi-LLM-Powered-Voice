
import speech_recognition
import paramiko
from scp import SCPClient
import numpy as np
import pyaudio
import whisper
import time


PI_IP = "192.168.43.229"
#PI_IP = '192.168.149.1'
PI_USER = "pi"
PI_PASSWORD = "raspberry"
LOCAL_FILE_PATH = "temp/agent_plan.txt"
REMOTE_FILE_PATH = "/home/pi/PC端/OpenVINO/temp/agent_plan.txt"

REMOTE_SPEECH_FILE = "/home/pi/PC端/OpenVINO/temp/speech_recognition.txt"
LOCAL_SPEECH_FILE = "temp/speech_recognition.txt"
local_file_path = 'D:/project-file/PyCharm/openvino_tonypi-main/openvino_tonypi-main/temp/speech_recognition.txt'

def play_welcome():
    print('语音指令')
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(PI_IP, username=PI_USER, password=PI_PASSWORD)
        #stdin, stdout, stderr = client.exec_command('python3 /home/pi/PC端/Functions/lab.py')
        stdin, stdout, stderr = client.exec_command('cvlc --start-time=0 --stop-time=10 /home/pi/bershuang.mp3 vlc://quit')
        print(stdout.read().decode())
        print(stderr.read().decode())
    except Exception as e:
        print("SSH 连接或命令执行出错：", e)
    finally:
        client.close()



# 语音识别
def speech_recognition():

    # 加载模型
    model = whisper.load_model("medium")
    # “tiny”“base”“small”“medium”“large”

    # 配置音频捕获
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    RECORD_SECONDS = 5

    p = pyaudio.PyAudio()

    # 打开音频流
    stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK
    )

    frames = []
    print("开始...")
    start_time = time.time()

    # 录音
    for _ in range(int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)
        elapsed_time = time.time() - start_time
        progress = int((elapsed_time / RECORD_SECONDS) * 100)
        print(f"\r录音进度: [{'#' * (progress // 10)}{'-' * (10 - progress // 10)}] {progress}%", end="")

    print("\n录音结束")
    stream.stop_stream()
    stream.close()

    # 将音频帧转换为 NumPy 数组
    audio_data = np.frombuffer(b''.join(frames), dtype=np.int16).flatten().astype(np.float32) / 32768.0

    # 进行语音识别
    result = model.transcribe(audio_data, language='zh')
    transcription = result["text"]
    print(transcription)

    # 将识别结果写入本地文件
    with open("识别结果.txt", "w", encoding="utf-8") as f:
        f.write(transcription)

    # 释放资源
    p.terminate()
    return transcription


def tts(ai_response):
    # 写入文件
    with open('D:/project-file/PyCharm/openvino_tonypi-main/openvino_tonypi-main/temp/ai_response.txt', 'w', encoding='utf-8') as f:
        f.write(ai_response)
        print("ai_response")
        print(ai_response)

    # 传到开发板
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        # 连接远程设备
        client.connect(PI_IP, username=PI_USER, password=PI_PASSWORD)

        # 创建 SCP 客户端并传输文件
        with SCPClient(client.get_transport()) as scp:
            scp.put('D:/project-file/PyCharm/openvino_tonypi-main/openvino_tonypi-main/temp/ai_response.txt', '/home/pi/PC端/OpenVINO/temp')
            print('文件传输成功！')

        # 执行远程命令
        print('开始语音合成')
        stdin, stdout, stderr = client.exec_command('python3 /home/pi/PC端/OpenVINO/utils_tts.py')
        print(stdout.read().decode())
        print(stderr.read().decode())
    except Exception as e:
        print("操作出错：", e)
    finally:
        client.close()


# 函数：将编排好的动作传输给树莓派并运行
def send_txt(agent_plan_list):
    agent_plan_str = str(agent_plan_list)
    # 写入txt文件
    with open('temp/agent_plan.txt', 'w') as f:
        f.write(agent_plan_str)

    print('开始动作编排txt文件传输')
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        # 连接远程设备
        client.connect(PI_IP, username=PI_USER, password=PI_PASSWORD)

        # 创建 SCP 客户端
        with SCPClient(client.get_transport()) as scp:
            scp.put(LOCAL_FILE_PATH, REMOTE_FILE_PATH)
            print('文件传输成功！')
    except Exception as e:
        print("文件传输出错：", e)
    finally:
        client.close()


