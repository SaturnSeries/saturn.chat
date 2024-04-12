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

from maze import Maze, Item, Cell


# Set up basic configuration for logging
logging.basicConfig(
    level=logging.CRITICAL, format="%(asctime)s - %(levelname)s - %(message)s"
)


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
    def __init__(self, width: int, height: int):
        # Directly use the Maze class for creating the maze
        self.maze = Maze(width, height)
        self.current_location = self.maze.start_point  # instead of self.get_random_start()

    def intro_maze(self):
        """Introduce the maze to the player and show available moves."""
        return "Welcome to the maze! Try to find your way out.\n" + self.get_location_description()

    def get_current_position(self):
        return self.get_location_description()
    
    # def get_random_start(self):
    #     # Use the Maze class method if available or define it here if not
    #     return random.choice(self.maze.get_all_locations())

    def get_location_description(self):
        """Provide a description of the current location, possible paths, and any items present."""
        x, y = self.current_location
        cell = self.maze.maze_grid[x][y]
        directions = []
        item_description = ""

        # Check for available directions
        if not cell.walls["N"] and y > 0: directions.append("North")
        if not cell.walls["S"] and y < self.maze.height - 1: directions.append("South")
        if not cell.walls["E"] and x < self.maze.width - 1: directions.append("East")
        if not cell.walls["W"] and x > 0: directions.append("West")

        paths = "Paths available: " + ", ".join(directions) if directions else "You are trapped with no paths available."

        # Check for an item in the current cell and create a description if present
        if cell.item:
            item_description = f"You see an item here: {cell.item.name} - {cell.item.description}"
        else:
            item_description = "There is nothing of interest here, lets go somewhere else."
        # Combine descriptions of paths and items
        location_description = f"You are now at location ({x}, {y}). {paths}"
        if item_description:
            location_description += "\n" + item_description

        return location_description


    @annotate_self
    def move_player(self, direction: str):
        """Move the player in the specified direction if possible, handling synonyms like 'up' for 'north', etc."""
        x, y = self.current_location
        current_cell = self.maze.maze_grid[x][y]

        # Extended direction map to include synonyms
        direction_map = {
            "north": (0, -1), "n": (0, -1), "up": (0, -1), "u": (0, -1),
            "south": (0, 1), "s": (0, 1), "down": (0, 1), "d": (0, 1),
            "east": (1, 0), "e": (1, 0), "right": (1, 0), "r": (1, 0),
            "west": (-1, 0), "w": (-1, 0), "left": (-1, 0), "l": (-1, 0)
        }

        direction = direction.lower()
        if direction in direction_map:
            dx, dy = direction_map[direction]
            nx, ny = x + dx, y + dy

            if 0 <= nx < self.maze.width and 0 <= ny < self.maze.height:
                next_cell = self.maze.maze_grid[nx][ny]
                wall_key = {'n': 'N', 's': 'S', 'e': 'E', 'w': 'W',
                            'u': 'N', 'd': 'S', 'r': 'E', 'l': 'W'}.get(direction[0])
                if wall_key and not next_cell.walls[wall_key]:
                    self.current_location = (nx, ny)
                    return self.get_location_description()
            return "You can't move that way."
        else:
            return "Invalid direction. Use 'north', 'south', 'east', 'west', or their abbreviations and synonyms like 'up' for north."

    @annotate_self
    def display_maze(self):
        """Utilize the Maze display function or define here if needed."""
        return self.maze.display_maze(self.current_location)
    
    @annotate_self
    def inspect_item(self):
        x, y = self.current_location
        cell: Cell = self.maze.maze_grid[x][y]
        if cell.item:
            return cell.item.inspect_item()
        else:
            return "There is no item here to inspect."
        
    @annotate_self
    def use_item(self):
        x, y = self.current_location
        cell: Cell = self.maze.maze_grid[x][y]
        if cell.item:
            return cell.item.use_item()
        else:
            return "There is no item here to use."

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
        elif tool_name == "get_location_description":
            return self.rpg_instance.get_location_description()
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
            You do not make up any stories, you only provide information about the maze based on the context of the conversation.
            DO NOT MAKE STUFF UP!
            """,
            rpg_maze_instance=self.rpg_maze,  # Pass RPG instance
        )

        # Agent 2, User proxy agent for the explorer
        self.explorer = UserProxyAgent(
            name="Explorer",
            system_message="Exploring the maze, executing commands for movement.",
            code_execution_config={"work_dir": work_dir},
        )

        # Agent 3-9: Legend Characters
        self.legends = []  # List to store multiple Legend agents
        for i in range(1,8):
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


        def get_location_description_wrapper() -> str:
            return self.rpg_maze.get_location_description()
        
        def inspect_item_wrapper() -> str:
            return self.rpg_maze.inspect_item()

        def use_item_wrapper() -> str:
            return self.rpg_maze.use_item()
        
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
            description="Returns the current position of the player. use this when they ask for their coordinates",
        )

        register_function(
            display_maze_wrapper,
            caller=self.saturnbot,
            executor=self.explorer,
            name="display_maze",
            description="Displays the current state of the maze.",
        )

        register_function(
            get_location_description_wrapper,
            caller=self.saturnbot,
            executor=self.explorer,
            name="get_location_description",
            description="Returns the description of the current location in the maze. use this when the user is confused about their current location and whats around them.",
        )

        register_function(
            inspect_item_wrapper,
            caller=self.saturnbot,
            executor=self.explorer,
            name="inspect_item",
            description="Returns detailed information about the item in the current location.",
        )

        register_function(
            use_item_wrapper,
            caller=self.saturnbot,
            executor=self.explorer,
            name="use_item",
            description="Uses the item in the current location.",
        )
        
    def setup_group_chat(self):
        # All agents are added to the group chat, ensuring they can send and receive messages
        self.group_chat = GroupChat(
            [self.saturnbot, self.explorer] + self.legends,  # Include all relevant agents here
            [],                                            # Message history is empty to start
            speaker_selection_method='auto',           # Here we pass the custom speaker selection function
            max_round=30
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
maze_app.initiate_chat("what's around me??")
