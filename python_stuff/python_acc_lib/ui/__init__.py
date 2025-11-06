from win32api import GetSystemMetrics
import pyglet
from typing import Literal

alignment_option = Literal["bottom_left","bottom_right","top_left","top_right"] # Possible alignments

# Get monitor statistics
MONITOR_WIDTH = GetSystemMetrics(0)
MONITOR_HEIGHT = GetSystemMetrics(1)

def align(position:tuple[int,int],alignment:alignment_option="bottom_right",padding:int=0) -> tuple[int,int] | None:
    """
    Aligns a position based on alignment option to a corner of the screen
    
    Arguments:
        position:
            Starting position
        alignment:
            Alignment on the monitor
        padding:
            Distance from the corner of the screen
    """
    
    # Choose alignment based on option
    match alignment:
        
        case "top_left":
            
            return (position[0]+padding,position[1]+padding)
        
        case "top_right":
            
            return (position[0]+MONITOR_WIDTH-padding,position[1]+padding)
        
        case "bottom_left":
            
            return (position[0]+padding,position[1]+MONITOR_HEIGHT-padding)
            
        case "bottom_right":
            
            return (position[0]+MONITOR_WIDTH-padding,position[1]+MONITOR_HEIGHT-padding)

class Window(pyglet.window.Window):
    def __init__(self):
        """
        Generates the subtitle window
        
        Arguments:
            width:
                Window width
            height:
                Window height
        """
        
        # Generate window
        pyglet.window.Window.__init__(self,visible=True,width=MONITOR_WIDTH,height=MONITOR_HEIGHT,style=Window.WINDOW_STYLE_OVERLAY,caption="Enablr Overlay")
        
        # Set window position
        self.set_location(0,0)
        
        # Push handlers
        self.push_handlers(on_draw=self.on_draw)

    def on_draw(self):
        
        self.clear()
        
        button_highlight = pyglet.shapes.Rectangle(button_highlight_coords[0],MONITOR_HEIGHT-button_highlight_coords[1]-button_highlight_coords[3],button_highlight_coords[2],button_highlight_coords[3],(255,255,255,150))
        
        if is_button_highlighted:
            
            button_highlight.draw()

is_button_highlighted = False
button_highlight_coords = [0,0,0,0]