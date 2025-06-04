import asyncio
import cv2
import numpy as np
import time
import warnings
import random
import sys
from toio import *
from typing import Dict, List
from threading import Thread
import queue

warnings.filterwarnings('ignore')
from ultralytics import YOLO

# 导入视频流服务器
try:
    from video_stream_server import update_detection_frame, start_server
    VIDEO_STREAM_AVAILABLE = True
    print("✅ 视频流服务器模块已加载")
except ImportError:
    VIDEO_STREAM_AVAILABLE = False
    print("⚠️  视频流服务器模块未找到，将仅显示本地窗口")

# ========== YOLO配置参数 ==========
MODEL_PATH = 'Yolo/yolo-obb-best.pt'
CAMERA_INDEX = 1
CONF_THRESHOLD = 0.5
INPUT_SIZE = 640

# ========== 圆圈检测配置 ==========
CIRCLE_CENTER_X = 355
CIRCLE_CENTER_Y = 200
CIRCLE_RADIUS = 97
CIRCLE_COLOR = (0, 0, 0)
CIRCLE_THICKNESS = 1

# ========== 全局变量 ==========
model = None
cap = None
target_status = {}
exit_event_queue = queue.Queue()  # 用于传递离开圆圈的事件
video_stream_server_running = False

class ToioController:
    """单个toio的控制器"""
    
    def __init__(self, cube, cube_id: int):
        self.cube = cube
        self.id = cube_id
        self.state = "random"
        self.state_event = asyncio.Event()
        self.last_detected_time = time.time()  # 添加最后检测时间
        self.is_detected = False  # 添加检测状态标志
        
    async def random_move(self):
        """随机移动 - 每个ID有不同的移动特性"""
        
        try:
            # 根据ID设置不同的移动参数
            if self.id == 0:  # ID 0: 快速直行型
                base_speed = random.randint(15, 40)  # 较快速度
                turn_offset = random.randint(-10, 10)  # 较小转向
                
            elif self.id == 1:  # ID 1: 转圈型
                base_speed = random.randint(10, 25)  # 中等速度
                turn_offset = random.randint(-25, 25)  # 大幅转向
                
            elif self.id == 2:  # ID 2: 谨慎型
                base_speed = random.randint(5, 20)  # 较慢速度
                # 偶尔停顿
                if random.random() < 0.1:  # 10%概率停顿
                    await self.cube.api.motor.motor_control(left=0, right=0)
                    await asyncio.sleep(random.uniform(0.5, 1.0))
                    return
                turn_offset = random.randint(-15, 15)  # 中等转向
            
            else:  # 默认行为
                base_speed = random.randint(20, 40)
                turn_offset = random.randint(-20, 20)
            
            left_speed = base_speed + turn_offset
            right_speed = base_speed - turn_offset
            
            # 限制速度范围
            left_speed = max(-50, min(50, left_speed))
            right_speed = max(-50, min(50, right_speed))
            
            await self.cube.api.motor.motor_control(left=left_speed, right=right_speed)
            
        except Exception as e:
            # 静默处理连接错误
            if "Not connected" not in str(e) and "Unreachable" not in str(e):
                print(f"⚠️  Toio {self.id}: 移动命令失败 - {e}")
        
    async def special_move(self):
        """特殊移动：原地转，然后前进"""
        try:
            print(f"🤖 Toio {self.id}: 执行特殊动作（离开圆圈）")
            
            # 原地转180度（0.5秒）
            await self.cube.api.motor.motor_control(left=30, right=-30)
            await asyncio.sleep(0.5)
            
            # 向前移动1秒
            await self.cube.api.motor.motor_control(left=40, right=40)
            await asyncio.sleep(0.9)
            
            # 恢复随机移动状态
            self.state = "random"
            print(f"🤖 Toio {self.id}: 回到随机移动状态")
            
        except Exception as e:
            # 出错时也要恢复状态
            self.state = "random"
            if "Not connected" not in str(e) and "Unreachable" not in str(e):
                print(f"⚠️  Toio {self.id}: 特殊动作失败 - {e}")
        
    async def handle_detection_lost(self):
        """处理检测丢失的情况"""
        current_time = time.time()
        if not self.is_detected and current_time - self.last_detected_time > 0.4:  # 0.2秒未检测到
            if self.state != "lost":
                print(f"⚠️  Toio {self.id}: 检测丢失")
                self.state = "lost"
                # 停止移动
                try:
                    await self.cube.api.motor.motor_control(left=0, right=0)
                except:
                    pass
                
    def update_detection_status(self, detected: bool):
        """更新检测状态"""
        if detected:
            self.last_detected_time = time.time()
            self.is_detected = True
            if self.state == "lost":
                self.state = "random"
                print(f"✅ Toio {self.id}: 恢复检测")
        else:
            self.is_detected = False
            
    async def control_loop(self):
        """主控制循环"""
        try:
            while True:
                try:
                    # 检查检测状态
                    await self.handle_detection_lost()
                    
                    if self.state == "random" and self.is_detected:
                        await self.random_move()
                        
                        # 根据ID设置不同的等待时间
                        if self.id == 0:  # ID 0: 快速反应
                            await asyncio.sleep(random.uniform(0.1, 0.2))
                        elif self.id == 1:  # ID 1: 中等节奏
                            await asyncio.sleep(random.uniform(0.2, 0.3))
                        elif self.id == 2:  # ID 2: 缓慢节奏
                            await asyncio.sleep(random.uniform(0.3, 0.4))
                        else:
                            await asyncio.sleep(random.uniform(0.4, 0.5))
                            
                    elif self.state == "special" and self.is_detected:
                        await self.special_move()
                    else:
                        await asyncio.sleep(0.1)  # 未检测到时的等待时间
                        
                    if self.state_event.is_set():
                        self.state_event.clear()
                        
                except Exception as e:
                    # 捕获蓝牙连接错误，避免程序崩溃
                    if "Not connected" in str(e) or "Unreachable" in str(e):
                        print(f"⚠️  Toio {self.id}: 连接断开")
                        break
                    else:
                        print(f"⚠️  Toio {self.id}: 控制错误 - {e}")
                        await asyncio.sleep(1)  # 短暂等待后继续
                        
        except asyncio.CancelledError:
            # 正常取消，尝试停止电机
            try:
                await self.cube.api.motor.motor_control(left=0, right=0)
            except:
                pass  # 忽略断开连接的错误
            raise

class CombinedController:
    """组合控制器 - 整合YOLO检测和toio控制"""
    
    def __init__(self):
        self.controllers: Dict[int, ToioController] = {}
        self.running = True
        self.yolo_thread = None
        
    async def initialize_toio(self, cubes):
        """初始化所有toio控制器"""
        colors = [
            Color(r=255, g=0, b=0),    # 0号：红色
            Color(r=0, g=255, b=0),    # 1号：绿色
            Color(r=0, g=0, b=255),    # 2号：蓝色
        ]
        
        # 根据实际连接的设备数量进行初始化，避免索引超出范围
        actual_cube_count = len(cubes)
        print(f"📱 实际连接的toio设备数量: {actual_cube_count}")
        
        for i in range(actual_cube_count):
            try:
                controller = ToioController(cubes[i], i)
                self.controllers[i] = controller
                
                if i > 0:
                    await asyncio.sleep(0.5)
                
                # 确保不超出颜色数组的范围
                color_index = i if i < len(colors) else i % len(colors)
                await cubes[i].api.indicator.turn_on(
                    IndicatorParam(duration_ms=0, color=colors[color_index])
                )
                
                print(f"✅ Toio {i} 初始化成功")
                
            except Exception as e:
                print(f"⚠️  Toio {i} 初始化失败: {e}")
                # 继续初始化其他toio
            
    async def event_handler(self):
        """处理来自YOLO的离开圆圈事件"""
        while self.running:
            try:
                # 非阻塞地检查队列
                try:
                    toio_id = exit_event_queue.get_nowait()
                    
                    # 将YOLO的ID转换为toio的ID（0,1,2）
                    if toio_id in ['0', '1', '2']:
                        toio_index = int(toio_id)
                        if toio_index in self.controllers:
                            controller = self.controllers[toio_index]
                            # 只有在random状态时才触发特殊动作，避免重复触发
                            if controller.state == "random":
                                controller.state = "special"
                                controller.state_event.set()
                                print(f"✅ 触发Toio {toio_index}的特殊动作")
                            else:
                                print(f"⚠️  Toio {toio_index}忽略重复的离开圆圈事件（当前状态：{controller.state}）")
                            
                except queue.Empty:
                    pass
                    
                await asyncio.sleep(0.1)
                
            except asyncio.CancelledError:
                break
                
    def start_yolo_detection(self):
        """在单独的线程中运行YOLO检测"""
        self.yolo_thread = Thread(target=run_yolo_detection, args=(lambda: self.running,))
        self.yolo_thread.daemon = True
        self.yolo_thread.start()
        
    async def run(self):
        """运行主程序"""
        print("=== YOLO + Toio 联合控制系统 ===")
        print("正在初始化系统...")
        
        # 连接toio设备 - 添加重试机制
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                print(f"\n尝试连接toio设备... (第{retry_count + 1}次)")
                
                async with MultipleToioCoreCubes(cubes=3, names=["0", "1", "2"]) as cubes:
                    print("✅ 成功连接3个toio设备！")
                    
                    await asyncio.sleep(2)
                    await self.initialize_toio(cubes)
                    
                    # 在toio初始化成功后启动YOLO检测线程
                    print("🔧 正在启动YOLO检测系统...")
                    self.start_yolo_detection()
                    print("✅ YOLO检测系统启动成功！")
                    
                    # 创建任务
                    tasks = []
                    
                    # toio控制任务
                    for controller in self.controllers.values():
                        tasks.append(asyncio.create_task(controller.control_loop()))
                    
                    # 事件处理任务
                    event_task = asyncio.create_task(self.event_handler())
                    tasks.append(event_task)
                    
                    print("✅ 系统启动完成！")
                    print("📷 YOLO检测已启动，当机器人离开圆圈时会自动执行特殊动作")
                    print("按 'q' 键退出程序")
                    
                    # 等待直到程序结束
                    while self.running:
                        await asyncio.sleep(1)
                        
                    # 清理
                    print("\n正在安全关闭程序...")
                    
                    # 先设置运行标志为False
                    self.running = False
                    
                    # 取消所有任务
                    for task in tasks:
                        if not task.done():
                            task.cancel()
                            
                    # 等待任务完成（忽略取消异常）
                    await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # 停止所有toio
                    print("正在停止所有toio...")
                    stop_tasks = []
                    for i in range(3):
                        try:
                            stop_tasks.append(cubes[i].api.motor.motor_control(left=0, right=0))
                            stop_tasks.append(cubes[i].api.indicator.turn_off())
                        except Exception:
                            pass  # 忽略断开连接的错误
                            
                    await asyncio.gather(*stop_tasks, return_exceptions=True)
                    
                    # 成功完成，退出重试循环
                    break
                    
            except Exception as e:
                error_msg = str(e)
                if error_msg:
                    print(f"❌ 连接错误: {error_msg}")
                else:
                    print("❌ 连接错误: 未知错误（可能是蓝牙连接问题）")
                
                retry_count += 1
                
                if retry_count < max_retries:
                    wait_time = retry_count * 3
                    print(f"⏳ 等待{wait_time}秒后重试...")
                    await asyncio.sleep(wait_time)
                else:
                    print("\n❌ 无法连接toio设备，请检查：")
                    print("1. toio设备是否已开机")
                    print("2. 蓝牙是否已开启")
                    print("3. toio是否已与其他设备连接")
                    print("4. 尝试重启toio设备")
                    
                self.running = False

