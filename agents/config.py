from autogen import config_list_from_json
import random 

gpt4_config = {
    "cache_seed": random.randint(0, 9999999999999999),
    "temperature": 0,
    "config_list": config_list_from_json("llm_config.json"),
    "timeout": 120,
}