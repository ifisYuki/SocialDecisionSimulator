import cv2
import numpy as np
from pyzbar.pyzbar import decode
import asyncio
import websockets
import json
from pyzbar.pyzbar import decode, ZBarSymbol
import threading
import time
import queue
from collections import deque

import warnings
warnings.filterwarnings('ignore')
from ultralytics import YOLO

# ========== 参数配置 ==========
VIDEO_URL = 0  
TARGET_CODES = ['0', '1', '2','3','4','5']
REFERENCE_LENGTH = 12.5
SEND_INTERVAL = 0.1
PORT = 9097         

# ========== 全局变量 ==========
cap = None
center = None
R = None
scale_factor = None
reference_angle = None
latest_poses = []  
websocket_clients = set()  
is_running = True

# 异步处理相关
frame_queue = queue.Queue(maxsize=2)  # 帧队列
detection_results = {}  # 检测结果缓存
last_detection_time = time.time()
DETECTION_INTERVAL = 0.1  # 检测间隔（秒），控制检测频率

# ========== YOLO模型 ==========
model = None

def initialize_model():
    """初始化YOLO模型"""
    global model
    try:
        print("🔧 Loading YOLO model...")
        model = YOLO('best-obb-225.pt')
    
        # 优化设置
        model.overrides.update({
            'verbose': False,
            'device': 0,
            'half': False,
            'dnn': False,
            'agnostic_nms': True,
            'max_det': 50,
        })   # 减少输出

        # #模型预热
        # print("🔥 Warming up model...")
        # dunmmy_input = np.zeros((640, 640, 3), dtype=np.uint8)
        # for i in range(3):
        #     _ = model.predict(dunmmy_input, verbose=False, imgsz=640)

        # print("✅ Model warmed up and optimized")
        # return True
    except Exception as e:
        print(f"❌ Model initialization error: {e}")
        return False

def detect_boxes(frame):
    """优化的检测函数"""
    global model, center, R, scale_factor, reference_angle
    
    if model is None:
        return []
    try:
        # # 输入预处理优化
        # h, w = frame.shape[:2]
        
        # # 动态调整输入尺寸，优先速度
        # if w > h:
        #     new_w = 640  # 进一步降低分辨率
        #     new_h = int(h * new_w / w)
        # else:
        #     new_h = 640
        #     new_w = int(w * new_h / h)
        
        # # 快速resize
        # resized_frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        
        # 使用更小的输入尺寸提高速度
        myresult = model.predict(
            source=frame,
            imgsz=640,  
            conf=0.3,   # 提高置信度阈值，减少检测数量
            # max_det=20,  #限制最大驾车数
            # stream_buffer=True,
            verbose=False,  # 关闭详细输出
            device=0,  # 如果有GPU可以改为0
            half=False
        )
    
        detections = []
        # scale_x = w / new_w  # 坐标还原比例
        # scale_y = h / new_h
        
        for r in myresult:
            if r.obb is not None and len(r.obb.data) > 0:
                for detection in r.obb.data:
                    try:
                        # 获取检测数据
                        det_data = detection.cpu().numpy()
                        center_x = det_data[0]
                        center_y = det_data[1]
                        width = det_data[2]
                        height = det_data[3]
                        angle = det_data[4]
                        conf = det_data[5]
                        cls = int(det_data[6])
                        
                        # 建立坐标系（使用5号目标）
                        if cls == 5 and center is None:
                            center = np.array([center_x, center_y], dtype=np.float32)
                            reference_angle = angle
                            cos_a = np.cos(-np.radians(reference_angle))
                            sin_a = np.sin(-np.radians(reference_angle))
                            R = np.array([[cos_a, -sin_a], [sin_a, cos_a]])
                            scale_factor = 50.0 / width
                            print(f"✅ Coordinate system: Center({center_x:.1f},{center_y:.1f}), Angle:{reference_angle:.1f}°")
                        
                        # 计算相对坐标（如果坐标系已建立）
                        if center is not None:
                            vec = np.array([center_x, center_y]) - center
                            transformed = scale_factor * (R @ vec)
    
                            x = np.clip(transformed[0], -25, 25)
                            z = np.clip(transformed[1], -25, 25)
    
                            # ID映射
                            output_id = str(cls)
                            if cls == 3:
                                output_id = "0"
                            elif cls == 0:
                                output_id = "3"

                            detection_result = {
                            "id": output_id,
                            "x": float(round(x, 2)),
                            "z": float(round(z, 2)),
                            "angle": float(round(angle - reference_angle, 2)),
                            "pixel_x": center_x,
                            "pixel_y": center_y,
                            "conf": float(conf)
                            }
                            detections.append(detection_result)

                        # 如果坐标系已建立，计算相对坐标；否则仅返回像素坐标
                        if center is not None and scale_factor is not None and R is not None:
                            vec = np.array([center_x, center_y]) - center
                            transformed = scale_factor * (R @ vec)

                            x = float(round(np.clip(transformed[0], -25, 25), 2))
                            z = float(round(np.clip(transformed[1], -25, 25), 2))
                        else:
                            x, z = None, None  # 尚未建立坐标系

                        detection_result = {
                            "id": output_id,
                            "x": x,
                            "z": z,
                            "angle": float(round(angle, 2)) if reference_angle is None else float(round(angle - reference_angle, 2)),
                            "pixel_x": center_x,
                            "pixel_y": center_y,
                            "conf": float(conf)
                        }
                        detections.append(detection_result)
                    except Exception as e:
                        print(f"Detection parsing error: {e}")
                        continue
            print("Detection:", detections)                  
        
        return detections
        
    except Exception as e:
        print(f"❌ Detection error: {e}")
        return []

