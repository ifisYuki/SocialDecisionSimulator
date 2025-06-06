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

# ========== 归正功能配置参数 ==========
STUCK_DISTANCE_THRESHOLD = 15  # 位置变化阈值（像素）
STUCK_TIME_THRESHOLD = 6.0     # 卡住时间阈值（秒）
RECOVERY_COOLDOWN_TIME = 15.0  # 归正冷却时间（秒）
DETECTION_LOST_THRESHOLD = 3.0 # 检测丢失触发归正的时间（秒）

# ========== 全局变量 ==========
model = None
cap = None
target_status = {}
exit_event_queue = queue.Queue()  # 用于传递离开圆圈的事件
video_stream_server_running = False

class ToioController:
    """单个toio的控制器 - 带有统一归正功能"""
    
    def __init__(self, cube, cube_id: int):
        self.cube = cube
        self.id = cube_id
        self.state = "random"
        self.state_event = asyncio.Event()
        self.last_detected_time = time.time()
        self.is_detected = False
        
        # 归正功能相关状态
        self.current_position = None
        self.stuck_detection_start_time = None
        self.position_samples = []
        self.last_recovery_time = 0
        
    async def random_move(self):
        """随机移动 - 每个ID有不同的移动特性"""
        try:
            # 根据ID设置不同的移动参数
            if self.id == 0:  # ID 0: 快速直行型
                base_speed = random.randint(15, 40)
                turn_offset = random.randint(-10, 10)
                
            elif self.id == 1:  # ID 1: 转圈型
                base_speed = random.randint(10, 25)
                turn_offset = random.randint(-25, 25)
                
            elif self.id == 2:  # ID 2: 谨慎型
                base_speed = random.randint(5, 20)
                if random.random() < 0.1:  # 10%概率停顿
                    await self.cube.api.motor.motor_control(left=0, right=0)
                    await asyncio.sleep(random.uniform(0.5, 1.0))
                    return
                turn_offset = random.randint(-15, 15)
            
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
            self.state = "random"
            if "Not connected" not in str(e) and "Unreachable" not in str(e):
                print(f"⚠️  Toio {self.id}: 特殊动作失败 - {e}")

    async def recovery_move(self):
        """
        统一归正动作 - 处理检测丢失和电机卡住两种情况
        动作序列：停止 → 后退 → 转180度 → 前进 → 调整方向
        """
        try:
            print(f"🔧 Toio {self.id}: ===== 开始执行归正脱困动作 =====")
            
            # 记录归正时间
            self.last_recovery_time = time.time()
            
            # 第一步：立即停止
            print(f"⏹️ Toio {self.id}: 步骤1 - 停止电机")
            await self.cube.api.motor.motor_control(left=0, right=0)
            await asyncio.sleep(0.5)
            
            # 第二步：强力后退
            print(f"⬅️ Toio {self.id}: 步骤2 - 强力后退（3秒，速度-30）")
            await self.cube.api.motor.motor_control(left=-30, right=-30)
            
            for i in range(6):  # 3秒 = 6 × 0.5秒
                if self.is_detected and self.state != "recovery":
                    print(f"✅ Toio {self.id}: 后退中检测恢复，脱困成功")
                    break
                print(f"   ⬅️ 后退进度: {(i+1)*0.5:.1f}/3.0秒")
                await asyncio.sleep(0.5)
            
            # 第三步：停顿准备转向
            print(f"⏸️ Toio {self.id}: 步骤3 - 准备转向")
            await self.cube.api.motor.motor_control(left=0, right=0)
            await asyncio.sleep(0.3)
            
            # 第四步：原地转180度
            print(f"🔄 Toio {self.id}: 步骤4 - 原地转180度")
            await self.cube.api.motor.motor_control(left=35, right=-35)
            await asyncio.sleep(1.3)
            
            # 第五步：停顿稳定
            await self.cube.api.motor.motor_control(left=0, right=0)
            await asyncio.sleep(0.3)
            
            # 第六步：中速前进
            print(f"➡️ Toio {self.id}: 步骤5 - 中速前进（2.5秒，速度30）")
            await self.cube.api.motor.motor_control(left=30, right=30)
            
            for i in range(5):  # 2.5秒 = 5 × 0.5秒
                if self.is_detected and self.state != "recovery":
                    print(f"✅ Toio {self.id}: 前进中检测恢复，脱困成功")
                    break
                print(f"   ➡️ 前进进度: {(i+1)*0.5:.1f}/2.5秒")
                await asyncio.sleep(0.5)
            
            # 第七步：随机方向微调
            print(f"↩️ Toio {self.id}: 步骤6 - 方向微调")
            if random.random() < 0.5:
                await self.cube.api.motor.motor_control(left=20, right=35)  # 右转
                print(f"   🔄 执行右转微调")
            else:
                await self.cube.api.motor.motor_control(left=35, right=20)  # 左转
                print(f"   🔄 执行左转微调")
            
            await asyncio.sleep(0.6)
            
            # 第八步：最终停止
            await self.cube.api.motor.motor_control(left=0, right=0)
            await asyncio.sleep(0.2)
            
            print(f"✅ Toio {self.id}: ===== 归正脱困动作完成 =====")
            
        except Exception as e:
            print(f"⚠️ Toio {self.id}: 归正动作执行异常 - {e}")
            try:
                await self.cube.api.motor.motor_control(left=0, right=0)
            except:
                pass
        finally:
            # 重置状态
            self.state = "random"
            self.stuck_detection_start_time = None
            self.position_samples = []
            print(f"↩️ Toio {self.id}: 状态重置，恢复随机移动模式")

    def update_position_for_stuck_detection(self, position):
        """更新toio位置信息，用于卡住检测"""
        self.current_position = position

    async def check_need_recovery(self):
        """
        统一的归正检测函数
        检测条件：
        1. 检测丢失超过一定时间 OR
        2. 检测到位置不变但电机在运行
        """
        current_time = time.time()
        
        # 检查冷却时间
        if current_time - self.last_recovery_time < RECOVERY_COOLDOWN_TIME:
            return False
        
        # 条件1: 检测丢失超过阈值时间
        if not self.is_detected:
            time_lost = current_time - self.last_detected_time
            if time_lost > DETECTION_LOST_THRESHOLD:
                print(f"🚫 Toio {self.id}: 检测丢失超过 {time_lost:.1f}秒，触发归正")
                return True
        
        # 条件2: 位置不变但电机在运行（只有在被检测到时才检查）
        if self.is_detected and self.state == "random":
            if self.current_position is None:
                return False
            
            # 记录位置样本
            self.position_samples.append((current_time, self.current_position))
            
            # 只保留最近8秒的样本
            self.position_samples = [
                (t, pos) for t, pos in self.position_samples 
                if current_time - t <= 8.0
            ]
            
            # 需要至少有3秒的样本才开始检测
            if len(self.position_samples) < 30:  # 30个样本约3秒
                return False
            
            # 计算位置变化
            positions = [pos for _, pos in self.position_samples]
            
            # 计算最大位置变化距离
            max_distance = 0
            for i in range(len(positions)):
                for j in range(i + 1, len(positions)):
                    distance = ((positions[i][0] - positions[j][0])**2 + 
                               (positions[i][1] - positions[j][1])**2)**0.5
                    max_distance = max(max_distance, distance)
            
            # 检查是否卡住
            if max_distance < STUCK_DISTANCE_THRESHOLD:
                # 位置变化很小，开始计时
                if self.stuck_detection_start_time is None:
                    self.stuck_detection_start_time = current_time
                    print(f"⚠️ Toio {self.id}: 开始检测卡住状态（位置变化: {max_distance:.1f}像素）")
                
                # 检查是否超过卡住时间阈值
                stuck_duration = current_time - self.stuck_detection_start_time
                
                if stuck_duration > STUCK_TIME_THRESHOLD:
                    print(f"🚫 Toio {self.id}: 检测到电机空转卡住！")
                    print(f"   📊 位置变化: {max_distance:.1f}像素（阈值: {STUCK_DISTANCE_THRESHOLD}）")
                    print(f"   ⏱️ 卡住时长: {stuck_duration:.1f}秒")
                    print(f"   🔧 触发归正脱困程序")
                    
                    # 重置检测状态
                    self.stuck_detection_start_time = None
                    self.position_samples = []
                    return True
            else:
                # 位置有明显变化，重置检测
                if self.stuck_detection_start_time is not None:
                    print(f"✅ Toio {self.id}: 位置恢复变化（{max_distance:.1f}像素），重置卡住检测")
                self.stuck_detection_start_time = None
        
        return False

    async def handle_recovery_check(self):
        """
        简化的恢复检测处理函数
        替代原来复杂的状态处理逻辑
        """
        # 检查是否需要归正
        if await self.check_need_recovery():
            print(f"🔧 Toio {self.id}: 切换到归正模式")
            self.state = "recovery"
            self.state_event.set()
            return True
        
        # 如果不需要归正，但检测丢失了，进入暂停状态
        if not self.is_detected and self.state == "random":
            current_time = time.time()
            time_lost = current_time - self.last_detected_time
            
            if time_lost > 0.4:  # 短暂丢失就暂停，等待归正检测
                print(f"⚠️  Toio {self.id}: 检测丢失，暂停运动等待归正检测")
                self.state = "lost"
                try:
                    await self.cube.api.motor.motor_control(left=0, right=0)
                except:
                    pass
        
        return False
                
    def update_detection_status(self, detected: bool):
        """更新视觉检测状态，控制状态恢复"""
        if detected:
            self.last_detected_time = time.time()
            self.is_detected = True
            
            # 检测恢复时，从任何异常状态回到正常状态
            if self.state in ["lost", "recovery"]:
                print(f"✅ Toio {self.id}: 检测恢复，退出 {self.state} 状态")
                self.state = "random"
                self.state_event.set()
                
                # 重置相关检测状态
                self.stuck_detection_start_time = None
                self.position_samples = []
        else:
            self.is_detected = False
            
    async def control_loop(self):
        """主控制循环 - 简化版"""
        try:
            while True:
                try:
                    # 统一的恢复检测
                    await self.handle_recovery_check()
                    
                    if self.state == "random" and self.is_detected:
                        await self.random_move()
                        
                        # 根据ID设置不同的等待时间
                        if self.id == 0:
                            await asyncio.sleep(random.uniform(0.1, 0.2))
                        elif self.id == 1:
                            await asyncio.sleep(random.uniform(0.2, 0.3))
                        elif self.id == 2:
                            await asyncio.sleep(random.uniform(0.3, 0.4))
                        else:
                            await asyncio.sleep(random.uniform(0.4, 0.5))
                            
                    elif self.state == "special" and self.is_detected:
                        await self.special_move()
                    elif self.state == "recovery":  # 统一的归正处理
                        await self.recovery_move()
                    elif self.state == "lost":
                        # 暂停状态，等待检测恢复或归正触发
                        await asyncio.sleep(0.1)
                    else:
                        await asyncio.sleep(0.1)
                        
                    if self.state_event.is_set():
                        self.state_event.clear()
                        
                except Exception as e:
                    if "Not connected" in str(e) or "Unreachable" in str(e):
                        print(f"⚠️  Toio {self.id}: 连接断开")
                        break
                    else:
                        print(f"⚠️  Toio {self.id}: 控制错误 - {e}")
                        await asyncio.sleep(1)
                        
        except asyncio.CancelledError:
            try:
                await self.cube.api.motor.motor_control(left=0, right=0)
            except:
                pass
            raise

