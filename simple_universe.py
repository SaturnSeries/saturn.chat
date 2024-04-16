import os
import logging
import random
import copy
from typing import Literal, Union
import requests
import json
from agents import NPC, Legend, SaturnBot
from maze.controller import MazeController
from dotenv import load_dotenv

# Custom imports
from agents.config import gpt4_config
from autogen import (Agent, GroupChat, GroupChatManager,
                     UserProxyAgent, register_function)

load_dotenv()

# Set up basic configuration for logging
logging.basicConfig(
    level=logging.CRITICAL, format="%(asctime)s - %(levelname)s - %(message)s"
)



####################################
# Group Chat and Application Logic #
####################################

# In your application initialization
class SaturnChatApp:
    def __init__(self, work_dir="./maze"):
        # Instantiate explorer first
        # Agent 1, User proxy agent for the explorer
        self.explorer = UserProxyAgent(
            name="Explorer",
            system_message="Exploring the maze, executing commands for movement.",
            code_execution_config={"work_dir": work_dir},
        )
        # Agent 2: Guardian
        # Create the NPC with explorer passed as an argument

        guardian_llm_config = copy.deepcopy(gpt4_config)

        self.guardian_npc = NPC(
            name="Guardian",
            llm_config=guardian_llm_config,
            system_message="I'm a spectral figure that from the shadows.",
            backstory="Guardian of the ancient labyrinth, keeper of its secrets.",
            dialogues=["Welcome, traveler, to the labyrinth of doom.", "Beware the paths that twist and turn.", "Seek the treasure but watch for traps."],
            explorer=self.explorer,
        )
        # Pass the NPC list to MazeExplorer
        self.rpg_maze = MazeController(10, 10, npcs=[self.guardian_npc])
        # print(f"Maze created with Guardian NPC. {self.rpg_maze.maze.npcs}")
        # Agent 3

        saturnbot_llm_config = copy.deepcopy(gpt4_config)

        self.saturnbot = SaturnBot(
            name="SaturnBot",
            llm_config=saturnbot_llm_config,
            system_message="""You are Saturn Bot, you guide the player across a maze and they need to find the exit. 
            You have the possibility to move around, display the map and tell stories about Saturn.
            You do not make up any stories, you only provide information about the maze based on the context of the conversation.
            DO NOT MAKE STUFF UP!
            """,
            rpg_maze_instance=self.rpg_maze,  # Pass RPG Maze instance
        )



#         # Agent 3-9: Legend Characters
#         legend_llm_config = copy.deepcopy(gpt4_config)

