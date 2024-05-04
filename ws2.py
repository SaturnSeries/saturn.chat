from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import autogen
import json
import os

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins='*')

llm_config={
    "model": 'gpt-4',
    "api_key": os.getenv("OPENAI_API_KEY"),
    "timeout": 600,
    "seed": 42,
    "temperature": 0
}

def handle_response(msg):
        socketio.emit('message', { "text": msg['content'], "isSender": False, "avatarSrc": "/assets/images/legendsAvatars/578.png", "complete": True })



assistant = autogen.AssistantAgent(
    name="CTO",
    llm_config=llm_config,
    system_message="Chief technical officer of a tech company"
)

user_proxy = autogen.UserProxyAgent(
    name="user_proxy",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=1,
    is_termination_msg=lambda x: (handle_response(x) or x.get("content", "").rstrip().endswith("TERMINATE")),
    code_execution_config={"work_dir": "web", "use_docker": False},  # Set Docker to False here
    llm_config=llm_config,
    system_message=""" continue if the task wasn't done and TERMINATE if the task done """
)


@socketio.on('message')
def handle_message(task):
    data_json = json.loads(task)
    print(task)
    text = data_json['text']

    response = user_proxy.initiate_chat(
        assistant,
        message=text
    )



if __name__ == '__main__':
    socketio.run(app, port=8000)
