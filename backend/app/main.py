"""
FastAPI Application Entry Point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Optional, List
import uvicorn

from app.core.client import CoreClient
from app.core.api import CoreAPI
from app.websocket.manager import WebSocketManager
from app.services.realtime_service import RealtimeService
from app.api import console, dashboard, players
from app.utils.logging import setup_logging


def create_app(cors_origins: Optional[List[str]] = None, component_instance=None) -> FastAPI:
    """
    创建FastAPI应用实例
    
    Args:
        cors_origins: CORS允许的源列表
        component_instance: Web组件实例（用于核心集成）
    """
    # 默认CORS源
    if cors_origins is None:
        cors_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # 全局实例
    core_client = CoreClient()
    websocket_manager = WebSocketManager()
    realtime_service = None  # Will be initialized after core is ready
    
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Application lifespan events"""
        # Startup
        setup_logging()
        
        # 如果有组件实例，使用组件的核心连接
        if component_instance:
            app.state.component = component_instance
            app.state.core = component_instance.core_adapter
        else:
            # 独立运行时初始化核心客户端
            await core_client.initialize()
            app.state.core = core_client
        
        # 存储WebSocket管理器到应用状态
        app.state.websocket_manager = websocket_manager
        
        # 初始化实时服务
        core_api = CoreAPI(app.state.core)
        realtime_service = RealtimeService(websocket_manager, core_api)
        app.state.realtime_service = realtime_service
        
        # 启动实时服务
        await realtime_service.start()
        
        yield
        
        # Shutdown
        # 停止实时服务
        if realtime_service:
            await realtime_service.stop()
        
        if not component_instance:
            # 只有独立运行时才清理核心客户端
            await core_client.cleanup()
        await websocket_manager.cleanup()

    # Create FastAPI application
    app = FastAPI(
        title="Aetherius Component: Web API",
        description="Web interface backend for Aetherius server management",
        version="0.1.0",
        lifespan=lifespan
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    return app


# 为向后兼容性创建默认应用实例
app = create_app()

# Include routers
app.include_router(console.router, prefix="/api/v1", tags=["console"])
app.include_router(dashboard.router, prefix="/api/v1", tags=["dashboard"])
app.include_router(players.router, prefix="/api/v1", tags=["players"])

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "core_connected": await core_client.is_connected(),
        "websocket_connections": websocket_manager.get_connection_count()
    }


# Development server
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )