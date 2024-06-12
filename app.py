from flask import Flask, render_template, Response, request, redirect, url_for
import torch
import cv2
import os

app = Flask(__name__)

# Load YOLOv5 model
model = torch.hub.load('ultralytics/yolov5', 'yolov5s')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/live_detection')
def live_detection():
    return render_template('live_detection.html')

@app.route('/upload_video')
def upload_video():
    return render_template('upload_video.html')

@app.route('/detect_video', methods=['POST'])
def detect_video():
    if 'videoFile' not in request.files:
        return redirect(request.url)
    file = request.files['videoFile']
    if file.filename == '':
        return redirect(request.url)
    if file:
        filename = 'uploaded_video.mp4'
        file.save(filename)
        return redirect(url_for('video_result', filename=filename))
    return redirect(url_for('upload_video'))

@app.route('/video_result/<filename>')
def video_result(filename):
    return render_template('video_result.html', filename=filename)

def gen():
    cap = cv2.VideoCapture(0)
    
    # Adjust camera settings
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 5)
    cap.set(cv2.CAP_PROP_FPS, 24)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Perform object detection
        results = model(frame)
        frame = results.render()[0]

        ret, jpeg = cv2.imencode('.jpg', frame)
        frame = jpeg.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')

def process_video(video_path):
    cap = cv2.VideoCapture(video_path)
    output_path = 'static/output_video.mp4'
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, 30.0, (int(cap.get(3)), int(cap.get(4))))

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        results = model(frame)
        out.write(results.render()[0])
    
    cap.release()
    out.release()
    return output_path

@app.route('/video_result_output/<filename>')
def video_result_output(filename):
    video_path = os.path.join('static', filename)
    output_video_path = process_video(video_path)
    return render_template('video_result_output.html', output_video=output_video_path)

if __name__ == '__main__':
    app.run(debug=True)
