# YOLO + Toio 联合控制系统

这个程序将YOLO视觉检测和toio机器人控制结合在一起，实现当检测到机器人离开指定圆形区域时自动执行特殊动作。

## 🚀 快速开始指南

> **注意**：前两步是**每次部署时执行一次**，后面的步骤是**每次开机时执行**

### 1. 克隆项目 （⚙️ 部署时执行）

```bash
git clone https://github.com/your-username/shjzmnq_toio_control.git
cd shjzmnq_toio_control
```

### 2. 虚拟环境配置 （⚙️ 部署时执行）

#### 创建虚拟环境（如果还没有）
```bash
# 使用conda创建虚拟环境
conda create -n myenv python=3.9
```

#### 激活虚拟环境
```powershell
# Windows PowerShell
$env:PATH = "C:\Users\YourUsername\Desktop\shjzmnq_toio_control\myenv\Scripts;$env:PATH"

# 或者使用批处理文件
.\myenv\Scripts\activate.bat
```

#### 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 系统要求检查 （⚙️ 部署时检查）

确保以下设备和软件就绪：
- ✅ Windows 10/11 系统
- ✅ VS Code + Live Server 扩展（用于前端界面）
- ✅ 摄像头（USB或内置）
- ✅ 蓝牙适配器（支持BLE）
- ✅ 3个toio机器人

> ✅ **部署完成！** 以上步骤只需要在首次安装时执行一次。

---

# 🔄 日常使用指南

> **以下步骤是每次开机后使用系统时需要执行的操作**

## 📋 每次运行步骤

### 第一步：准备工作
1. **开启电脑蓝牙**
   - 设置 → 设备 → 蓝牙和其他设备 → 开启蓝牙

2. **开启toio机器人**
   - 按下3个toio机器人的电源按钮
   - 确认指示灯亮起

3. **摄像头准备**
   - 确保摄像头正常工作

### 第二步：激活虚拟环境
```powershell
# 打开PowerShell，导航到项目目录
cd C:\Users\YourUsername\Desktop\shjzmnq_toio_control

# 激活虚拟环境
$env:PATH = "C:\Users\YourUsername\Desktop\shjzmnq_toio_control\myenv\Scripts;$env:PATH"

# 验证环境激活
python --version  # 应该显示 Python 3.9.19
```

### 第三步：运行后端程序
```bash
# 运行主程序（连接蓝牙和YOLO检测）
python combined_yolo_toio_control.py
```

**程序启动成功标志：**
```
✅ 视频流服务器模块已加载
=== YOLO + Toio 联合控制系统 ===
✅ 成功连接3个toio设备！
🔴 红色LED → "恐惧制造者" (ID: 0)
🟢 绿色LED → "行业专家" (ID: 1)
🔵 蓝色LED → "先驱者" (ID: 2)
✅ YOLO检测系统启动成功！
🎥 视频流服务器启动在 http://localhost:5000
```

### 第四步：运行前端程序
1. **启动Live Server**
   - 在VS Code中打开项目
   - 右键单击 `object-detection-visualization/label_visualization.html`
   - 选择 **"Open with Live Server"**

2. **全屏显示**
   - 在打开的浏览器页面中按 **F11** 键进入全屏模式
   - 获得最佳的可视化体验

3. **备用方案**
   - 如果没有Live Server，也可以直接双击HTML文件打开
   - 或者访问：http://localhost:5000（基础视频流）

## 🎮 操作指南

### 基本操作
- **启动系统**：运行后端程序后，系统自动开始检测
- **退出程序**：在程序窗口按 **'q'** 键
- **全屏切换**：在浏览器中按 **F11** 键

### 系统监控
- **主要界面**：通过Live Server打开的 `label_visualization.html`（推荐）
- **视频流地址**：http://localhost:5000/video_feed
- **测试页面**：http://localhost:5000/
- **实时检测**：可视化界面显示YOLO检测结果

## 🔧 功能特点

### 实时视觉检测
- 使用YOLO模型检测toio机器人位置
- 实时显示检测画面和边界框
- 智能识别机器人ID（0, 1, 2）

### 圆形区域监控
- 设定虚拟圆形区域
- 监控机器人是否在区域内
- 自动触发响应动作

### 自动响应控制
- 机器人离开圆形区域时自动执行特殊动作
- 支持多机器人同时控制
- 异步处理，不影响其他机器人

### 视觉反馈系统
- **绿色圆圈**：监控区域边界
- **机器人边框颜色**：
  - 🔵 蓝色：在圆圈内
  - 🔴 红色：在圆圈外
- **ID标签**：显示每个机器人的ID

