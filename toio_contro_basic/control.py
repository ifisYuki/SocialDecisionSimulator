import asyncio

from toio import *

async def cube_connect():
    """连接到toio设备"""
    print("正在搜索toio设备...")
    device_list = await BLEScanner.scan(1)
    assert len(device_list) > 0
    print(f"找到设备: {device_list[0].name}")
    
    cube = ToioCoreCube(device_list[0].interface)
    await cube.connect()
    print("成功连接到toio!")
    return cube

async def cube_disconnect(cube):
    """断开toio连接"""
    await cube.disconnect()
    print("已断开toio连接")
    await asyncio.sleep(2)

async def toio_demo(cube):
    """toio演示程序 - 展示各种控制功能"""
    
    # 1. LED控制 - 点亮红色LED
    print("1. 点亮红色LED...")
    await cube.api.indicator.turn_on(
        IndicatorParam(duration_ms=2000, color=Color(r=255, g=0, b=0))
    )
    await asyncio.sleep(2)
    
    # 2. 基本运动 - 前进
    print("2. 前进...")
    await cube.api.motor.motor_control(left=50, right=50)
    await asyncio.sleep(2)
    
    # 3. 转向 - 右转
    print("3. 右转...")
    await cube.api.motor.motor_control(left=50, right=-50)
    await asyncio.sleep(1)
    
    # 4. LED控制 - 点亮绿色LED
    print("4. 点亮绿色LED...")
    await cube.api.indicator.turn_on(
        IndicatorParam(duration_ms=2000, color=Color(r=0, g=255, b=0))
    )
    
    # 5. 后退
    print("5. 后退...")
    await cube.api.motor.motor_control(left=-50, right=-50)
    await asyncio.sleep(2)
    
    # 6. 左转
    print("6. 左转...")
    await cube.api.motor.motor_control(left=-50, right=50)
    await asyncio.sleep(1)
    
    # 7. LED控制 - 点亮蓝色LED
    print("7. 点亮蓝色LED...")
    await cube.api.indicator.turn_on(
        IndicatorParam(duration_ms=2000, color=Color(r=0, g=0, b=255))
    )
    
    # 8. 播放声音 (如果支持)
    print("8. 播放声音...")
    try:
        await cube.api.sound.play_preset_sound(sound_id=2, volume=100)
        await asyncio.sleep(1)
    except Exception as e:
        print(f"声音播放可能不支持: {e}")
    
    # 9. 停止运动
    print("9. 停止运动...")
    await cube.api.motor.motor_control(left=0, right=0)
    
    # 10. 关闭LED
    print("10. 关闭LED...")
    await cube.api.indicator.turn_off()
    
    print("演示完成!")

async def main():
    """主程序"""
    try:
        # 连接toio
        cube = await cube_connect()
        
        # 运行演示
        await toio_demo(cube)
        
        # 断开连接
        await cube_disconnect(cube)
        
    except Exception as e:
        print(f"程序运行出错: {e}")

if __name__ == "__main__":
    print("=== toio控制演示程序 ===")
    print("请确保toio设备已开启并在附近...")
    asyncio.run(main())




