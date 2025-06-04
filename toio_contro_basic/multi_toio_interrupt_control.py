import asyncio
import random
import sys
from toio import *
from typing import Dict, List

class ToioController:
    """单个toio的控制器"""
    
    def __init__(self, cube, cube_id: int):
        self.cube = cube
        self.id = cube_id
        self.state = "random"  # "random" 或 "special"
        self.state_event = asyncio.Event()
        
    async def random_move(self):
        """随机移动"""
        # 随机生成速度（20-50）
        base_speed = random.randint(20, 40)
        # 随机生成转向（-20到20的偏差）
        turn_offset = random.randint(-20, 20)
        
        left_speed = base_speed + turn_offset
        right_speed = base_speed - turn_offset
        
        # 限制速度范围
        left_speed = max(-50, min(50, left_speed))
        right_speed = max(-50, min(50, right_speed))
        
        await self.cube.api.motor.motor_control(left=left_speed, right=right_speed)
        
    async def special_move(self):
        """特殊移动：原地转180度，然后前进1秒"""
        print(f"Toio {self.id}: 执行特殊动作")
        
        # 原地转180度（0.5秒）
        await self.cube.api.motor.motor_control(left=50, right=-50)
        await asyncio.sleep(0.5)
        
        # 向前移动1秒
        await self.cube.api.motor.motor_control(left=40, right=40)
        await asyncio.sleep(1)
        
        # 恢复随机移动状态
        self.state = "random"
        print(f"Toio {self.id}: 回到随机移动状态")
        
    async def control_loop(self):
        """主控制循环"""
        try:
            while True:
                if self.state == "random":
                    await self.random_move()
                    # 随机移动持续时间（0.5-2秒）
                    await asyncio.sleep(random.uniform(0.5, 2.0))
                elif self.state == "special":
                    await self.special_move()
                    
                # 检查是否有状态变化请求
                if self.state_event.is_set():
                    self.state_event.clear()
                    
        except asyncio.CancelledError:
            # 停止移动
            await self.cube.api.motor.motor_control(left=0, right=0)
            raise

class MultiToioController:
    """多toio控制器"""
    
    def __init__(self):
        self.controllers: Dict[int, ToioController] = {}
        self.running = True
        
    async def initialize(self, cubes):
        """初始化所有toio控制器"""
        for i in range(4):
            controller = ToioController(cubes[i], i)
            self.controllers[i] = controller
            
            # 设置不同颜色的LED以便区分
            colors = [
                Color(r=255, g=0, b=0),    # 0号：红色
                Color(r=0, g=255, b=0),    # 1号：绿色
                Color(r=0, g=0, b=255),    # 2号：蓝色
                Color(r=255, g=255, b=0),  # 3号：黄色
            ]
            
            await cubes[i].api.indicator.turn_on(
                IndicatorParam(duration_ms=0, color=colors[i])
            )
            
    async def input_handler(self):
        """处理控制台输入"""
        print("\n控制说明：")
        print("- 输入 0、1、2、3 控制对应的toio执行特殊动作")
        print("- 输入 q 退出程序")
        print("-" * 40)
        
        loop = asyncio.get_event_loop()
        
        while self.running:
            try:
                # 使用线程执行器来处理阻塞的input()
                user_input = await loop.run_in_executor(None, input, "\n请输入toio ID (0-3) 或 q 退出: ")
                
                if user_input.lower() == 'q':
                    print("正在退出程序...")
                    self.running = False
                    break
                    
                try:
                    toio_id = int(user_input)
                    if 0 <= toio_id <= 3:
                        controller = self.controllers[toio_id]
                        if controller.state == "random":
                            controller.state = "special"
                            controller.state_event.set()
                            print(f"Toio {toio_id}: 切换到特殊动作模式")
                        else:
                            print(f"Toio {toio_id}: 正在执行特殊动作，请稍后再试")
                    else:
                        print("无效的ID，请输入0-3之间的数字")
                except ValueError:
                    print("无效输入，请输入数字或'q'")
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"输入处理错误: {e}")
                
    async def run(self):
        """运行主程序"""
        print("=== 多Toio中断控制程序 ===")
        print("正在连接4个toio设备...")
        
        try:
            async with MultipleToioCoreCubes(cubes=4, names=["0", "1", "2", "3"]) as cubes:
                print("成功连接4个toio设备！")
                
                # 初始化控制器
                await self.initialize(cubes)
                
                # 创建所有任务
                tasks = []
                
                # 为每个toio创建控制任务
                for controller in self.controllers.values():
                    tasks.append(asyncio.create_task(controller.control_loop()))
                    
                # 创建输入处理任务
                input_task = asyncio.create_task(self.input_handler())
                tasks.append(input_task)
                
                print("所有toio开始随机移动...")
                
                try:
                    # 等待直到用户退出
                    await input_task
                except asyncio.CancelledError:
                    pass
                finally:
                    # 取消所有控制任务
                    for task in tasks:
                        if not task.done():
                            task.cancel()
                            
                    # 等待所有任务完成
                    await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # 停止所有toio并关闭LED
                    print("正在停止所有toio...")
                    stop_tasks = []
                    for i in range(4):
                        stop_tasks.append(cubes[i].api.motor.motor_control(left=0, right=0))
                        stop_tasks.append(cubes[i].api.indicator.turn_off())
                    await asyncio.gather(*stop_tasks)
                    
        except Exception as e:
            print(f"程序错误: {e}")
            import traceback
            traceback.print_exc()

async def main():
    """主程序入口"""
    controller = MultiToioController()
    await controller.run()
    print("程序已退出")

if __name__ == "__main__":
    # 设置事件循环策略（Windows系统需要）
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n程序被用户中断") 