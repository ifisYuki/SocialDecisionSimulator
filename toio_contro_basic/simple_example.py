import asyncio
from toio import *

async def simple_toio_control():
    """简单的toio控制例子"""
    
    print("正在搜索toio设备...")
    
    # 1. 搜索并连接toio
    device_list = await BLEScanner.scan(1)
    if len(device_list) == 0:
        print("未找到toio设备，请检查设备是否开启")
        return
    
    cube = ToioCoreCube(device_list[0].interface)
    await cube.connect()
    print("已连接到toio!")
    
    try:
        # 2. 点亮LED（红色）
        print("点亮红色LED...")
        await cube.api.indicator.turn_on(
            IndicatorParam(duration_ms=1000, color=Color(r=255, g=0, b=0))
        )
        await asyncio.sleep(1)
        
        # 3. 前进2秒
        print("前进...")
        await cube.api.motor.motor_control(left=30, right=30)
        await asyncio.sleep(2)
        
        # 4. 点亮绿色LED并右转
        print("右转...")
        await cube.api.indicator.turn_on(
            IndicatorParam(duration_ms=1000, color=Color(r=0, g=255, b=0))
        )
        await cube.api.motor.motor_control(left=30, right=-30)
        await asyncio.sleep(1)
        
        # 5. 停止并关闭LED
        print("停止...")
        await cube.api.motor.motor_control(left=0, right=0)
        await cube.api.indicator.turn_off()
        
        print("控制完成!")
        
    finally:
        # 6. 断开连接
        await cube.disconnect()
        print("已断开连接")

if __name__ == "__main__":
    print("=== 简单toio控制例子 ===")
    asyncio.run(simple_toio_control()) 