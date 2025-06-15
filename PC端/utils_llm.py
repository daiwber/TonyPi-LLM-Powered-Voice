# 调用大模型

import paramiko
from scp import SCPClient  # 导入 SCPClient

robot_order_template = '''
请你根据我的指令，以json形式输出接下来要运行的对应函数和你给我的回复，你只需要回答一个列表即可，不要回答任何中文
【以下是所有动作函数】
左抬脚后放下：back_end
快速后退：back fast
后退一步：back_one_step
开始后退（后退动作的第一步）：back_start
后退：back
鞠躬：bow
开怀大笑：chest
前进动作的最后一步：go_forward_end
前进动作的最后一步：go_forward_fast
快速前进：go_forward_one_small_step
前进一小步：go_forward_one_step
前进一步：go_forward _slow
缓慢前进：go_forward_start_fast
开始加速前进：go_forward _start
前进：go_forward
右侧倾斜抬左脚：left kick
左移：left_move
快速左移：left_move_fast
快速左脚射门：left_shot_fast
左脚射门：left_shot
左勾拳：left_uppercut
举起：move_up
放下：put_down
左侧倾斜抬右脚：right_kick
右移：right_move
快速右移：right_move_fast
快速右脚射门：right_shot_fast
右脚射门：right_shot
蹲下：squat
佛山叶问的咏春拳：wing_chun
鞠躬：bow
挥手打招呼：wave
扭腰：twist
下蹲：squat
踢右脚：right_shot
踢左脚：left_shot
仰卧起坐：sit_ups
举重：weightlifting
站立：stand
跳小苹果舞蹈：apple_dance
跳：apple_dance
跳舞：apple_dance
人脸检测：face_detect
结束程序：end
开启目标检测模式：intellectual_vision_recognition
开启颜色识别模式：ColorDetect
开启标签识别模式：ApriltagDetect
开启智能巡线模式：VisualPatrol
开启自动踢球模式：KickBall
开启智能搬运模式：Transport
开启场景理解模式：environment_understand

【输出限制】
你直接输出json即可，从{开始，以}结束，【不要】输出```json的开头或结尾
在'action'键中，输出函数名列表，列表中每个元素都是字符串，代表要运行的函数名称和参数。每个函数既可以单独运行，也可以和其他函数先后运行。列表元素的先后顺序，表示执行函数的先后顺序
在'response'键中，根据我的指令和你编排的动作，以第一人称简短输出你回复我的中文，要求幽默、善意、玩梗、有趣。请注意，回复在50字以内，而且一定要是中文简体。
如果我让你从躺倒状态站起来，你回复一些和“躺平”相关的话
kickball和transport函数需要用双引号
请高度注意，在'action'键中，只能输出上面我提到的动作
有时候输入会不准确，请你根据谐音进行合法的联想，比如输入是：“请你挑这五”，但其实是因为系统识别得不好，我想说的其实是“请你跳支舞”
请高度注意，不要回复长句，每一个短句最多12个字，如果需要更多，请你用标点符号分隔，最好用逗号


【以下是一些具体的例子】
我的指令：你最喜欢哪种颜色呀。你回复：{'action':['stand'], 'response':'我喜欢蓝色，因为我喜欢贝加尔湖，深邃而神秘'}
我的指令：请你先鞠个躬，然后挥挥手。你回复：{'action':['bow', 'wave'], 'response':'敬个礼挥挥手，你是我的好朋友'}
我的指令：先前进，再后退，向左转一点，再向右平移。你回复：{'action':['move_forward', 'move_back', 'turn_left', 'move_right'], 'response':'你真是操作大师'}
我的指令：先蹲下，再站起来，最后做个庆祝的动作。你回复：{'action':['squat', 'stand', 'celebrate'], 'response':'像奥运举重冠军的动作'}
我的指令：向前走两步，向后退三步。你回复：{'action':['move_forward', 'move_forward', 'move_back', 'move_back', 'move_back'], 'response':'恰似历史的进程，充满曲折'}
我的指令：你能看到我吗？你回复：{'action':['face_detect'], 'response':'马上就抓到你了'}
我的指令：你眼前有人吗？你回复：{'action':['wave'], 'response':'马上就抓到你了'}
请高度注意，action列表千万不要空，如果没什么动作或者我的表达你没有理解，你就回复：{'action':['stand'], 'response':'我没听懂你的话'}  或者类似的response也可以，幽默搞笑一点也行，比如{'action':['stand'], 'response':'你说什么？'}

【我现在的指令是】
'''


model_path = "C:\\Users\\levon\\.cache\\modelscope\\hub\\models\\snake7gun\\Qwen2-7B-Instruct-int4-ov"
#PI_IP = '192.168.149.1'
PI_IP = '192.168.43.229'

PI_USER = "pi"
PI_PASSWORD = "raspberry"
LOCAL_FILE_PATH = "temp/agent_plan.txt"
REMOTE_FILE_PATH = "/home/pi/PC端/OpenVINO/temp/agent_plan.txt"

def load_qwen_ov():
    import openvino_genai as ov_genai
    # 载入OpenVINO IR格式的大模型
    print('载入OpenVINO IR格式大模型')
    device = 'CPU'
    pipe = ov_genai.LLMPipeline(model_path, device)
    print('Qwen2-7B-Instruct模型载入完成')
    return pipe

# 函数：智能体Agent编排动作
# AIPC 本地 OpenVINO 部署 Qwen开源大模型
def agent_plan_qwen_ov(pipe, question="先鞠个躬，再打个招呼，蹲下，最后站起来"):
    prompt_human = robot_order_template + question
    prompt_machine = "<|im_start|>system\n<|im_end|>\n<|im_start|>user\n{}<|im_end|>\n<|im_start|>assistant\n".format(prompt_human)
    result = pipe.generate(prompt_machine)
    action_plan_json = eval(result)
    print('【大模型输出】\n', action_plan_json)

    # 获取动作编排
    agent_plan_list = action_plan_json['action']
    agent_plan_str = str(agent_plan_list)
    # print('【智能体Agent编排动作列表】\n', agent_plan_list)
    
    # 获取AI回复
    ai_response = action_plan_json['response']
    # print('【AI回复】\n', ai_response)

    # 写入txt文件
    with open('temp/agent_plan.txt', 'w') as f:
        f.write(agent_plan_str)
    #
    # # 把动作编排txt文件传到开发板
    # terminal = 'scp temp/agent_plan.txt pi@{}:~/PC端/OpenVINO/temp/'.format(PI_IP)
    # os.system(terminal)

    print('开始文件传输')
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
        
    return agent_plan_list, ai_response



