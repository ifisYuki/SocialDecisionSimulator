import asyncio
import sys
from toio import *
import time

async def test_bluetooth():
    """测试蓝牙和toio连接"""
    print("=== Toio 蓝牙连接测试 ===")
    print("1. 确保toio设备已开机（按电源键，指示灯应该亮起）")
    print("2. 确保Windows蓝牙已开启")
    print("3. 确保toio没有连接到其他设备\n")
    
    print("正在扫描toio设备...")
    
    try:
        # 尝试扫描toio设备
        devices = await BLEScanner.scan(num=3, timeout=10.0)
        
        if not devices:
            print("❌ 未找到任何toio设备")
            print("\n解决方案：")
            print("1. 检查toio是否开机")
            print("2. 重启toio（长按电源键关机，再开机）")
            print("3. 检查Windows蓝牙设置")
            print("4. 尝试在蓝牙设置中删除已配对的toio设备")
            return
        
        print(f"✅ 找到 {len(devices)} 个toio设备")
        
        # 尝试连接每个设备
        for i, device in enumerate(devices):
            print(f"\n测试连接toio {i}...")
            try:
                async with CoreCube(device) as cube:
                    print(f"✅ 成功连接toio {i}")
                    
                    # 测试指示灯
                    await cube.api.indicator.turn_on(
                        IndicatorParam(
                            duration_ms=1000,
                            color=Color(r=0, g=255, b=0)
                        )
                    )
                    
                    # 测试电机
                    await cube.api.motor.motor_control(left=20, right=20)
                    await asyncio.sleep(0.5)
                    await cube.api.motor.motor_control(left=0, right=0)
                    
                    print(f"✅ toio {i} 功能正常")
                    
            except Exception as e:
                print(f"❌ toio {i} 连接失败: {e}")
        
        print("\n✅ 测试完成！")
        
        # 测试同时连接多个
        print("\n测试同时连接3个toio...")
        try:
            async with MultipleToioCoreCubes(cubes=3) as cubes:
                print("✅ 成功同时连接3个toio！")
                await asyncio.sleep(2)
        except Exception as e:
            print(f"❌ 同时连接失败: {e}")
            print("建议逐个重启toio设备后重试")
            
    except Exception as e:
        print(f"❌ 扫描失败: {e}")
        print("\n可能的原因：")
        print("1. Windows蓝牙服务未启动")
        print("2. 蓝牙驱动问题")
        print("3. 需要以管理员权限运行")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    try:
        asyncio.run(test_bluetooth())
    except KeyboardInterrupt:
        print("\n测试中断")
    except Exception as e:
        print(f"测试错误: {e}")
    
    input("\n按Enter键退出...") 