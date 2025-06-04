import { OBJECT_TYPES, DEFAULT_OBJECT_TYPE, getObjectTypeConfig } from './objectTypes.js';

// 播放配置
export const FRAME_CONFIG = {
    START_FRAME: 1,      // 从第1帧开始
    END_FRAME: 689,      // 到第689帧结束
    FRAME_RATE: 10 // frames per second
};

// 可视化配置
export const VISUAL_CONFIG = {
    MARGIN: 50,
    AXIS_COLOR: '#ffffff',
    POINT_RADIUS: 6,
    GRID_SIZE: 40,
    SCAN_LINE_SPEED: 3000 // milliseconds
};

// 类别配置 - 从objectTypes.js导入
export const CLASS_NAMES = Object.fromEntries(
    Object.entries(OBJECT_TYPES).map(([id, config]) => [id, config.name.toLowerCase()])
);

// 基础颜色配置
export const COLOR_SCHEME = {
    PRIMARY: '#ffffff',      // 主白色
    SECONDARY: '#ffff00',    // 黄色
    BACKGROUND: '#000000',   // 纯黑色
    GRID: 'rgba(255, 255, 255, 0.3)',
    TEXT: '#ffffff',
    WARNING: '#ffaa00',
    DANGER: '#ff4444'
};

// 样式配置
export const STYLE_CONFIG = {
    NORMAL: {
        SATURATION: '70%',
        LIGHTNESS: '40%',
        LINE_WIDTH: 1,
        FONT: '10px JetBrains Mono'
    },
    HIGHLIGHT: {
        SATURATION: '100%',
        LIGHTNESS: '60%',
        LINE_WIDTH: 2,
        FONT: 'bold 12px JetBrains Mono'
    }
};

// 动画配置
export const ANIMATION_CONFIG = {
    BLINK_SPEED: 1500,
    SCAN_SPEED: 3000,
    FADE_DURATION: 300
};

// 工具函数：获取对象配置
export const getObjectConfig = (classId) => {
    return getObjectTypeConfig(classId);
};

// 工具函数：获取对象颜色
export const getObjectColor = (classId, isSecondary = false) => {
    const config = getObjectConfig(classId);
    return isSecondary ? config.colors.secondary : config.colors.primary;
};

// 工具函数：获取对象名称
export const getObjectName = (classId) => {
    const config = getObjectConfig(classId);
    return config.name;
};

// 工具函数：生成编码ID
export const generateObjectId = (classId, index) => {
    const config = getObjectConfig(classId);
    const prefix = config.prefix;
    return `${prefix}_${String(index + 1).padStart(3, '0')}`;
}; 