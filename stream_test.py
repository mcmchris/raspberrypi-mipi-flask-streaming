#!/usr/bin/env python

import cv2
import sys
import numpy as np
from flask import Flask, render_template, Response
from picamera2 import Picamera2, Preview

# Full sensor resolution for IMX219
sensor_full = (3280, 2464)

# Target output resolution (aspect-ratio preserved with padding)
output_size = (191, 191)

# Flask app
app = Flask(__name__, static_folder='templates/assets')


def resize_and_pad(img, target_size=(640, 480)):
    h, w = img.shape[:2]
    target_w, target_h = target_size
    scale = min(target_w / w, target_h / h)
    new_w = int(w * scale)
    new_h = int(h * scale)
    resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

    # Compute padding
    top = (target_h - new_h) // 2
    bottom = target_h - new_h - top
    left = (target_w - new_w) // 2
    right = target_w - new_w - left

    # Pad with black bars
    padded = cv2.copyMakeBorder(
        resized, top, bottom, left, right,
        borderType=cv2.BORDER_CONSTANT, value=[0, 0, 0]
    )
    return padded


def generate_frames():
    picam2 = Picamera2()

    # Disable HDMI preview
    picam2.start_preview(Preview.NULL)

    # Full resolution for best field of view
    config = picam2.create_preview_configuration(
        main={"size": sensor_full, "format": "RGB888"}
    )
    picam2.configure(config)
    picam2.start()

    while True:
        full_frame = picam2.capture_array()

        # Resize and pad to maintain aspect ratio
        processed_frame = resize_and_pad(full_frame, output_size)

        # Encode frame as JPEG
        ret, buffer = cv2.imencode('.jpg', processed_frame)
        if not ret:
            continue
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/')
def index():
    return render_template('streaming.html')


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=4912, debug=False)
