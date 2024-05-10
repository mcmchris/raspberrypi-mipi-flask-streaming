#!/usr/bin/env python

import cv2
import time
import sys, getopt
from flask import Flask, render_template, Response
from picamera2 import MappedArray, Picamera2, Preview

normalSize = (1920, 1080)
lowresSize = (1024, 576)

app = Flask(__name__, static_folder='templates/assets')

def now():
    return round(time.time() * 1000)

def get_webcams():
    port_ids = []
    for port in range(5):
        print("Looking for a camera in port %s:" %port)
        camera = cv2.VideoCapture(port)
        if camera.isOpened():
            ret = camera.read()[0]
            if ret:
                backendName =camera.getBackendName()
                w = camera.get(3)
                h = camera.get(4)
                print("Camera %s (%s x %s) found in port %s " %(backendName,h,w, port))
                port_ids.append(port)
            camera.release()
    return port_ids

def help():
    print('python classify.py <path_to_model.eim> <Camera port ID, only required when more than 1 camera is present>')

def main(argv):

    picam2 = Picamera2()
    picam2.start_preview(Preview.DRM, x=0, y=0, width=1920, height=1080)
    config = picam2.create_preview_configuration(main={"size": normalSize},
                                                 lores={"size": lowresSize, "format": "YUV420"})
    picam2.configure(config)

    stride = picam2.stream_configuration("lores")["stride"]
    #picam2.post_callback = DrawRectangles

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