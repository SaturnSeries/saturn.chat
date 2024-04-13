
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