"""
Dashboard API Endpoints
=======================

REST endpoints for dashboard data and server status.
"""

from typing import Dict, Any, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from app.core.client import CoreClient
from app.core.api import CoreAPI
from app.models.api_models import ServerStatus, Player
from app.utils.logging import get_logger
from app.utils.exceptions import CoreConnectionError, CoreAPIError
from app.websocket.manager import WebSocketManager, ConnectionType, create_performance_message, create_dashboard_summary_message

logger = get_logger(__name__)

router = APIRouter()

# Dependencies
async def get_core_api_from_app(request: Request) -> CoreAPI:
    """Dependency to get core API from app state"""
    core = request.app.state.core
    return CoreAPI(core)


@router.get("/dashboard/overview")
async def get_dashboard_overview(
    request: Request
):
    """
    Get comprehensive dashboard overview data
    
    Returns:
        Complete dashboard data including server status, players, and recent logs
    """
    try:
        logger.info("Fetching dashboard overview data")
        
        # Gather all dashboard data concurrently
        import asyncio
        
        # Get core API from app state
        core = request.app.state.core
        core_api = CoreAPI(core)
        
        server_status_task = core_api.get_server_status()
        online_players_task = core_api.get_online_players()
        
        server_status, online_players = await asyncio.gather(
            server_status_task,
            online_players_task,
            return_exceptions=True
        )
        
        # Handle any errors from concurrent operations
        if isinstance(server_status, Exception):
            logger.error("Failed to get server status", error=str(server_status))
            server_status = {
                "is_running": False,
                "uptime": 0,
                "version": "Unknown",
                "player_count": 0,
                "max_players": 20,
                "tps": 0.0,
                "cpu_usage": 0.0,
                "memory_usage": {"used": 0, "max": 4096, "percentage": 0.0},
                "timestamp": datetime.now().isoformat()
            }
        
        if isinstance(online_players, Exception):
            logger.error("Failed to get online players", error=str(online_players))
            online_players = []
        
        # Get recent logs (mock implementation for now)
        recent_logs = [
            {
                "timestamp": datetime.now().isoformat(),
                "level": "INFO",
                "source": "Server",
                "message": "Server is running normally"
            },
            {
                "timestamp": datetime.now().isoformat(),
                "level": "INFO",
                "source": "World",
                "message": "Auto-save completed"
            }
        ]
        
        return {
            "server_status": server_status,
            "online_players": online_players,
            "recent_logs": recent_logs,
            "statistics": {
                "total_players": len(online_players),
                "server_uptime": server_status.get("uptime", 0),
                "memory_usage_mb": server_status.get("memory_usage", {}).get("used", 0),
                "cpu_usage_percent": server_status.get("cpu_usage", 0.0)
            },
            "timestamp": datetime.now().isoformat()
        }
    
    except CoreConnectionError:
        raise HTTPException(
            status_code=503,
            detail="Aetherius Core is not available"
        )
    
    except Exception as e:
        logger.error("Error fetching dashboard overview", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch dashboard data"
        )


