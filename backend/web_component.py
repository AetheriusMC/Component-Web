"""
Aetherius Component: Web - 主组件类
=================================

基于Aetherius核心Component基类的Web组件实现
"""

import asyncio
import uvicorn
from typing import Optional
from pathlib import Path

try:
    from aetherius.core.component import Component
    from aetherius.core.events import event_handler
    from aetherius.core.logger import get_logger
except ImportError:
    # 开发模式下使用模拟接口
    from mock_aetherius import Component, event_handler, get_logger

from app.main import create_app
from component_info import component_info


class WebComponent(Component):
    """Web界面组件主类"""
    
    def __init__(self):
        super().__init__(component_info)
        self.logger = get_logger(f"component.{self.info.name}")
        self.web_server: Optional[uvicorn.Server] = None
        self.server_task: Optional[asyncio.Task] = None
        
    async def on_load(self):
        """组件加载时调用"""
        self.logger.info("Web组件正在加载...")
        
        # 获取配置
        self.web_host = self.config.get("web_host", "0.0.0.0")
        self.web_port = self.config.get("web_port", 8000)
        self.cors_origins = self.config.get("cors_origins", ["http://localhost:3000"])
        self.log_level = self.config.get("log_level", "INFO")
        
        # 创建FastAPI应用
        self.app = create_app(
            cors_origins=self.cors_origins,
            component_instance=self
        )
        
        # 设置应用状态中的核心适配器
        from app.core.aetherius_adapter import AetheriusCoreAdapter
        self.core_adapter = AetheriusCoreAdapter(self.core)
        
        # 创建Uvicorn服务器配置
        self.server_config = uvicorn.Config(
            app=self.app,
            host=self.web_host,
            port=self.web_port,
            log_level=self.log_level.lower(),
            access_log=False,  # 由组件自己记录访问日志
            loop="asyncio"
        )
        
        self.logger.info(f"Web组件加载完成 - 配置端口: {self.web_port}")
        
    async def on_enable(self):
        """组件启用时调用"""
        self.logger.info("Web组件正在启用...")
        
        try:
            # 创建并启动Web服务器
            self.web_server = uvicorn.Server(self.server_config)
            self.server_task = asyncio.create_task(self.web_server.serve())
            
            self.logger.info(f"Web服务器已启动 - http://{self.web_host}:{self.web_port}")
            self.logger.info(f"API文档地址: http://{self.web_host}:{self.web_port}/docs")
            
        except Exception as e:
            self.logger.error(f"Web服务器启动失败: {e}")
            raise
            
    async def on_disable(self):
        """组件禁用时调用"""
        self.logger.info("Web组件正在禁用...")
        
        if self.web_server:
            # 停止Web服务器
            self.web_server.should_exit = True
            
            if self.server_task and not self.server_task.done():
                self.server_task.cancel()
                try:
                    await self.server_task
                except asyncio.CancelledError:
                    pass
            
            self.logger.info("Web服务器已停止")
        
    async def on_unload(self):
        """组件卸载时调用"""
        self.logger.info("Web组件正在卸载...")
        
        # 确保服务器已完全停止
        await self.on_disable()
        
        self.logger.info("Web组件已卸载")
    
    # 事件处理器
    @event_handler("server.start")
    async def on_server_start(self, event_data):
        """服务器启动事件处理"""
        self.logger.info("检测到服务器启动事件")
        # 通过WebSocket广播服务器启动消息
        if hasattr(self.app.state, 'websocket_manager'):
            from app.websocket.manager import create_status_message, ConnectionType
            message = create_status_message({
                "event": "server_start",
                "timestamp": event_data.get("timestamp"),
                "status": "running"
            })
            await self.app.state.websocket_manager.broadcast_to_type(
                ConnectionType.STATUS, message
            )
    
    @event_handler("server.stop")
    async def on_server_stop(self, event_data):
        """服务器停止事件处理"""
        self.logger.info("检测到服务器停止事件")
        if hasattr(self.app.state, 'websocket_manager'):
            from app.websocket.manager import create_status_message, ConnectionType
            message = create_status_message({
                "event": "server_stop",
                "timestamp": event_data.get("timestamp"),
                "status": "stopped"
            })
            await self.app.state.websocket_manager.broadcast_to_type(
                ConnectionType.STATUS, message
            )
    
    @event_handler("player.join")
    async def on_player_join(self, event_data):
        """玩家加入事件处理"""
        player_name = event_data.get("player_name", "Unknown")
        self.logger.info(f"玩家 {player_name} 加入了服务器")
        
        if hasattr(self.app.state, 'websocket_manager'):
            from app.websocket.manager import create_player_event_message, ConnectionType
            message = create_player_event_message("join", {
                "name": player_name,
                "uuid": event_data.get("player_uuid"),
                "timestamp": event_data.get("timestamp")
            })
            await self.app.state.websocket_manager.broadcast_to_type(
                ConnectionType.EVENTS, message
            )
    
    @event_handler("player.quit")
    async def on_player_quit(self, event_data):
        """玩家退出事件处理"""
        player_name = event_data.get("player_name", "Unknown")
        self.logger.info(f"玩家 {player_name} 离开了服务器")
        
        if hasattr(self.app.state, 'websocket_manager'):
            from app.websocket.manager import create_player_event_message, ConnectionType
            message = create_player_event_message("quit", {
                "name": player_name,
                "uuid": event_data.get("player_uuid"),
                "timestamp": event_data.get("timestamp")
            })
            await self.app.state.websocket_manager.broadcast_to_type(
                ConnectionType.EVENTS, message
            )
    
    @event_handler("console.log")
    async def on_console_log(self, event_data):
        """控制台日志事件处理"""
        if hasattr(self.app.state, 'websocket_manager'):
            from app.websocket.manager import create_console_message, ConnectionType
            message = create_console_message(
                level=event_data.get("level", "INFO"),
                message=event_data.get("message", ""),
                source=event_data.get("source", "Server")
            )
            await self.app.state.websocket_manager.broadcast_to_type(
                ConnectionType.CONSOLE, message
            )
    
    # 公共API方法，供其他组件或核心调用
    def get_web_status(self) -> dict:
        """获取Web组件状态"""
        return {
            "enabled": self.is_enabled,
            "server_running": self.web_server is not None and not self.web_server.should_exit,
            "host": self.web_host,
            "port": self.web_port,
            "active_connections": (
                self.app.state.websocket_manager.get_connection_count()
                if hasattr(self.app.state, 'websocket_manager')
                else 0
            )
        }
    
    async def execute_console_command(self, command: str) -> dict:
        """执行控制台命令（供Web API调用）"""
        try:
            # 通过核心执行命令
            result = await self.core.execute_command(command)
            
            self.logger.info(f"Web界面执行命令: {command}")
            
            return {
                "success": True,
                "command": command,
                "result": result,
                "timestamp": asyncio.get_event_loop().time()
            }
            
        except Exception as e:
            self.logger.error(f"命令执行失败: {command} - {e}")
            return {
                "success": False,
                "command": command,
                "error": str(e),
                "timestamp": asyncio.get_event_loop().time()
            }


# 导出组件实例创建函数
def create_component() -> WebComponent:
    """创建Web组件实例"""
    return WebComponent()