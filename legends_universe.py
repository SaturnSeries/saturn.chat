import logging
import random
from typing import Dict, Literal, Union

from autogen import (Agent, ConversableAgent, GroupChat, GroupChatManager,
                     UserProxyAgent, config_list_from_json, register_function)

# Setup logging
logging.basicConfig(
    level=logging.CRITICAL, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Define the Cell and Maze classes
class Cell:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.walls = {"N": True, "S": True, "E": True, "W": True}
        self.visited = False

class Maze:
    def __init__(self, width: int, height: int):
        self.width, self.height = width, height
        self.maze_grid = [[Cell(x, y) for y in range(height)] for x in range(width)]

# Define the RPG class for maze navigation
class RPG:
    def __init__(self, width=10, height=10):
        self.maze = Maze(width, height)
        self.current_location = self.get_random_start()

    def intro_maze(self):
        message = "Welcome to the maze! Try to find your way out."
        return message + "\n" + self.get_location_description()

    def get_random_start(self):
        return random.choice(
            [(x, y) for x in range(self.maze.width) for y in range(self.maze.height)]
        )

    def move_player(self, direction: str):
        x, y = self.current_location
        cell = self.maze.maze_grid[x][y]
        dx, dy = {"N": (0, -1), "S": (0, 1), "E": (1, 0), "W": (-1, 0)}.get(
            direction, (0, 0)
        )
        nx, ny = x + dx, y + dy
        if (
            0 <= nx < self.maze.width
            and 0 <= ny < self.maze.height
            and not cell.walls[direction]
        ):
            self.current_location = nx, ny
            return self.get_location_description()
        return "You can't move that way."

    def get_location_description(self):
        x, y = self.current_location
        cell = self.maze.maze_grid[x][y]
        directions = [dir for dir, open in cell.walls.items() if not open]
        return (
            f"You are now at location ({x}, {y}). Paths available: "
            + ", ".join(directions)
            + "."
        )

    def display_maze(self):
        representation = ""
        for y in range(self.maze.height):
            for x in range(self.maze.width):
                cell = self.maze.maze_grid[x][y]
                representation += f"{'O' if (x, y) == self.current_location else ' '} "
            representation += "\n"
        return representation

# Configuration for agents
gpt4_config = {
    "cache_seed": random.randint(0, 9999999999999999),
    "temperature": 0,
    "config_list": config_list_from_json("llm_config.json"),
    "timeout": 120,
}

# Define the MazeNavigator class
class MazeNavigator(ConversableAgent):
    def __init__(
        self, name: str, llm_config: Dict, system_message: str, rpg_instance: RPG
    ):
        super().__init__(
            name=name, llm_config=llm_config, system_message=system_message
        )
        self.rpg_instance = rpg_instance

    def on_tool_invocation(self, tool_name: str, *args, **kwargs) -> str:
        if tool_name == "move_player":
            return self.rpg_instance.move_player(kwargs.get("direction", ""))
        if tool_name == "display_maze":
            return self.rpg_instance.display_maze()
        return "Unknown tool invocation."

# Define the MazeApp class
class MazeApp:
    def __init__(self, work_dir: str = "./maze"):
        self.rpg = RPG(10, 10)
        self.agents = [
            self.create_navigator(),
            UserProxyAgent("Explorer", "Exploring the maze.", {"work_dir": work_dir}),
        ]
        self.setup_group_chat()
        self.register_tools()

    def create_navigator(self) -> MazeNavigator:
        navigator = MazeNavigator(
            "Navigator", gpt4_config, "Navigating the maze.", self.rpg
        )
        navigator._is_termination_msg = self.custom_termination_check
        return navigator

    @staticmethod
    def custom_termination_check(message: Dict) -> bool:
        return False

    def setup_group_chat(self):
        self.group_chat = GroupChat(self.agents, [], self.custom_speaker_selection_func)
        self.group_chat_manager = GroupChatManager(self.group_chat, gpt4_config)

    def custom_speaker_selection_func(
        self, last_speaker: Agent, groupchat: GroupChat
    ) -> Union[Agent, Literal["auto", "manual", "random", "round_robin"], None]:
        return self.agents[1] if last_speaker == self.agents[0] else self.agents[0]

    def register_tools(self):
        def move_player_wrapper(direction: str) -> str:
            return self.rpg.move_player(direction)

        def get_current_position_wrapper() -> str:
            return f"Current position: {self.rpg.get_current_coordinates()}."

        def display_maze_wrapper() -> str:
            return self.rpg.display_maze()

        register_function(
            move_player_wrapper,
            caller=self.agents[0],
            executor=self.agents[1],
            name="move_player",
            description="Moves the player in the specified direction within the maze.",
        )
        register_function(
            get_current_position_wrapper,
            caller=self.agents[0],
            executor=self.agents[1],
            name="get_current_position",
            description="Returns the current position of the player.",
        )
        register_function(
            display_maze_wrapper,
            caller=self.agents[0],
            executor=self.agents[1],
            name="display_maze",
            description="Displays the current state of the maze.",
        )

    def initiate_chat(self, message: str):
        self.agents[0].send(self.rpg.intro_maze(), self.agents[1])
        self.agents[1].initiate_chat(self.agents[0], message=message)

# Main entry point of the application
if __name__ == "__main__":
    maze_app = MazeApp()
    maze_app.initiate_chat("move N")
