# src/llm_tool_hub/transports/base_transport.py

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class BaseTransport(ABC):
    """
    Abstract base class for MCP transport implementations.
    
    Defines the interface for different transport mechanisms (stdio, SSE, WebSocket, etc.)
    """

    def __init__(self):
        """Initialize the transport."""
        self._running = False

    @abstractmethod
    async def start(self) -> None:
        """
        Start the transport.
        
        Should initialize connections and prepare to send/receive messages.
        """
        pass

    @abstractmethod
    async def stop(self) -> None:
        """
        Stop the transport.
        
        Should gracefully shutdown and cleanup resources.
        """
        pass

    @abstractmethod
    async def send(self, message: Dict[str, Any]) -> None:
        """
        Send a message through the transport.
        
        Args:
            message: The message to send (will be JSON serialized)
        """
        pass

    @abstractmethod
    async def receive(self) -> Optional[Dict[str, Any]]:
        """
        Receive a message from the transport.
        
        Returns:
            The received message as a dict, or None if no message available
        """
        pass

    @property
    def is_running(self) -> bool:
        """Check if the transport is running."""
        return self._running

    async def run_message_loop(self, handler) -> None:
        """
        Run the message receive/process loop.
        
        Args:
            handler: Async function to handle received messages
                    Should accept a message dict and return a response dict
        """
        self._running = True
        try:
            while self._running:
                try:
                    # Receive message with timeout to allow checking _running flag
                    message = await asyncio.wait_for(
                        self.receive(),
                        timeout=0.5
                    )
                    
                    if message is None:
                        continue
                    
                    # Handle the message
                    response = await handler(message)
                    
                    # Send response if handler returned one
                    if response is not None:
                        await self.send(response)
                        
                except asyncio.TimeoutError:
                    # Timeout is normal - just loop again to check _running flag
                    continue
                except Exception as e:
                    logger.error(f"Error in message loop: {e}", exc_info=True)
                    
        finally:
            self._running = False
            await self.stop()
