# Import libraries
from .logger.basic_logs import *
import pyautogui
from typing import Literal
from .server import server_ticker
from . import ui
import pyglet

UITypeOptions = Literal["button"]

# Define queue
class TabNavOrder():
    
    selectedElementIndex:int
    selectedElement:dict
    order:list
    
    def __init__(self):
        """
        Allow for generating and playing edge tts audio in tandem
        
        Use function
        .xxx() to yyy
        """
        
        self.order = []
        self.selectedElementIndex = 0
        self.selectedElement = {}

    # can we have a callback passed like this between languages?
    def addUIElement(self, buttonRect: list, UIType: UITypeOptions, ariaText: str):
        self.order.append({"rect": buttonRect, "type": UIType, "ariaText": ariaText})

        info(f"Added UI Element for {ariaText}", __name__)

    def handleTabPress(self,shift:bool=False):
        
        if len(self.order) == 0:
            
            return
        
        # Track which UI element is being tabbed
        self.selectedElementIndex = (self.selectedElementIndex + (-1 if shift else 1)) % len(self.order)
        self.selectedElement = self.order[self.selectedElementIndex]

        # Say the text
        server_ticker.SERVER.tts_queue.queue_play(f".\\temp\\output_{self.selectedElement['ariaText']}.mp3",-1,self.selectedElement["ariaText"],True,True)
        
        # Update UI Rectangle
        ui.is_button_highlighted = True
        ui.button_highlight_coords = self.selectedElement["rect"]

        # Log text was created
        info(f"Switched tab focus to element named {self.selectedElement["ariaText"]}", __name__)
        
    def handleEnterPress(self):

        # Log button was pressed
        info(f"Pressed button {self.selectedElement["ariaText"]}",__name__)
        
        # Press the button and return mouse
        mousePos = pyautogui.position()
        rect:list = self.selectedElement["rect"]
        pyautogui.click(rect[0]+rect[2]/2,rect[1]+rect[3]/2)
        pyautogui.position(mousePos.x,mousePos.y)