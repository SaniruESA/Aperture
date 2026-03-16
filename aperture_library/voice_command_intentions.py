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
]
