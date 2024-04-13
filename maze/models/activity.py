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

