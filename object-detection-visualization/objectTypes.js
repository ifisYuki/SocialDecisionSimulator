/**
 * 对象类型配置文件
 * 
 * 这个文件专门用于管理检测对象的类型、颜色和命名
 * 当需要添加新的对象类型时，只需要在这里添加配置即可
 */

// 🎯 对象类型配置
// 添加新对象类型时，在这里添加配置
export const OBJECT_TYPES = {
    0: {
        // Agent Pioneer - 白色主题
        name: 'AGENT_PIONEER',
        colors: {
            primary: '#ffffff',     // 主色：白色
            secondary: '#FFFB1F'    // 辅色：浅灰色
        },
        prefix: 'AGENT_PIONEER'     // ID前缀
    },
    
    4: {
        // Resource - 红白主题
        name: 'RESOURCE',
        colors: {
            primary: '#ff4444',     // 主色：红色
            secondary: '#ffffff'    // 辅色：白色
        },
        prefix: 'RESOURCE'          // ID前缀
    }

    // ✨ 添加新对象类型示例：
    // 1: {
    //     name: 'TARGET',
    //     colors: {
    //         primary: '#00ff41',     // 绿色
    //         secondary: '#00cc33'    // 深绿色
    //     },
    //     prefix: 'TARGET'
    // },
    
    // 2: {
    //     name: 'THREAT',
    //     colors: {
    //         primary: '#ff8800',     // 橙色
    //         secondary: '#ffaa44'    // 浅橙色
    //     },
    //     prefix: 'THREAT'
    // },
    
    // 3: {
    //     name: 'NEUTRAL',
    //     colors: {
    //         primary: '#00aaff',     // 蓝色
    //         secondary: '#88ccff'    // 浅蓝色
    //     },
    //     prefix: 'NEUTRAL'
    // }
};

// 🔧 默认未知对象配置
export const DEFAULT_OBJECT_TYPE = {
    name: 'UNKNOWN',
    colors: {
        primary: '#ffaa00',         // 橙色
        secondary: '#ffffff'        // 白色
    },
    prefix: 'UNKNOWN'
};

// 📋 预设配色方案（便于快速选择）
export const COLOR_PRESETS = {
    WHITE: { primary: '#ffffff', secondary: '#cccccc' },
    RED: { primary: '#ff4444', secondary: '#ffffff' },
    GREEN: { primary: '#00ff41', secondary: '#00cc33' },
    BLUE: { primary: '#00aaff', secondary: '#88ccff' },
    YELLOW: { primary: '#ffff00', secondary: '#ffcc00' },
    ORANGE: { primary: '#ff8800', secondary: '#ffaa44' },
    PURPLE: { primary: '#aa44ff', secondary: '#cc88ff' },
    CYAN: { primary: '#00ffff', secondary: '#88ffff' }
};

// 🛠️ 工具函数：获取对象类型配置
export const getObjectTypeConfig = (classId) => {
    return OBJECT_TYPES[classId] || DEFAULT_OBJECT_TYPE;
};

// 🛠️ 工具函数：添加新对象类型
export const addObjectType = (classId, name, colorPreset, customPrefix = null) => {
    const colors = COLOR_PRESETS[colorPreset] || colorPreset;
    const prefix = customPrefix || name.toUpperCase().replace(/\s+/g, '_');
    
    OBJECT_TYPES[classId] = {
        name: name.toUpperCase().replace(/\s+/g, '_'),
        colors: colors,
        prefix: prefix
    };
    
    console.log(`Added new object type: ${classId} -> ${name}`);
};

// 🛠️ 工具函数：修改现有对象类型
export const updateObjectType = (classId, updates) => {
    if (OBJECT_TYPES[classId]) {
        OBJECT_TYPES[classId] = { ...OBJECT_TYPES[classId], ...updates };
        console.log(`Updated object type ${classId}:`, updates);
    } else {
        console.warn(`Object type ${classId} not found`);
    }
};

// 📖 使用说明
export const USAGE_EXAMPLES = `
// 🔥 使用示例：

// 1. 添加新的对象类型
addObjectType(5, 'VEHICLE', 'BLUE');

// 2. 使用自定义颜色添加对象类型
addObjectType(6, 'BUILDING', { primary: '#8B4513', secondary: '#DEB887' });

// 3. 修改现有对象类型的颜色
updateObjectType(0, { colors: COLOR_PRESETS.GREEN });

// 4. 修改对象名称
updateObjectType(4, { name: 'SUPPLY_DEPOT', prefix: 'SUPPLY' });
`;

// 导出所有配置（兼容现有系统）
export const LEGACY_CLASS_NAMES = Object.fromEntries(
    Object.entries(OBJECT_TYPES).map(([id, config]) => [id, config.name.toLowerCase()])
);

export const LEGACY_OBJECT_COLORS = Object.fromEntries(
    Object.entries(OBJECT_TYPES).map(([id, config]) => [id, config.colors])
); 