"""
Handles live UI updates on the client-side software.
Ensures proper UI element registry within Aperture library.

Runs asynchronously with Aperture library to provide live
updates on shown/hidden UI elements.
"""

import json
import socket


class LiveUI:

    # Open registry of all UI elements from JSON, initialize class
    def __init__(self):
        with open("ui_elements.json", "r", encoding="utf-8") as file:
            self.ui_json = json.load(file)
            self.file_count = self.ui_json["_type_b_count"]
            self.curr_file_count = 0

        self.to_change = []

    def show_element(self, content):
        """Scans through software code for server calls for
        showing UI elements"""

        # Increment searched-through files
        if content == "EOF":
            self.curr_file_count += 1

            # Update all UI elements once all files have been searched
            if self.curr_file_count >= self.file_count:
                self.update_ui()

        # If a server call w/ UI change is received, change it
        else:
            self.to_change.append(self.ui_json[content])

    def update_ui(self):
        """Sends call to update UI server side"""

        # Clear all buttons
        socket.send(json.dumps({"type": "clear_button", "content": ""}))

        # Re-add buttons that need to be shown
        for ui in self.to_change:
            pos_list = [
                self.ui_json["x"],
                self.ui_json["y"],
                self.ui_json["width"],
                self.ui_json["height"],
            ]
            socket.send(
                json.dumps(
                    {
                        "type": "add_button",
                        "content": pos_list,
                        "name": self.ui_json["description"],
                    }
                )
            )

        # Reset file-searching trackers for shown elements
        self.to_change = []
        self.curr_file_count = 0
