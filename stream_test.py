#!/usr/bin/env python

import cv2
import sys
from flask import Flask, render_template, Response
from picamera2 import Picamera2, Preview

# Full sensor resolution for IMX219 (still mode)
sensor_full = (3280, 2464)

# Target resolution for streaming
output_size = (191, 191)

# Initialize Flask app
app = Flask(__name__, static_folder='templates/assets')

def generate_frames():
    picam2 = Picamera2()

    # Optional: show preview on HDMI or not
    picam2.start_preview(Preview.NULL)

    # Use full resolution for main stream to avoid cropping
    config = picam2.create_preview_configuration(
        main={"size": sensor_full, "format": "RGB888"}
    )
    picam2.configure(config)
    picam2.start()

    while True:
        # Capture full resolution image
        full_frame = picam2.capture_array()

        # Resize to 640x480 preserving full FOV
        resized_frame = cv2.resize(full_frame, output_size, interpolation=cv2.INTER_AREA)

        # Encode as JPEG
        ret, buffer = cv2.imencode('.jpg', resized_frame)
        if not ret:
            continue
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    # Streaming route
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def index():
    return render_template('streaming.html')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=4912, debug=True)