#         self.legends = []  # List to store multiple Legend agents
#         for i in range(1,8):
#             traits = self.get_legend_metadata(i)
#             legend = Legend(
#                 name=f"Legend_{i}",  # Give a unique name
#                 llm_config=copy.deepcopy(legend_llm_config)
# ,
#                 system_message=f"I am Legend_{i}. I'm in a maze trying to escape. Treasures await in this maze, if we're able to find them. I'll be talking with an explorer, let's explore and get out! \n\n These are my traits: \n\n {traits}"
#             )
#             self.legends.append(legend)  # Append to the list
            
        self.register_tools() 
        self.group_chat = GroupChat([self.explorer, self.saturnbot], [], max_round=1000, speaker_selection_method="round_robin")
        self.initial_group_chat = GroupChat([self.explorer] + [self.saturnbot] + [self.guardian_npc], [], max_round=1000, speaker_selection_method="round_robin")
        self.group_chat_manager = GroupChatManager(groupchat=self.initial_group_chat)

        self.update_group_chat_participants()  # Initialize group chat participants based on initial NPC locations



    def update_group_chat_participants(self):
        """Update the group chat participants based on current location NPCs."""
        current_npcs = self.rpg_maze.get_npcs_at_location()
        current_participants = [self.saturnbot, self.explorer] + current_npcs

        # Update the GroupChat instance that the GroupChatManager is managing
        self.group_chat_manager.groupchat.participants = current_participants



    def move_player_and_update_chat(self, direction):
        """Move player and update chat based on new location."""
        move_result = self.rpg_maze.move_player(direction)
        self.update_group_chat_participants()  # Update participants after moving
        return move_result
    
    def get_legend_metadata(self, id: int):
        url = f"https://api.opensea.io/api/v2/chain/ethereum/contract/0xD45b8768C9d5Cb57a130fa63fEab85Ba9f52Cc22/nfts/{id}"
        headers = {
            "accept": "application/json",
            "x-api-key": os.getenv("OPENSEA_API_KEY"),
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
        
        def interact_with_activity_wrapper() -> str:
            return self.rpg_maze.interact_with_activity()
        
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

        register_function(
            interact_with_activity_wrapper,
            caller=self.saturnbot,
            executor=self.explorer,
            name="interact_with_activity",
            description="Interacts with the activity in the current location.",
        )

    def send_group_message(self, group_chat: GroupChat, message):
        """Send a message to all participants in a group chat."""
        for participant in group_chat.agents:
            participant.send(message, self.explorer, request_reply=False) 


    def update_group_chat_participants(self):
        """Update the group chat participants based on current location NPCs."""
        current_npcs = self.rpg_maze.get_npcs_at_location()
        current_participants = [self.saturnbot, self.explorer] + current_npcs
        # Directly assign the participants attribute
        self.group_chat.agents = current_participants

    def move_player_and_update_chat(self, direction):
        """Move player and update chat based on new location."""
        move_result = self.rpg_maze.move_player(direction)
        self.update_group_chat_participants()  # Update participants after moving
        return move_result

    def custom_speaker_selection_func(self, last_speaker: Agent, groupchat: GroupChat) -> Union[Agent, Literal["auto", "manual", "random", "round_robin"], None]:
        """
        Custom logic to select who speaks next based on the last speaker and the conversation turn, including handling Legends.
        """
        # If the last speaker was the explorer, let the SaturnBot provide some context or guidance.
        if last_speaker == self.explorer:
            return self.saturnbot

        # If the last speaker was the SaturnBot, check if there are Legends to speak next.
        elif last_speaker == self.saturnbot:
            # Check for presence of Legends in the current group chat.
            legends_present = [legend for legend in self.legends if legend in groupchat.agents]
            if legends_present:
                # If Legends are present, let one of them speak next.
                # Here, you can decide to either select a specific Legend based on your game's logic or randomly.
                return legends_present[0]  # This example selects the first Legend for simplicity.
            
            # If no Legends are present, check for NPCs.
            npcs = self.rpg_maze.get_npcs_at_location()
            if npcs:
                return random.choice(npcs)
            else:
                return self.explorer

        # If the last speaker was one of the Legends, check if there are NPCs to respond.
        elif last_speaker in self.legends:
            npcs = self.rpg_maze.get_npcs_at_location()
            if npcs:
                return random.choice(npcs)
            else:
                return self.explorer

        # If the last speaker was one of the NPCs, the conversation should logically return to the explorer.
        elif last_speaker in self.rpg_maze.get_npcs_at_location():
            return self.explorer

        # If none of the above conditions are met, maintain a default or fallback behavior.
        return "round_robin"  # This could be adjusted to return 'None' or a specific default agent.

            
    
    def initiate_chat(self, message):
        intro_message = self.rpg_maze.intro_maze()
        self.saturnbot.send(intro_message, self.explorer, request_reply=False)

        self.update_group_chat_participants()

        # Create and configure a new GroupChat instance
        self.group_chat = GroupChat([self.saturnbot, self.explorer] + self.rpg_maze.get_npcs_at_location(), [], max_round=1000, speaker_selection_method='round_robin')

        # Use the GroupChatManager to handle the chat session
        self.group_chat_manager.run_chat(
            config=self.group_chat,
            sender=self.explorer,  # Assuming the explorer initiates the chat
            messages=[{"content": message, "role": self.explorer}]
        )


############################
# Run the chat application #
############################

maze_app = SaturnChatApp()
# maze_app.initiate_chat("Hello! Who am I talking to right now? Who is present in this conversation so far?")
maze_app.initiate_chat("perform the available activity")
