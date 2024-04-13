

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
