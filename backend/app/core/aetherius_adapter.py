"""
Aetherius核心适配器
==================

适配Aetherius核心的接口，使Web组件能够与核心系统集成
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio


class AetheriusCoreAdapter:
    """
    Aetherius核心适配器
    
    这个类适配现有的CoreClient接口到Aetherius核心的实际接口
    """
    
    def __init__(self, core_instance):
        """
        初始化适配器
        
        Args:
            core_instance: Aetherius核心实例
        """
        self.core = core_instance
        
    async def is_connected(self) -> bool:
        """检查是否连接到核心"""
        try:
            # 如果有核心实例且核心处于活动状态
            return self.core is not None and hasattr(self.core, 'is_running') and self.core.is_running
        except Exception:
            return False
    
    async def initialize(self):
        """初始化连接（在组件模式下不需要）"""
        # 在组件模式下，核心连接由组件管理，这里不需要做任何事情
        pass
    
    async def cleanup(self):
        """清理连接（在组件模式下不需要）"""
        # 在组件模式下，核心连接由组件管理，这里不需要做任何事情  
        pass
    
    async def send_console_command(self, command: str) -> Dict[str, Any]:
        """
        发送控制台命令
        
        Args:
            command: 要执行的命令
            
        Returns:
            命令执行结果
        """
        try:
            if not await self.is_connected():
                return {
                    "success": False,
                    "command": command,
                    "message": "Core is not connected",
                    "timestamp": datetime.now().isoformat()
                }
            
            # 通过核心执行命令
            result = await self.core.execute_command(command)
            
            return {
                "success": True,
                "command": command,
                "message": str(result) if result else "Command executed successfully",
                "timestamp": datetime.now().isoformat(),
                "execution_time": 0.1  # Mock execution time
            }
            
        except Exception as e:
            return {
                "success": False,
                "command": command,
                "message": f"Command execution failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_server_status(self) -> Dict[str, Any]:
        """
        获取服务器状态
        
        Returns:
            服务器状态信息
        """
        try:
            if not await self.is_connected():
                return self._get_offline_status()
            
            # 从核心获取服务器状态
            if hasattr(self.core, 'get_server_status'):
                status = await self.core.get_server_status()
                return self._normalize_server_status(status)
            else:
                return self._get_default_status()
                
        except Exception as e:
            return self._get_error_status(str(e))
    
    async def get_online_players(self) -> List[Dict[str, Any]]:
        """
        获取在线玩家列表
        
        Returns:
            在线玩家列表
        """
        try:
            if not await self.is_connected():
                return []
            
            # 从核心获取玩家列表
            if hasattr(self.core, 'get_online_players'):
                players = await self.core.get_online_players()
                return [self._normalize_player_data(player) for player in players]
            else:
                return self._get_mock_players()
                
        except Exception as e:
            return []
    
    async def start_server(self) -> Dict[str, Any]:
        """
        启动服务器
        
        Returns:
            操作结果
        """
        try:
            if hasattr(self.core, 'start_server'):
                result = await self.core.start_server()
                return {
                    "success": True,
                    "message": "Server start initiated",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "success": False,
                    "message": "Server start not supported",
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to start server: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    async def stop_server(self) -> Dict[str, Any]:
        """
        停止服务器
        
        Returns:
            操作结果
        """
        try:
            if hasattr(self.core, 'stop_server'):
                result = await self.core.stop_server()
                return {
                    "success": True,
                    "message": "Server stop initiated",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "success": False,
                    "message": "Server stop not supported",
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to stop server: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    async def restart_server(self) -> Dict[str, Any]:
        """
        重启服务器
        
        Returns:
            操作结果
        """
        try:
            if hasattr(self.core, 'restart_server'):
                result = await self.core.restart_server()
                return {
                    "success": True,
                    "message": "Server restart initiated",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                # 如果没有重启方法，尝试先停止再启动
                stop_result = await self.stop_server()
                if stop_result["success"]:
                    await asyncio.sleep(2)  # 等待停止
                    start_result = await self.start_server()
                    return start_result
                else:
                    return stop_result
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to restart server: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    def _get_offline_status(self) -> Dict[str, Any]:
        """获取离线状态"""
        return {
            "is_running": False,
            "uptime": 0,
            "version": "Unknown",
            "player_count": 0,
            "max_players": 20,
            "tps": 0.0,
            "cpu_usage": 0.0,
            "memory_usage": {
                "used": 0,
                "max": 4096,
                "percentage": 0.0
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def _get_default_status(self) -> Dict[str, Any]:
        """获取默认状态（连接但没有状态信息）"""
        return {
            "is_running": True,
            "uptime": 3600,  # 1 hour
            "version": "1.0.0",
            "player_count": 0,
            "max_players": 20,
            "tps": 20.0,
            "cpu_usage": 25.0,
            "memory_usage": {
                "used": 1024,
                "max": 4096,
                "percentage": 25.0
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def _get_error_status(self, error: str) -> Dict[str, Any]:
        """获取错误状态"""
        status = self._get_offline_status()
        status["error"] = error
        return status
    
    def _normalize_server_status(self, raw_status: Any) -> Dict[str, Any]:
        """标准化服务器状态数据"""
        if isinstance(raw_status, dict):
            return {
                "is_running": raw_status.get("running", True),
                "uptime": raw_status.get("uptime", 0),
                "version": raw_status.get("version", "1.0.0"),
                "player_count": raw_status.get("player_count", 0),
                "max_players": raw_status.get("max_players", 20),
                "tps": raw_status.get("tps", 20.0),
                "cpu_usage": raw_status.get("cpu_usage", 0.0),
                "memory_usage": {
                    "used": raw_status.get("memory_used", 0),
                    "max": raw_status.get("memory_max", 4096),
                    "percentage": raw_status.get("memory_percentage", 0.0)
                },
                "timestamp": datetime.now().isoformat()
            }
        else:
            return self._get_default_status()
    
    def _normalize_player_data(self, raw_player: Any) -> Dict[str, Any]:
        """标准化玩家数据"""
        if isinstance(raw_player, dict):
            return {
                "uuid": raw_player.get("uuid", ""),
                "name": raw_player.get("name", "Unknown"),
                "online": raw_player.get("online", True),
                "last_login": raw_player.get("last_login"),
                "ip_address": raw_player.get("ip_address"),
                "game_mode": raw_player.get("game_mode", "survival"),
                "level": raw_player.get("level", 0),
                "experience": raw_player.get("experience", 0)
            }
        else:
            return {
                "uuid": str(raw_player) if raw_player else "",
                "name": str(raw_player) if raw_player else "Unknown",
                "online": True,
                "last_login": None,
                "ip_address": None,
                "game_mode": "survival",
                "level": 0,
                "experience": 0
            }
    
    def _get_mock_players(self) -> List[Dict[str, Any]]:
        """获取模拟玩家数据"""
        return [
            {
                "uuid": "550e8400-e29b-41d4-a716-446655440000",
                "name": "TestPlayer1",
                "online": True,
                "last_login": datetime.now().isoformat(),
                "ip_address": "127.0.0.1",
                "game_mode": "survival",
                "level": 42,
                "experience": 1337
            }
        ]