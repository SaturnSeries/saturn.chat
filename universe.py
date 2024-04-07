import random
import re
import sys
from io import StringIO
import contextlib

from autogen import (
    AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager,
    config_list_from_json
)

from autogen.coding import LocalCommandLineCodeExecutor

# Configuration for GPT-4, assuming autogen provides the necessary configuration structure
gpt4_config = {
    "cache_seed": random.randint(0, 9999999999999999),
    "temperature": 0,
    "config_list": config_list_from_json("llm_config.json"),
    "timeout": 120,
}


class RPGAgent(AssistantAgent):
    def __init__(self, name, llm_config, system_message, rpg_instance):
        super().__init__(name=name, llm_config=llm_config, system_message=system_message)
        self.rpg = rpg_instance

    def response_fn(self, message, chat_history):
        current_coordinates = self.rpg.get_current_coordinates()
        location_description = self.rpg.get_location_description()
        location_info = f"Your current coordinates are: {current_coordinates}\n{location_description}"
        return location_info

class ContextInserterAgent(AssistantAgent):
    def __init__(self, name, llm_config, system_message, rpg_instance):
        super().__init__(name=name, llm_config=llm_config, system_message=system_message)
        self.rpg = rpg_instance  # Store a reference to the RPG instance
        
    def insert_contextual_message(self, groupchat):
        """Generate and insert a contextual message based on the RPG state."""
        current_coordinates = self.rpg.get_current_coordinates()  # Retrieve current coordinates
        location_description = self.rpg.get_location_description()  # Get the detailed location description
        
        # Construct the message based on RPG state
        message = f"Your current coordinates are: {current_coordinates}\n{location_description}"
        self.append_message_to_conversation(message, groupchat)

        
    def append_message_to_conversation(self, message, groupchat, speaker_name="system"):
        """Appends a new message to the conversation with a specified speaker."""
        new_message = {"content": message, "role": speaker_name}
        groupchat.messages.append(new_message)



class SimplifiedUniverse:
    """
    Simplified Universe class for managing an RPG game within a conversational interface.
    """

    def __init__(self, work_dir="./universe"):
        """Initialize the universe with an RPG game and set up agents for interaction."""
        self.rpg = RPG(10, 10)
        self.guide = AssistantAgent(
            name="Guide",
            llm_config=gpt4_config,
            system_message="Guiding through the maze with dynamic location updates."
        )
        self.user_proxy = UserProxyAgent(
            name="Explorer",
            system_message="Exploring the maze, executing commands for movement."
        )
        self.context_inserter = ContextInserterAgent(
            name="ContextInserter",
            llm_config=gpt4_config,
            system_message="Provides RPG context.",
            rpg_instance=self.rpg
        )
        self.executor = LocalCommandLineCodeExecutor(
            work_dir=work_dir
        )

        self.rpg_agent = RPGAgent(
            name="RPGAgent",
            llm_config=gpt4_config,
            system_message="Providing location information in the maze.",
            rpg_instance=self.rpg
        )

        self.phase = "planning"

        # Setting up the group chat with all the agents including the Context Inserter
        self.setup_group_chat(gpt4_config)


    def execute_python_codeblock(self, text):
        """Execute a Python code block, capturing and printing output and errors."""
        code_blocks = re.findall(r"```python([\s\S]*?)```", text)
        for code in code_blocks:
            code = code.strip()
            with contextlib.redirect_stdout(StringIO()) as new_stdout, contextlib.redirect_stderr(StringIO()) as new_stderr:
                try:
                    exec(code)
                    output = new_stdout.getvalue()
                    error = new_stderr.getvalue()
                except Exception as e:
                    error = str(e)

                if output:
                    print("Output:", output)
                if error:
                    print("Error:", error)

    def custom_speaker_selection(self, last_speaker, groupchat):
        """
        Custom logic for selecting the speaker based on the message content,
        handling commands, managing conversation phases, and integrating the RPG functions.
        """
        messages = groupchat.messages
        last_message = messages[-1]["content"].strip().lower() if messages else ""

        print(f"DEBUG: Last command: '{last_message}'")

        # Call RPG functions based on specific commands
        if "where am i" in last_message:
            return self.rpg_agent
        elif last_speaker == self.context_inserter:
            # Continue the conversation with the Guide after Context Inserter
            return self.guide
        else:
            # Default speaker selection logic
            return self.user_proxy if last_speaker == self.guide else self.guide



    def _process_commands(self, command, groupchat):
        """Process specific commands including greetings and movements."""
        if command == "hello":
            # Fetch and communicate the current location and paths dynamically
            response = "Hello! " + self.rpg.get_location_description()
            print(f"DEBUG: Responding with dynamic location: '{response}'")
            self.append_message_to_conversation(response, groupchat)
        elif command.startswith("move "):
            direction = command.split(" ")[1]
            if direction in ["north", "south", "east", "west"]:
                response = self.rpg.move_player(direction)
                print(f"DEBUG: Moving {direction}, response: '{response}'")
                self.append_message_to_conversation(response, groupchat)
            else:
                response = "Please specify a valid direction: north, south, east, or west."
                print(f"DEBUG: Invalid direction provided. Responding with: '{response}'")
                self.append_message_to_conversation(response, groupchat)
        if "need help" in command:
            # This is a simplistic trigger example
            help_message = "Remember, you can always ask for hints if you're stuck."
            self.append_message_to_conversation(help_message, groupchat, "ContextInserter")



    def _manage_phases(self, command, last_speaker, groupchat):
        """Manage conversation phases based on commands."""
        if "up next" in command:
            self.phase = "planning"
            print(f"DEBUG: Phase reset to 'planning' due to 'Up Next' command.")
        elif "approve" in command and self.phase in ["planning", "review"]:
            self.phase = "approved"
            print(f"DEBUG: Phase set to 'approved' due to 'Approve' command.")
        if self.phase == "approved" and last_speaker is self.guide:
            self.phase = "executing"
            print(f"DEBUG: Executing code block. Phase set to 'executing'.")
            self.execute_python_codeblock(groupchat.messages[-1]["content"])
            self.phase = "review"
            print(f"DEBUG: Code block executed. Phase set to 'review'.")

    def append_message_to_conversation(self, message, groupchat, speaker_name="system"):
        """Appends a new message to the conversation with a specified speaker."""
        if speaker_name != "RPGAgent":
            current_coordinates = self.rpg.get_current_coordinates()
            location_description = self.rpg.get_location_description()
            location_info = f"Your current coordinates are: {current_coordinates}\n{location_description}"
            new_message = {"content": location_info, "role": "system"}
            groupchat.messages.append(new_message)

        new_message = {"content": message, "role": speaker_name}
        groupchat.messages.append(new_message)
        print(f"DEBUG: Appended new message from '{speaker_name}': '{message}'")

    def setup_group_chat(self, llm_config):
        """Sets up the group chat with all agents, including the Context Inserter."""

        self.groupchat = GroupChat(
            agents=[self.guide, self.user_proxy, self.context_inserter, self.rpg_agent],
            messages=[],
            max_round=1000,
            speaker_selection_method=self.custom_speaker_selection,
        )
        self.manager = GroupChatManager(groupchat=self.groupchat, llm_config=llm_config)



    def initiate_chat(self, message):
        """Initiate the chat with a starting message."""
        first_speaker = self.custom_speaker_selection(None, self.groupchat)
        if isinstance(first_speaker, UserProxyAgent):
            self.user_proxy.send(message, first_speaker, request_reply=True)
        else:
            self.user_proxy.initiate_chat(self.manager, message=message)

