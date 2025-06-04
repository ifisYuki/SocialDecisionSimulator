import { VISUAL_CONFIG, STYLE_CONFIG, COLOR_SCHEME, getObjectColor, getObjectName, generateObjectId } from './config.js';
import { dataManager } from './dataManager.js';

class Renderer {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.animationTime = 0; // 添加动画时间追踪
        this.setupCanvas();
    }

    setupCanvas() {
        const container = this.canvas.parentElement;
        this.canvas.width = container.clientWidth;
        this.canvas.height = container.clientHeight;
    }

    // 绘制网格系统
    drawGridSystem() {
        // 清空画布 - 纯黑色背景
        this.ctx.fillStyle = COLOR_SCHEME.BACKGROUND;
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        // 绘制主网格
        this.ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
        this.ctx.lineWidth = 0.5;
        
        const gridSize = 40;
        for (let x = 0; x <= this.canvas.width; x += gridSize) {
            this.ctx.beginPath();
            this.ctx.moveTo(x, 0);
            this.ctx.lineTo(x, this.canvas.height);
            this.ctx.stroke();
        }
        
        for (let y = 0; y <= this.canvas.height; y += gridSize) {
            this.ctx.beginPath();
            this.ctx.moveTo(0, y);
            this.ctx.lineTo(this.canvas.width, y);
            this.ctx.stroke();
        }
        
        // 绘制主坐标轴（白色）
        this.ctx.strokeStyle = COLOR_SCHEME.PRIMARY;
        this.ctx.lineWidth = 1;
        
        // X轴
        this.ctx.beginPath();
        this.ctx.moveTo(VISUAL_CONFIG.MARGIN, this.canvas.height - VISUAL_CONFIG.MARGIN);
        this.ctx.lineTo(this.canvas.width - VISUAL_CONFIG.MARGIN, this.canvas.height - VISUAL_CONFIG.MARGIN);
        this.ctx.stroke();
        
        // Y轴
        this.ctx.beginPath();
        this.ctx.moveTo(VISUAL_CONFIG.MARGIN, this.canvas.height - VISUAL_CONFIG.MARGIN);
        this.ctx.lineTo(VISUAL_CONFIG.MARGIN, VISUAL_CONFIG.MARGIN);
        this.ctx.stroke();
        
        // 绘制坐标标记
        this.drawCoordinateMarkers();
        
        // 绘制中心十字线
        this.drawCenterCrosshairs();
    }

    // 绘制坐标标记
    drawCoordinateMarkers() {
        this.ctx.fillStyle = COLOR_SCHEME.PRIMARY;
        this.ctx.font = '10px JetBrains Mono, monospace';
        this.ctx.textAlign = 'center';
        this.ctx.textBaseline = 'top';
        
        const steps = 5;
        for (let i = 0; i <= steps; i++) {
            const x = VISUAL_CONFIG.MARGIN + (i / steps) * (this.canvas.width - 2 * VISUAL_CONFIG.MARGIN);
            const y = this.canvas.height - VISUAL_CONFIG.MARGIN + 5;
            this.ctx.fillText((i / steps).toFixed(1), x, y);
        }
        
        this.ctx.textAlign = 'right';
        this.ctx.textBaseline = 'middle';
        
        for (let i = 0; i <= steps; i++) {
            const x = VISUAL_CONFIG.MARGIN - 5;
            const y = this.canvas.height - VISUAL_CONFIG.MARGIN - (i / steps) * (this.canvas.height - 2 * VISUAL_CONFIG.MARGIN);
            this.ctx.fillText((i / steps).toFixed(1), x, y);
        }
    }

    // 绘制中心十字线
    drawCenterCrosshairs() {
        const centerX = this.canvas.width / 2;
        const centerY = this.canvas.height / 2;
        
        this.ctx.strokeStyle = 'rgba(255, 255, 255, 0.4)';
        this.ctx.lineWidth = 1;
        this.ctx.setLineDash([5, 5]);
        
        // 垂直线
        this.ctx.beginPath();
        this.ctx.moveTo(centerX, VISUAL_CONFIG.MARGIN);
        this.ctx.lineTo(centerX, this.canvas.height - VISUAL_CONFIG.MARGIN);
        this.ctx.stroke();
        
        // 水平线
        this.ctx.beginPath();
        this.ctx.moveTo(VISUAL_CONFIG.MARGIN, centerY);
        this.ctx.lineTo(this.canvas.width - VISUAL_CONFIG.MARGIN, centerY);
        this.ctx.stroke();
        
        this.ctx.setLineDash([]);
    }

    // 转换坐标到画布空间
    transformToCanvas(point) {
        return [
            VISUAL_CONFIG.MARGIN + point[0] * (this.canvas.width - 2 * VISUAL_CONFIG.MARGIN),
            VISUAL_CONFIG.MARGIN + (1 - point[1]) * (this.canvas.height - 2 * VISUAL_CONFIG.MARGIN)
        ];
    }

    // 绘制目标锁定圈
    drawTargetReticle(centerX, centerY, radius, isLocked, primaryColor, secondaryColor) {
        // 使用主色绘制外圈和十字线
        this.ctx.strokeStyle = isLocked ? primaryColor : `${primaryColor}aa`;
        this.ctx.lineWidth = 1;
        
        // 外圈
        this.ctx.beginPath();
        this.ctx.arc(centerX, centerY, radius + 10, 0, Math.PI * 2);
        this.ctx.stroke();
        
        // 十字线
        const crossSize = 15;
        this.ctx.beginPath();
        this.ctx.moveTo(centerX - crossSize, centerY);
        this.ctx.lineTo(centerX + crossSize, centerY);
        this.ctx.moveTo(centerX, centerY - crossSize);
        this.ctx.lineTo(centerX, centerY + crossSize);
        this.ctx.stroke();
        
        // 角落标记 - 使用次要颜色
        this.ctx.strokeStyle = isLocked ? secondaryColor : `${secondaryColor}aa`;
        const cornerSize = 8;
        const corners = [
            [-1, -1], [1, -1], [1, 1], [-1, 1]
        ];
        
        corners.forEach(([dx, dy]) => {
            const x = centerX + dx * (radius + 20);
            const y = centerY + dy * (radius + 20);
            
            this.ctx.beginPath();
            this.ctx.moveTo(x, y + dy * cornerSize);
            this.ctx.lineTo(x, y);
            this.ctx.lineTo(x + dx * cornerSize, y);
            this.ctx.stroke();
        });
    }

    // 绘制单个对象
    drawObject(obj, index) {
        const isHighlighted = index === dataManager.hoveredObjectIndex;
        const points = dataManager.getObjectPoints(obj);
        const canvasPoints = points.map(point => this.transformToCanvas(point));
        
        // 获取对象颜色
        const primaryColor = getObjectColor(obj[0], false);
        const secondaryColor = getObjectColor(obj[0], true);
        const strokeColor = isHighlighted ? primaryColor : `${primaryColor}cc`;
        
        // 绘制连接线（轨迹效果）
        if (canvasPoints.length >= 4) {
            this.ctx.strokeStyle = `${primaryColor}66`;
            this.ctx.lineWidth = 1;
            this.ctx.setLineDash([2, 2]);
            
            this.ctx.beginPath();
            this.ctx.moveTo(canvasPoints[0][0], canvasPoints[0][1]);
            for (let i = 1; i < canvasPoints.length; i++) {
                this.ctx.lineTo(canvasPoints[i][0], canvasPoints[i][1]);
            }
            this.ctx.closePath();
            this.ctx.stroke();
            this.ctx.setLineDash([]);
        }
        
        // 绘制边界框
        this.ctx.strokeStyle = strokeColor;
        this.ctx.lineWidth = isHighlighted ? 2 : 1;
        
        this.ctx.beginPath();
        this.ctx.moveTo(canvasPoints[0][0], canvasPoints[0][1]);
        for (let i = 1; i < canvasPoints.length; i++) {
            this.ctx.lineTo(canvasPoints[i][0], canvasPoints[i][1]);
        }
        this.ctx.closePath();
        this.ctx.stroke();
        
        // 计算中心点
        const center = dataManager.getObjectCenter(obj);
        const canvasCenter = this.transformToCanvas([center.x, center.y]);
        
        // 绘制目标锁定圈
        const isLocked = obj[9] > 0.8;
        this.drawTargetReticle(canvasCenter[0], canvasCenter[1], VISUAL_CONFIG.POINT_RADIUS, 
                              isLocked || isHighlighted, primaryColor, secondaryColor);
        
        // 绘制中心点
        this.ctx.beginPath();
        this.ctx.arc(
            canvasCenter[0], 
            canvasCenter[1], 
            isHighlighted ? VISUAL_CONFIG.POINT_RADIUS + 2 : VISUAL_CONFIG.POINT_RADIUS, 
            0, 
            Math.PI * 2
        );
        this.ctx.fillStyle = strokeColor;
        this.ctx.fill();
        
        // 添加目标标签
        this.ctx.fillStyle = primaryColor;
        this.ctx.textAlign = 'left';
        this.ctx.textBaseline = 'bottom';
        this.ctx.font = isHighlighted ? 'bold 12px JetBrains Mono' : '10px JetBrains Mono';
        
        const label = generateObjectId(obj[0], index);
        const subLabel = `${getObjectName(obj[0])} [${(obj[9] * 100).toFixed(0)}%]`;
        
        this.ctx.fillText(label, canvasCenter[0] + 15, canvasCenter[1] - 5);
        this.ctx.font = '8px JetBrains Mono';
        this.ctx.fillStyle = secondaryColor;
        this.ctx.fillText(subLabel, canvasCenter[0] + 15, canvasCenter[1] + 8);
    }

    // 绘制红色物体之间的连线
    drawResourceConnections() {
        // 获取所有红色物体(RESOURCE, ID=4)
        const resourceObjects = dataManager.currentObjects.filter(obj => obj[0] === 4);
        
        if (resourceObjects.length < 3) return; // 至少需要3个点才能形成外圈
        
        // 获取所有红色物体的中心点
        const centers = resourceObjects.map(obj => {
            const center = dataManager.getObjectCenter(obj);
            return {
                x: center.x,
                y: center.y,
                obj: obj
            };
        });
        
        // 计算凸包来找到最外圈的点
        const hull = this.convexHull(centers);
        
        if (hull.length < 3) return;
        
        // 绘制外圈连线
        for (let i = 0; i < hull.length; i++) {
            const current = hull[i];
            const next = hull[(i + 1) % hull.length];
            
            const canvasCenter1 = this.transformToCanvas([current.x, current.y]);
            const canvasCenter2 = this.transformToCanvas([next.x, next.y]);
            
            // 使用非常细和半透明的线
            this.ctx.strokeStyle = 'rgba(255, 68, 68, 0.59)'; // 更加半透明
            this.ctx.lineWidth = 1; // 细线
            // this.ctx.setLineDash([3, 3]); // 细虚线
            
            this.ctx.beginPath();
            this.ctx.moveTo(canvasCenter1[0], canvasCenter1[1]);
            this.ctx.lineTo(canvasCenter2[0], canvasCenter2[1]);
            this.ctx.stroke();
        }
        
        this.ctx.setLineDash([]);
    }

    // 计算凸包 (Graham扫描算法的简化版本)
    convexHull(points) {
        if (points.length < 3) return points;
        
        // 找到最底部的点（y最小），如果有多个则选择x最小的
        let start = 0;
        for (let i = 1; i < points.length; i++) {
            if (points[i].y < points[start].y || 
                (points[i].y === points[start].y && points[i].x < points[start].x)) {
                start = i;
            }
        }
        
        // 将起始点放到第一位
        [points[0], points[start]] = [points[start], points[0]];
        
        // 按照极角排序
        const startPoint = points[0];
        const sortedPoints = points.slice(1).sort((a, b) => {
            const angleA = Math.atan2(a.y - startPoint.y, a.x - startPoint.x);
            const angleB = Math.atan2(b.y - startPoint.y, b.x - startPoint.x);
            return angleA - angleB;
        });
        
        // 构建凸包
        const hull = [startPoint];
        
        for (const point of sortedPoints) {
            // 移除不在凸包上的点
            while (hull.length > 1 && this.crossProduct(hull[hull.length-2], hull[hull.length-1], point) <= 0) {
                hull.pop();
            }
            hull.push(point);
        }
        
        return hull;
    }

    // 计算叉积来判断三点的方向
    crossProduct(o, a, b) {
        return (a.x - o.x) * (b.y - o.y) - (a.y - o.y) * (b.x - o.x);
    }

    // 绘制Agent雷达探测圈
    drawAgentRadarRings() {
        // 获取所有Agent对象(AGENT_PIONEER, ID=0)
        const agentObjects = dataManager.currentObjects.filter(obj => obj[0] === 0);
        
        agentObjects.forEach((obj, index) => {
            const center = dataManager.getObjectCenter(obj);
            const canvasCenter = this.transformToCanvas([center.x, center.y]);
            
            // 绘制多层雷达圈
            const baseRadius = 40;
            const ringCount = 3;
            
            for (let ring = 0; ring < ringCount; ring++) {
                const ringOffset = ring * 25;
                const animationOffset = (this.animationTime * 0.002 + ring * 0.8) % (Math.PI * 2);
                
                // 雷达圈半径动态变化
                const radius = baseRadius + ringOffset + Math.sin(animationOffset) * 10;
                
                // 透明度随动画变化
                const alpha = (Math.sin(animationOffset) * 0.3 + 0.4) * (1 - ring * 0.2);
                
                // 绘制雷达圈
                this.ctx.strokeStyle = `rgba(255, 255, 255, ${alpha})`;
                this.ctx.lineWidth = 2 - ring * 0.3;
                this.ctx.setLineDash([4, 4]);
                
                this.ctx.beginPath();
                this.ctx.arc(canvasCenter[0], canvasCenter[1], radius, 0, Math.PI * 2);
                this.ctx.stroke();
                
                // 绘制雷达扫描线
                const sweepAngle = (this.animationTime * 0.01 + index * 1.2) % (Math.PI * 2);
                this.ctx.strokeStyle = `rgba(255, 251, 31, ${alpha * 0.8})`;
                this.ctx.lineWidth = 1;
                this.ctx.setLineDash([]);
                
                this.ctx.beginPath();
                this.ctx.moveTo(canvasCenter[0], canvasCenter[1]);
                this.ctx.lineTo(
                    canvasCenter[0] + Math.cos(sweepAngle) * radius,
                    canvasCenter[1] + Math.sin(sweepAngle) * radius
                );
                this.ctx.stroke();
                
                // 绘制扫描点
                const pointDistance = radius * 0.7;
                const pointX = canvasCenter[0] + Math.cos(sweepAngle) * pointDistance;
                const pointY = canvasCenter[1] + Math.sin(sweepAngle) * pointDistance;
                
                this.ctx.fillStyle = `rgba(255, 251, 31, ${alpha})`;
                this.ctx.beginPath();
                this.ctx.arc(pointX, pointY, 2, 0, Math.PI * 2);
                this.ctx.fill();
            }
            
            this.ctx.setLineDash([]);
        });
    }

    // 绘制所有对象
    drawObjects() {
        if (!dataManager.currentObjects || dataManager.currentObjects.length === 0) return;
        
        // 先绘制连线效果（在对象下方）
        this.drawResourceConnections();
        
        // 然后绘制对象
        dataManager.currentObjects.forEach((obj, index) => this.drawObject(obj, index));
        
        // 最后绘制雷达圈（在对象上方）
        this.drawAgentRadarRings();
    }

    // 完整重绘
    render() {
        // 更新动画时间
        this.animationTime = Date.now();
        
        this.drawGridSystem();
        this.drawObjects();
    }
}

export const createRenderer = (canvas) => new Renderer(canvas); 