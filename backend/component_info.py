"""
Aetherius Component: Web - 组件信息定义
==========================================

符合Aetherius核心规范的组件元数据定义
"""

try:
    from aetherius.core.component import ComponentInfo
except ImportError:
    # 开发模式下使用模拟接口
    from mock_aetherius import ComponentInfo

# 组件信息定义
component_info = ComponentInfo(
    name="web",
    display_name="Web Console",
    description="Aetherius的官方图形化界面，提供实时控制台、状态监控和管理功能",
    version="0.1.0",
    author="Aetherius Team",
    website="https://github.com/aetherius/component-web",
    
    # 组件依赖
    dependencies=[],
    
    # 软依赖（可选）
    soft_dependencies=[],
    
    # 支持的Aetherius版本
    aetherius_version=">=1.0.0",
    
    # 组件类型标识
    category="interface",
    
    # 权限要求
    permissions=[
        "aetherius.console.execute",
        "aetherius.status.read",
        "aetherius.players.read",
        "aetherius.players.manage",
        "aetherius.files.read",
        "aetherius.files.write"
    ],
    
    # 配置选项
    config_schema={
        "web_host": {
            "type": "string",
            "default": "0.0.0.0",
            "description": "Web服务器监听地址"
        },
        "web_port": {
            "type": "integer",
            "default": 8000,
            "description": "Web服务器端口"
        },
        "cors_origins": {
            "type": "array",
            "default": ["http://localhost:3000"],
            "description": "允许的CORS源"
        },
        "log_level": {
            "type": "string",
            "default": "INFO",
            "enum": ["DEBUG", "INFO", "WARNING", "ERROR"],
            "description": "日志级别"
        },
        "max_log_lines": {
            "type": "integer",
            "default": 1000,
            "description": "控制台最大日志行数"
        },
        "websocket_timeout": {
            "type": "integer",
            "default": 60,
            "description": "WebSocket连接超时时间（秒）"
        },
        "enable_file_manager": {
            "type": "boolean",
            "default": True,
            "description": "是否启用文件管理器功能"
        },
        "enable_player_management": {
            "type": "boolean",
            "default": True,
            "description": "是否启用玩家管理功能"
        }
    },
    
    # 默认配置
    default_config={
        "web_host": "0.0.0.0",
        "web_port": 8000,
        "cors_origins": ["http://localhost:3000"],
        "log_level": "INFO",
        "max_log_lines": 1000,
        "websocket_timeout": 60,
        "enable_file_manager": True,
        "enable_player_management": True
    }
)