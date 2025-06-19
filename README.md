# TonyPi-LLM-Powered-Voice

## 仓库介绍
本仓库旨在对 TonyPi 人形机器人进行功能升级，通过接入大模型技术，实现语音交互控制。我们致力于优化现有功能，打造更智能、更便捷的人机交互体验。

## 效果演示
https://www.bilibili.com/video/BV1xhNbzpEDY?vd_source=6676309e77ea6c150e8afa91e21ef38e

## 功能介绍

### 机器人端功能

  * **自动踢球** ：通过摄像头识别足球并执行踢球动作（`KickBall.py`）。
  * **颜色识别** ：识别特定颜色物体，并可播报识别结果（`ColorDetect.py`、`ColorDetectAndTTS.py`）。
  * **智能巡线** ：沿预设线路自主行驶（`VisualPatrol.py`）。
  * **颜色追踪** ：追踪指定颜色的物体（`ColorTrack.py`）。
  * **人脸识别** ：检测并识别图像中的人脸（`FaceDetect.py`）。
  * **标签识别** ：识别 AprilTag 标签并执行对应动作（`ApriltagDetect.py`）。
  * **语音控制** ：通过语音指令控制机器人执行动作（`ASRControl.py`、`Transport_ASR.py`）。
  * **智能搬运** ：结合颜色识别和路径规划，实现物体的智能搬运（`Transport.py`）。
  * **物体追踪** ：追踪特定物体并执行跟随动作（`Follow.py`）。

### PC 端功能

  * **目标检测服务器** ：部署 YOLOv5 模型，提供物体检测服务（`Yolov5.py`）。
  * **语音识别与控制** ：通过语音指令调用大模型，生成决策并传输给机器人执行（`Agent_go.py`）。
  * **大模型应用** ：利用大模型进行语音合成和环境理解（`Utils_llm.py`）。

## 使用方法

### 环境准备

  * **树莓派配置** ：安装 Python 3 及必备库，如 opencv-python、numpy、pytorch、flask 等；配置摄像头和麦克风；设置环境变量（如 API 密钥等）。
  * **PC 端配置** ：同样需要安装 Python 3 和相关库，并配置目标检测服务器（`Yolov5.py`），确保其与机器人端网络连通。

### 启动项目

  1. 启动 PC 端目标检测服务器：`python3 Yolov5.py`。
  2. 启动机器人端功能：根据需要运行不同的功能脚本，例如`python3 Detect.py`，或者通过语音控制脚本启动其他功能：`python3 ASRControl.py`。
  3. 执行特定任务：通过语音指令控制机器人执行动作，或运行特定功能脚本以完成颜色识别、物体检测等任务。

## 安装步骤

  1. 克隆项目仓库：
     * `git clone https://github.com/daiwber/TonyPi-LLM-Powered-Voice.git`
     * `cd TonyPi-LLM-Powered-Voice`

  2. 安装依赖：`pip3 install -r requirements.txt`。
  3. 配置环境：设置树莓派的摄像头和麦克风权限，配置 OpenAI API 密钥和其他必要环境变量。
  4. 下载模型文件：下载 YOLOv5 模型文件并放置在指定路径，下载语音合成相关的模型和配置文件。

## 动作组文件
【TonyPi 机器人小苹果舞蹈】  apple_dance/d6a.tar

## 部分代码说明
robot.py 通过多线程来同时播放音乐和执行舞蹈动作，实现动作和音乐的同步。

## 免责声明  
本项目仅供学习参考，**严禁商用**。

若仓库中的文件无意侵犯了您的权益，或存在任何不妥之处，我们深表歉意！

同时请[邮件联系我](mailto:1846327762@qq.com)，我会第一时间核实并处理。

