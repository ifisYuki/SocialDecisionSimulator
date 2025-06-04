import { dataManager } from './dataManager.js';
import { createRenderer } from './renderer.js';
import { createUIPanel } from './uiPanel.js';
import { FRAME_CONFIG } from './config.js';

// 获取DOM元素
const canvas = document.getElementById('visualCanvas');
const dataPanel = document.getElementById('dataPanel');

// 创建渲染器和UI面板
const renderer = createRenderer(canvas);
const uiPanel = createUIPanel(dataPanel);

// 窗口大小调整处理
window.addEventListener('resize', () => {
    renderer.setupCanvas();
    renderer.render();
});

// 对象悬停处理
window.handleObjectHover = (index) => {
    dataManager.setHoveredObject(index);
    renderer.render();
    uiPanel.update();
};

window.handleObjectUnhover = () => {
    dataManager.setHoveredObject(-1);
    renderer.render();
    uiPanel.update();
};

let isPlaying = true;
let playInterval = null;

// 自动播放
function autoPlay() {
    if (playInterval) {
        clearInterval(playInterval);
    }

    playInterval = setInterval(async () => {
        if (!isPlaying) return;

        let nextFrame = dataManager.currentFrame + 1;
        if (nextFrame > FRAME_CONFIG.END_FRAME) {
            nextFrame = FRAME_CONFIG.START_FRAME;
        }
        
        console.log('Loading next frame:', nextFrame); // 调试信息
        if (await dataManager.loadFrame(nextFrame)) {
            renderer.render();
            uiPanel.update();
        } else {
            console.error('Failed to load frame:', nextFrame);
            isPlaying = false;
            clearInterval(playInterval);
        }
    }, 1000 / FRAME_CONFIG.FRAME_RATE);
}

// 初始化并开始自动播放
async function initialize() {
    console.log('Initializing visualization...'); // 调试信息
    try {
        if (await dataManager.loadFrame(FRAME_CONFIG.START_FRAME)) {
            console.log('Initial frame loaded successfully'); // 调试信息
            renderer.render();
            uiPanel.update();
            autoPlay();
        } else {
            console.error('Failed to load initial frame');
        }
    } catch (error) {
        console.error('Initialization error:', error);
    }
}

// 添加键盘控制
document.addEventListener('keydown', (event) => {
    switch (event.key) {
        case ' ': // 空格键暂停/播放
            isPlaying = !isPlaying;
            if (isPlaying) {
                autoPlay();
            }
            break;
        case 'ArrowRight': // 右箭头前进一帧
            if (!isPlaying) {
                let nextFrame = dataManager.currentFrame + 1;
                if (nextFrame <= FRAME_CONFIG.END_FRAME) {
                    dataManager.loadFrame(nextFrame).then(() => {
                        renderer.render();
                        uiPanel.update();
                    });
                }
            }
            break;
        case 'ArrowLeft': // 左箭头后退一帧
            if (!isPlaying) {
                let prevFrame = dataManager.currentFrame - 1;
                if (prevFrame >= FRAME_CONFIG.START_FRAME) {
                    dataManager.loadFrame(prevFrame).then(() => {
                        renderer.render();
                        uiPanel.update();
                    });
                }
            }
            break;
    }
});

// 启动应用
console.log('Starting application...'); // 调试信息
initialize(); 