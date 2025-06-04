import { dataManager } from './dataManager.js';
import { getObjectColor, getObjectName, generateObjectId } from './config.js';
import { imageManager } from './imageManager.js';

class UIPanel {
    constructor(panelElement) {
        this.panel = panelElement;
        this.isInitialized = false;
        
        // 监听图片轮换事件
        document.addEventListener('imagesRotated', () => {
            this.updateImages();
        });
        
        // 初始化固定结构
        this.initializeStructure();
    }

    // 初始化固定的HTML结构
    initializeStructure() {
        console.log('正在初始化UI面板结构...');
        
        const fixedStructure = `
            <div class="panel-header">检测信息 DETECTION DATA</div>
            
            <div class="data-panel-content">
                <div class="system-info compact">
                    <div class="frame-info compact">
                        <div class="info-grid">
                            <span id="frame-display">FRAME: 0001</span>
                            <span id="time-display">TIME: 00:00:00</span>
                            <span id="targets-display">TARGETS: 00</span>
                            <span id="status-display">STATUS: OPERATIONAL</span>
                        </div>
                    </div>
                </div>
                
                <div class="data-columns fixed-height">
                    <!-- 左列：只有一张图片 + 大量数据卡片 -->
                    <div class="data-column left-column">
                        <!-- 单张主图片 -->
                        <div class="image-slot main-image" id="main-image-slot">
                            <img id="main-image-img" src="" alt="主显示图片" class="slot-image">
                            <div class="image-label">MAIN VIEW</div>
                        </div>
                        
                        <!-- 左列数据卡片 -->
                        <div id="left-data-1"></div>
                        <div id="left-data-2"></div>
                        <div id="left-data-3"></div>
                        <div id="left-data-4"></div>
                        <div id="left-data-5"></div>
                    </div>
                    
                    <!-- 右列：全部数据卡片 -->
                    <div class="data-column right-column">
                        <div id="right-data-1"></div>
                        <div id="right-data-2"></div>
                        <div id="right-data-3"></div>
                        <div id="right-data-4"></div>
                        <div id="right-data-5"></div>
                        <div id="right-data-6"></div>
                        <div id="right-data-7"></div>
                        <div id="right-data-8"></div>
                        <div id="right-data-extra"></div>
                    </div>
                </div>
            </div>
            
            <div class="video-section">
                <div class="video-header">
                    <span class="video-title">SEQUENCE VIDEO</span>
                    <span class="video-status" id="video-status">READY</span>
                </div>
                <div class="video-container">
                    <video id="sequence-video" controls muted loop preload="metadata">
                        <source src="video/Sequence 01.mp4" type="video/mp4">
                        <source src="video/Sequence 02.avi" type="video/avi">
                        <div class="video-fallback">
                            <p>视频加载失败</p>
                            <p>可能的原因：</p>
                            <ul>
                                <li>浏览器不支持AVI格式</li>
                                <li>视频文件路径错误</li>
                                <li>需要将AVI转换为MP4</li>
                                <li>服务器MIME类型配置问题</li>
                            </ul>
                        </div>
                    </video>
                </div>
            </div>
        `;
        
        this.panel.innerHTML = fixedStructure;
        this.isInitialized = true;
        
        console.log('UI面板HTML结构已设置');
        console.log('面板元素:', this.panel);
        
        // 验证视频区域是否存在
        const videoSection = document.querySelector('.video-section');
        const videoElement = document.getElementById('sequence-video');
        console.log('视频区域找到:', !!videoSection);
        console.log('视频元素找到:', !!videoElement);
        
        // 初始化图片
        this.updateImages();
        
        // 初始化视频（现在在面板内部）
        this.initializeVideo();
    }

    // 格式化坐标显示
    formatCoordinate(value) {
        return value.toFixed(6).padStart(10, '0');
    }

    // 格式化置信度显示
    formatConfidence(value) {
        const percentage = (value * 100).toFixed(1);
        return `${percentage}%`.padStart(6, ' ');
    }

    // 获取目标状态描述
    getTargetStatus(confidence) {
        if (confidence > 0.8) return "LOCKED";
        if (confidence > 0.5) return "TRACK";
        return "DETECT";
    }