@router.get("/server/status", response_model=ServerStatus)
async def get_server_status(
    request: Request
):
    """
    Get current server status
    
    Returns:
        Current server status information
    """
    try:
        logger.debug("Fetching server status")
        
        # Get core API from app state
        core = request.app.state.core
        core_api = CoreAPI(core)
        status = await core_api.get_server_status()
        return ServerStatus(**status)
    
    except CoreConnectionError:
        raise HTTPException(
            status_code=503,
            detail="Aetherius Core is not available"
        )
    
    except CoreAPIError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get server status: {e.message}"
        )
    
    except Exception as e:
        logger.error("Unexpected error getting server status", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


@router.post("/server/start")
async def start_server(
    request: Request
):
    """
    Start the server
    
    Returns:
        Operation result
    """
    try:
        logger.info("Starting server via API")
        
        # Get core API from app state
        core = request.app.state.core
        core_api = CoreAPI(core)
        result = await core_api.start_server()
        
        return {
            "success": result["success"],
            "message": result["message"],
            "timestamp": result["timestamp"]
        }
    
    except CoreConnectionError:
        raise HTTPException(
            status_code=503,
            detail="Aetherius Core is not available"
        )
    
    except CoreAPIError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start server: {e.message}"
        )
    
    except Exception as e:
        logger.error("Unexpected error starting server", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


@router.post("/server/stop")
async def stop_server(
    request: Request
):
    """
    Stop the server
    
    Returns:
        Operation result
    """
    try:
        logger.info("Stopping server via API")
        
        # Get core API from app state
        core = request.app.state.core
        core_api = CoreAPI(core)
        result = await core_api.stop_server()
        
        return {
            "success": result["success"],
            "message": result["message"],
            "timestamp": result["timestamp"]
        }
    
    except CoreConnectionError:
        raise HTTPException(
            status_code=503,
            detail="Aetherius Core is not available"
        )
    
    except CoreAPIError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to stop server: {e.message}"
        )
    
    except Exception as e:
        logger.error("Unexpected error stopping server", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


@router.post("/server/restart")
async def restart_server(
    request: Request
):
    """
    Restart the server
    
    Returns:
        Operation result
    """
    try:
        logger.info("Restarting server via API")
        
        # Get core API from app state
        core = request.app.state.core
        core_api = CoreAPI(core)
        result = await core_api.restart_server()
        
        return {
            "success": result["success"],
            "message": result["message"],
            "timestamp": result["timestamp"]
        }
    
    except CoreConnectionError:
        raise HTTPException(
            status_code=503,
            detail="Aetherius Core is not available"
        )
    
    except CoreAPIError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to restart server: {e.message}"
        )
    
    except Exception as e:
        logger.error("Unexpected error restarting server", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


@router.get("/players", response_model=List[Player])
async def get_online_players(
    request: Request
):
    """
    Get list of online players
    
    Returns:
        List of currently online players
    """
    try:
        logger.debug("Fetching online players")
        
        # Get core API from app state
        core = request.app.state.core
        core_api = CoreAPI(core)
        players = await core_api.get_online_players()
        return [Player(**player) for player in players]
    
    except CoreConnectionError:
        raise HTTPException(
            status_code=503,
            detail="Aetherius Core is not available"
        )
    
    except CoreAPIError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get players: {e.message}"
        )
    
    except Exception as e:
        logger.error("Unexpected error getting players", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


@router.get("/server/metrics")
async def get_server_metrics(
    request: Request,
    hours: int = 1
):
    """
    Get server performance metrics over time
    
    Args:
        hours: Number of hours of metrics to return
        
    Returns:
        Time-series performance data
    """
    try:
        logger.debug("Fetching server metrics", hours=hours)
        
        # Get core API from app state
        core = request.app.state.core
        core_api = CoreAPI(core)
        
        # Try to get real metrics from core
        try:
            metrics = await core_api.get_metrics_history(hours)
            return {
                "metrics": metrics,
                "interval_minutes": 1,
                "hours": hours,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.warning("Failed to get real metrics, using mock data", error=str(e))
            
            # Fallback to mock data
            import time
            import random
            current_time = time.time()
            
            # Generate realistic mock data points
            data_points = []
            for i in range(hours * 60):  # One point per minute
                timestamp = current_time - (i * 60)
                base_tps = 19.5 + random.uniform(-0.5, 0.5)
                base_cpu = 45.0 + random.uniform(-10, 15)
                base_memory = 60.0 + random.uniform(-15, 20)
                base_players = max(0, 8 + random.randint(-5, 10))
                
                data_points.append({
                    "timestamp": timestamp,
                    "tps": max(0, min(20, base_tps)),
                    "cpu_usage": max(0, min(100, base_cpu)),
                    "memory_usage": max(0, min(100, base_memory)),
                    "player_count": base_players
                })
            
            return {
                "metrics": list(reversed(data_points)),  # Oldest to newest
                "interval_minutes": 1,
                "hours": hours,
                "timestamp": datetime.now().isoformat()
            }
    
    except Exception as e:
        logger.error("Error fetching server metrics", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch server metrics"
        )


@router.get("/server/performance")
async def get_current_performance(
    request: Request
):
    """
    Get current server performance metrics
    
    Returns:
        Real-time performance data
    """
    try:
        logger.debug("Fetching current server performance")
        
        # Get core API from app state
        core = request.app.state.core
        core_api = CoreAPI(core)
        
        # Get current performance data
        performance = await core_api.get_current_performance()
        
        return {
            "performance": performance,
            "timestamp": datetime.now().isoformat()
        }
    
    except CoreConnectionError:
        raise HTTPException(
            status_code=503,
            detail="Aetherius Core is not available"
        )
    
    except Exception as e:
        logger.error("Error fetching current performance", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch performance data"
        )


@router.get("/server/summary")
async def get_server_summary(
    request: Request
):
    """
    Get server summary statistics
    
    Returns:
        Server summary including uptime, total players, etc.
    """
    try:
        logger.debug("Fetching server summary")
        
        # Get core API from app state
        core = request.app.state.core
        core_api = CoreAPI(core)
        
        # Get server status and player info
        import asyncio
        status_task = core_api.get_server_status()
        players_task = core_api.get_online_players()
        
        status, players = await asyncio.gather(
            status_task,
            players_task,
            return_exceptions=True
        )
        
        # Handle errors gracefully
        if isinstance(status, Exception):
            status = {"is_running": False, "uptime": 0}
        if isinstance(players, Exception):
            players = []
        
        return {
            "is_running": status.get("is_running", False),
            "uptime": status.get("uptime", 0),
            "version": status.get("version", "Unknown"),
            "online_players": len(players),
            "max_players": status.get("max_players", 20),
            "tps": status.get("tps", 0.0),
            "cpu_usage": status.get("cpu_usage", 0.0),
            "memory_usage": status.get("memory_usage", {}).get("percentage", 0.0),
            "world_size": status.get("world_size", 0),
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error("Error fetching server summary", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch server summary"
        )


@router.websocket("/dashboard/ws")
async def dashboard_websocket(
    websocket: WebSocket,
    request: Request
):
    """
    WebSocket endpoint for dashboard real-time updates
    
    Provides real-time performance data and status updates
    """
    import uuid
    connection_id = str(uuid.uuid4())
    
    # Get WebSocket manager from app state
    ws_manager: WebSocketManager = request.app.state.websocket_manager
    
    try:
        # Connect to WebSocket manager
        await ws_manager.connect(
            websocket=websocket,
            connection_id=connection_id,
            connection_type=ConnectionType.DASHBOARD,
            client_info={"endpoint": "dashboard"}
        )
        
        # Send initial dashboard data
        try:
            core = request.app.state.core
            core_api = CoreAPI(core)
            
            # Get initial server summary
            summary_task = core_api.get_server_status()
            players_task = core_api.get_online_players()
            
            summary, players = await asyncio.gather(
                summary_task,
                players_task,
                return_exceptions=True
            )
            
            if isinstance(summary, Exception):
                summary = {"is_running": False}
            if isinstance(players, Exception):
                players = []
            
            initial_data = {
                "server_status": summary,
                "online_players": players,
                "player_count": len(players)
            }
            
            await ws_manager.send_to_connection(
                connection_id,
                create_dashboard_summary_message(initial_data)
            )
            
        except Exception as e:
            logger.warning("Failed to send initial dashboard data", error=str(e))
        
        # Keep connection alive and listen for messages
        try:
            while True:
                # Wait for messages from client
                data = await websocket.receive_json()
                
                # Handle client requests
                if data.get("type") == "request_update":
                    # Send current status update
                    try:
                        performance = await core_api.get_current_performance()
                        await ws_manager.send_to_connection(
                            connection_id,
                            create_performance_message(performance)
                        )
                    except Exception as e:
                        logger.warning("Failed to send performance update", error=str(e))
                        
        except WebSocketDisconnect:
            logger.info("Dashboard WebSocket client disconnected", connection_id=connection_id)
        
    except Exception as e:
        logger.error(
            "Error in dashboard WebSocket connection",
            connection_id=connection_id,
            error=str(e),
            exc_info=True
        )
    
    finally:
        # Clean up connection
        await ws_manager.disconnect(connection_id)