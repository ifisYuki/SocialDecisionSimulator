import cv2
import numpy as np
import time
import warnings

warnings.filterwarnings('ignore')
from ultralytics import YOLO

# ========== 配置参数 ==========
MODEL_PATH = 'Yolo/best-obb-225.pt'  # 模型文件路径
CAMERA_INDEX = 0                # 摄像头索引
CONF_THRESHOLD = 0.3            # 置信度阈值
INPUT_SIZE = 640               # 输入图像尺寸

# ========== 圆圈检测配置 ==========
CIRCLE_CENTER_X = 355           # 圆圈中心X坐标
CIRCLE_CENTER_Y = 200           # 圆圈中心Y坐标  
CIRCLE_RADIUS = 110             # 圆圈半径
CIRCLE_COLOR = (120, 205, 0)      # 圆圈颜色（绿色）
CIRCLE_THICKNESS = 2            # 圆圈线条粗细

def list_available_cameras():
    """列出所有可用的摄像头"""
    available_cameras = []
    print("🔍 扫描可用摄像头...")
    
    for i in range(10):  # 检查前10个摄像头索引
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None:
                # 获取摄像头信息
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = int(cap.get(cv2.CAP_PROP_FPS))
                
                camera_info = {
                    'index': i,
                    'width': width,
                    'height': height,
                    'fps': fps
                }
                available_cameras.append(camera_info)
                print(f"📷 摄像头 {i}: {width}x{height} @ {fps}FPS")
            cap.release()
    
    if not available_cameras:
        print("❌ 未找到可用摄像头")
    
    return available_cameras

# ========== 全局变量 ==========
model = None
cap = None
target_status = {}              # 跟踪每个目标是否在圆圈内的状态

