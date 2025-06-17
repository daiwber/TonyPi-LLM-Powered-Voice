import os
import json
import pyaudio
from vosk import Model, KaldiRecognizer


def load_model(model_path="/home/pi/TonyPi/OpenVINO/vosk-model-small-cn-0.22"):
    """加载Vosk中文语音识别模型"""
    if not os.path.exists(model_path):
        print(f"错误：模型目录 '{model_path}' 不存在")
        print("请从 https://alphacephei.com/vosk/models   下载中文模型并解压")
        exit(1)
    return Model(model_path)


def recognize_speech(model, record_seconds=5):
    """使用Vosk进行语音识别"""
    # 音频参数
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 48000  # 设置为麦克风支持的采样率，例如 16000 Hz
    CHUNK = 4096

    p = pyaudio.PyAudio()

    # 查看可用的音频设备
    for i in range(p.get_device_count()):
        dev = p.get_device_info_by_index(i)
        print(f"设备索引: {i}, 设备名称: {dev['name']}")

    # 指定音频设备索引
    input_device_index = 2  # 根据 arecord -l 的输出设置为 2

    print(f"使用音频设备: {p.get_device_info_by_index(input_device_index)['name']} (索引: {input_device_index})")

    # 创建音频流 - 明确指定设备
    stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        input_device_index=input_device_index,
        frames_per_buffer=CHUNK
    )

    recognizer = KaldiRecognizer(model, RATE)

    print(f"开始录音({record_seconds}秒)...")

    # 录音并识别
    for _ in range(0, int(RATE / CHUNK * record_seconds)):
        data = stream.read(CHUNK, exception_on_overflow=False)
        if recognizer.AcceptWaveform(data):
            pass  # 可以实时获取部分结果

    # 获取最终结果
    result = recognizer.FinalResult()
    stream.stop_stream()
    stream.close()
    p.terminate()

    return json.loads(result)["text"]


def main():
    # 1. 加载模型
    model = load_model()

    # 2. 进行语音识别
    try:
        text = recognize_speech(model, record_seconds=5)
        print(f"识别结果: {text}")

        # 3. 保存结果到文件
        with open("/home/pi/TonyPi/OpenVINO/temp/speech_recognition.txt", "w", encoding="utf-8") as f:
            f.write(text)
            print("结果已保存到 recognized_text.txt")

    except Exception as e:
        print(f"发生错误: {e}")


if __name__ == "__main__":
    main()

