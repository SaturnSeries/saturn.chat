import random
import logging

from . import POAPActivity, Cell, Item
# Set up basic configuration for logging
logging.basicConfig(
    level=logging.CRITICAL, format="%(asctime)s - %(levelname)s - %(message)s"
)


##############################
# Custom Maze Implementation #
##############################


class Maze:
    def __init__(self, width, height, items_prob=0.7, npcs=None):
        self.width = width
        self.height = height
        self.maze_grid = [[Cell(x, y) for y in range(height)] for x in range(width)]
        self.start_point = random.choice(self.get_all_locations())
        self.finish_point = (width - 2, height - 2)
        self.generate_maze()
        self.place_starting_loot()
        self.setup_activities()
        if npcs:
            self.place_npcs(npcs)  


    def place_npcs(self, npcs):
        # Place NPCs at specific and random locations as needed
        status = False
        for npc in npcs:
            # Place the first NPC in the starting location
            if status == False:
                self.place_npc(npc, self.start_point[0], self.start_point[1])
                status = True
            # Place the rest of the NPCs in random locations
            else:
                x, y = random.choice(self.get_all_locations())
                self.place_npc(npc, x, y)
            

            # x, y = (1, 1)  # Example fixed position, change as needed
            # self.maze_grid[x][y].place_npc(npc)
            # npc.send_initial_greeting()

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
        mining_activity = POAPActivity(
            "Mine for rare crystals",
            # lambda: "You found some rare crystals!" if random.random() > 0.5 else "No crystals here.",
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
