# 视频文件说明

## 当前视频
- `Sequence 02.avi` - 检测序列视频

## 浏览器兼容性

### 支持的视频格式（按兼容性排序）：
1. **MP4** (.mp4) - 最佳兼容性，推荐使用
2. **WebM** (.webm) - 现代浏览器支持
3. **OGV** (.ogv) - Firefox支持
4. **AVI** (.avi) - 兼容性有限

## 格式转换建议

如果视频播放有问题，建议将AVI文件转换为MP4格式：

### 使用FFmpeg转换（推荐）：
```bash
ffmpeg -i "Sequence 02.avi" -c:v libx264 -c:a aac "Sequence 02.mp4"
```

### 在线转换工具：
- CloudConvert
- Online-Convert
- Convertio

## 文件命名
- 保持原文件名格式
- 如果添加MP4版本，命名为 `Sequence 02.mp4`
- 系统会自动选择最兼容的格式播放

## 技术说明
- 视频会在界面底部显示
- 支持播放控制（播放、暂停、音量、全屏）
- 默认静音并循环播放
- 视频状态会在右上角显示（READY/PLAYING/PAUSED/ERROR） 