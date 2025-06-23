"""
Console API Endpoints
=====================

WebSocket and REST endpoints for server console functionality.
"""

import uuid
import asyncio
from typing import Dict, Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from app.core.client import CoreClient
from app.core.api import CoreAPI
from app.websocket.manager import WebSocketManager, ConnectionType, create_console_message
from app.models.api_models import ConsoleCommand, CommandResponse
from app.utils.logging import get_logger
from app.utils.exceptions import CoreConnectionError, CoreAPIError

logger = get_logger(__name__)

router = APIRouter()

# Dependencies
async def get_core_from_app(request) -> Any:
    """Dependency to get core from app state"""
    return request.app.state.core

async def get_websocket_manager_from_app(request) -> WebSocketManager:
    """Dependency to get WebSocket manager from app state"""
    return request.app.state.websocket_manager

async def get_core_api(request) -> CoreAPI:
    """Dependency to get core API"""
    core = request.app.state.core
    return CoreAPI(core)


@router.websocket("/console/ws")
async def console_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for real-time console communication
    
    Handles:
    - Real-time server log streaming
    - Command execution from web interface
    - Bidirectional communication with the client
    """
    connection_id = str(uuid.uuid4())
    
    # Get dependencies from app state
    ws_manager = websocket.app.state.websocket_manager
    core = websocket.app.state.core
    core_api = CoreAPI(core)
    
    try:
        # Establish WebSocket connection
        await ws_manager.connect(
            websocket=websocket,
            connection_id=connection_id,
            connection_type=ConnectionType.CONSOLE,
            client_info={
                "user_agent": websocket.headers.get("user-agent"),
                "origin": websocket.headers.get("origin")
            }
        )
        
        logger.info("Console WebSocket connection established", connection_id=connection_id)
        
        # Start background task to send mock log messages
        log_task = asyncio.create_task(send_mock_logs(ws_manager, connection_id))
        
        try:
            while True:
                # Receive message from client
                data = await websocket.receive_json()
                
                logger.debug("Received WebSocket message", connection_id=connection_id, data=data)
                
                message_type = data.get("type")
                
                if message_type == "command":
                    # Handle command execution
                    command = data.get("command", "").strip()
                    
                    if not command:
                        await ws_manager.send_to_connection(
                            connection_id,
                            create_console_message("ERROR", "Empty command received")
                        )
                        continue
                    
                    try:
                        # Execute command through core API
                        result = await core_api.send_console_command(command)
                        
                        # Send command echo
                        await ws_manager.send_to_connection(
                            connection_id,
                            create_console_message("COMMAND", f"> {command}")
                        )
                        
                        # Send command result
                        level = "INFO" if result["success"] else "ERROR"
                        await ws_manager.send_to_connection(
                            connection_id,
                            create_console_message(level, result["message"])
                        )
                        
                    except CoreAPIError as e:
                        await ws_manager.send_to_connection(
                            connection_id,
                            create_console_message("ERROR", f"Command failed: {e.message}")
                        )
                    except Exception as e:
                        logger.error("Error executing command", command=command, error=str(e), exc_info=True)
                        await ws_manager.send_to_connection(
                            connection_id,
                            create_console_message("ERROR", f"Internal error: {str(e)}")
                        )
                
                elif message_type == "ping":
                    # Handle ping/pong for connection keepalive
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": data.get("timestamp")
                    })
                
                else:
                    logger.warning("Unknown message type", message_type=message_type, connection_id=connection_id)
                    await ws_manager.send_to_connection(
                        connection_id,
                        create_console_message("WARN", f"Unknown message type: {message_type}")
                    )
        
        except WebSocketDisconnect:
            logger.info("Console WebSocket disconnected", connection_id=connection_id)
        
        finally:
            # Cancel background tasks
            log_task.cancel()
            try:
                await log_task
            except asyncio.CancelledError:
                pass
    
    except Exception as e:
        logger.error("Console WebSocket error", connection_id=connection_id, error=str(e), exc_info=True)
    
    finally:
        # Clean up connection
        await ws_manager.disconnect(connection_id)
        logger.info("Console WebSocket cleanup completed", connection_id=connection_id)


async def send_mock_logs(ws_manager: WebSocketManager, connection_id: str):
    """
    Send mock log messages for development/testing
    
    Args:
        ws_manager: WebSocket manager instance
        connection_id: Target connection ID
    """
    mock_messages = [
        ("INFO", "Server started successfully"),
        ("INFO", "Loading world 'world'..."),
        ("INFO", "World loaded successfully"),
        ("INFO", "Server is ready for connections"),
        ("INFO", "Player TestPlayer1 joined the game"),
        ("WARN", "Can't keep up! Is the server overloaded?"),
        ("INFO", "Player TestPlayer1 left the game"),
        ("INFO", "Saving world data..."),
        ("INFO", "World saved successfully"),
    ]
    
    try:
        for i, (level, message) in enumerate(mock_messages):
            await asyncio.sleep(2)  # Send a message every 2 seconds
            
            await ws_manager.send_to_connection(
                connection_id,
                create_console_message(level, f"[{i+1:02d}] {message}")
            )
            
            # Reset and repeat
            if i == len(mock_messages) - 1:
                i = 0
                await asyncio.sleep(5)  # Longer pause before repeating
    
    except asyncio.CancelledError:
        logger.debug("Mock log sender cancelled", connection_id=connection_id)
    except Exception as e:
        logger.error("Error in mock log sender", connection_id=connection_id, error=str(e))


@router.post("/console/command", response_model=CommandResponse)
async def execute_console_command(
    command_data: ConsoleCommand,
    request: Request
):
    """
    Execute a console command via REST API
    
    Args:
        command_data: Command to execute
        
    Returns:
        Command execution result
    """
    try:
        logger.info("Executing console command via REST", command=command_data.command)
        
        # Get core API from app state
        core = request.app.state.core
        core_api = CoreAPI(core)
        result = await core_api.send_console_command(command_data.command)
        
        return CommandResponse(**result)
    
    except CoreConnectionError:
        raise HTTPException(
            status_code=503,
            detail="Aetherius Core is not available"
        )
    
    except CoreAPIError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Command execution failed: {e.message}"
        )
    
    except Exception as e:
        logger.error("Unexpected error in command execution", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


@router.get("/console/history")
async def get_console_history(
    request: Request,
    limit: int = 100
):
    """
    Get recent console output history
    
    Args:
        limit: Maximum number of log entries to return
        
    Returns:
        List of recent console log entries
    """
    try:
        # TODO: Implement actual log history retrieval from core
        # For now, return mock data
        
        mock_history = [
            {
                "timestamp": "2024-01-15T10:00:00Z",
                "level": "INFO",
                "source": "Server",
                "message": "Server started successfully"
            },
            {
                "timestamp": "2024-01-15T10:00:01Z",
                "level": "INFO",
                "source": "World",
                "message": "Loading world 'world'..."
            },
            {
                "timestamp": "2024-01-15T10:00:02Z",
                "level": "INFO",
                "source": "World",
                "message": "World loaded successfully"
            }
        ]
        
        return {
            "history": mock_history[:limit],
            "total": len(mock_history),
            "limit": limit
        }
    
    except Exception as e:
        logger.error("Error retrieving console history", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve console history"
        )