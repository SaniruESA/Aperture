# Import libraries
import pygame
from server import server_ticker
from .logger.basic_logs import *

# Initialize pygame
pygame.init()

# Define queue
class TabNavOrder():
    
    def __init__(self):
        """
        Allow for generating and playing edge tts audio in tandem
        
        Use function
        .xxx() to yyy
        """
        
        self.order = []
        self.selectedElement = -1

    # can we have a callback passed like this between languages?
    def addUIElement(self, buttonRect: pygame.Rect, UIType: str, ariaText: str, enterCallback):
        self.order.append({"rect": buttonRect, "type": UIType, "ariaText": ariaText, "callback": enterCallback})

        info(f"Added UI Element for {ariaText}", __name__)

    def handleTabPress(self):
        # Track which UI element is being tabbed
        self.selectedElement = (self.selectedElement + 1) % len(self.order)

        # Here add implmeentation from the TTS library to add this narration to the queue
        server_ticker.queue_generate_tts(server=server_ticker.SERVER, json={"content": self.selectedElement["ariaText"]})

        # IF both mouse movement narration and tab narration are happening at the same time,
        # prioritize tab narration

        # Maybe make a class or file to handle UI element narration

        info(f"Switched tab focus to element named {self.order[self.selectedElement]["ariaText"]}", __name__)
        
    def handleEnterPress(self):
        # HOw the heck is this gonna work
        self.order[self.selectedElement]["callback"]()

