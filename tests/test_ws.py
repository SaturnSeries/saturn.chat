#!/usr/bin/env python

import asyncio
import websockets
import sys  # Import sys to handle command line arguments

async def test_websocket():
    uri = "ws://localhost:8000/ws"
    message = "move south"  # Default message

    # Check if a command line argument was provided
    if len(sys.argv) > 1:
        message = sys.argv[1]  # Take the first command line argument as the message

    async with websockets.connect(uri) as websocket:
        # Send the message obtained from command line argument or default
        await websocket.send(message)
        print(f"> {message}")

        # Receive and print the response
        response = await websocket.recv()
        print(f"< {response}")

# Run the test
asyncio.run(test_websocket())
