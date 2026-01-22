import json
import socket

class LiveUI():
    def __init__(self):
        with open("ui_elements.json", "r", encoding="utf-8") as file:
            self.ui_json = json.load(file)
            self.file_count = self.ui_json["_type_b_count"]
            self.curr_file_count = 0

        self.to_change = []

    def show_element(self, content):
        if content == "EOF":
            self.curr_file_count += 1

            if self.curr_file_count >= self.file_count:
                self.update_ui()
        
        else:
            self.to_change.append(self.ui_json[content])

    def update_ui(self):
        socket.send(json.dumps({"type":"clear_button","content":""}))

        for ui in self.to_change:
            pos_list = [self.ui_json["x"], self.ui_json["y"], self.ui_json["width"], self.ui_json["height"]]
            socket.send(json.dumps({"type":"add_button","content":pos_list,"name":self.ui_json["description"]}))

        self.to_change = []
        self.curr_file_count = 0
        