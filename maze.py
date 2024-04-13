import random
import logging

from autogen import (Agent, ConversableAgent, GroupChat, GroupChatManager,
                     UserProxyAgent, config_list_from_json)

# Set up basic configuration for logging
logging.basicConfig(
    level=logging.CRITICAL, format="%(asctime)s - %(levelname)s - %(message)s"
)

#########################
# Custom Activity Class #
#########################

class Activity:
    def __init__(self, description, execute):
        self.description = description
        self.execute = execute  # This is a function that performs the activity
        self.interact = execute  
    def perform_activity(self):
        """Perform the activity and return the result of the execution."""
        return self.execute()



#####################
# Custom Item Class #
#####################

class Item:
    def __init__(self, name, description, inspection_detail=None, durability=None, custom_functionality=None):
        self.name = name
        self.description = description
        self.durability = durability  # None for items without durability, implies infinite use
        self.inspection_detail = inspection_detail  # Additional detail revealed upon inspection
        self.custom_functionality = custom_functionality  # Callback function to execute on use

    def inspect_item(self):
        """Return detailed information about this item."""
        if self.inspection_detail:
            return f"{self.name} - {self.description}. Further Details: {self.inspection_detail}"
        return f"{self.name} - {self.description}. No additional details available."

    def use_item(self):
        """Use the item, reducing durability if applicable and executing a callback if present."""
        if self.durability is not None:
            if self.durability == 0:
                return f"The {self.name} is already worn out and cannot be used."
            self.durability -= 1
            use_message = f"You use the {self.name}."
            if self.durability > 0:
                use_message += f" It can be used {self.durability} more times."
            else:
                use_message += " It has worn out and can no longer be used."
        else:
            use_message = f"You use the {self.name}, but it seems to last forever."

        if self.custom_functionality:
            functionality_result = self.custom_functionality()
            use_message += " " + functionality_result

        return use_message

    def __str__(self):
        durability_str = f", Durability: {'Infinite' if self.durability is None else self.durability}"
        return f"{self.name}: {self.description}{durability_str}"

##############################
# Custom Maze Implementation #
##############################

class Cell:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.walls = {"N": True, "S": True, "E": True, "W": True}
        self.item = None
        self.npcs = []
        self.visited = False
        self.activities = []  # New list to hold activities

    def place_activity(self, activity):
        self.activities.append(activity)


    def place_item(self, item):
        self.item = item

        
    def place_npc(self, npc):
        self.npcs.append(npc)

