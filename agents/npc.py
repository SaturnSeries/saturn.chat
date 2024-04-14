from autogen import ConversableAgent


class NPC(ConversableAgent):
    def __init__(self, name, llm_config, system_message, backstory, dialogues, explorer):
        super().__init__(
            name=name,
            llm_config=llm_config,
            system_message=system_message,
            human_input_mode="NEVER"
        )
        self.backstory = backstory
        self.dialogues = dialogues
        self.dialogue_index = 0
        self.explorer = explorer  # Add explorer as an attribute

    def send_initial_greeting(self):
        # Send initial greeting to the explorer
        self.send(self.backstory, self.explorer)

    def advance_dialogue(self):
        if self.dialogue_index < len(self.dialogues):
            self.send(self.dialogues[self.dialogue_index], self.explorer)
            self.dialogue_index += 1
        else:
            self.send("I have told you all I know.", self.explorer)

