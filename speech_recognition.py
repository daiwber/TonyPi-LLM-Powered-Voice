
import speech_recognition as sr
import paramiko
from scp import SCPClient

PI_IP = "192.168.43.229"
PI_USER = "pi"
PI_PASSWORD = "raspberry"
LOCAL_FILE_PATH = "temp/agent_plan.txt"
REMOTE_FILE_PATH = "/home/pi/TonyPi/OpenVINO/temp/agent_plan.txt"

REMOTE_SPEECH_FILE = "/home/pi/TonyPi/OpenVINO/temp/speech_recognition.txt"
LOCAL_SPEECH_FILE = "temp/speech_recognition.txt"
local_file_path = 'D:/project-file/PyCharm/openvino_tonypi-main/openvino_tonypi-main/temp/speech_recognition.txt'

# 语音识别
def speech_recognition():
    '''
    使用 Whisper 进行语音识别
    '''
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("请说话...")
        audio = recognizer.listen(source)
        try:
            text = recognizer.recognize_whisper(audio, language="zh")
            print(f"识别结果：{text}")
        except Exception as e:
            print(f"识别失败：{e}")

        # 将识别结果写入本地文件
        with open(local_file_path, 'w', encoding='utf-8') as f:
            f.write(text)
            print('语音识别结果已写入本地txt文件')

    return text


# 发送文件到远程树莓派
def send_txt1():
    # 配置远程树莓派的信息
    PI_USER = 'pi'
    PI_IP = '192.168.43.229'
    PI_PASSWORD = "raspberry"
    REMOTE_FILE_PATH = '/home/pi/TonyPi/OpenVINO/temp/speech_recognition.txt'

    print('开始动作编排txt文件传输')
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        # 连接远程设备
        client.connect(PI_IP, username=PI_USER, password=PI_PASSWORD)

        # 创建 SCP 客户端
        with SCPClient(client.get_transport()) as scp:
            scp.put(local_file_path, REMOTE_FILE_PATH)
            print('文件传输成功！')
    except Exception as e:
        print("文件传输出错：", e)
    finally:
        client.close()


def asr_aipc():
    # 语音识别
    text = speech_recognition()
    # 发送文件到远程树莓派
    send_txt1()

    return text