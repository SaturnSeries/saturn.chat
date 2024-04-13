
from typing import Literal, Union, Callable, get_type_hints, Tuple

from maze.models.cell import Cell
from maze.models.maze import Maze  # Adjust if Maze class location is changed


# from maze import Maze, Item, Cell
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


class MazeController:
    """
    A class to manage and control the exploration of a maze.

    Attributes:
        maze (Maze): The maze object representing the environment.
        current_location (Tuple[int, int]): The current location of the player in the maze.

    Methods:
        intro_maze(): Introduces the maze to the player and shows available moves.
        get_current_position(): Returns a description of the current location.
        get_location_description(): Provides a description of the current location, including possible paths, items, and NPCs.
        get_npcs_at_location(): Retrieves NPCs present at the current location.
        move_player(direction: str) -> str: Moves the player in the specified direction if possible.
        can_move(current_cell, next_cell, direction): Checks if the player can move from the current cell to the next cell in the specified direction.
        display_maze(): Displays the current state of the maze.
        inspect_item(): Returns detailed information about the item in the current location.
        use_item(): Uses the item in the current location.
        interact_with_activity(): Interacts with the activity in the current location.
    """
    def __init__(self, width: int, height: int, npcs: list = []):
        # Directly use the Maze class for creating the maze
        self.maze = Maze(width, height, npcs=npcs)
        self.current_location = self.maze.start_point  # instead of self.get_random_start()

    def intro_maze(self):
        """Introduce the maze to the player and show available moves."""
        return "Welcome to the maze! Try to find your way out.\n" + self.get_location_description()

    def get_current_position(self):
        return self.get_location_description()


    def get_location_description(self):
        """Provide a description of the current location, possible paths, and any items or NPCs present."""
        x, y = self.current_location
        cell = self.maze.maze_grid[x][y]
        directions = []
        descriptions = []

        print(str(cell))
        # Check for available directions
        if not cell.walls["N"] and y > 0:
            directions.append("North")
        if not cell.walls["S"] and y < self.maze.height - 1:
            directions.append("South")
        if not cell.walls["E"] and x < self.maze.width - 1:
            directions.append("East")
        if not cell.walls["W"] and x > 0:
            directions.append("West")
        paths = "Paths available: " + ", ".join(directions) if directions else "You are trapped with no paths available."

        # Check for an item in the current cell and create a description if present
        if cell.item:
            descriptions.append(f"You see an item here: {cell.item.name} - {cell.item.description}")
        else:
            descriptions.append("There is nothing of interest here.")

        # Check if there is an NPC in this cell
        if cell.npcs:
            for npc in cell.npcs:
                descriptions.append(f"You encounter a character: {npc.name}. {npc.system_message}")

        # Describing activities
        for activity in cell.activities:
            descriptions.append(f"Activity available: {activity.description}")


        # Combine descriptions of paths, items, and NPCs
        location_description = f"You are now at location ({x}, {y}). {paths}"
        location_description += "\n" + "\n".join(descriptions)
        
        return location_description

    def get_npcs_at_location(self):
        """Retrieve NPCs present at the current location."""
        x, y = self.current_location
        cell = self.maze.maze_grid[x][y]
        return cell.npcs


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
                if self.can_move(current_cell, next_cell, direction[0]):
                    self.current_location = (nx, ny)
                    return self.get_location_description()
                else:
                    return "You can't move that way."
            else:
                return "You can't move beyond the maze boundaries."
        else:
            return "Invalid direction. Use 'north', 'south', 'east', 'west', or their abbreviations and synonyms like 'up' for north."

    def can_move(self, current_cell, next_cell, direction):
        """Check if the player can move from the current cell to the next cell in the specified direction."""
        if direction == 'n':  # Moving North
            return not current_cell.walls['N'] and not next_cell.walls['S']
        elif direction == 's':  # Moving South
            return not current_cell.walls['S'] and not next_cell.walls['N']
        elif direction == 'e':  # Moving East
            return not current_cell.walls['E'] and not next_cell.walls['W']
        elif direction == 'w':  # Moving West
            return not current_cell.walls['W'] and not next_cell.walls['E']
        else:
            return False  # Invalid direction
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
        
    @annotate_self
    def interact_with_activity(self):
        x, y = self.current_location
        cell: Cell = self.maze.maze_grid[x][y]
        if cell.activities:
            return cell.activities[0].interact()
        else:
            return "There is no activity here to interact with."
