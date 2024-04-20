import threading 
from contextlib import asynccontextmanager
import os
import random
import asyncio
import dotenv
from fastapi import FastAPI, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import uvicorn
from autogen.io.websockets import IOWebsockets
import autogen
from autogen.cache import Cache
from tempfile import TemporaryDirectory
import traceback
import logging
from websockets.exceptions import ConnectionClosedError


# Load environment variables
dotenv.load_dotenv()

logging.basicConfig(level=logging.DEBUG)

# Generate configuration for the model
config_list = [{
    "cache_seed": random.randint(0, 9999999999999999),
    "temperature": 0,
    "timeout": 120,
    "model": "gpt-4",
    "api_key": os.getenv("OPENAI_API_KEY"),
}]

print(config_list[0]["model"])

# Function that handles WebSocket connections
def on_connect(iostream: IOWebsockets):
    try:
        print(f" - on_connect(): Connected to client using IOWebsockets {iostream}", flush=True)
        print(" - on_connect(): Receiving message from client.", flush=True)

        initial_msg = iostream.input()

        llm_config = {
            "config_list": config_list,
            "stream": True,
        }

        agent = autogen.ConversableAgent(
            name="chatbot",
            system_message="Complete a task given to you and reply TERMINATE when the task is done. If asked about the weather, use tool weather_forecast(city) to get the weather forecast for a city.",
            llm_config=llm_config,
        )

        user_proxy = autogen.UserProxyAgent(
            name="user_proxy",
            system_message="A proxy for the user.",
            is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
            human_input_mode="ALWAYS",
            max_consecutive_auto_reply=10,
            code_execution_config=False,
        )

        @user_proxy.register_for_execution()
        @agent.register_for_llm(description="Weather forecast for a city")
        def weather_forecast(city: str) -> str:
            return f"The weather forecast for {city} is sunny."

        with TemporaryDirectory() as cache_path_root:
            with Cache.disk(cache_path_root=cache_path_root) as cache:
                print(f" - on_connect(): Initiating chat with agent {agent} using message '{initial_msg}'", flush=True)
                user_proxy.initiate_chat(
                    agent,
                    message=initial_msg,
                    cache=cache,
                )
    except ConnectionClosedError as e:
        logging.error(f"WebSocket connection closed unexpectedly: {str(e)}")
    except Exception as e:
        logging.error("Unexpected error in on_connect:", exc_info=True)


# Setup the FastAPI application
app = FastAPI()

# HTML content for the WebSocket chat
html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Autogen websocket test</title>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
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
                ws.send(input.value); // Ensure this sends correctly
                input.value = '';
                event.preventDefault();
            }
        </script>

    </body>
</html>
"""
from fastapi import WebSocket

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            logging.debug(f"Received via WebSocket: {data}")
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect as e:
        logging.warning(f"WebSocket client disconnected: {e.code}")
        logging.debug(e.reason)
    except Exception as e:
        logging.error(f"Unhandled error: {e}")
        logging.debug(traceback.format_exc())



# Async context manager to manage the lifecycle of the WebSocket server
@asynccontextmanager
async def run_websocket_server(app):
    with IOWebsockets.run_server_in_thread(on_connect=on_connect, port=8080) as uri:
        print(f"Websocket server started at {uri}.", flush=True)

        yield

# FastAPI application configuration
app = FastAPI(lifespan=run_websocket_server)

@app.get("/")
async def get():
    return HTMLResponse(html)

# Main function to run the FastAPI server
async def main():
    # Configure and run the FastAPI server
    config = uvicorn.Config(app=app, host="127.0.0.1", port=8000, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())
