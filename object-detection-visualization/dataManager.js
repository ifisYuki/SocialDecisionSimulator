import { CLASS_NAMES, FRAME_CONFIG } from './config.js';

class DataManager {
    constructor() {
        this.currentFrame = FRAME_CONFIG.START_FRAME;
        this.currentObjects = [];
        this.hoveredObjectIndex = -1;
    }

    // 获取类别名称
    getClassName(classId) {
        return CLASS_NAMES[classId] || `unknown_${classId}`;
    }

    // 格式化帧号为三位数
    formatFrameNumber(number) {
        return number.toString().padStart(3, '0');
    }

    // 加载帧数据
    async loadFrame(frameNumber) {
        try {
            const formattedNumber = this.formatFrameNumber(frameNumber);
            const url = `labels/Sequence 02_${frameNumber}.txt`;
            console.log('Attempting to load:', url); // 调试信息

            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const text = await response.text();
            if (!text.trim()) {
                throw new Error('Empty file content');
            }

            this.currentObjects = text.trim().split('\n')
                .filter(line => line.trim() !== '')
                .map(line => {
                    const values = line.split(' ').map(Number);
                    if (values.length !== 10) {
                        console.warn('Invalid data format:', line);
                        return null;
                    }
                    return values;
                })
                .filter(obj => obj !== null);
            
            this.currentFrame = frameNumber;
            console.log(`Loaded frame ${frameNumber} with ${this.currentObjects.length} objects`); // 调试信息
            return true;
        } catch (error) {
            console.error('Error loading frame:', error);
            console.error('Frame number:', frameNumber);
            this.currentObjects = [];
            return false;
        }
    }

    // 获取对象中心点
    getObjectCenter(obj) {
        const centerX = (obj[1] + obj[3] + obj[5] + obj[7]) / 4;
        const centerY = (obj[2] + obj[4] + obj[6] + obj[8]) / 4;
        return { x: centerX, y: centerY };
    }

    // 获取对象角点
    getObjectPoints(obj) {
        return [
            [obj[1], obj[2]],
            [obj[3], obj[4]],
            [obj[5], obj[6]],
            [obj[7], obj[8]]
        ];
    }

    // 设置悬停对象
    setHoveredObject(index) {
        this.hoveredObjectIndex = index;
    }
}

export const dataManager = new DataManager(); 