class CombinedController:
    """组合控制器 - 整合YOLO检测和toio控制"""
    
    def __init__(self):
        self.controllers: Dict[int, ToioController] = {}
        self.running = True
        self.yolo_thread = None
        
    async def initialize_toio(self, cubes):
        """初始化所有toio控制器 - 增强版"""
        colors = [
            Color(r=255, g=0, b=0),    # 0号：红色
            Color(r=0, g=255, b=0),    # 1号：绿色
            Color(r=0, g=0, b=255),    # 2号：蓝色
        ]
        
        actual_cube_count = len(cubes)
        print(f"📱 实际连接的toio设备数量: {actual_cube_count}")
        print("🔧 开始逐个初始化toio设备...")
        
        for i in range(actual_cube_count):
            try:
                print(f"\n🔄 正在初始化 Toio {i}...")
                
                # 创建控制器
                print(f"   📦 创建控制器对象...")
                controller = ToioController(cubes[i], i)
                self.controllers[i] = controller
                
                # 设备间隔等待
                if i > 0:
                    print(f"   ⏳ 等待0.5秒避免冲突...")
                    await asyncio.sleep(0.5)
                
                # 检查设备连接
                print(f"   🔍 检查设备连接状态...")
                if not hasattr(cubes[i], 'api') or cubes[i].api is None:
                    raise Exception("设备API不可用")
                
                # 设置指示灯
                print(f"   🎨 设置指示灯颜色...")
                color_index = i if i < len(colors) else i % len(colors)
                color = colors[color_index]
                color_name = ["红色", "绿色", "蓝色"][color_index] if color_index < 3 else f"颜色{color_index}"
                
                print(f"   💡 点亮{color_name}指示灯...")
                await cubes[i].api.indicator.turn_on(
                    IndicatorParam(duration_ms=0, color=color)
                )
                
                # 等待指示灯生效
                await asyncio.sleep(0.3)
                
                # 测试电机
                print(f"   🔧 测试电机功能...")
                await cubes[i].api.motor.motor_control(left=0, right=0)
                await asyncio.sleep(0.1)
                
                print(f"✅ Toio {i} 初始化完成！（{color_name}）")
                
            except Exception as e:
                print(f"❌ Toio {i} 初始化失败: {e}")
                print(f"   🔍 错误详情: {type(e).__name__}")
                
                # 尝试基本恢复
                try:
                    if hasattr(cubes[i], 'api') and cubes[i].api is not None:
                        print(f"   🔄 尝试基本初始化...")
                        await cubes[i].api.motor.motor_control(left=0, right=0)
                        await cubes[i].api.indicator.turn_off()
                        await asyncio.sleep(0.2)
                        
                        color_index = i if i < len(colors) else i % len(colors)
                        await cubes[i].api.indicator.turn_on(
                            IndicatorParam(duration_ms=0, color=colors[color_index])
                        )
                        print(f"✅ Toio {i} 基本初始化成功")
                    else:
                        print(f"⚠️  Toio {i} 设备API不可用，跳过初始化")
                except Exception as retry_e:
                    print(f"⚠️  Toio {i} 重试失败: {retry_e}")
                
                continue
        
        # 初始化总结
        print(f"\n📊 初始化总结:")
        print(f"   🎯 尝试初始化: {actual_cube_count} 个设备")
        print(f"   ✅ 成功初始化: {len(self.controllers)} 个设备")
        
        if len(self.controllers) == 0:
            raise Exception("没有任何toio设备初始化成功")
        
        # 指示灯闪烁确认
        print(f"🎉 执行指示灯闪烁确认...")
        for i in self.controllers.keys():
            try:
                for _ in range(3):
                    await cubes[i].api.indicator.turn_off()
                    await asyncio.sleep(0.2)
                    color_index = i if i < len(colors) else i % len(colors)
                    await cubes[i].api.indicator.turn_on(
                        IndicatorParam(duration_ms=0, color=colors[color_index])
                    )
                    await asyncio.sleep(0.2)
            except Exception as e:
                print(f"⚠️  Toio {i} 闪烁确认失败: {e}")
        
        print(f"✅ 所有toio设备初始化完成！")
            
    async def event_handler(self):
        """处理来自YOLO的离开圆圈事件"""
        while self.running:
            try:
                try:
                    toio_id = exit_event_queue.get_nowait()
                    
                    if toio_id in ['0', '1', '2']:
                        toio_index = int(toio_id)
                        if toio_index in self.controllers:
                            controller = self.controllers[toio_index]
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
        print("=== YOLO + Toio 联合控制系统（带统一归正功能）===")
        print("正在初始化系统...")
        
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                print(f"\n🔄 尝试连接toio设备... (第{retry_count + 1}次)")
                print("📡 正在扫描蓝牙设备...")
                
                async with MultipleToioCoreCubes(cubes=3, names=["0", "1", "2"]) as cubes:
                    print("✅ 蓝牙连接成功！")
                    print(f"📱 检测到 {len(cubes)} 个toio设备")
                    
                    # 验证每个设备
                    for i, cube in enumerate(cubes):
                        try:
                            print(f"🔍 验证设备 {i}: {cube}")
                            if hasattr(cube, 'api') and cube.api is not None:
                                print(f"   ✅ 设备 {i} API可用")
                            else:
                                print(f"   ⚠️  设备 {i} API不可用")
                        except Exception as e:
                            print(f"   ❌ 设备 {i} 验证失败: {e}")
                    
                    print("⏳ 等待2秒让设备稳定...")
                    await asyncio.sleep(2)
                    
                    print("🔧 开始初始化toio控制器...")
                    await self.initialize_toio(cubes)
                    
                    print("🔧 正在启动YOLO检测系统...")
                    self.start_yolo_detection()
                    print("✅ YOLO检测系统启动成功！")
                    
                    # 创建任务
                    tasks = []
                    
                    for controller in self.controllers.values():
                        tasks.append(asyncio.create_task(controller.control_loop()))
                    
                    event_task = asyncio.create_task(self.event_handler())
                    tasks.append(event_task)
                    
                    print("✅ 系统启动完成！")
                    print("📷 YOLO检测已启动，具备以下功能：")
                    print("   🎯 离开圆圈时自动执行特殊动作")
                    print("   🔧 统一归正功能：检测丢失或卡住时自动脱困")
                    print(f"   📊 归正参数：检测丢失>{DETECTION_LOST_THRESHOLD}秒 或 位置变化<{STUCK_DISTANCE_THRESHOLD}像素且持续>{STUCK_TIME_THRESHOLD}秒")
                    print("按 'q' 键退出程序")
                    
                    while self.running:
                        await asyncio.sleep(1)
                        
                    print("\n正在安全关闭程序...")
                    self.running = False
                    
                    for task in tasks:
                        if not task.done():
                            task.cancel()
                            
                    await asyncio.gather(*tasks, return_exceptions=True)
                    
                    print("正在停止所有toio...")
                    stop_tasks = []
                    for i in range(len(cubes)):
                        try:
                            stop_tasks.append(cubes[i].api.motor.motor_control(left=0, right=0))
                            stop_tasks.append(cubes[i].api.indicator.turn_off())
                        except Exception:
                            pass
                            
                    await asyncio.gather(*stop_tasks, return_exceptions=True)
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
    
    if previous_in_circle and not current_in_circle:
        print(f"⚠️  检测到: ID:{object_id} 离开了圆圈！")
        exit_event_queue.put(object_id)
    
    target_status[object_id] = current_in_circle

