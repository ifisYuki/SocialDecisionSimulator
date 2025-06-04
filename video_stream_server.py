from flask import Flask, Response, render_template_string
from flask_cors import CORS
import cv2
import threading
import time
import queue
import numpy as np

app = Flask(__name__)
CORS(app)  # 允许跨域访问

# 全局变量
latest_frame = None
frame_lock = threading.Lock()
frame_queue = queue.Queue(maxsize=2)

class VideoStreamServer:
    def __init__(self):
        self.frame = None
        self.lock = threading.Lock()
        
    def update_frame(self, frame):
        """更新最新的检测画面"""
        global latest_frame
        with frame_lock:
            latest_frame = frame.copy()
            
        # 非阻塞方式更新队列
        try:
            if not frame_queue.full():
                frame_queue.put(frame.copy(), block=False)
        except:
            pass
    
    def get_frame(self):
        """获取最新画面并编码为JPEG"""
        global latest_frame
        
        if latest_frame is None:
            # 创建一个黑色画面作为默认
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(frame, 'Waiting for YOLO stream...', (50, 240), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        else:
            with frame_lock:
                frame = latest_frame.copy()
        
        # 编码为JPEG
        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if ret:
            return buffer.tobytes()
        return None

# 创建视频流服务器实例
video_server = VideoStreamServer()

def generate_frames():
    """生成视频流"""
    while True:
        frame_bytes = video_server.get_frame()
        if frame_bytes:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        time.sleep(0.033)  # 约30FPS

@app.route('/video_feed')
def video_feed():
    """视频流端点"""
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/status')
def status():
    """状态检查端点"""
    global latest_frame
    has_frame = latest_frame is not None
    return {
        'status': 'active' if has_frame else 'waiting',
        'has_frame': has_frame,
        'timestamp': time.time()
    }

@app.route('/')
def index():
    """测试页面"""
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>YOLO Video Stream Test</title>
        <style>
            body { font-family: Arial, sans-serif; background: #000; color: #fff; }
            .container { text-align: center; padding: 20px; }
            img { max-width: 100%; border: 2px solid #fff; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>YOLO检测视频流测试</h1>
            <img src="{{ url_for('video_feed') }}" alt="YOLO检测视频流">
            <p>如果看到实时画面，说明视频流服务器工作正常</p>
        </div>
    </body>
    </html>
    ''')

# 提供给外部调用的函数
def update_detection_frame(frame):
    """供YOLO程序调用，更新检测画面"""
    video_server.update_frame(frame)

def start_server(host='localhost', port=5000, debug=False):
    """启动视频流服务器"""
    print(f"🎥 视频流服务器启动在 http://{host}:{port}")
    print(f"📺 视频流地址: http://{host}:{port}/video_feed")
    print(f"🔍 测试页面: http://{host}:{port}/")
    app.run(host=host, port=port, debug=debug, threaded=True)

if __name__ == '__main__':
    # 独立运行时的测试代码
    import threading
    
    def test_frames():
        """生成测试画面"""
        import time
        frame_count = 0
        while True:
            # 创建测试画面
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(frame, f'Test Frame {frame_count}', (50, 240), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(frame, f'Time: {time.strftime("%H:%M:%S")}', (50, 280), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            update_detection_frame(frame)
            frame_count += 1
            time.sleep(0.033)  # 30 FPS
    
    # 启动测试画面生成线程
    test_thread = threading.Thread(target=test_frames, daemon=True)
    test_thread.start()
    
    # 启动服务器
    start_server(debug=True) 