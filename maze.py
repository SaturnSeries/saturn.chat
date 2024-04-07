# maze.py

import random

class Cell:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.walls = {'N': True, 'S': True, 'E': True, 'W': True}
        self.visited = False

class Maze:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.maze_grid = [[Cell(x, y) for y in range(height)] for x in range(width)]
        self.generate_maze()


    def generate_maze(self):
        stack = []
        start_cell = self.maze_grid[0][0]
        start_cell.visited = True
        stack.append(start_cell)

        while len(stack) > 0:
            current_cell = stack[-1]
            unvisited_neighbours = self.get_unvisited_neighbours(current_cell)

            if len(unvisited_neighbours) == 0:
                stack.pop()
            else:
                neighbour_cell = random.choice(unvisited_neighbours)
                self.remove_wall(current_cell, neighbour_cell)

                neighbour_cell.visited = True
                stack.append(neighbour_cell)

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
                cell1.walls['N'] = False
                cell2.walls['S'] = False
            else:
                cell1.walls['S'] = False
                cell2.walls['N'] = False
        else:
            if cell1.x > cell2.x:
                cell1.walls['W'] = False
                cell2.walls['E'] = False
            else:
                cell1.walls['E'] = False
                cell2.walls['W'] = False

    def get_maze(self):
        return [[cell.walls for cell in row] for row in self.maze_grid]




    def get_all_locations(self):
        """Return a list of all cell coordinates in the maze."""
        locations = [(x, y) for x in range(self.width) for y in range(self.height)]
        return locations

def create_maze(width, height):
    maze = Maze(width, height)
    return maze.get_maze()
