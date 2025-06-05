# 🏗️ 项目架构说明

## 📁 项目目录结构

```
shjzmnq_toio_control/
├── 📄 combined_yolo_toio_control.py    # 🎯 主程序文件
├── 📄 video_stream_server.py           # 🌐 Web视频流服务器
├── 📄 test_bluetooth.py                # 🔧 蓝牙连接测试工具
├── 📄 simple_yolo_control.py           # 📝 简化版本（占位文件）
├── 📄 requirements.txt                 # 📦 Python依赖包列表
├── 📄 README_combined_control.md       # 📖 项目使用说明
├── 📄 .gitignore                      # 🚫 Git忽略文件配置
│
├── 📂 myenv/                          # 🐍 Python虚拟环境
│   └── ...                           # Conda/pip安装的所有包
│
├── 📂 Yolo/                           # 🤖 YOLO模型和相关脚本
│   ├── 📄 yolo11n.pt                 # 🎯 主要使用的YOLO模型文件
│   ├── 📄 best-obb-225.pt            # 🎯 备用YOLO模型（大文件）
│   ├── 📄 yolo-obb-best.pt           # 🎯 备用YOLO模型
│   ├── 📄 control_with_yolo.py       # 🔧 YOLO控制脚本v1
│   ├── 📄 control_with_yolo_2.py     # 🔧 YOLO控制脚本v2
│   ├── 📄 toio_yolo_detect4.py       # 🔧 YOLO检测脚本
│   └── 📄 toio_control.py            # 🔧 Toio控制基础脚本
│
├── 📂 object-detection-visualization/ # 🎨 前端可视化界面
│   ├── 📄 label_visualization.html   # 🌟 主要前端界面
│   ├── 📄 video_test.html            # 🧪 视频测试页面
│   ├── 📄 styles.css                 # 🎨 CSS样式文件
│   ├── 📄 visualization.js           # ⚙️ 主要JS逻辑
│   ├── 📄 config.js                  # ⚙️ 配置文件
│   ├── 📄 dataManager.js             # 📊 数据管理
│   ├── 📄 imageManager.js            # 🖼️ 图像管理
│   ├── 📄 objectTypes.js             # 🏷️ 对象类型定义
│   ├── 📄 renderer.js                # 🎬 渲染引擎
│   ├── 📄 uiPanel.js                 # 🖥️ UI面板控制
│   ├── 📄 README.md                  # 📖 前端说明文档
│   ├── 📂 video/                     # 🎥 视频资源文件夹
│   ├── 📂 labels/                    # 🏷️ 标签数据文件夹
│   └── 📂 images/                    # 🖼️ 图像资源文件夹
│
├── 📂 toio_contro_basic/             # 🤖 Toio控制基础模块
│   ├── 📄 multi_toio_simple.py      # 🔧 简单多机器人控制
│   ├── 📄 multi_toio_interrupt_control.py      # 🔧 中断控制
│   ├── 📄 multi_toio_interrupt_control_3devices.py  # 🔧 3设备控制
│   ├── 📄 multi_toio_interrupt_control_4devices_optimized.py  # 🔧 4设备优化版
│   ├── 📄 multi_toio_example.py     # 📚 示例代码
│   ├── 📄 simple_example.py         # 📚 简单示例
│   ├── 📄 control.py                # 🔧 基础控制脚本
│   ├── 📄 requirements.txt          # 📦 模块依赖
│   └── 📄 README*.md                # 📖 各种说明文档
│
└── 📂 __pycache__/                   # 🗂️ Python缓存文件夹
```

## 🎯 核心文件作用

### 主程序文件
- **`combined_yolo_toio_control.py`** - 系统核心，整合YOLO检测和Toio控制
- **`video_stream_server.py`** - 提供Web视频流服务，被主程序调用

### 模型文件
- **`Yolo/yolo11n.pt`** - 当前使用的YOLO模型
- **`Yolo/best-obb-225.pt`** - 备用模型（训练定制版）
- **`Yolo/yolo-obb-best.pt`** - 备用模型（优化版）

### 前端界面
- **`object-detection-visualization/label_visualization.html`** - 主要可视化界面
- **`object-detection-visualization/styles.css`** - 科幻风格样式
- **`object-detection-visualization/visualization.js`** - 前端核心逻辑

### 开发工具
- **`test_bluetooth.py`** - 蓝牙连接测试工具
- **`toio_contro_basic/`** - Toio控制的各种实验和示例代码

## 🔄 系统工作流程

```
┌─────────────────────────────────────────────────────┐
│                  系统启动流程                        │
└─────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  主程序启动      │  │  模型加载        │  │  设备连接        │
│                │  │                │  │                │
│ combined_yolo_  │─▶│ • yolo11n.pt   │─▶│ • 3个Toio设备   │
│ toio_control.py │  │ • 摄像头初始化   │  │ • 蓝牙BLE连接   │
│                │  │ • YOLO检测启动  │  │ • LED角色分配   │
└─────────────────┘  └─────────────────┘  └─────────────────┘
                                                  │
                                                  ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  Web服务启动     │  │  前端界面        │  │  实时检测        │
│                │  │                │  │                │
│ video_stream_   │─▶│ label_visuali-  │─▶│ • 圆形区域监控   │
│ server.py       │  │ zation.html     │  │ • 机器人追踪     │
│                │  │ (Live Server)   │  │ • 行为触发      │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

## 📦 模块依赖关系

### 核心依赖链
```
combined_yolo_toio_control.py
├── video_stream_server.py (Web服务)
├── Yolo/yolo11n.pt (AI模型)
├── toio (蓝牙控制库)
└── ultralytics (YOLO框架)
```

### 前端依赖链
```
label_visualization.html
├── styles.css (界面样式)
├── visualization.js (主逻辑)
├── config.js (配置)
├── renderer.js (渲染)
├── uiPanel.js (UI控制)
└── http://localhost:5000/video_feed (后端视频流)
```

## 🎨 角色与LED对应

| 机器人ID | LED颜色 | 角色名称 | RGB值 |
|---------|--------|---------|-------|
| 0 | 🔴 红色 | 恐惧制造者 | (255,0,0) |
| 1 | 🟢 绿色 | 行业专家 | (0,255,0) |
| 2 | 🔵 蓝色 | 先驱者 | (0,0,255) |

## 🚀 启动顺序

1. **后端启动** - `python combined_yolo_toio_control.py`
2. **前端启动** - Live Server打开 `label_visualization.html`
3. **设备连接** - 自动连接Toio设备
4. **系统运行** - 开始检测和控制

## 📝 文件用途说明

### 必需文件 🌟
- `combined_yolo_toio_control.py` - 系统主入口
- `video_stream_server.py` - Web服务核心
- `object-detection-visualization/` - 完整前端界面
- `Yolo/yolo11n.pt` - AI检测模型
- `myenv/` - 运行环境

### 开发支持文件 🔧
- `Yolo/` 其他文件 - 不同版本的模型和控制脚本
- `toio_contro_basic/` - 控制功能的各种实验版本
- `test_bluetooth.py` - 调试工具

### 配置文件 ⚙️
- `requirements.txt` - 依赖管理
- `README_combined_control.md` - 使用指南
- `.gitignore` - 版本控制配置

---

**总结**：整个项目采用模块化设计，核心功能集中在主程序中，前端提供可视化界面，其他文件夹包含开发过程中的各种实验和备用方案，都有其存在价值。 