    // 生成数据项HTML（简化版）
    generateDataItem(obj, index) {
        const center = dataManager.getObjectCenter(obj);
        const isHighlighted = index === dataManager.hoveredObjectIndex;
        const targetStatus = this.getTargetStatus(obj[9]);
        const targetId = generateObjectId(obj[0], index);
        const primaryColor = getObjectColor(obj[0], false);
        const secondaryColor = getObjectColor(obj[0], true);
        const objectName = getObjectName(obj[0]);
        
        return `
            <div class="data-item compact ${isHighlighted ? 'highlighted' : ''}" 
                 onmouseover="window.handleObjectHover(${index})" 
                 onmouseout="window.handleObjectUnhover()">
                <strong style="color: ${primaryColor};">${targetId}</strong>
                <div class="data-item-line">CLS: <span style="color: ${primaryColor}; font-weight: bold;">${objectName}</span></div>
                <div class="data-grid">
                    <div class="coord-pair">
                        <span>X: ${this.formatCoordinate(center.x)}</span>
                        <span>Y: ${this.formatCoordinate(center.y)}</span>
                    </div>
                    <div class="status-pair">
                        <span>CNF: <span class="confidence">${this.formatConfidence(obj[9])}</span></span>
                        <span>STA: <span style="color: ${secondaryColor};">${targetStatus}</span></span>
                    </div>
                </div>
            </div>
        `;
    }

    // 更新图片内容
    updateImages() {
        if (!this.isInitialized) return;
        
        const slot = { id: 'main-image-slot', category: 'main' };
        const imgElement = document.getElementById('main-image-img');
        
        if (imgElement) {
            // 首先尝试获取当前轮换的图片
            let imageUrl = imageManager.getCurrentImage(slot.id);
            
            if (!imageUrl) {
                // 如果没有轮换图片，获取随机图片
                imageUrl = imageManager.getRandomImage('all');
            }
            
            if (imageUrl) {
                // 预加载图片以确保能正确显示
                imageManager.preloadImage(imageUrl).then(() => {
                    imgElement.src = imageUrl;
                    imgElement.style.display = 'block';
                    imgElement.style.opacity = '0.8';
                    console.log(`主图片已加载:`, imageUrl);
                }).catch(() => {
                    // 预加载失败，使用SVG占位符
                    this.setFallbackImage(imgElement, slot);
                });
            } else {
                // 没有可用图片，使用SVG占位符
                this.setFallbackImage(imgElement, slot);
            }
        }
    }
    
    // 设置备用SVG图片
    setFallbackImage(imgElement, slot) {
        const sizes = {
            'main-image-slot': { width: 200, height: 150 }
        };
        const size = sizes[slot.id] || { width: 200, height: 150 };
        const svg = imageManager.generateRandomSVG(size.width, size.height, slot.category);
        const base64SVG = btoa(svg);
        imgElement.src = `data:image/svg+xml;base64,${base64SVG}`;
        imgElement.style.display = 'block';
        imgElement.style.opacity = '0.6';
        console.log(`使用SVG占位符 ${slot.id}:`, slot.category);
    }

    // 更新系统信息（不重建DOM）
    updateSystemInfo() {
        if (!this.isInitialized) return;
        
        const timestamp = new Date().toISOString().split('T')[1].split('.')[0];
        
        const frameElement = document.getElementById('frame-display');
        const timeElement = document.getElementById('time-display');
        const targetsElement = document.getElementById('targets-display');
        const statusElement = document.getElementById('status-display');
        
        if (frameElement) frameElement.textContent = `FRAME: ${String(dataManager.currentFrame).padStart(4, '0')}`;
        if (timeElement) timeElement.textContent = `TIME: ${timestamp}`;
        if (targetsElement) targetsElement.textContent = `TARGETS: ${String(dataManager.currentObjects.length).padStart(2, '0')}`;
        if (statusElement) statusElement.textContent = `STATUS: OPERATIONAL`;
    }

