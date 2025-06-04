import asyncio
from toio import *

async def multi_toio_control():
    """多toio控制例子"""
    
    print("=== 多toio控制演示 ===")
    print("正在搜索toio设备...")
    
    # 1. 搜索多个toio设备（最多搜索3个）
    device_list = await BLEScanner.scan(3, timeout=10)
    
    if len(device_list) == 0:
        print("未找到任何toio设备，请检查设备是否开启")
        return
    elif len(device_list) == 1:
        print("只找到1个toio设备，将进行单设备演示")
    else:
        print(f"找到{len(device_list)}个toio设备")
    
    # 2. 为每个设备分配名称
    toio_names = ["红队", "蓝队", "绿队"]
    cubes = []
    
    # 3. 连接所有设备
    for i, device in enumerate(device_list):
        try:
            cube = ToioCoreCube(device.interface)
            await cube.connect()
            cube.name = toio_names[i]  # 给每个toio分配名称
            cubes.append(cube)
            print(f"已连接到{cube.name}toio")
        except Exception as e:
            print(f"连接设备{i+1}失败: {e}")
    
    if len(cubes) == 0:
        print("没有成功连接任何设备")
        return
    
    try:
        # 4. 单独控制演示
        await individual_control_demo(cubes)
        
        # 5. 协同控制演示
        if len(cubes) >= 2:
            await coordination_demo(cubes)
        
        # 6. 竞赛演示
        if len(cubes) >= 2:
            await race_demo(cubes)
            
    finally:
        # 7. 断开所有连接
        await disconnect_all_cubes(cubes)

async def individual_control_demo(cubes):
    """单独控制演示"""
    print("\n--- 单独控制演示 ---")
    
    for i, cube in enumerate(cubes):
        color_map = [
            Color(r=255, g=0, b=0),    # 红色
            Color(r=0, g=0, b=255),    # 蓝色  
            Color(r=0, g=255, b=0),    # 绿色
        ]
        
        print(f"{cube.name}开始单独演示...")
        
        # 点亮对应颜色的LED
        await cube.api.indicator.turn_on(
            IndicatorParam(duration_ms=2000, color=color_map[i])
        )
        
        # 每个toio执行不同的动作
        if i == 0:  # 第一个toio：前进后退
            await cube.api.motor.motor_control(left=40, right=40)
            await asyncio.sleep(1)
            await cube.api.motor.motor_control(left=-40, right=-40)
            await asyncio.sleep(1)
        elif i == 1:  # 第二个toio：原地旋转
            await cube.api.motor.motor_control(left=40, right=-40)
            await asyncio.sleep(2)
        else:  # 第三个toio：八字形
            await cube.api.motor.motor_control(left=50, right=30)
            await asyncio.sleep(1)
            await cube.api.motor.motor_control(left=30, right=50)
            await asyncio.sleep(1)
        
        # 停止并关闭LED
        await cube.api.motor.motor_control(left=0, right=0)
        await cube.api.indicator.turn_off()
        
        await asyncio.sleep(0.5)  # 稍作间隔

async def coordination_demo(cubes):
    """协同控制演示"""
    print("\n--- 协同控制演示 ---")
    print("所有toio将同时执行动作...")
    
    # 同时点亮所有LED（不同颜色）
    led_tasks = []
    colors = [
        Color(r=255, g=0, b=0),    # 红色
        Color(r=0, g=0, b=255),    # 蓝色
        Color(r=0, g=255, b=0),    # 绿色
    ]
    
    for i, cube in enumerate(cubes):
        task = cube.api.indicator.turn_on(
            IndicatorParam(duration_ms=3000, color=colors[i % 3])
        )
        led_tasks.append(task)
    
    await asyncio.gather(*led_tasks)
    print("所有LED已点亮")
    
    # 同时前进
    print("同时前进...")
    move_tasks = []
    for cube in cubes:
        task = cube.api.motor.motor_control(left=35, right=35)
        move_tasks.append(task)
    
    await asyncio.gather(*move_tasks)
    await asyncio.sleep(2)
    
    # 同时停止
    print("同时停止...")
    stop_tasks = []
    for cube in cubes:
        task = cube.api.motor.motor_control(left=0, right=0)
        stop_tasks.append(task)
    
    await asyncio.gather(*stop_tasks)
    
    # 关闭所有LED
    led_off_tasks = []
    for cube in cubes:
        task = cube.api.indicator.turn_off()
        led_off_tasks.append(task)
    
    await asyncio.gather(*led_off_tasks)

async def race_demo(cubes):
    """竞赛演示"""
    print("\n--- 竞赛演示 ---")
    print("两个toio将进行短距离竞赛...")
    
    # 只使用前两个toio
    racer1, racer2 = cubes[0], cubes[1]
    
    # 准备阶段 - 闪烁LED
    print("3...")
    await asyncio.gather(
        racer1.api.indicator.turn_on(IndicatorParam(duration_ms=500, color=Color(r=255, g=0, b=0))),
        racer2.api.indicator.turn_on(IndicatorParam(duration_ms=500, color=Color(r=0, g=0, b=255)))
    )
    await asyncio.sleep(1)
    
    print("2...")
    await asyncio.gather(
        racer1.api.indicator.turn_on(IndicatorParam(duration_ms=500, color=Color(r=255, g=255, b=0))),
        racer2.api.indicator.turn_on(IndicatorParam(duration_ms=500, color=Color(r=255, g=255, b=0)))
    )
    await asyncio.sleep(1)
    
    print("1...")
    await asyncio.gather(
        racer1.api.indicator.turn_on(IndicatorParam(duration_ms=500, color=Color(r=0, g=255, b=0))),
        racer2.api.indicator.turn_on(IndicatorParam(duration_ms=500, color=Color(r=0, g=255, b=0)))
    )
    await asyncio.sleep(1)
    
    print("开始！")
    # 同时开始竞赛
    await asyncio.gather(
        racer1.api.motor.motor_control(left=60, right=60),
        racer2.api.motor.motor_control(left=60, right=60),
        racer1.api.indicator.turn_on(IndicatorParam(duration_ms=3000, color=Color(r=255, g=0, b=0))),
        racer2.api.indicator.turn_on(IndicatorParam(duration_ms=3000, color=Color(r=0, g=0, b=255)))
    )
    
    # 竞赛持续3秒
    await asyncio.sleep(3)
    
    print("竞赛结束！")
    # 同时停止
    await asyncio.gather(
        racer1.api.motor.motor_control(left=0, right=0),
        racer2.api.motor.motor_control(left=0, right=0),
        racer1.api.indicator.turn_off(),
        racer2.api.indicator.turn_off()
    )

async def disconnect_all_cubes(cubes):
    """断开所有toio连接"""
    print("\n正在断开所有连接...")
    
    disconnect_tasks = []
    for cube in cubes:
        task = cube.disconnect()
        disconnect_tasks.append(task)
    
    await asyncio.gather(*disconnect_tasks)
    print("所有toio已断开连接")

if __name__ == "__main__":
    print("请确保所有toio设备都已开启...")
    print("建议至少准备2个toio设备以体验完整功能")
    input("按回车键开始...")
    
    asyncio.run(multi_toio_control()) 