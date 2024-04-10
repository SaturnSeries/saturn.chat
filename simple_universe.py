import logging
import random
from autogen import register_function
from typing import Literal, Union

from autogen import (Agent, ConversableAgent, GroupChat, GroupChatManager,
                     UserProxyAgent, config_list_from_json)

# Set up basic configuration for logging
logging.basicConfig(
    level=logging.CRITICAL, format="%(asctime)s - %(levelname)s - %(message)s"
)


class Cell:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.walls = {"N": True, "S": True, "E": True, "W": True}
        self.visited = False


################
# Maze Generation AND Movement LogiC
################
import random

from maze import Maze

# Assuming the Cell and Maze classes are defined above as you have provided.


class RPG:
    def __init__(self, width=10, height=10):
        self.maze = Maze(width, height)
        self.current_location = self.get_random_start()

    def intro_maze(self):
        """Introduce the maze to the player and show available moves."""
        message = "Welcome to the maze! Try to find your way out."
        message += "\n" + self.get_location_description()  # Includes available moves
        return message

    def get_random_start(self):
        """Get a random starting position within the maze."""
        possible_starts = [
            (x, y) for x in range(self.maze.width) for y in range(self.maze.height)
        ]
        return random.choice(possible_starts)

    def move_player(self, direction):
        """Move the player in the specified direction if possible."""
        x, y = self.current_location
        cell = self.maze.maze_grid[x][y]
        logging.warning(
            f"Attempting to move {direction} from ({x}, {y}) with walls {cell.walls}"
        )

        if direction == "N" and not cell.walls["N"]:
            if y > 0:  # Ensure not at the top boundary
                y -= 1
                moved = True
        elif direction == "S" and not cell.walls["S"]:
            if y < self.maze.height - 1:  # Ensure not at the bottom boundary
                y += 1
                moved = True
        elif direction == "E" and not cell.walls["E"]:
            if x < self.maze.width - 1:  # Ensure not at the right boundary
                x += 1
                moved = True
        elif direction == "W" and not cell.walls["W"]:
            if x > 0:  # Ensure not at the left boundary
                x -= 1
                moved = True
        else:
            moved = False

        if moved:
            self.current_location = (x, y)
            return self.get_location_description()
        else:
            return "You can't move that way."

    def get_location_description(self):
        """Provide a description of the current location and possible paths."""
        x, y = self.current_location
        cell = self.maze.maze_grid[x][y]
        directions = []
        if not cell.walls["N"] and y > 0:
            directions.append("North")
        if not cell.walls["S"] and y < self.maze.height - 1:
            directions.append("South")
        if not cell.walls["E"] and x < self.maze.width - 1:
            directions.append("East")
        if not cell.walls["W"] and x > 0:
            directions.append("West")

        description = f"You are now at location ({x}, {y})."
        if directions:
            description += " Paths available: " + ", ".join(directions) + "."
        else:
            description += " You are trapped with no paths available."
        return description

    def get_current_coordinates(self):
        """Return the coordinates of the player's current location."""
        # This method had been defined twice in your initial submission. Consolidating to one.
        return self.current_location

    def get_current_location_info(self):
        """Alias for get_location_description for clarity in conversational use."""
        return self.get_location_description()

    def display_maze(self):
        maze_representation = ""
        player_x, player_y = self.current_location  # Get player's current coordinates
        for y in range(self.maze.height):
            top_row = ""
            middle_row = ""
            for x in range(self.maze.width):
                cell = self.maze.maze_grid[x][y]
                top_row += "X" if cell.walls["N"] else " "
                top_row += "X"

                middle_row += "X" if cell.walls["W"] else " "
                # Mark player's location with 'O'
                if (x, y) == (player_x, player_y):
                    middle_row += "O"
                else:
                    middle_row += " "
            middle_row += "X"

            maze_representation += top_row + "\n" + middle_row + "\n"

        bottom_row = ""
        for x in range(self.maze.width):
            bottom_row += "XX"
        maze_representation += bottom_row

        return maze_representation


from typing import Callable, get_type_hints


def annotate_self(func: Callable) -> Callable:
    """
    A decorator to explicitly annotate the `self` parameter of a class method
    with its own class type. This is a workaround for frameworks that require
    all parameters, including `self`, to be annotated.
    """
    # Assuming the first parameter of a method is always named 'self',
    # and its type should be the class itself.
    # This uses get_type_hints to infer the type of 'self' dynamically.
    if "self" in func.__code__.co_varnames:
        func.__annotations__["self"] = get_type_hints(func).get("return", object)
    return func


from typing import Tuple


