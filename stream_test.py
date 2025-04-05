#!/usr/bin/env python

import cv2
import time
import sys, getopt
from flask import Flask, render_template, Response
from picamera2 import MappedArray, Picamera2, Preview

normalSize = (640, 480)   # original camera resolution preview
lowresSize = (640, 480)    # low resolution for the streaming

app = Flask(__name__, static_folder='templates/assets')

def main(argv):

    picam2 = Picamera2()
    #picam2.start_preview(Preview.DRM, x=0, y=0, width=1920, height=1080) # uncomment this line if you have an HDMI display connected and want to preview the streaming on it.
    picam2.start_preview(Preview.NULL)  # disable HDMI preview. Comment this if you have an HDMI display
    config = picam2.create_preview_configuration(main={"size": normalSize},lores={"size": lowresSize, "format": "YUV420"})
    picam2.configure(config)

    stride = picam2.stream_configuration("lores")["stride"]

    picam2.start()

    while True:
        buffer = picam2.capture_array("lores")
        rgb = cv2.cvtColor(buffer, cv2.COLOR_YUV420p2RGB)
        #grey = buffer[:stride * lowresSize[1]].reshape((lowresSize[1], stride))
        (ret, buffer) = cv2.imencode('.jpg', rgb) #change rgb to grey for grayscale streaming
        if not ret:
            continue
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # concat frame one by one and show result


@app.route('/video_feed')
def video_feed():
    #Video streaming route. Put this in the src attribute of an img tag
    return Response(main(sys.argv[1:]), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/')
def index():
    return render_template('streaming.html')

if __name__ == "__main__":
   #main(sys.argv[1:])
   app.run(host="0.0.0.0", port=4912, debug=True) 