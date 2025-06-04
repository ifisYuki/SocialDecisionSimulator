import asyncio
from toio import *

async def simple_multi_toio():
    """使用MultipleToioCoreCubes的简单多toio控制"""
    
    print("=== 简单多toio控制 ===")
    
    # 使用MultipleToioCoreCubes自动管理多个设备
    # cubes=2 表示连接2个设备，names可以给设备命名
    async with MultipleToioCoreCubes(cubes=2, names=("小红", "小蓝")) as cubes:
        
        print("已成功连接2个toio设备!")
        
        # 方法1：通过索引访问
        print("\n--- 通过索引控制 ---")
        # 让第一个toio点亮红色LED
        await cubes[0].api.indicator.turn_on(
            IndicatorParam(duration_ms=2000, color=Color(r=255, g=0, b=0))
        )
        
        # 让第二个toio点亮蓝色LED
        await cubes[1].api.indicator.turn_on(
            IndicatorParam(duration_ms=2000, color=Color(r=0, g=0, b=255))
        )
        
        await asyncio.sleep(2)
        
        # 方法2：通过名称访问
        print("\n--- 通过名称控制 ---")
        # 小红前进
        await cubes.named("小红").api.motor.motor_control(left=40, right=40)
        print("小红开始前进")
        
        # 小蓝原地旋转
        await cubes.named("小蓝").api.motor.motor_control(left=40, right=-40)
        print("小蓝开始旋转")
        
        await asyncio.sleep(3)
        
        # 方法3：同时控制所有toio
        print("\n--- 同时控制所有toio ---")
        # 同时停止
        await asyncio.gather(
            cubes[0].api.motor.motor_control(left=0, right=0),
            cubes[1].api.motor.motor_control(left=0, right=0)
        )
        
        # 同时关闭LED
        await asyncio.gather(
            cubes[0].api.indicator.turn_off(),
            cubes[1].api.indicator.turn_off()
        )
        
        print("演示完成!")
        
    print("所有设备已自动断开连接")

async def formation_demo():
    """编队演示 - 3个toio编队移动"""
    
    print("\n=== 编队移动演示 ===")
    
    try:
        async with MultipleToioCoreCubes(cubes=3, names=("队长", "左翼", "右翼")) as cubes:
            
            print("3个toio编队准备完成!")
            
            # 点亮不同颜色的LED表示队形
            await asyncio.gather(
                cubes.named("队长").api.indicator.turn_on(
                    IndicatorParam(duration_ms=0, color=Color(r=255, g=255, b=0))  # 黄色队长
                ),
                cubes.named("左翼").api.indicator.turn_on(
                    IndicatorParam(duration_ms=0, color=Color(r=255, g=0, b=0))    # 红色左翼
                ),
                cubes.named("右翼").api.indicator.turn_on(
                    IndicatorParam(duration_ms=0, color=Color(r=0, g=0, b=255))    # 蓝色右翼
                )
            )
            
            print("编队前进...")
            # 编队前进 - 队长速度稍快
            await asyncio.gather(
                cubes.named("队长").api.motor.motor_control(left=45, right=45),
                cubes.named("左翼").api.motor.motor_control(left=40, right=40),
                cubes.named("右翼").api.motor.motor_control(left=40, right=40)
            )
            await asyncio.sleep(2)
            
            print("编队右转...")
            # 编队右转 - 外侧速度快，内侧速度慢
            await asyncio.gather(
                cubes.named("队长").api.motor.motor_control(left=50, right=30),
                cubes.named("左翼").api.motor.motor_control(left=55, right=25),  # 外侧更快
                cubes.named("右翼").api.motor.motor_control(left=45, right=35)   # 内侧较慢
            )
            await asyncio.sleep(2)
            
            print("编队停止...")
            # 同时停止
            await asyncio.gather(
                cubes.named("队长").api.motor.motor_control(left=0, right=0),
                cubes.named("左翼").api.motor.motor_control(left=0, right=0),
                cubes.named("右翼").api.motor.motor_control(left=0, right=0)
            )
            
            # 关闭LED
            await asyncio.gather(
                cubes.named("队长").api.indicator.turn_off(),
                cubes.named("左翼").api.indicator.turn_off(),
                cubes.named("右翼").api.indicator.turn_off()
            )
            
            print("编队演示完成!")
            
    except Exception as e:
        print(f"编队演示失败 (可能设备数量不足): {e}")

async def interactive_control():
    """交互式控制 - 用户可以选择控制哪个toio"""
    
    print("\n=== 交互式控制 ===")
    
    async with MultipleToioCoreCubes(cubes=2, names=("A号", "B号")) as cubes:
        
        # 为每个toio设置不同颜色以便区分
        await asyncio.gather(
            cubes.named("A号").api.indicator.turn_on(
                IndicatorParam(duration_ms=0, color=Color(r=255, g=0, b=0))  # A号红色
            ),
            cubes.named("B号").api.indicator.turn_on(
                IndicatorParam(duration_ms=0, color=Color(r=0, g=255, b=0))  # B号绿色
            )
        )
        
        print("A号toio显示红色，B号toio显示绿色")
        print("您可以分别控制它们:")
        
        while True:
            choice = input("\n选择控制: [A] A号toio [B] B号toio [Q] 退出: ").upper()
            
            if choice == 'Q':
                break
            elif choice == 'A':
                print("控制A号toio前进2秒...")
                await cubes.named("A号").api.motor.motor_control(left=40, right=40)
                await asyncio.sleep(2)
                await cubes.named("A号").api.motor.motor_control(left=0, right=0)
            elif choice == 'B':
                print("控制B号toio旋转2秒...")
                await cubes.named("B号").api.motor.motor_control(left=40, right=-40)
                await asyncio.sleep(2)
                await cubes.named("B号").api.motor.motor_control(left=0, right=0)
            else:
                print("无效选择，请输入 A、B 或 Q")
        
        # 关闭LED
        await asyncio.gather(
            cubes.named("A号").api.indicator.turn_off(),
            cubes.named("B号").api.indicator.turn_off()
        )

async def main():
    """主程序菜单"""
    
    print("=== 多toio控制演示程序 ===")
    print("请选择演示模式:")
    print("1. 简单多toio控制")
    print("2. 编队移动演示 (需要3个toio)")
    print("3. 交互式控制")
    
    choice = input("请输入选择 (1-3): ")
    
    if choice == '1':
        await simple_multi_toio()
    elif choice == '2':
        await formation_demo()
    elif choice == '3':
        await interactive_control()
    else:
        print("无效选择")

if __name__ == "__main__":
    asyncio.run(main()) 