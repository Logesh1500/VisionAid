from flask import Flask, jsonify, Response, render_template
import threading
import cv2
import time

app = Flask(__name__)
detector = None  # Will hold our detection instance

class FlaskDetectorWrapper:
    def __init__(self):
        self.frame = None
        self.last_announcements = []
        self.lock = threading.Lock()
        self.running = True

        # Original detection system
        from object_detection import ObjectDetectionVoiceOutput
        self.detector = ObjectDetectionVoiceOutput()
        
        # Start camera thread
        self.camera_thread = threading.Thread(target=self._run_detection)
        self.camera_thread.start()

    def _run_detection(self):
        """Modified detection loop that shares data with Flask"""
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        while self.running:
            ret, frame = cap.read()
            if not ret:
                continue

            # Store latest frame
            with self.lock:
                self.frame = cv2.imencode('.jpg', frame)[1].tobytes()

            # Run detection (modify original code to store announcements)
            results = self.detector.model(frame, conf=0.6, imgsz=640, verbose=False)[0]
            # ... (rest of your detection logic)

            # Store announcements
            if new_announcements:
                with self.lock:
                    self.last_announcements = new_announcements

        cap.release()

    def get_frame(self):
        with self.lock:
            return self.frame

    def get_announcements(self):
        with self.lock:
            return self.last_announcements.copy()

@app.before_first_request
def initialize_detector():
    global detector
    detector = FlaskDetectorWrapper()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    def generate():
        while True:
            frame = detector.get_frame()
            if frame:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            time.sleep(0.1)
    return Response(generate(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/get_announcements')
def get_announcements():
    return jsonify({
        'announcements': detector.get_announcements(),
        'timestamp': time.time()
    })

@app.route('/update_settings', methods=['POST'])
def update_settings():
    # Implement settings update logic
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)