import pyglet
from typing import Literal
from . import popup
import time

class Window(pyglet.window.Window):
    def __init__(self,width,height):
        """
        Generates the subtitle window
        
        Arguments:
            width:
                Window width
            height:
                Window height
        """
        global window_stats
        
        # Generate window
        pyglet.window.Window.__init__(self,visible=True,width=width,height=height,style=Window.WINDOW_STYLE_OVERLAY,caption="Aperture Overlay")
        
        # Set window position
        self.set_location(0,0)
        
        # Push handlers
        self.push_handlers(on_draw=self.on_draw)
        
        # Save window stats
        window_stats = [0,0,width,height]
        
        # Reset popup timer
        popup.start_time = time.time()

    def on_draw(self):
        
        global update_window
        
        # Update window
        if update_window:
            
            x,y,w,h = window_stats
            
            self.set_location(x,y)
            self.set_size(w,h)
            
            update_window = False
        
        # Clear window
        self.clear()
        
        # Draw popups
        popup.make_popups(window_stats).draw()
        
        # Draw buttons if highlighted
        if is_button_highlighted:
            
            button_highlight = pyglet.shapes.Rectangle(button_highlight_coords[0],self.height-button_highlight_coords[1]-button_highlight_coords[3],button_highlight_coords[2],button_highlight_coords[3],(255,255,255,150))
            
            button_highlight.draw()
            
    def on_key_press(symbol, modifiers):
        if symbol == pyglet.window.key.ESCAPE:
            return pyglet.event.EVENT_HANDLED

is_button_highlighted:bool = False
button_highlight_coords:list = [0,0,0,0]
update_window:bool = False
window_stats:list = [0,0,0,0]