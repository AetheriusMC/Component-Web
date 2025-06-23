"""
Aetherius Core Client
====================

Manages connection and communication with Aetherius Core engine.
"""

import asyncio
from typing import Optional, Any, Dict
from contextlib import asynccontextmanager

from app.utils.logging import get_logger
from app.utils.exceptions import CoreConnectionError, CoreAPIError

logger = get_logger(__name__)


class CoreClient:
    """Client for connecting to Aetherius Core engine"""
    
    def __init__(self):
        self._core = None
        self._initialized = False
        self._lock = asyncio.Lock()
    
    async def initialize(self):
        """Initialize connection to Aetherius Core"""
        async with self._lock:
            if self._initialized:
                return
            
            try:
                # TODO: Replace with actual Aetherius Core integration
                # from aetherius.api import get_core
                # self._core = get_core()
                
                # Mock implementation for development
                self._core = MockCore()
                
                logger.info("Core client initialized successfully")
                self._initialized = True
                
            except Exception as e:
                logger.error("Failed to initialize core client", error=str(e), exc_info=True)
                raise CoreConnectionError(f"Failed to connect to core: {e}")
    
    async def cleanup(self):
        """Cleanup core connection"""
        async with self._lock:
            if self._core and hasattr(self._core, 'cleanup'):
                try:
                    await self._core.cleanup()
                except Exception as e:
                    logger.warning("Error during core cleanup", error=str(e))
            
            self._core = None
            self._initialized = False
            logger.info("Core client cleaned up")
    
    async def is_connected(self) -> bool:
        """Check if connected to core"""
        return self._initialized and self._core is not None
    
    @asynccontextmanager
    async def get_core(self):
        """Get core instance with error handling"""
        if not await self.is_connected():
            raise CoreConnectionError("Core not connected")
        
        try:
            yield self._core
        except Exception as e:
            logger.error("Core operation failed", error=str(e), exc_info=True)
            raise CoreAPIError(f"Core operation failed: {e}")


class MockCore:
    """Mock implementation of Aetherius Core for development"""
    
    def __init__(self):
        self.is_running = True
        self.players = [
            {"uuid": "123e4567-e89b-12d3-a456-426614174000", "name": "TestPlayer1", "online": True},
            {"uuid": "123e4567-e89b-12d3-a456-426614174001", "name": "TestPlayer2", "online": False},
        ]
        self.server_logs = []
        self._log_counter = 0
    
    async def send_command(self, command: str) -> Dict[str, Any]:
        """Mock command execution"""
        logger.info("Executing command", command=command)
        
        # Simulate different command responses
        if command.startswith("say "):
            message = command[4:]
            return {
                "success": True,
                "message": f"Broadcasted: {message}",
                "timestamp": asyncio.get_event_loop().time()
            }
        elif command == "list":
            online_players = [p["name"] for p in self.players if p["online"]]
            return {
                "success": True,
                "message": f"Online players ({len(online_players)}): {', '.join(online_players)}",
                "timestamp": asyncio.get_event_loop().time()
            }
        elif command == "stop":
            self.is_running = False
            return {
                "success": True,
                "message": "Server stopping...",
                "timestamp": asyncio.get_event_loop().time()
            }
        else:
            return {
                "success": False,
                "message": f"Unknown command: {command}",
                "timestamp": asyncio.get_event_loop().time()
            }
    
    async def get_server_status(self) -> Dict[str, Any]:
        """Mock server status"""
        return {
            "is_running": self.is_running,
            "uptime": 3600,  # 1 hour
            "version": "1.20.1",
            "player_count": len([p for p in self.players if p["online"]]),
            "max_players": 20,
            "tps": 20.0,
            "cpu_usage": 45.2,
            "memory_usage": {
                "used": 2048,
                "max": 4096,
                "percentage": 50.0
            }
        }
    
    async def get_online_players(self) -> list:
        """Mock online players list"""
        return [p for p in self.players if p["online"]]
    
    def generate_log_entry(self, level: str = "INFO", message: str = None) -> Dict[str, Any]:
        """Generate mock log entry"""
        self._log_counter += 1
        
        if message is None:
            messages = [
                "Server started successfully",
                "Player TestPlayer1 joined the game",
                "Player TestPlayer2 left the game",
                "Saving world data...",
                "World saved successfully",
            ]
            message = messages[self._log_counter % len(messages)]
        
        return {
            "timestamp": asyncio.get_event_loop().time(),
            "level": level,
            "source": "Server",
            "message": message
        }
    
    async def cleanup(self):
        """Mock cleanup"""
        pass