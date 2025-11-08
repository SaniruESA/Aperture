# Import libraries
from .logger.basic_logs import *
import pyautogui
from typing import Literal
from .server import server_ticker
from . import ui

UITypeOptions = Literal["button", "text"]

# Check if a point and rect are colliding
def rect_point_collision(rectBounds: list, point: list):
    return abs(point[0] - rectBounds[0]) <= abs(rectBounds[2]) and abs(point[1] - rectBounds[1]) <= abs(rectBounds[3])

# Define queue
class TabNavOrder():
    
    tabbedElementIndex:int
    tabbedElement:dict
    hoveredElement:dict
    order:dict
    
    def __init__(self):
        """
        Allow for generating and playing edge tts audio in tandem
        
        Use function
        .xxx() to yyy
        """
        
        self.order = {
            "button": [],
            "text": []
        }
        self.tabbedElementIndex = 0
        self.tabbedElement = None
        self.hoveredElement = {"rect": None, "ariaText": None}

    # can we have a callback passed like this between languages?
    def addUIElement(self, buttonRect: list, UIType: UITypeOptions, ariaText: str):
        self.order[UIType].append({"rect": buttonRect, "ariaText": ariaText})

        info(f"Added UI Element for {ariaText}", __name__)

    def handleTabPress(self,shift:bool=False):
        
        if len(self.order["button"]) == 0:
            return
        
        # Track which UI element is being tabbed
        self.tabbedElementIndex = (self.tabbedElementIndex + (-1 if shift else 1)) % len(self.order["button"])
        self.tabbedElement = self.order["button"][self.tabbedElementIndex]

        # Say the text
        server_ticker.SERVER.tts_queue.queue_play(f".\\temp\\output_{self.tabbedElement['ariaText']}.mp3",-1,self.tabbedElement["ariaText"],True,True)
        
        # Update UI Rectangle
        ui.is_button_highlighted = True
        ui.button_highlight_coords = self.tabbedElement["rect"]

        # Log text was created
        info(f"Switched tab focus to element named {self.tabbedElement["ariaText"]}", __name__)
        
    def handleEnterPress(self):

        # Don't do anything if no element is tab-selected
        if self.tabbedElement == None:
            return

        # Log that the button was pressed
        info(f"Pressed button {self.tabbedElement["ariaText"]}",__name__)
        
        # Press the button and return mouse to original location
        mousePos = pyautogui.position()
        rect:list = self.tabbedElement["rect"]
        pyautogui.click(rect[0]+rect[2]/2,rect[1]+rect[3]/2)
        pyautogui.position(mousePos.x,mousePos.y)

    def hoverTTS(self):
        mousePos = pyautogui.position()
        flattenedUIElements = [item for row in self.order.values() for item in row]
        foundHoveredElement = False

        # Check collision between mouse and UI elements
        for UIElement in flattenedUIElements:
            if rect_point_collision(UIElement["rect"], mousePos):
                foundHoveredElement = True

                # Play TTS to narrate the UI element, if not already done
                if self.hoveredElement["ariaText"] != UIElement["ariaText"]:
                    server_ticker.SERVER.tts_queue.queue_play(f".\\temp\\output_{UIElement['ariaText']}.mp3",99,UIElement["ariaText"],True,True)
                    self.hoveredElement = UIElement

                    # Return if done finding UI element
                    return
                
        # Reset hovered element to default (none) if none found
        if not foundHoveredElement:
            self.hoveredElement = {"rect": None, "ariaText": None}