def detection_worker():
    """检测工作线程"""
    global frame_queue, detection_results, latest_poses, is_running
    
    while is_running:
        try:
            # 从队列获取帧
            if not frame_queue.empty():
                frame = frame_queue.get_nowait()
                
                # 执行检测
                start_time = time.time()
                poses = detect_boxes(frame)
                detection_time = time.time() - start_time
                
                # 更新结果
                detection_results['poses'] = poses
                detection_results['detection_time'] = detection_time
                latest_poses = poses
                
                # 清空队列中的旧帧
                while not frame_queue.empty():
                    try:
                        frame_queue.get_nowait()
                    except queue.Empty:
                        break
            else:
                time.sleep(0.01)
                
        except Exception as e:
            print(f"❌ Detection worker error: {e}")
            time.sleep(0.1)

def camera_loop():
    global cap, center, R, scale_factor, is_running, frame_queue, detection_results
    
    cv2.namedWindow("Real-time Detection", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Real-time Detection", 1000, 750)
    
    print("📺 Camera started with optimized detection")
    
    frame_count = 0
    fps_start_time = time.time()
    display_fps = 0
    detection_fps = 0
    
    # 缓存最后的检测结果用于显示
    cached_poses = []
    
    try:
        while is_running:
            ret, frame = cap.read()
            if not ret:
                continue

            frame_count += 1
            current_time = time.time()
            
            # 计算显示FPS
            if frame_count % 30 == 0:
                display_fps = 30 / (current_time - fps_start_time)
                fps_start_time = current_time

            # 添加每一帧到检测队列
            if frame_queue.empty():  # 只在队列为空时添加新帧
                frame_queue.put(frame.copy())

            # 获取最新检测结果
            if 'poses' in detection_results:
                cached_poses = detection_results['poses']
                if 'detection_time' in detection_results:
                    detection_fps = 1.0 / detection_results['detection_time'] if detection_results['detection_time'] > 0 else 0

            # 创建显示画面
            display_frame = frame.copy()
            
            # 显示性能信息
            cv2.putText(display_frame, f"Display FPS: {display_fps:.1f}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            cv2.putText(display_frame, f"Detection FPS: {detection_fps:.1f}", (10, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
            
            status = "Coordinate System Ready" if center is not None else "Waiting for Ground Target (ID:5)"
            cv2.putText(display_frame, status, (10, 90), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
            
            cv2.putText(display_frame, f"WebSocket Clients: {len(websocket_clients)}", (10, 120), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
            
            cv2.putText(display_frame, "Press 'q' to quit", (10, 150), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            # 绘制坐标系原点
            if center is not None:
                cv2.circle(display_frame, (int(center[0]), int(center[1])), 10, (0, 0, 255), -1)
                cv2.putText(display_frame, "Origin", (int(center[0])+15, int(center[1])), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            # 绘制检测结果（使用缓存的结果）
            for det in cached_poses:
                id_ = det["id"]
                x_unity = det["x"]
                z_unity = det["z"]
                angle = det["angle"]
                
                if 'pixel_x' in det and 'pixel_y' in det:
                    pixel_x = int(det['pixel_x'])
                    pixel_y = int(det['pixel_y'])
                elif center is not None and R is not None and scale_factor is not None:
                    unity_vec = np.array([x_unity, z_unity])
                    pixel_vec = (np.linalg.inv(R) @ (unity_vec / scale_factor))
                    pixel_x = int(center[0] + pixel_vec[0])
                    pixel_y = int(center[1] + pixel_vec[1])
                else:
                    continue
                
                # 绘制目标
                cv2.circle(display_frame, (pixel_x, pixel_y), 8, (0, 255, 0), -1)
                
                label = f"ID:{id_} Angle:{angle:.1f}"
                cv2.putText(display_frame, label, (pixel_x + 15, pixel_y), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.2, (0, 255, 255), 1)
                
                coord_label = f"({x_unity:.1f}, {z_unity:.1f})"
                cv2.putText(display_frame, coord_label, (pixel_x + 15, pixel_y + 25), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.2, (255, 255, 0), 1)

            cv2.imshow("Real-time Detection", display_frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                print("User pressed 'q' to quit")
                is_running = False
                break
                
    except Exception as e:
        print(f"❌ Camera loop error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cv2.destroyWindow("Real-time Detection")

def initialize_camera():
    global cap
    
    print("Initializing camera...")
    camera_indices = [0, 1]
    
    for index in camera_indices:
        print(f"Trying camera index {index}...")
        cap = cv2.VideoCapture(index)
        
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None:
                print(f"✅ Camera {index} working normally!")
                return True
            else:
                cap.release()
                cap = None
    
    print("❌ Cannot open any camera!")
    return False

# WebSocket处理函数
async def handle_client(websocket, path):
    global websocket_clients, latest_poses, is_running
    
    websocket_clients.add(websocket)
    client_addr = websocket.remote_address
    print(f"📱 New client connected: {client_addr}")
    
    try:
        while is_running:
            if latest_poses:
                message = json.dumps({"poses": latest_poses})
                await websocket.send(message)
            await asyncio.sleep(SEND_INTERVAL)
            
    except websockets.exceptions.ConnectionClosed:
        print(f"🔌 Client {client_addr} disconnected")
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
    finally:
        websocket_clients.discard(websocket)

async def websocket_server():
    global is_running
    print(f"🚀 Starting WebSocket service: ws://localhost:{PORT}")
    
    server = None
    try:
        server = await websockets.serve(handle_client, "0.0.0.0", PORT)
        while is_running:
            await asyncio.sleep(0.1)
    except Exception as e:
        print(f"❌ WebSocket server error: {e}")
    finally:
        if server:
            server.close()
            await server.wait_closed()
        print("🔚 WebSocket server closed")

def main():
    global is_running
    
    try:
        # 初始化摄像头
        if not initialize_camera():
            print("Camera initialization failed")
            return
        
        # 初始化模型
        initialize_model()
        
        print("🎬 Starting optimized real-time detection system...")
        
        # 启动检测工作线程
        detection_thread = threading.Thread(target=detection_worker, daemon=True)
        detection_thread.start()
        
        # 启动摄像头循环线程
        camera_thread = threading.Thread(target=camera_loop, daemon=True)
        camera_thread.start()
        
        # 启动WebSocket服务器
        asyncio.run(websocket_server())
        
    except KeyboardInterrupt:
        print("\nProgram interrupted")
    finally:
        is_running = False
        if cap is not None:
            cap.release()
        cv2.destroyAllWindows()
        print("程序被用户中断")

if __name__ == "__main__":
    main()