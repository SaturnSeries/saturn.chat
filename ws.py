import os
import asyncio
import logging
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
import uvicorn
from contextlib import asynccontextmanager
from typing import AsyncIterator

import autogen
from autogen.io.websockets import IOWebsockets
from simple_universe import SaturnChatApp  # Ensure correct import
import dotenv

dotenv.load_dotenv()

PORT = 8000
logger = logging.getLogger("uvicorn")

app = FastAPI()

# Assuming the SaturnChatApp is correctly imported and configured
game_app = SaturnChatApp()

# Function to get configuration list for agents
def _get_config_list():
    config_list = [
        {
            "model": "gpt-35-turbo-16k",
            "api_key": os.getenv("OPENAI_API_KEY"),
            "base_url": "https://api.openai.com/",
            "api_type": "openai",
            "api_version": "v1",
        }
    ]
    return [config for config in config_list if config["api_key"]]

# Define on_connect to be used with IOWebsockets
async def on_connect(iostream: IOWebsockets):
    logger.info("Connected to client using IOWebsockets.")
    try:
        while True:
            initial_msg = await iostream.receive_text()
            logger.info(f"Receiving message from client: {initial_msg}")
            response = game_app.process_input(initial_msg)
            await iostream.send_text(response)
            logger.info("Message processed successfully.")
    except Exception as e:
        logger.error(f"Error during WebSocket communication: {e}")

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Autogen websocket test</title>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off" value="Enter your command..."/>
            <button>Send</button>
        </form>
        <ul id='messages'></ul>
        <script>
            var ws = new WebSocket("ws://localhost:8080/ws");
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages');
                var message = document.createElement('li');
                var content = document.createTextNode(event.data);
                message.appendChild(content);
                messages.appendChild(message);
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText");
                ws.send(input.value);
                input.value = '';
                event.preventDefault();
            }
        </script>
    </body>
</html>
"""

@app.get("/")
async def get() -> HTMLResponse:
    return HTMLResponse(html)

@asynccontextmanager
async def run_websocket_server(app: FastAPI) -> AsyncIterator[None]:
    with IOWebsockets.run_server_in_thread(on_connect=on_connect, port=8080) as uri:
        logger.info(f"Websocket server started at {uri}.")
        yield

app = FastAPI(lifespan=run_websocket_server)

async def start_uvicorn():
    config = uvicorn.Config(app, host="0.0.0.0", port=PORT, log_level="info")
    server = uvicorn.Server(config)
    try:
        await server.serve()
    except KeyboardInterrupt:
        logger.info("Shutting down server")

if __name__ == "__main__":
    logger.setLevel(logging.INFO)
    asyncio.run(start_uvicorn())
