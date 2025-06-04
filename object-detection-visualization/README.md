# Object Detection Visualization System

一个用于实时可视化目标检测数据的Web应用系统。采用科幻风格的界面设计，支持实时显示检测目标的坐标轨迹，具备颜色编码和交互控制功能。使用Canvas API绘制检测框和标签，支持键盘控制播放暂停，鼠标悬停查看详细信息。系统采用模块化ES6架构，配置灵活，易于扩展新的对象类型和数据源。

## Quick Start

```bash
# Clone and run
git clone [repository-url]
cd frontend
python -m http.server 8080
# Open http://localhost:8080
```

控制: 空格键播放/暂停，左右箭头导航，鼠标悬停查看详情。 