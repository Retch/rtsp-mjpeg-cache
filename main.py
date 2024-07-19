import cv2
import os
import time
import subprocess
from threading import Thread, Lock
from datetime import datetime as dt
from flask import Flask, Response

RTSP_URL = str(os.getenv('RTSP_URL', 'rtsp://127.0.0.1'))
RTSP_HOST = str(os.getenv('RTSP_HOST', '127.0.0.1'))
MJPEG_FEED = str(os.getenv('MJPEG_FEED', 'mjpeg'))

app = Flask(__name__)
lock = Lock()

last_frame = None

def is_host_reachable():
    try:
        result = subprocess.run(['ping', '-c', '1', '-W', '1', RTSP_HOST], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.returncode == 0
    except Exception as e:
        print(f"Error pinging host: {e}")
        return False

def fetch_rtsp_stream(rtsp_url):
    global last_frame

    while True:
        if not is_host_reachable():
            print(str(dt.now()).split(".")[0] + " - Host is not reachable. Retrying...")
            time.sleep(1)
            continue

        cap = cv2.VideoCapture()

        def open_stream():
            cap.open(rtsp_url)

        thread = Thread(target=open_stream)
        thread.start()
        thread.join(timeout=5)

        if not cap.isOpened():
            print("Failed to open RTSP stream within 5 seconds. Retrying...")
            cap.release()
            time.sleep(1)
            continue

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                print("Failed to read frame from RTSP stream. Retrying...")
                break

            with lock:
                last_frame = frame

        cap.release()
        time.sleep(1)

def generate_mjpeg_stream():
    global last_frame
    while True:
        with lock:
            if last_frame is None:
                continue

            ret, jpeg = cv2.imencode('.jpg', last_frame)
            if not ret:
                continue

            frame = jpeg.tobytes()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
        time.sleep(0.1)

@app.route('/' + MJPEG_FEED)
def video_feed():
    return Response(generate_mjpeg_stream(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':  
    rtsp_thread = Thread(target=fetch_rtsp_stream, args=(RTSP_URL,))
    rtsp_thread.daemon = True
    rtsp_thread.start()
    
    app.run(host='0.0.0.0', port=5000)
