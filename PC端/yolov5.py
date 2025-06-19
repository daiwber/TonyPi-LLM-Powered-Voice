#!/usr/bin/python3
from flask import Flask, request, jsonify
import cv2
import numpy as np
import torch
from PIL import Image
import io
import time

app = Flask(__name__)

# 加载YOLOv5模型
model = torch.hub.load('ultralytics/yolov5', 'custom', path='D:\project-file\PyCharm\openvino_tonypi-main\openvino_tonypi-main\TonyPi-API-20241116_no_key\PC代码\yolov5s.pt')  # 替换为你的模型路径
model.conf = 0.5  # 置信度阈值
model.iou = 0.45  # IoU阈值


@app.route('/detect', methods=['POST'])
def detect():
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400

    # 读取图像
    file = request.files['image']
    img_bytes = file.read()
    img = Image.open(io.BytesIO(img_bytes))

    # 转换为OpenCV格式
    img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

    # 使用YOLOv5进行检测
    results = model(img_cv)

    # 解析检测结果
    detections = []
    for *xyxy, conf, cls in results.xyxy[0]:
        label = model.names[int(cls)]
        detections.append({
            'label': label,
            'confidence': float(conf),
            'bbox': [int(x) for x in xyxy]  # x1, y1, x2, y2
        })

    return jsonify({
        'detections': detections,
        'timestamp': time.time()
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)
