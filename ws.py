#!/usr/bin/env python

import asyncio
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

import uvicorn

from simple_universe import SaturnChatApp  # Ensure your import path is correct

logger = logging.getLogger("uvicorn")
PORT = 8000

app = FastAPI()

# HTML for the WebSocket client
html = """
<!DOCTYPE html>
<html>
<head>
    <title>Saturn Series WebSocket Chat</title>
</head>
<body>
    <h1>WebSocket Interaction with Saturn Series Game</h1>
    <form action="" onsubmit="sendMessage(event)">
        <input type="text" id="messageText" autocomplete="off" placeholder="Enter command..."/>
        <button>Send</button>
    </form>
    <ul id='messages'>
    </ul>
    <script>
        var ws = new WebSocket("ws://localhost:8000/ws");
        ws.onmessage = function(event) {
            var messages = document.getElementById('messages')
            var message = document.createElement('li')
            var content = document.createTextNode(event.data)
            message.appendChild(content)
            messages.appendChild(message)
        };
        function sendMessage(event) {
            var input = document.getElementById("messageText")
            ws.send(input.value)
            input.value = ''
            event.preventDefault()
        }
    </script>
</body>
</html>
"""

@app.get("/")
async def get() -> HTMLResponse:
    return HTMLResponse(html)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    print("WebSocket connection attempted")
    await websocket.accept()
    print("WebSocket connection accepted")
    game = SaturnChatApp()  # Instantiate your game application

    try:
        while True:
            data = await websocket.receive_text()
            response = game.process_input(data)  # Process input through the new method
            await websocket.send_text(response)
    except WebSocketDisconnect:
        print("Client disconnected")

@app.get("/maze")
async def display_maze():
    game = SaturnChatApp()  # Instantiate your game application or get it from session
    maze_state = game.rpg_maze.display_maze()
    return {"maze": maze_state}

if __name__ == "__main__":
    logger.setLevel("INFO")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
