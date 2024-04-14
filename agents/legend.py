from autogen import ConversableAgent

class Legend(ConversableAgent):
    def __init__(self, name, llm_config, system_message):
        super().__init__(
            name=name,
            llm_config=llm_config,
            system_message=system_message,
            human_input_mode="NEVER"
        )
