import json


class ConfigLoader:
    def __init__(self, json_path):
        self.json_path = json_path
        self.data = self.load_json()

    def load_json(self):
        try:
            with open(self.json_path, "r") as file:
                data = json.load(file)
            return data
        except FileNotFoundError:
            print("JSON文件不存在")
            return {}

    def save_json(self):
        try:
            with open(self.json_path, "w") as file:
                json.dump(self.data, file, indent=4)
            self.data = self.load_json()
        except IOError:
            print("无法保存JSON文件")
