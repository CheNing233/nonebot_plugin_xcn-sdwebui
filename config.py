from pydantic import BaseModel


class Plugin_Config(BaseModel):
    enable: bool = True

    enable_groups: list = []
    enable_friends: list = []

    servers: list = [
        {
            "name": "Default Server",
            "type": "SDWebUI",
            "host": "0.0.0.0",
            "port": 7860,
            "avalible": None,
        }
    ]

    r18: bool = True
