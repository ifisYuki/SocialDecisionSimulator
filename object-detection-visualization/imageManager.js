// 增强的图片管理器 - 支持真实图片加载
class ImageManager {
    constructor() {
        this.images = {
            technical: [],
            objects: [],
            schematics: [],
            all: [] // 所有图片的统一池
        };
        this.currentRotationImages = {};
        this.rotationInterval = null;
        this.loadImages();
        this.startRotation();
    }

    // 加载实际的图片文件
    loadImages() {
        // 使用images文件夹中的实际PNG文件
        const imageFiles = [
            'images/1.png',
            'images/2.png',
            'images/3.png',
            'images/4.png',
            'images/5.png',
            'images/6.png',
            'images/7.png'
        ];

        // 将所有图片添加到各个分类中（重复使用以增加变化）
        this.images.all = [...imageFiles];
        this.images.technical = [...imageFiles];
        this.images.objects = [...imageFiles];
        this.images.schematics = [...imageFiles];

        console.log('图片管理器已加载图片:', this.images.all.length, '个文件');
    }

    // 获取随机图片
    getRandomImage(category = 'all') {
        const categoryImages = this.images[category] || this.images.all;
        if (categoryImages.length === 0) {
            console.warn(`类别 ${category} 没有可用图片`);
            return null;
        }
        
        const randomIndex = Math.floor(Math.random() * categoryImages.length);
        const selectedImage = categoryImages[randomIndex];
        console.log(`获取随机图片 [${category}]:`, selectedImage);
        return selectedImage;
    }

    // 开始图片轮换
    startRotation() {
        // 立即轮换一次
        this.rotateImages();
        
        // 每4秒轮换一次
        this.rotationInterval = setInterval(() => {
            this.rotateImages();
        }, 4000);
        
        console.log('图片轮换已启动，间隔4秒');
    }

    // 停止轮换
    stopRotation() {
        if (this.rotationInterval) {
            clearInterval(this.rotationInterval);
            this.rotationInterval = null;
            console.log('图片轮换已停止');
        }
    }

    // 轮换图片
    rotateImages() {
        const slotId = 'main-image-slot';
        const newImage = this.getRandomImage('all');
        if (newImage) {
            this.currentRotationImages[slotId] = newImage;
        }

        // 触发更新事件
        document.dispatchEvent(new CustomEvent('imagesRotated', {
            detail: { images: this.currentRotationImages }
        }));
    }

    // 获取当前轮换的图片
    getCurrentImage(slotId) {
        return this.currentRotationImages[slotId] || this.getRandomImage('all');
    }

    // 预加载图片（确保图片能正确显示）
    preloadImage(src) {
        return new Promise((resolve, reject) => {
            const img = new Image();
            img.onload = () => {
                console.log('图片预加载成功:', src);
                resolve(img);
            };
            img.onerror = () => {
                console.warn('图片预加载失败:', src);
                reject(new Error(`Failed to load image: ${src}`));
            };
            img.src = src;
        });
    }

    // 生成随机SVG占位符（备用）
    generateRandomSVG(width, height, category) {
        const colors = ['#00ff41', '#ffffff', '#ffff00', '#ff4444'];
        const bgColor = colors[Math.floor(Math.random() * colors.length)];
        const textColor = bgColor === '#ffffff' ? '#000000' : '#ffffff';
        
        return `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">
            <rect width="100%" height="100%" fill="${bgColor}" opacity="0.3"/>
            <rect x="10" y="10" width="${width-20}" height="${height-20}" fill="none" stroke="${textColor}" stroke-width="2"/>
            <text x="50%" y="50%" font-family="monospace" font-size="14" fill="${textColor}" text-anchor="middle" dominant-baseline="middle">
                ${category.toUpperCase()}
            </text>
            <text x="50%" y="60%" font-family="monospace" font-size="10" fill="${textColor}" text-anchor="middle" dominant-baseline="middle">
                ${width}×${height}
            </text>
        </svg>`;
    }

    // 销毁实例
    destroy() {
        this.stopRotation();
        this.images = { technical: [], objects: [], schematics: [], all: [] };
        this.currentRotationImages = {};
    }
}

// 创建全局实例
export const imageManager = new ImageManager(); 