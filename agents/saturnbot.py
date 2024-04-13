from autogen import ConversableAgent
import logging
from maze.controller import MazeController
class SaturnBot(ConversableAgent):
    def __init__(self, name, llm_config, system_message, rpg_maze_instance: MazeController):
        super().__init__(
            name=name,
            llm_config=llm_config,
            system_message=system_message,
            human_input_mode="NEVER"
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
        elif tool_name == "inspect_item":
            return self.rpg_instance.inspect_item()
        elif tool_name == "use_item":
            return self.rpg_instance.use_item()
        elif tool_name == "interact_with_activity":
            return self.rpg_instance.interact_with_activity()
        else:
            return "Unknown tool invocation."