import asyncio
import websockets
import json
from toio import ToioCoreCube

PORT = 9099
cube = None

SPEED = 25
ROTATE = 7
T_Per = 0.02  # 动作持续时间

# 执行一个动作
async def run_single_action(action):
    try:
        if action == 1:
            await cube.api.motor.motor_control(SPEED, SPEED)
        elif action == 2:
            await cube                                                                                                                                                                                                                                                                                                                                                                                                                                      .api.motor.motor_control(-SPEED, -SPEED)
        elif action == 3:
            await cube.api.motor.motor_control(ROTATE, -ROTATE)
        elif action == 4:
            await cube.api.motor.motor_control(-ROTATE, ROTATE) 
        else:
            await cube.api.motor.motor_control(0, 0)
        await asyncio.sleep(T_Per)
    except Exception as e:
        print(f"⚠️ 控制失败: {e}")

# # 执行整个动作列
# async def handle_action_list(action_list, websocket):
#     for item in action_list:
#         if not isinstance(item, list) or len(item) != 2:
#             continue
#         _, action = item
#         await run_single_action(action)
    
#     await cube.api.motor.motor_control(0, 0)  # 最后停止
#     # await websocket.send(json.dumps({"status": "done"}))  # 向 Unity 回复完成

# async def control_server(websocket):
#     print("📡 等待 Unity 动作命令...")
#     async for message in websocket:
#         try:
#             data = json.loads(message)
#             if isinstance(data, list) and all(isinstance(d, list) and len(d) == 2 for d in data):
#                 await handle_action_list(data, websocket)
#         except Exception as e:
#             print(f"⚠️ 数据解析失败: {e}")

async def receive_detection_data():
    uri = "ws://localhost:9097"
    async with websockets.connect(uri) as websocket:
        while True:
            try:
                message = await websocket.recv() #接收消息
                data = json.loads(message) #解析JSON数据
                if "poses" in data:
                    poses = data["poses"]
                    for pose in poses:
                        action = map_pose_to_action(pose)
                        await run_single_action(action)
            except Exception as e:
                print(f"接收数据错误: {e}")

def map_pose_to_action(pose):
    # 将pose数据映射为toio动作
    # 根据pose['id] 返回一个动作

    return 0

async def connect_toio():
    global cube
    cube = ToioCoreCube()
    print("🔍 正在扫描 toio 小车...")
    await cube.scan()
    await cube.connect()
    print("✅ 已连接 toio 小车")

async def main():
    await connect_toio()
    print(f"🚀 WebSocket 服务启动: ws://localhost:{PORT}")
    async with websockets.serve(control_server, "0.0.0.0", PORT):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