def initialize_model():
    """初始化YOLO模型"""
    global model
    try:
        print("🔧 正在加载YOLO模型...")
        model = YOLO(MODEL_PATH)
        
        # 检测可用设备
        try:
            import torch
            if torch.cuda.is_available():
                device = 'cuda'
                print("✅ 检测到CUDA支持，使用GPU")
            else:
                device = 'cpu'
                print("⚠️ 未检测到CUDA支持，使用CPU")
        except:
            device = 'cpu'
            print("⚠️ 无法检测设备，使用CPU")
        
        # 模型优化设置
        model.overrides.update({
            'verbose': False,      # 关闭详细输出
            'device': device,      # 自动选择设备
            'half': False,        # 不使用半精度
            'agnostic_nms': True, # 类别无关的非极大值抑制
            'max_det': 50,        # 最大检测数量
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
    
    # 直接使用1号摄像头
    camera_index = 1
    print(f"📷 正在初始化摄像头 {camera_index}...")
    
    # 尝试不同的后端
    backends = [cv2.CAP_DSHOW, cv2.CAP_ANY]
    
    for backend in backends:
        cap = cv2.VideoCapture(camera_index, backend)
        if cap.isOpened():
            # 设置摄像头属性
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            cap.set(cv2.CAP_PROP_FPS, 30)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # 减少缓冲延迟
            
            ret, frame = cap.read()
            if ret and frame is not None:
                actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                actual_fps = int(cap.get(cv2.CAP_PROP_FPS))
                
                print(f"✅ 摄像头 {camera_index} 初始化成功！")
                print(f"   分辨率: {actual_width}x{actual_height}")
                print(f"   帧率: {actual_fps}FPS")
                print(f"   后端: {'DirectShow' if backend == cv2.CAP_DSHOW else 'Default'}")
                return True
            else:
                cap.release()
        
    print(f"❌ 摄像头 {camera_index} 初始化失败！")
    return False

def detect_objects(frame):
    """目标检测函数"""
    global model
    
    if model is None:
        return []
    
    try:
        # 检测可用设备
        try:
            import torch
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
        except:
            device = 'cpu'
        
        # 执行YOLO检测
        results = model.predict(
            source=frame,
            imgsz=INPUT_SIZE,
            conf=CONF_THRESHOLD,
            verbose=False,
            device=device  # 自动选择设备
        )
        
        detections = []
        
        # 解析检测结果
        for r in results:
            if r.obb is not None and len(r.obb.data) > 0:
                for detection in r.obb.data:
                    try:
                        # 获取检测数据
                        det_data = detection.cpu().numpy()
                        center_x = float(det_data[0])
                        center_y = float(det_data[1])
                        width = float(det_data[2])
                        height = float(det_data[3])
                        angle = float(det_data[4])
                        confidence = float(det_data[5])
                        class_id = int(det_data[6])
                        
                        # ID映射（根据原代码的映射规则）
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
                        print(f"检测数据解析错误: {e}")
                        continue
        
        return detections
        
    except Exception as e:
        print(f"❌ 检测错误: {e}")
        return []

def draw_detections(frame, detections):
    """在画面上绘制检测结果"""
    
    # 绘制大圆圈
    cv2.circle(frame, (CIRCLE_CENTER_X, CIRCLE_CENTER_Y), CIRCLE_RADIUS, CIRCLE_COLOR, CIRCLE_THICKNESS)
    
    # 在圆圈中心绘制一个小点作为参考
    cv2.circle(frame, (CIRCLE_CENTER_X, CIRCLE_CENTER_Y), 3, CIRCLE_COLOR, -1)
    
    for det in detections:
        # 只显示ID为0、1、2、3的检测结果
        object_id = det['id']
        if object_id not in ['0', '1', '2', '3']:
            continue  # 跳过其他ID
            
        center_x = int(det['center_x'])
        center_y = int(det['center_y'])
        width = det['width']
        height = det['height']
        angle = det['angle']
        confidence = det['confidence']
        
        # 检查目标是否离开圆圈
        check_circle_exit(object_id, center_x, center_y)
        
        # 根据目标是否在圆圈内选择颜色
        in_circle = is_target_in_circle(center_x, center_y)
        center_color = (0, 255, 0) if in_circle else (0, 0, 255)  # 绿色：圆圈内，红色：圆圈外
        box_color = (255, 0, 0) if in_circle else (0, 0, 255)     # 蓝色：圆圈内，红色：圆圈外
        
        # 绘制中心点
        cv2.circle(frame, (center_x, center_y), 2, center_color, -1)
        
        # 绘制旋转矩形框
        try:
            # 计算矩形的四个角点
            cos_a = np.cos(np.radians(angle))
            sin_a = np.sin(np.radians(angle))
            
            # 矩形的半宽和半高
            w_half = width / 2
            h_half = height / 2
            
            # 计算四个角点
            corners = np.array([
                [-w_half, -h_half],
                [w_half, -h_half],
                [w_half, h_half],
                [-w_half, h_half]
            ])
            
            # 旋转变换
            rotation_matrix = np.array([
                [cos_a, -sin_a],
                [sin_a, cos_a]
            ])
            
            rotated_corners = corners @ rotation_matrix.T
            rotated_corners[:, 0] += center_x
            rotated_corners[:, 1] += center_y
            
            # 绘制矩形
            points = rotated_corners.astype(int)
            cv2.polylines(frame, [points], True, box_color, 1)  # 调细线条粗细
            
        except Exception as e:
            # 如果旋转矩形绘制失败，绘制普通矩形
            x1 = int(center_x - width/2)
            y1 = int(center_y - height/2)
            x2 = int(center_x + width/2)
            y2 = int(center_y + height/2)
            cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 1)
        
        # 文字标签设置
        font = cv2.FONT_HERSHEY_DUPLEX  # 使用更清晰的字体
        font_scale = 0.35  # 减小字体尺寸
        thickness = 1     # 最小字体粗细
        
        # 只显示ID标签
        label = f"ID:{object_id}"
        
        # 计算文本位置
        text_x = center_x + 10
        text_y = center_y - 10
        
        # 直接绘制黄色文本（无背景）- 使用更细的线条
        cv2.putText(frame, label, (text_x, text_y), font, font_scale, (0, 255, 255), 1, cv2.LINE_AA)

def is_target_in_circle(center_x, center_y):
    """检查目标是否在圆圈内"""
    distance = np.sqrt((center_x - CIRCLE_CENTER_X)**2 + (center_y - CIRCLE_CENTER_Y)**2)
    return distance <= CIRCLE_RADIUS

def check_circle_exit(object_id, center_x, center_y):
    """检查目标是否离开圆圈并打印警告"""
    global target_status
    
    current_in_circle = is_target_in_circle(center_x, center_y)
    
    # 如果这是第一次检测到这个目标，记录其状态
    if object_id not in target_status:
        target_status[object_id] = current_in_circle
        return
    
    # 检查状态是否发生变化（从圆圈内移动到圆圈外）
    previous_in_circle = target_status[object_id]
    
    if previous_in_circle and not current_in_circle:
        print(f"⚠️  警告: ID:{object_id} 离开了圆圈！")
    
    # 更新状态
    target_status[object_id] = current_in_circle

def main():
    """主函数"""
    global cap
    
    print("🚀 启动YOLO目标检测系统...")
    
    # 初始化模型
    if not initialize_model():
        print("❌ 模型初始化失败，程序退出")
        return
    
    # 初始化摄像头
    if not initialize_camera():
        print("❌ 摄像头初始化失败，程序退出")
        return
    
    # 创建显示窗口
    cv2.namedWindow("YOLO Detection", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("YOLO Detection", 1000, 750)
    
    print("✅ 系统初始化完成！")
    print("📺 开始实时检测...")
    print("💡 按 'q' 键退出程序")
    
    # 性能统计变量
    frame_count = 0
    fps_start_time = time.time()
    fps = 0
    
    try:
        while True:
            # 读取摄像头帧
            ret, frame = cap.read()
            if not ret:
                print("❌ 无法读取摄像头数据")
                break
            
            frame_count += 1
            current_time = time.time()
            
            # 计算FPS
            if frame_count % 30 == 0:
                fps = 30 / (current_time - fps_start_time)
                fps_start_time = current_time
            
            # 执行目标检测
            start_time = time.time()
            detections = detect_objects(frame)
            detection_time = time.time() - start_time
            
            # 绘制检测结果
            draw_detections(frame, detections)
            
            # 性能信息显示设置
            info_font = cv2.FONT_HERSHEY_SIMPLEX  # 使用更细的字体
            info_font_scale = 0.5  # 减小字体大小
            info_thickness = 1  # 最小字体粗细
            
            # 性能信息列表
            info_texts = [
                f"FPS: {fps:.1f}",
                f"Detection Time: {detection_time*1000:.1f}ms", 
                f"Objects: {len(detections)}",
                "Press 'q' to quit"
            ]
            
            # 文字颜色列表
            info_colors = [
                (0, 255, 0),      # 绿色 - FPS
                (0, 100, 255),    # 橙色 - 检测时间
                (0, 255, 255),    # 黄色 - 对象数量
                (255, 255, 255)   # 白色 - 退出提示
            ]
            
            # 绘制性能信息（无背景）
            for i, (text, color) in enumerate(zip(info_texts, info_colors)):
                # 计算文本位置
                text_x = 10
                text_y = 25 + i * 25  # 减小行间距
                
                # 直接绘制文本（无背景）- 使用抗锯齿让文字更细腻
                cv2.putText(frame, text, (text_x, text_y), 
                           info_font, info_font_scale, color, 1, cv2.LINE_AA)
            
            # 显示图像
            cv2.imshow("YOLO Detection", frame)
            
            # 检查退出键
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                print("🛑 用户退出程序")
                break
                
    except KeyboardInterrupt:
        print("\n🛑 程序被中断")
    except Exception as e:
        print(f"❌ 程序运行错误: {e}")
    finally:
        # 清理资源
        if cap is not None:
            cap.release()
        cv2.destroyAllWindows()
        print("🔚 程序结束")

if __name__ == "__main__":
    main()