    // 初始化视频（在数据面板内部）
    initializeVideo() {
        // 视频现在已经在HTML结构中，只需要添加事件监听器
        const video = document.getElementById('sequence-video');
        const videoStatus = document.getElementById('video-status');
        
        if (video && videoStatus) {
            // 检查是否有MP4版本
            this.checkVideoFormats();
            
            video.addEventListener('loadstart', () => {
                videoStatus.textContent = 'LOADING';
                videoStatus.style.color = '#ffaa00';
            });
            
            video.addEventListener('loadedmetadata', () => {
                videoStatus.textContent = 'READY';
                videoStatus.style.color = '#00ff41';
                console.log(`视频时长: ${video.duration.toFixed(2)}秒`);
            });
            
            video.addEventListener('canplay', () => {
                videoStatus.textContent = 'READY';
                videoStatus.style.color = '#00ff41';
            });
            
            video.addEventListener('play', () => {
                videoStatus.textContent = 'PLAYING';
                videoStatus.style.color = '#00ff41';
            });
            
            video.addEventListener('pause', () => {
                videoStatus.textContent = 'PAUSED';
                videoStatus.style.color = '#ffff00';
            });
            
            video.addEventListener('error', (e) => {
                videoStatus.textContent = 'ERROR';
                videoStatus.style.color = '#ff4444';
                console.error('视频加载错误:', e);
                this.handleVideoError();
            });
            
            video.addEventListener('stalled', () => {
                videoStatus.textContent = 'BUFFERING';
                videoStatus.style.color = '#ffaa00';
            });
        }
    }
    
    // 检查可用的视频格式
    checkVideoFormats() {
        const video = document.getElementById('sequence-video');
        if (video) {
            // 检查浏览器支持的格式
            const canPlayMP4 = video.canPlayType('video/mp4');
            const canPlayAVI = video.canPlayType('video/avi');
            
            console.log('视频格式支持:');
            console.log('MP4:', canPlayMP4 || '不支持');
            console.log('AVI:', canPlayAVI || '不支持');
            
            if (!canPlayMP4 && !canPlayAVI) {
                console.warn('当前浏览器可能不支持视频播放');
            }
        }
    }
    
    // 处理视频错误
    handleVideoError() {
        const video = document.getElementById('sequence-video');
        if (video) {
            // 尝试重新加载
            setTimeout(() => {
                video.load();
            }, 2000);
        }
    }

    // 更新数据内容（不重建DOM）
    updateDataContent() {
        if (!this.isInitialized) return;
        
        const objects = dataManager.currentObjects;
        const maxObjects = Math.min(objects.length, 13); // 总共13个数据槽位
        
        // 定义所有数据槽位
        const dataSlots = [
            'left-data-1', 'left-data-2', 'left-data-3', 'left-data-4', 'left-data-5',
            'right-data-1', 'right-data-2', 'right-data-3', 'right-data-4', 'right-data-5',
            'right-data-6', 'right-data-7', 'right-data-8'
        ];
        
        // 填充数据到各个槽位
        dataSlots.forEach((slotId, index) => {
            const element = document.getElementById(slotId);
            if (element) {
                if (index < objects.length) {
                    element.innerHTML = this.generateDataItem(objects[index], index);
                } else {
                    element.innerHTML = ''; // 清空多余的槽位
                }
            }
        });
        
        // 额外数据槽位（统计信息等）
        const rightDataExtra = document.getElementById('right-data-extra');
        if (rightDataExtra) {
            if (objects.length === 0) {
                rightDataExtra.innerHTML = `
                    <div class="data-item compact">
                        <strong>SYS_MSG</strong>
                        <div class="data-item-line" style="color: #ffaa00;">NO TARGETS</div>
                        <div class="data-item-line">SCANNING...</div>
                    </div>
                `;
            } else if (objects.length > 13) {
                rightDataExtra.innerHTML = `
                    <div class="data-item compact summary">
                        <strong>OVERFLOW</strong>
                        <div class="data-item-line">SHOWN: 13/${objects.length}</div>
                        <div class="data-item-line">HIDDEN: ${objects.length - 13}</div>
                        <div class="data-item-line" style="color: #ffaa00;">EXPAND VIEW</div>
                    </div>
                `;
            } else {
                // 显示总体统计
                rightDataExtra.innerHTML = `
                    <div class="data-item compact summary">
                        <strong>SUMMARY</strong>
                        <div class="data-item-line">TOTAL: ${objects.length}</div>
                        <div class="data-item-line">DISPLAYED: ${Math.min(objects.length, 13)}</div>
                        <div class="data-item-line" style="color: #00ff41;">ALL VISIBLE</div>
                    </div>
                `;
            }
        }
    }

    // 主更新函数（只更新数据，不重建结构）
    update() {
        if (!this.isInitialized) {
            this.initializeStructure();
            return;
        }
        
        this.updateSystemInfo();
        this.updateDataContent();
    }
}

export const createUIPanel = (element) => new UIPanel(element); 