class MazeExplorer:
    """Creates maze and places you in a start position"""
    def __init__(self, width: int, height: int):
        self.maze = Maze(width, height)
        self.current_location = self.get_random_start()

    def get_random_start(self) -> Tuple[int, int]:
        possible_starts = [
            (x, y) for x in range(self.maze.width) for y in range(self.maze.height)
        ]
        return random.choice(possible_starts)

    @annotate_self
    def move_player(self, direction):
        """Move the player in the specified direction if possible."""
        x, y = self.current_location
        current_cell = self.maze.maze_grid[x][y]

        next_x, next_y = x, y  # Initialize next position as the current position
        if direction == "north" and not current_cell.walls["N"]:
            next_y -= 1
        elif direction == "south" and not current_cell.walls["S"]:
            next_y += 1
        elif direction == "east" and not current_cell.walls["E"]:
            next_x += 1
        elif direction == "west" and not current_cell.walls["W"]:
            next_x -= 1
        else:
            return "You can't move that way."

        # Check if the next position is within the maze bounds
        if 0 <= next_x < self.maze.width and 0 <= next_y < self.maze.height:
            self.current_location = (next_x, next_y)
            return self.get_location_description()
        else:
            return "You can't move that way."

    @annotate_self
    def get_current_position(self) -> str:
        return f"Current position: {self.current_location}."


gpt4_config = {
    "cache_seed": random.randint(0, 9999999999999999),
    "temperature": 0,
    "config_list": config_list_from_json("llm_config.json"),
    "timeout": 120,
}

class SaturnBot(ConversableAgent):
    def __init__(self, name, llm_config, system_message, rpg_instance):
        super().__init__(
            name=name, llm_config=llm_config, system_message=system_message
        )
        self.rpg_instance = rpg_instance
        logging.warn("MazeNavigator initialized with RPG instance.")

    def on_tool_invocation(self, tool_name, *args, **kwargs):
        if tool_name == "move_player":
            direction = kwargs.get("direction")
            return self.rpg_instance.move_player(direction)
        elif tool_name == "get_current_position":
            return self.rpg_instance.get_current_location_info()
        elif tool_name == "display_maze":
            return self.rpg_instance.display_maze()
        else:
            return "Unknown tool invocation."
        
class Legend(ConversableAgent):
    def __init__(self, name, llm_config, system_message):
        super().__init__(
          name=name, llm_config=llm_config, system_message=system_message
        )



class SaturnChatApp:
    def __init__(self, work_dir="./maze"):
        self.rpg = RPG(10, 10)  # Instantiate the RPG game

        # Agent 1
        self.saturnbot = SaturnBot(
            name="Saturn Bot",
            llm_config=gpt4_config,
            system_message="""You are Saturn Bot, you guide the player across a maze and they need to find the exit. 
            You have the possibility to move around, display the map and tell stories about Saturn.
            """,
            rpg_instance=self.rpg,  # Pass RPG instance
        )

        # Agent 2
        self.explorer = UserProxyAgent(
            name="Explorer",
            system_message="Exploring the maze, executing commands for movement.",
            code_execution_config={"work_dir": work_dir},
        )
        self.legend = Legend(name="Oberon", llm_config=gpt4_config,
            system_message="""You are a legend with solar sign Sagittarius and lunar sign Lion.
            You are in a maze trying to escape, you need to find a way out with the help of an explorer.
            """,)
        self.register_tools()  # New method for registering tools
        self.setup_group_chat()

    def register_tools(self):
        def move_player_wrapper(direction: str) -> str:
            """Wrapper function for moving the player in the RPG maze. Move the player 1 block toward a specific direction, and returns the location of the new block"""
            return self.rpg.move_player(direction)

        def get_current_position_wrapper() -> str:
            position = self.rpg.get_current_coordinates()
            return f"Current position: {position}."

        def display_maze_wrapper() -> str:
            return self.rpg.display_maze()

        register_function(
            move_player_wrapper,
            caller=self.saturnbot,
            executor=self.explorer,
            name="move_player",
            description="Moves the player in the specified direction within the maze.",
        )

        register_function(
            get_current_position_wrapper,
            caller=self.saturnbot,
            executor=self.explorer,
            name="get_current_position",
            description="Returns the current position of the player.",
        )

        register_function(
            display_maze_wrapper,
            caller=self.saturnbot,
            executor=self.explorer,
            name="display_maze",
            description="Displays the current state of the maze.",
        )

    def setup_group_chat(self):
        # Assuming GroupChat and GroupChatManager are configured to use the agents
        self.group_chat = GroupChat(
            [self.saturnbot, self.explorer, self.legend], [], self.custom_speaker_selection_func
        )
        self.group_chat_manager = GroupChatManager(self.group_chat, gpt4_config)

    def custom_speaker_selection_func(
        self, last_speaker: Agent, groupchat: GroupChat
    ) -> Union[Agent, Literal["auto", "manual", "random", "round_robin"], None]:
        """Define a customized speaker selection function."""
        if last_speaker == self.saturnbot:
            return self.explorer
        elif last_speaker == self.explorer:
            return self.legend
        return None

    def initiate_chat(self, message):
        # Send RPG intro message as the first conversation piece
        self.saturnbot.send(self.rpg.intro_maze(), self.explorer)
        self.explorer.initiate_chat(self.saturnbot, message=message)


# Example usage:
maze_app = SaturnChatApp()
maze_app.initiate_chat("Hello! Who am I talking to right now?")
