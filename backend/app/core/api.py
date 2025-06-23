"""
Core API Wrapper
================

High-level API wrapper for Aetherius Core operations.
"""

from typing import Dict, List, Any, Optional, Union
from datetime import datetime

from app.core.client import CoreClient
from app.utils.logging import get_logger
from app.utils.exceptions import CoreAPIError

logger = get_logger(__name__)


class CoreAPI:
    """High-level API wrapper for core operations"""
    
    def __init__(self, core_client_or_adapter):
        """
        初始化CoreAPI
        
        Args:
            core_client_or_adapter: CoreClient实例（独立模式）或适配器实例（组件模式）
        """
        self.client = core_client_or_adapter
    
    async def send_console_command(self, command: str) -> Dict[str, Any]:
        """
        Send a command to the server console
        
        Args:
            command: Console command to execute
            
        Returns:
            Command execution result
        """
        if not command or not command.strip():
            raise CoreAPIError("Command cannot be empty")
        
        command = command.strip()
        logger.info("Sending console command", command=command)
        
        # 检查是否为适配器模式
        if hasattr(self.client, 'send_console_command'):
            # 适配器模式（组件集成）
            result = await self.client.send_console_command(command)
        else:
            # 传统CoreClient模式（独立运行）
            async with self.client.get_core() as core:
                result = await core.send_command(command)
                
                result = {
                    "command": command,
                    "success": result.get("success", False),
                    "message": result.get("message", ""),
                    "timestamp": datetime.now().isoformat(),
                    "execution_time": result.get("timestamp", 0)
                }
        
        logger.info(
            "Console command executed",
            command=command,
            success=result.get("success", False),
            message=result.get("message", "")
        )
        
        return result
    
    async def get_server_status(self) -> Dict[str, Any]:
        """
        Get current server status
        
        Returns:
            Server status information
        """
        # 检查是否为适配器模式
        if hasattr(self.client, 'get_server_status'):
            # 适配器模式（组件集成）
            return await self.client.get_server_status()
        else:
            # 传统CoreClient模式（独立运行）
            async with self.client.get_core() as core:
                status = await core.get_server_status()
                
                return {
                    "is_running": status.get("is_running", False),
                    "uptime": status.get("uptime", 0),
                    "version": status.get("version", "Unknown"),
                    "player_count": status.get("player_count", 0),
                    "max_players": status.get("max_players", 20),
                    "tps": status.get("tps", 0.0),
                    "cpu_usage": status.get("cpu_usage", 0.0),
                    "memory_usage": status.get("memory_usage", {}),
                    "timestamp": datetime.now().isoformat()
                }
    
    async def get_online_players(self) -> List[Dict[str, Any]]:
        """
        Get list of online players
        
        Returns:
            List of online player information
        """
        # 检查是否为适配器模式
        if hasattr(self.client, 'get_online_players'):
            # 适配器模式（组件集成）
            return await self.client.get_online_players()
        else:
            # 传统CoreClient模式（独立运行）
            async with self.client.get_core() as core:
                players = await core.get_online_players()
                
                return [
                    {
                        "uuid": player.get("uuid", ""),
                        "name": player.get("name", "Unknown"),
                        "online": player.get("online", False),
                        "last_login": player.get("last_login"),
                        "ip_address": player.get("ip_address"),
                        "game_mode": player.get("game_mode", "survival"),
                        "level": player.get("level", 0),
                        "experience": player.get("experience", 0)
                    }
                    for player in players
                ]
    
    async def start_server(self) -> Dict[str, Any]:
        """
        Start the server
        
        Returns:
            Operation result
        """
        # 检查是否为适配器模式
        if hasattr(self.client, 'start_server'):
            # 适配器模式（组件集成）
            return await self.client.start_server()
        else:
            # 传统CoreClient模式（独立运行）
            return await self.send_console_command("start")
    
    async def stop_server(self) -> Dict[str, Any]:
        """
        Stop the server
        
        Returns:
            Operation result
        """
        # 检查是否为适配器模式
        if hasattr(self.client, 'stop_server'):
            # 适配器模式（组件集成）
            return await self.client.stop_server()
        else:
            # 传统CoreClient模式（独立运行）
            return await self.send_console_command("stop")
    
    async def restart_server(self) -> Dict[str, Any]:
        """
        Restart the server
        
        Returns:
            Operation result
        """
        # 检查是否为适配器模式
        if hasattr(self.client, 'restart_server'):
            # 适配器模式（组件集成）
            return await self.client.restart_server()
        else:
            # 传统CoreClient模式（独立运行）
            return await self.send_console_command("restart")
    
    async def kick_player(self, player_name: str, reason: str = "Kicked by admin") -> Dict[str, Any]:
        """
        Kick a player from the server
        
        Args:
            player_name: Name of the player to kick
            reason: Reason for kicking
            
        Returns:
            Operation result
        """
        command = f"kick {player_name} {reason}"
        return await self.send_console_command(command)
    
    async def ban_player(self, player_name: str, reason: str = "Banned by admin") -> Dict[str, Any]:
        """
        Ban a player from the server
        
        Args:
            player_name: Name of the player to ban
            reason: Reason for banning
            
        Returns:
            Operation result
        """
        command = f"ban {player_name} {reason}"
        return await self.send_console_command(command)
    
    async def op_player(self, player_name: str) -> Dict[str, Any]:
        """
        Give operator privileges to a player
        
        Args:
            player_name: Name of the player
            
        Returns:
            Operation result
        """
        command = f"op {player_name}"
        return await self.send_console_command(command)
    
    async def deop_player(self, player_name: str) -> Dict[str, Any]:
        """
        Remove operator privileges from a player
        
        Args:
            player_name: Name of the player
            
        Returns:
            Operation result
        """
        command = f"deop {player_name}"
        return await self.send_console_command(command)