# ========== YOLO检测相关函数 ==========

def initialize_model():
    """初始化YOLO模型"""
    global model
    try:
        print("🔧 正在加载YOLO模型...")
        model = YOLO(MODEL_PATH)
        
        try:
            import torch
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
            print(f"✅ 使用设备: {device}")
        except:
            device = 'cpu'
        
        model.overrides.update({
            'verbose': False,
            'device': device,
            'half': False,
            'agnostic_nms': True,
            'max_det': 50,
        })
        
        print("✅ YOLO模型加载成功！")
        return True
        
    except Exception as e:
        print(f"❌ 模型加载失败: {e}")
        return False

def initialize_camera():
    """初始化摄像头"""
    global cap
    
    print("🎥 正在初始化摄像头...")
    
    backends = [cv2.CAP_DSHOW, cv2.CAP_ANY]
    
    for backend in backends:
        cap = cv2.VideoCapture(CAMERA_INDEX, backend)
        if cap.isOpened():
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            cap.set(cv2.CAP_PROP_FPS, 30)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            ret, frame = cap.read()
            if ret and frame is not None:
                print(f"✅ 摄像头初始化成功！")
                return True
            else:
                cap.release()
        
    print(f"❌ 摄像头初始化失败！")
    return False

def detect_objects(frame):
    """目标检测函数"""
    global model
    
    if model is None:
        return []
    
    try:
        results = model.predict(
            source=frame,
            imgsz=INPUT_SIZE,
            conf=CONF_THRESHOLD,
            verbose=False
        )
        
        detections = []
        
        for r in results:
            if r.obb is not None and len(r.obb.data) > 0:
                for detection in r.obb.data:
                    try:
                        det_data = detection.cpu().numpy()
                        center_x = float(det_data[0])
                        center_y = float(det_data[1])
                        width = float(det_data[2])
                        height = float(det_data[3])
                        angle = float(det_data[4])
                        confidence = float(det_data[5])
                        class_id = int(det_data[6])
                        
                        # ID映射
                        output_id = str(class_id)
                        if class_id == 3:
                            output_id = "0"
                        elif class_id == 0:
                            output_id = "3"
                        
                        detection_result = {
                            "id": output_id,
                            "center_x": center_x,
                            "center_y": center_y,
                            "width": width,
                            "height": height,
                            "angle": angle,
                            "confidence": confidence,
                            "class_id": class_id
                        }
                        
                        detections.append(detection_result)
                        
                    except Exception as e:
                        continue
        
        return detections
        
    except Exception as e:
        print(f"❌ 检测错误: {e}")
        return []

