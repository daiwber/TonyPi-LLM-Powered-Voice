
from utils_rpi import *
from utils_llm import *
import sys


PI_IP = '192.168.43.229'
#PI_IP = '192.168.149.1'


pipe = load_qwen_ov()

def agent_play():

    speech_result = speech_recognition() # 录音+语音识别

    print('开始调用大模型')
    START_TIME = time.time() # 开始计时

    speech_result_str = str(speech_result)
    print(speech_result_str)
    # 智能体编排动作

    print('调用本地部署的Qwen开源大模型')
    agent_plan_list, ai_response = agent_plan_qwen_ov(pipe, speech_result_str)

    WAIT_TIME = time.time() - START_TIME
    print('大模型耗时 {:.2f} 秒'.format(WAIT_TIME))

    # 将编排好的动作传输给树莓派并运行
    send_txt(agent_plan_list)

    # 遍历agent_plan_list列表
    for item in agent_plan_list:
        print(f"Processing item: {item}")
        if item == "end":
            print("Encountered 'end', exiting the program.")
            sys.exit()  # 使用sys.exit()直接结束程序

    print(ai_response)

    # # 语音合成
    tts(ai_response)
    #

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(PI_IP, username=PI_USER, password=PI_PASSWORD)
        print('开始动作执行')
        stdin, stdout, stderr = client.exec_command('export DISPLAY=:0 && python3 ~/PC端/OpenVINO/utils_robot.py')
        print(stdout.read().decode())
        print(stderr.read().decode())
        print('所有动作完成')
    except Exception as e:
        print("操作出错：", e)
    finally:
        client.close()

while True:
    agent_play()
    

    

