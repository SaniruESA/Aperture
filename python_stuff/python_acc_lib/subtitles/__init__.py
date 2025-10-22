from win32api import GetSystemMetrics
from pyglet.window import Window
import pyglet
from typing import Literal

alignment_option = Literal["bottom_left","bottom_right","top_left","top_right"] # Possible alignments
WINDOW:Window = None # Generated pyglet window

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

def generate_window(width:int=500,height:int=250,alignment:alignment_option="bottom_right",padding:int=50):
    """
    Generates the subtitle window
    
    Arguments:
        width:
            Window width
        height:
            Window height
        alignment:
            Alignment on the monitor
        padding:
            Distance from the corners of the screen
    """
    global WINDOW
    
    # Generate window
    WINDOW = Window(visible=False,width=width,height=height,style=Window.WINDOW_STYLE_OVERLAY,caption="Subtitles")
    
    # Get window position
    window_x,window_y = list(align((0,0),alignment=alignment,padding=padding))
    
    # Shift window if it is on right and/or bottom
    if "bottom" in alignment:
        window_y -= height
        
    if "right" in alignment:
        window_x -= width
        
    # Position window
    WINDOW.set_location(window_x,window_y)
    
    # Enable window
    WINDOW.set_visible(True)

generate_window()

# TODO: Finish the subtitles

BACKGROUND = pyglet.shapes.RoundedRectangle(0,0,500,250,45,color=(100,100,100,50))

LABEL = pyglet.text.Label("Hello, world!",font_size=50)
LABEL2 = pyglet.text.Label("I, am steve",font_size=50,y=50)

@WINDOW.event
def on_draw():
    
    WINDOW.clear()
    BACKGROUND.draw()
    LABEL.draw()
    LABEL2.draw()
    
pyglet.app.run()