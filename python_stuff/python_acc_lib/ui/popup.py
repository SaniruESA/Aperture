"""
Popups in the pyglet window
"""
import pyglet
from ..server import server_ticker

def add_popup(popup:dict):
    """
    Adds a popup
    
    Arguments:
        popup:
            The popup to add, keys should be
            text: {text to contain}
    """
    
    popups.append({"text":popup["text"],"time":0})
    
def make_popups(window_stats:list):
    """
    Generates all popups for pyglet
    
    Arguments:
        window_stats:
            The size stats of the window [x,y,w,h]
    """
    global LABELS
    
    # Y to move through
    y = window_stats[3]
    
    # Rendering batch of popups
    batch = pyglet.graphics.Batch()
    
    # Temporary saving of labels
    labels = []
    
    for popup in popups:
        
        # Make label
        labels.append(pyglet.text.Label(popup["text"],0,y,font_size=30,batch=batch,anchor_y="top"))
                
        # Move label                  
        y -= 40
    
    # Push labels to global
    LABELS = labels
    
    return batch

popups:list[dict] = [{"text":"testing text"},{"text":"testing 2"}]
LABELS:list = [] # Holds labels and outline rectangles so python doesn't delete them