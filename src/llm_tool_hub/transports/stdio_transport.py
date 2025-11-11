# src/llm_tool_hub/transports/stdio_transport.py

import asyncio
import json
import logging
import sys
from typing import Any, Dict, Optional

from .base_transport import BaseTransport

logger = logging.getLogger(__name__)


class StdioTransport(BaseTransport):
    """
    Transport implementation using standard input/output streams.
    
    Suitable for:
    - Local command-line tools
    - Integration with VS Code, Claude Desktop
    - Testing and debugging
    
    Message format: JSON objects, one per line (newline-delimited JSON)
    """

    def __init__(self):
        """Initialize the stdio transport."""
        super().__init__()
        self._read_task: Optional[asyncio.Task] = None
        self._write_lock = asyncio.Lock()
        self._message_queue: asyncio.Queue = asyncio.Queue()
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    async def start(self) -> None:
        """
        Start the stdio transport.
        
        Sets up the message reading loop to read from stdin.
        """
        logger.info("Starting StdioTransport")
        self._running = True
        self._loop = asyncio.get_event_loop()
        
        # Start reading from stdin in the background
        self._read_task = asyncio.create_task(self._read_loop())

    async def stop(self) -> None:
        """
        Stop the stdio transport.
        
        Cancels the reading task and flushes stdout.
        """
        logger.info("Stopping StdioTransport")
        self._running = False
        
        if self._read_task and not self._read_task.done():
            self._read_task.cancel()
            try:
                await self._read_task
            except asyncio.CancelledError:
                pass
        
        # Flush stdout to ensure all messages are sent
        sys.stdout.flush()

    async def send(self, message: Dict[str, Any]) -> None:
        """
        Send a message through stdout.
        
        Args:
            message: Dict to send as JSON
        """
        async with self._write_lock:
            try:
                json_str = json.dumps(message)
                print(json_str, file=sys.stdout, flush=True)
                logger.debug(f"Sent: {json_str}")
            except Exception as e:
                logger.error(f"Error sending message: {e}", exc_info=True)
                raise

    async def receive(self) -> Optional[Dict[str, Any]]:
        """
        Receive a message from stdin.
        
        Returns:
            Parsed JSON message dict, or None if queue is empty
        """
        try:
            # Don't block - return immediately if queue is empty
            return self._message_queue.get_nowait()
        except asyncio.QueueEmpty:
            return None

    async def _read_loop(self) -> None:
        """
        Read messages from stdin in a background task.
        
        Reads lines from stdin, parses JSON, and puts them in the message queue.
        """
        loop = asyncio.get_event_loop()
        
        try:
            while self._running:
                try:
                    # Read from stdin asynchronously (non-blocking)
                    # This is the tricky part - we need to read in a thread pool
                    line = await loop.run_in_executor(
                        None,
                        lambda: sys.stdin.readline()
                    )
                    
                    if not line:
                        # EOF reached
                        logger.info("EOF reached on stdin")
                        self._running = False
                        break
                    
                    line = line.rstrip('\n')
                    if not line:
                        # Empty line, skip
                        continue
                    
                    try:
                        message = json.loads(line)
                        await self._message_queue.put(message)
                        logger.debug(f"Received: {line}")
                    except json.JSONDecodeError as e:
                        logger.error(f"Invalid JSON received: {line}, error: {e}")
                        # Send error response
                        error_response = {
                            "jsonrpc": "2.0",
                            "error": {
                                "code": -32700,
                                "message": "Parse error"
                            }
                        }
                        await self.send(error_response)
                        
                except Exception as e:
                    if self._running:
                        logger.error(f"Error in read loop: {e}", exc_info=True)
                        await asyncio.sleep(0.1)  # Brief pause before retry
                    break
                    
        except asyncio.CancelledError:
            logger.debug("Read loop cancelled")
        finally:
            self._running = False