def is_target_in_circle(center_x, center_y):
    """检查目标是否在圆圈内"""
    distance = np.sqrt((center_x - CIRCLE_CENTER_X)**2 + (center_y - CIRCLE_CENTER_Y)**2)
    return distance <= CIRCLE_RADIUS

def check_circle_exit(object_id, center_x, center_y):
    """检查目标是否离开圆圈并发送事件"""
    global target_status
    
    current_in_circle = is_target_in_circle(center_x, center_y)
    
    if object_id not in target_status:
        target_status[object_id] = current_in_circle
        return
    
    previous_in_circle = target_status[object_id]
    
    # 检测到从圆圈内移动到圆圈外
    if previous_in_circle and not current_in_circle:
        print(f"⚠️  检测到: ID:{object_id} 离开了圆圈！")
        # 将事件放入队列
        exit_event_queue.put(object_id)
    
    target_status[object_id] = current_in_circle

def draw_detections(frame, detections):
    """在画面上绘制检测结果"""
    
    # 更新所有toio的检测状态为未检测
    if controller:
        for toio_controller in controller.controllers.values():
            toio_controller.update_detection_status(False)
    
    # 绘制大圆圈
    cv2.circle(frame, (CIRCLE_CENTER_X, CIRCLE_CENTER_Y), CIRCLE_RADIUS, CIRCLE_COLOR, CIRCLE_THICKNESS)
    cv2.circle(frame, (CIRCLE_CENTER_X, CIRCLE_CENTER_Y), 3, CIRCLE_COLOR, -1)
    
    for det in detections:
        object_id = det['id']
        if object_id not in ['0', '1', '2', '3']:
            continue
            
        center_x = int(det['center_x'])
        center_y = int(det['center_y'])
        width = det['width']
        height = det['height']
        angle = det['angle']
        
        # 更新检测状态
        if controller and object_id in ['0', '1', '2']:
            toio_id = int(object_id)
            if toio_id in controller.controllers:
                controller.controllers[toio_id].update_detection_status(True)
        
        # 检查是否离开圆圈
        check_circle_exit(object_id, center_x, center_y)
        
        # 根据位置选择颜色
        in_circle = is_target_in_circle(center_x, center_y)
        center_color = (0, 255, 0) if in_circle else (0, 0, 255)
        box_color = (255, 0, 0) if in_circle else (0, 0, 255)
        
        # 绘制中心点
        cv2.circle(frame, (center_x, center_y), 2, center_color, -1)
        
        # 绘制旋转矩形框
        try:
            cos_a = np.cos(np.radians(angle))
            sin_a = np.sin(np.radians(angle))
            
            w_half = width / 2
            h_half = height / 2
            
            corners = np.array([
                [-w_half, -h_half],
                [w_half, -h_half],
                [w_half, h_half],
                [-w_half, h_half]
            ])
            
            rotation_matrix = np.array([
                [cos_a, -sin_a],
                [sin_a, cos_a]
            ])
            
            rotated_corners = corners @ rotation_matrix.T
            rotated_corners[:, 0] += center_x
            rotated_corners[:, 1] += center_y
            
            points = rotated_corners.astype(int)
            cv2.polylines(frame, [points], True, box_color, 1)
            
        except Exception:
            pass
        
        # 绘制ID标签
        label = f"ID:{object_id}"
        cv2.putText(frame, label, (center_x + 10, center_y - 10), 
                   cv2.FONT_HERSHEY_DUPLEX, 0.35, (0, 255, 255), 1, cv2.LINE_AA)