### Toio机器人角色设定
连接成功后，3个toio机器人将显示不同颜色的LED，对应不同角色：
- 🔴 **红色LED** → **"恐惧制造者"** (ID: 0)
- 🟢 **绿色LED** → **"行业专家"** (ID: 1)  
- 🔵 **蓝色LED** → **"先驱者"** (ID: 2)

## ⚙️ 配置参数

### YOLO检测参数
```python
MODEL_PATH = "Yolo/yolo11n.pt"      # YOLO模型路径
CAMERA_INDEX = 1                    # 摄像头索引
CONF_THRESHOLD = 0.5               # 检测置信度阈值
```

### 圆形区域参数
```python
CIRCLE_CENTER_X = 320              # 圆心X坐标
CIRCLE_CENTER_Y = 240              # 圆心Y坐标
CIRCLE_RADIUS = 100                # 圆形半径
```

### 机器人控制参数
```python
MOVE_DURATION = 0.5                # 移动持续时间
ROTATION_ANGLE = 180               # 旋转角度
LED_COLORS = [(255,0,0), (0,255,0), (0,0,255)]  # LED颜色设置
# LED颜色对应角色：
# (255,0,0) 红色 → "恐惧制造者" (ID: 0)
# (0,255,0) 绿色 → "行业专家" (ID: 1)
# (0,0,255) 蓝色 → "先驱者" (ID: 2)
```

## 🛠️ 故障排除

### 常见问题

#### 1. toio连接失败
**问题**：显示"实际连接的toio设备数量: 0"
**解决方案**：
- 确认电脑蓝牙已开启
- 确认toio机器人已开启且在附近（1-2米内）
- 重启程序重新连接

**角色识别**：连接成功后，观察LED颜色确认角色分配：
- 看到🔴红灯 = "恐惧制造者"已就位
- 看到🟢绿灯 = "行业专家"已就位  
- 看到🔵蓝灯 = "先驱者"已就位

#### 2. 摄像头无法启动
**问题**：摄像头初始化失败
**解决方案**：
- 检查摄像头是否被其他程序占用
- 尝试修改 `CAMERA_INDEX` 参数（0, 1, 2）
- 确认摄像头驱动正常

#### 3. YOLO模型加载失败
**问题**：模型文件找不到
**解决方案**：
- 确认 `Yolo/yolo11n.pt` 文件存在
- 检查文件路径是否正确
- 重新下载YOLO模型文件

#### 4. 网页无法访问
**问题**：http://localhost:5000 无法打开
**解决方案**：
- 确认后端程序正在运行
- 检查防火墙设置
- 尝试使用 http://127.0.0.1:5000

#### 5. Live Server无法启动
**问题**：右键没有"Open with Live Server"选项
**解决方案**：
- 在VS Code中安装"Live Server"扩展
- 重启VS Code后重试
- 或者直接双击HTML文件用默认浏览器打开

### 性能优化
- 确保摄像头分辨率适中（推荐640x480）
- 关闭不必要的后台程序
- 使用有线网络连接（如果需要）

## 📦 依赖包说明

主要依赖包：
```
ultralytics    # YOLO模型
opencv-python  # 图像处理
toio          # toio机器人控制
flask         # Web服务器
numpy         # 数值计算
asyncio       # 异步编程
```

## 🔄 系统架构

### 核心组件
```
📱 主程序 (combined_yolo_toio_control.py)
├── 🤖 YOLO检测模块 → 实时视觉检测和圆形区域监控
├── 🌐 Web服务模块 (video_stream_server.py) → Flask视频流
├── 🔵 Toio控制模块 → 蓝牙BLE通信和机器人控制
└── 📊 事件队列 → 连接检测和控制的桥梁
```

### 前端界面
```
🎨 可视化界面 (object-detection-visualization/)
├── 📄 label_visualization.html → 主界面
├── 🎨 styles.css → 科幻风格样式
├── ⚙️ visualization.js → 核心逻辑
└── 🔗 连接后端视频流 (localhost:5000)
```

### 数据流向
```
摄像头 → YOLO检测 → 圆形区域判断 → 事件队列 → Toio控制
    ↓
Flask服务 → Web界面 → 用户可视化
```

## 📝 更新日志

### v1.0.0 (2025-06-05)
- 初始版本发布
- 支持YOLO + Toio联合控制
- 实现圆形区域监控
- 添加Web视频流服务

---

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

## 📄 许可证

本项目采用 MIT 许可证。

---

**提示**：如果在使用过程中遇到问题，请先查看故障排除部分，或者提交Issue获取帮助。