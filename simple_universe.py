import logging
import random
from autogen import register_function
from typing import Literal, Union, Callable, get_type_hints, Tuple
import requests
import json
import config

# Custom imports
from autogen import (Agent, ConversableAgent, GroupChat, GroupChatManager,
                     UserProxyAgent, config_list_from_json)

from maze import Maze


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

######################################
# Maze Generation and Movement Logic #
######################################

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


class MazeExplorer:
    """
    This class creates a maze and places you in a start position
    to navigate through the maze. It provides methods to move in
    different directions and get the current position of the player.
    """
    def __init__(self, width: int, height: int):
        self.maze = self.generate_maze(width, height)
        self.current_location = self.get_random_start()

    def intro_maze(self):
        """Introduce the maze to the player and show available moves."""
        message = "Welcome to the maze! Try to find your way out."
        message += "\n" + self.get_location_description()  # Includes available moves
        return message
    
    def generate_maze(self, width: int, height: int) -> 'Maze':
        return Maze(width, height)

    def get_random_start(self) -> Tuple[int, int]:
        possible_starts = [
            (x, y) for x in range(self.maze.width) for y in range(self.maze.height)
        ]
        return random.choice(possible_starts)


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
    
    @annotate_self
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

######################################
# Custom ConversableAgent Subclasses #
######################################

gpt4_config = {
    "cache_seed": random.randint(0, 9999999999999999),
    "temperature": 0,
    "config_list": config_list_from_json("llm_config.json"),
    "timeout": 120,
}

class SaturnBot(ConversableAgent):
    def __init__(self, name, llm_config, system_message, rpg_maze_instance: MazeExplorer):
        super().__init__(
            name=name, llm_config=llm_config, system_message=system_message
        )
        self.rpg_instance = rpg_maze_instance
        logging.warning("SaturnBot initialized with RPG instance.")

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
        self.rpg_maze = MazeExplorer(10, 10)  # Instantiate the RPG game

        # Agent 1
        self.saturnbot = SaturnBot(
            name="SaturnBot",
            llm_config=gpt4_config,
            system_message="""You are Saturn Bot, you guide the player across a maze and they need to find the exit. 
            You have the possibility to move around, display the map and tell stories about Saturn.
            """,
            rpg_maze_instance=self.rpg_maze,  # Pass RPG instance
        )

        # Agent 2, User proxy agent for the explorer
        self.explorer = UserProxyAgent(
            name="Explorer",
            system_message="Exploring the maze, executing commands for movement.",
            code_execution_config={"work_dir": work_dir},
        )

        # Agent 3-6: Legend Characters
        self.legends = []  # List to store multiple Legend agents
        for i in range(1,4):
            traits = self.get_legend_metadata(i)
            legend = Legend(
                name=f"Legend_{i}",  # Give a unique name
                llm_config=gpt4_config,
                system_message=f"I am Legend_{i}. I'm in a maze trying to escape. Treasures await in this maze, if we're able to find them. I'll be talking with an explorer, let's explore and get out! \n\n These are my traits: \n\n {traits}"
            )
            self.legends.append(legend)  # Append to the list
            
        self.register_tools() 
        self.setup_group_chat()

    def get_legend_metadata(self, id: int):
        url = f"https://api.opensea.io/api/v2/chain/ethereum/contract/0xD45b8768C9d5Cb57a130fa63fEab85Ba9f52Cc22/nfts/{id}"
        headers = {
            "accept": "application/json",
            "x-api-key": config.opensea_api_key,
        }
        response = requests.get(url, headers=headers)
        data = response.text
        data = json.loads(data)
        # print(data)
        traits = data['nft']['traits']
        trait_text = "\n".join([f"{trait['trait_type']}: {trait['value']}" for trait in traits])
        return trait_text
    
    def register_tools(self):
        def move_player_wrapper(direction: str) -> str:
            """Wrapper function for moving the player in the RPG maze. Move the player 1 block toward a specific direction, and returns the location of the new block"""
            return self.rpg_maze.move_player(direction)
        
        def get_current_position_wrapper() -> str:
            position = self.rpg_maze.get_current_position() 
            return position


        def display_maze_wrapper() -> str:
            return self.rpg_maze.display_maze()


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
        # All agents are added to the group chat, ensuring they can send and receive messages
        self.group_chat = GroupChat(
            [self.saturnbot, self.explorer] + self.legends,  # Include all relevant agents here
            [],                                            # Message history is empty to start
            speaker_selection_method='auto'            # Here we pass the custom speaker selection function
        )
        self.group_chat_manager = GroupChatManager(groupchat=self.group_chat, llm_config=gpt4_config)

    def custom_speaker_selection_func(
        self, last_speaker: Agent, groupchat: GroupChat
    ) -> Union[Agent, Literal["auto", "manual", "random", "round_robin"], None]:
        # Custom logic to select who speaks next based on the last speaker and the conversation turn
        if last_speaker == self.explorer:
            return self.saturnbot
        elif last_speaker == self.legend:
            return self.explorer  
        elif last_speaker == self.saturnbot:
            return self.legend  
        return None  # Fallback case

    def initiate_chat(self, message):
        # Send RPG intro messages as the first conversation piece
        # self.legend.send(
        #                 "Hi, I'm Oberon, a Legend in the Saturn Series Universe. Ready to explore?",
        #                 self.saturnbot,
        #                 request_reply=False)
        self.saturnbot.send(
                        self.rpg_maze.intro_maze(), 
                        self.explorer, 
                        request_reply=False)
        
        self.explorer.initiate_chat(
                        self.group_chat_manager, 
                        message=message)


# Run the chat application
maze_app = SaturnChatApp()
# maze_app.initiate_chat("Hello! Who am I talking to right now? Who is present in this conversation so far?")
maze_app.initiate_chat("hello tell me more about you and your traits")