def draw_detections(frame, detections):
    """在画面上绘制检测结果 - 增加了位置更新功能"""
    
    if controller:
        for toio_controller in controller.controllers.values():
            toio_controller.update_detection_status(False)
    
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
        
        if controller and object_id in ['0', '1', '2']:
            toio_id = int(object_id)
            if toio_id in controller.controllers:
                controller.controllers[toio_id].update_detection_status(True)
                controller.controllers[toio_id].update_position_for_stuck_detection((center_x, center_y))
        
        check_circle_exit(object_id, center_x, center_y)
        
        in_circle = is_target_in_circle(center_x, center_y)
        center_color = (0, 255, 0) if in_circle else (0, 0, 255)
        box_color = (255, 0, 0) if in_circle else (0, 0, 255)
        
        cv2.circle(frame, (center_x, center_y), 2, center_color, -1)
        
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
        
        label = f"ID:{object_id}"
        cv2.putText(frame, label, (center_x + 10, center_y - 10), 
                   cv2.FONT_HERSHEY_DUPLEX, 0.35, (0, 255, 255), 1, cv2.LINE_AA)

        # 显示归正检测状态
        if controller and object_id in ['0', '1', '2']:
            toio_id = int(object_id)
            if toio_id in controller.controllers:
                toio_ctrl = controller.controllers[toio_id]
                if hasattr(toio_ctrl, 'stuck_detection_start_time') and toio_ctrl.stuck_detection_start_time:
                    stuck_time = time.time() - toio_ctrl.stuck_detection_start_time
                    cv2.putText(frame, f"Stuck: {stuck_time:.1f}s", (center_x + 10, center_y + 10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 0, 255), 1, cv2.LINE_AA)
                
                status_text = f"State: {toio_ctrl.state}"
                cv2.putText(frame, status_text, (center_x + 10, center_y + 25), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 255, 0), 1, cv2.LINE_AA)