def run_yolo_detection(is_running):
    """YOLO检测主循环（在单独线程中运行）"""
    global cap, video_stream_server_running
    
    if not initialize_model() or not initialize_camera():
        print("❌ YOLO初始化失败")
        return

    # 启动视频流服务器
    if VIDEO_STREAM_AVAILABLE and not video_stream_server_running:
        try:
            import threading
            server_thread = threading.Thread(
                target=start_server, 
                args=('localhost', 5000, False),
                daemon=True
            )
            server_thread.start()
            video_stream_server_running = True
            print("🎥 视频流服务器已启动在 http://localhost:5000")
            print("📺 视频流地址: http://localhost:5000/video_feed")
        except Exception as e:
            print(f"⚠️  视频流服务器启动失败: {e}")
    
    cv2.namedWindow("YOLO Detection", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("YOLO Detection", 1000, 750)
    
    frame_count = 0
    fps_start_time = time.time()
    fps = 0
    
    try:
        while is_running():
            ret, frame = cap.read()
            if not ret:
                continue
            
            frame_count += 1
            current_time = time.time()
            
            if frame_count % 30 == 0:
                fps = 30 / (current_time - fps_start_time)
                fps_start_time = current_time
            
            # 执行检测
            detections = detect_objects(frame)
            
            # 绘制结果
            draw_detections(frame, detections)
            
            # 显示FPS等信息
            cv2.putText(frame, f"FPS: {fps:.1f}", (10, 25), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1, cv2.LINE_AA)
            cv2.putText(frame, f"Objects: {len(detections)}", (10, 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1, cv2.LINE_AA)
            cv2.putText(frame, "Press 'q' to quit", (10, 75), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
            
            # 添加视频流状态信息
            if VIDEO_STREAM_AVAILABLE:
                cv2.putText(frame, "Stream: http://localhost:5000/video_feed", (10, 100), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 200, 0), 1, cv2.LINE_AA)
            
            # 发送画面到视频流服务器
            if VIDEO_STREAM_AVAILABLE:
                try:
                    update_detection_frame(frame)
                except Exception as e:
                    pass  # 静默处理流服务器错误
            
            cv2.imshow("YOLO Detection", frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                # 通知主程序退出
                controller.running = False
                break
                
    except Exception as e:
        print(f"❌ YOLO检测错误: {e}")
    finally:
        if cap is not None:
            cap.release()
        cv2.destroyAllWindows()

# ========== 主程序入口 ==========

controller = None  # 全局控制器实例

def signal_handler(signum, frame):
    """处理Ctrl+C信号"""
    global controller
    print("\n\n⚠️  收到退出信号，正在安全关闭程序...")
    if controller:
        controller.running = False

async def main():
    """主程序入口"""
    global controller
    
    # 设置信号处理
    import signal
    signal.signal(signal.SIGINT, signal_handler)
    
    controller = CombinedController()
    
    try:
        await controller.run()
    except Exception as e:
        print(f"主程序错误: {e}")
    finally:
        controller.running = False
        print("\n程序已退出")

if __name__ == "__main__":
    # Windows特定的事件循环策略
    if sys.platform == 'win32':
        # 使用ProactorEventLoop避免一些Windows上的问题
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
        # 设置事件循环的异常处理
        def exception_handler(loop, context):
            exception = context.get('exception')
            if isinstance(exception, SystemExit):
                return
            if exception and "Not connected" in str(exception):
                return  # 忽略蓝牙断开连接的错误
            print(f"事件循环异常: {context}")
        
        loop = asyncio.new_event_loop()
        loop.set_exception_handler(exception_handler)
        asyncio.set_event_loop(loop)
        
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n✅ 程序正常退出")
    except Exception as e:
        print(f"\n❌ 程序异常: {e}") 