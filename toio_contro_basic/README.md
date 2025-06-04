# YOLO实时目标检测系统

基于YOLO模型的实时目标检测系统，支持WebSocket通信和多线程处理。

## 系统要求

### 硬件要求
- 摄像头（USB或内置）
- NVIDIA GPU（推荐，用于加速）
- 至少4GB内存

### 软件要求
- Python 3.8+
- CUDA 11.6+（如果使用GPU）

## 安装步骤

### 1. 克隆项目
```bash
git clone <your-repo-url>
cd ybw_toio_control
```

### 2. 安装Python依赖
```bash
pip install -r requirements.txt
```

### 3. 准备模型文件
确保`best-obb-225.pt`模型文件在`Yolo/`目录下。

### 4. 检查摄像头
确保摄像头已连接并可用：
```bash
python -c "import cv2; cap = cv2.VideoCapture(0); print('摄像头可用' if cap.isOpened() else '摄像头不可用'); cap.release()"
```

### 5. 检查CUDA（可选）
```bash
python -c "import torch; print(f'CUDA可用: {torch.cuda.is_available()}')"
```

## 运行程序

### 启动检测系统
```bash
cd Yolo
python toio_yolo_detect4.py
```

### 程序功能
- **实时目标检测**：检测ID为0-5的目标
- **坐标系建立**：以ID=5目标为原点建立坐标系
- **WebSocket服务**：在端口9097提供实时数据
- **可视化显示**：显示检测结果和性能信息

### 操作说明
- 按`q`键退出程序
- 确保ID=5的目标在视野中以建立坐标系
- WebSocket客户端可连接`ws://localhost:9097`获取实时数据

## 输出数据格式

WebSocket发送的JSON数据格式：
```json
{
  "poses": [
    {
      "id": "1",
      "x": 10.5,        // 相对X坐标
      "z": -5.2,        // 相对Z坐标  
      "angle": 45.0,    // 相对角度
      "pixel_x": 320,   // 像素X坐标
      "pixel_y": 240,   // 像素Y坐标
      "conf": 0.85      // 检测置信度
    }
  ]
}
```

## 故障排除

### 摄像头问题
- 检查摄像头连接
- 尝试不同的摄像头索引
- 确保其他程序未占用摄像头

### GPU问题
- 如果没有GPU，修改代码中的`device=0`为`device='cpu'`
- 检查CUDA驱动和PyTorch版本兼容性

### 模型文件问题
- 确保`best-obb-225.pt`文件存在且完整
- 检查文件路径是否正确

### 网络问题
- 确保端口9097未被占用
- 检查防火墙设置

## 性能优化

- 使用GPU可大幅提升检测速度
- 调整`conf`参数可平衡检测精度和速度
- 修改`imgsz`参数可调整输入图像大小 