class Maze:
    def __init__(self, width, height, items_prob=0.7, npcs=None):
        self.width = width
        self.height = height
        self.maze_grid = [[Cell(x, y) for y in range(height)] for x in range(width)]
        self.start_point = (1, 1)
        self.finish_point = (width - 2, height - 2)
        self.generate_maze()
        self.place_starting_loot()
        self.setup_activities()
        if npcs:
            self.place_npcs(npcs)  


    def place_npcs(self, npcs):
        # Place NPCs at specific or random locations as needed
        for npc in npcs:
            x, y = (1, 1)  # Example fixed position, change as needed
            self.maze_grid[x][y].place_npc(npc)
            npc.send_initial_greeting()

    def place_npc(self, npc, x, y):
        # Assigning NPC to the npc property of the cell
        self.maze_grid[x][y].npc = npc
        logging.critical(f"NPC {npc.name} placed at {x}, {y}")


    def generate_maze(self):
        stack = []
        start_cell = self.maze_grid[self.start_point[0]][self.start_point[1]]
        start_cell.visited = True
        start_cell.state = 0  # Mark the start cell as part of the path
        stack.append(start_cell)

        while stack:
            current_cell = stack[-1]
            unvisited_neighbours = self.get_unvisited_neighbours(current_cell)

            if not unvisited_neighbours:
                stack.pop()
            else:
                neighbour_cell = random.choice(unvisited_neighbours)
                self.remove_wall(current_cell, neighbour_cell)

                neighbour_cell.visited = True
                neighbour_cell.state = 0  # Mark as part of the path
                stack.append(neighbour_cell)


    def setup_activities(self):
        # Example activity setup
        mining_activity = Activity(
            "Mine for rare crystals",
            lambda: "You found some rare crystals!" if random.random() > 0.5 else "No crystals here."
        )
        # Place the activity in the starting location
        self.maze_grid[self.start_point[0]][self.start_point[1]].place_activity(mining_activity)


    # def populate_items(self, prob):
    #     # Populating items with a certain probability in each cell
    #     items = [
    #         Item("Key", "A small rusty key, wonder what it opens."),
    #         Item("Coin", "A shiny gold coin, valuable."),
    #         Item("Sword", "An old sword, still sharp. Might come in handy."),
    #         Item("Potion", "A mysterious potion. Drink at your own risk!")
    #     ]
    #     for row in self.maze_grid:
    #         for cell in row:
    #             if random.random() < prob:
    #                 cell.place_item(random.choice(items))

    def place_starting_loot(self):
        """Place a specific item at the starting point of the maze."""
        starting_item = Item("Map", "An old map showing hints of hidden doors.",
                             "The path to the exit is marked with a red line. When you inspect the map, it read 'The key to the exit is in the room with the sword.",
                             durability=5,
                             # The custom functionality removes a random wall when used
                             custom_functionality=lambda: "A hidden door opens somewhere in the maze.")
        self.maze_grid[self.start_point[0]][self.start_point[1]].item = starting_item


    def get_unvisited_neighbours(self, cell):
        neighbours = []

        if cell.y != 0:
            north_neighbour = self.maze_grid[cell.x][cell.y - 1]
            if not north_neighbour.visited:
                neighbours.append(north_neighbour)

        if cell.y != self.height - 1:
            south_neighbour = self.maze_grid[cell.x][cell.y + 1]
            if not south_neighbour.visited:
                neighbours.append(south_neighbour)

        if cell.x != 0:
            west_neighbour = self.maze_grid[cell.x - 1][cell.y]
            if not west_neighbour.visited:
                neighbours.append(west_neighbour)

        if cell.x != self.width - 1:
            east_neighbour = self.maze_grid[cell.x + 1][cell.y]
            if not east_neighbour.visited:
                neighbours.append(east_neighbour)

        return neighbours

    def remove_wall(self, cell1, cell2):
        if cell1.x == cell2.x:
            if cell1.y > cell2.y:
                cell1.walls["N"] = False
                cell2.walls["S"] = False
            else:
                cell1.walls["S"] = False
                cell2.walls["N"] = False
        else:
            if cell1.x > cell2.x:
                cell1.walls["W"] = False
                cell2.walls["E"] = False
            else:
                cell1.walls["E"] = False
                cell2.walls["W"] = False

    def get_maze(self):
        return [[cell.walls for cell in row] for row in self.maze_grid]

    def get_all_locations(self):
        """Return a list of all cell coordinates in the maze."""
        locations = [(x, y) for x in range(self.width) for y in range(self.height)]
        return locations

    

    def display_maze(self, player_location):
        # Initialize an empty string to store the maze representation
        maze_representation = ""

        # Iterate over each row in the maze
        for y in range(self.height):
            # Initialize strings to represent the top and middle rows of each cell
            top_row = ""
            middle_row = ""

            # Iterate over each column in the maze
            for x in range(self.width):
                # Access the cell at position (x, y) in the maze grid
                cell = self.maze_grid[x][y]

                # Represent horizontal walls at the top of each cell
                top_row += "+--" if cell.walls["N"] else "+  "

                # Represent vertical walls on the left side of each cell
                middle_row += "| " if cell.walls["W"] else "  "

                # Check if the current cell is the player's location
                if (x, y) == player_location:
                    # If yes, mark the player's location with 'O'
                    middle_row += "O"
                else:
                    # If no player is in this cell, mark paths with ' ' and walls with 'X'
                    middle_row += " " if cell.walls["W"] else " "

            # Close the cell with a vertical wall on the right side
            middle_row += "|"

            # Append the top and middle rows of the current cell to the maze representation
            maze_representation += top_row + "+\n" + middle_row + "\n"

        # Initialize a string to represent the bottom row of the maze
        bottom_row = "+"

        # Add horizontal walls to the bottom row to close the maze
        for x in range(self.width):
            bottom_row += "--+"

        # Append the bottom row to the maze representation
        maze_representation += bottom_row

        # Print the maze representation
        print(maze_representation)