def run_yolo_detection(is_running):
    """YOLO检测主循环（在单独线程中运行）"""
    global cap, video_stream_server_running
    
    if not initialize_model() or not initialize_camera():
        print("❌ YOLO初始化失败")
        return

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
    
    cv2.namedWindow("YOLO Detection with Unified Recovery", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("YOLO Detection with Unified Recovery", 1000, 750)
    
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
            
            detections = detect_objects(frame)
            draw_detections(frame, detections)
            
            cv2.putText(frame, f"FPS: {fps:.1f}", (10, 25), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1, cv2.LINE_AA)
            cv2.putText(frame, f"Objects: {len(detections)}", (10, 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1, cv2.LINE_AA)
            cv2.putText(frame, "Press 'q' to quit", (10, 75), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
            
            cv2.putText(frame, f"Recovery: Lost>{DETECTION_LOST_THRESHOLD}s OR Stuck<{STUCK_DISTANCE_THRESHOLD}px>{STUCK_TIME_THRESHOLD}s", (10, 100), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 150, 0), 1, cv2.LINE_AA)
            
            if VIDEO_STREAM_AVAILABLE:
                cv2.putText(frame, "Stream: http://localhost:5000/video_feed", (10, 125), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 200, 0), 1, cv2.LINE_AA)
            
            if VIDEO_STREAM_AVAILABLE:
                try:
                    update_detection_frame(frame)
                except Exception as e:
                    pass
            
            cv2.imshow("YOLO Detection with Unified Recovery", frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                controller.running = False
                break
                
    except Exception as e:
        print(f"❌ YOLO检测错误: {e}")
    finally:
        if cap is not None:
            cap.release()
        cv2.destroyAllWindows()

# ========== 主程序入口 ==========

controller = None

def signal_handler(signum, frame):
    """处理Ctrl+C信号"""
    global controller
    print("\n\n⚠️  收到退出信号，正在安全关闭程序...")
    if controller:
        controller.running = False

async def main():
    """主程序入口"""
    global controller
    
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
        print("🚀 启动带统一归正功能的YOLO + Toio控制系统...")
        print("🔧 统一归正功能参数：")
        print(f"   📊 位置变化阈值: {STUCK_DISTANCE_THRESHOLD} 像素")
        print(f"   ⏱️ 卡住时间阈值: {STUCK_TIME_THRESHOLD} 秒")
        print(f"   🕐 检测丢失阈值: {DETECTION_LOST_THRESHOLD} 秒")
        print(f"   🔄 归正冷却时间: {RECOVERY_COOLDOWN_TIME} 秒")
        print("")
        print("💡 归正触发条件:")
        print("   1️⃣ 检测丢失超过3秒 → 立即归正")
        print("   2️⃣ 位置不变超过6秒且电机运行 → 归正")
        print("   🎯 两种情况都使用同一套归正动作")
        print("")
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n✅ 程序正常退出")
    except Exception as e:
        print(f"\n❌ 程序异常: {e}")