import random
from maze import Maze

class RPG:

    def __init__(self, width=10, height=10):
        self.maze = Maze(width, height)
        start_x, start_y = self.get_random_start()
        self.current_location = self.maze.maze_grid[start_x][start_y]  # Ensures current_location is a Cell instance
        print(self.intro_maze())

    def intro_maze(self):
        # Introduce the maze to the user
        message = "Welcome to the maze! Try to find your way out."
        message += "\n" + self.get_location_description()
        return message


    def get_random_start(self):
        """Choose a random starting location from the maze."""
        possible_starts = self.maze.get_all_locations()
        return random.choice(possible_starts)


    def move_player(self, direction):
        current_cell = self.maze.maze_grid[self.current_location.x][self.current_location.y]
        print(f"Current location before moving: ({self.current_location.x}, {self.current_location.y}) - Moving {direction}")

        # Check direction and if movement is possible, adjust coordinates accordingly
        if direction == "north" and not current_cell.walls['N']:
            self.current_location.y -= 1
        elif direction == "south" and not current_cell.walls['S']:
            self.current_location.y += 1
        elif direction == "east" and not current_cell.walls['E']:
            self.current_location.x += 1
        elif direction == "west" and not current_cell.walls['W']:
            self.current_location.x -= 1
        else:
            return "You can't move that way."

        print(f"New location after moving: ({self.current_location.x}, {self.current_location.y})")
        # Generate and return a detailed description of the new location
        return self.get_location_description()

    def get_location_description(self):
        cell = self.maze.maze_grid[self.current_location.x][self.current_location.y]
        description = f"You are now at location ({self.current_location.x}, {self.current_location.y})."
        
        # Generate a list of possible directions based on the current cell's walls
        directions = []
        if not cell.walls['N']: directions.append('North')
        if not cell.walls['S']: directions.append('South')
        if not cell.walls['E']: directions.append('East')
        if not cell.walls['W']: directions.append('West')
        
        if directions:
            description += " Paths available: " + ", ".join(directions) + "."
        else:
            description += " There are no paths available from here."

        return description


    def get_current_coordinates(self):
        """Return the coordinates of the player's current location."""
        return self.current_location.x, self.current_location.y


    def get_current_location_info(self):
        """Provide information about the current location and available paths."""
        return self.get_location_description()
    

