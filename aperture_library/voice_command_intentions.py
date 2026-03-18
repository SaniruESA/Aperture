"""
Stores voice command intentions
(Written in Python in order to avoid issues with
local imports)
"""

intention_json = [
    {
        "intention_type": "move_screens",
        "triggers": ["move to the XXX", "the XXX screen", "go to the XXX", "XXX page"],
    },
    {
        "intention_type": "press_button",
        "triggers": ["click the XXX", "press the XXX", "tap the XXX", "hit the XXX"],
    },
    {
        "intention_type": "open_menu",
        "triggers": ["open the XXX menu", "show the XXX menu", "expand XXX", "pull up XXX"],
    },
    {
        "intention_type": "scroll",
        "triggers": ["scroll down", "scroll up", "scroll to the XXX", "go down a bit", "move up the page"],
    },
    {
        "intention_type": "type_input",
        "triggers": ["type XXX", "enter XXX", "fill in XXX", "write XXX"],
    },
    {
        "intention_type": "select_option",
        "triggers": ["select XXX", "choose XXX", "pick XXX", "switch to XXX", "set it to XXX"],
    },
    {
        "intention_type": "search",
        "triggers": ["search for XXX", "look up XXX", "find XXX", "search XXX"],
    },
]