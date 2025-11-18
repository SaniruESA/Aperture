"""
Popups in the pyglet window
"""
import pyglet
from ..server import server_ticker
from .. import settings
from ..logger.basic_logs import *
import time

def add_popup(popup:dict):
    """
    Adds a popup
    
    Arguments:
        popup:
            The popup to add, keys should be
            text: The text to contain
            background-color: The background color
            text-color: The text color
            position: The position of the popup or none
    """
    
    # Add time item
    popup["time"] = 0
    
    # Add popup to list start
    popups.insert(0,popup)
    
    # Notify
    info(f"Added popup with text: {popup['text']}",__name__)
    
    # Play tts
    server_ticker.SERVER.tts_queue.generate(popup["text"])
    
def make_popups(window_stats:list):
    """
    Generates all popups for pyglet
    
    Arguments:
        window_stats:
            The size stats of the window [x,y,w,h]
    """
    global LABELS,start_time
    
    # Get delta
    curr_time = time.time()
    delta = curr_time - start_time
    start_time = curr_time
    
    # Rendering batch of popups
    batch = pyglet.graphics.Batch()
    
    # Groups to prevent incorrect overlap
    rect_group = pyglet.graphics.Group(-1)
    label_group = pyglet.graphics.Group(0)
    
    # Temporary saving of labels
    labels = []
    
    # Store padding values
    padding = PADDING
    window_padding = WINDOW_PADDING
    text_padding = TEXT_PADDING
    popup_max_time = POPUP_MAX_TIME
    
    # Y to move through
    y = window_stats[3] - window_padding - text_padding
    
    i = 0
    while i < len(popups):
        
        popup = popups[i]
        
        # Check if label should be delete
        popup["time"] += delta
        if popup["time"] > popup_max_time:
            
            # Remove and shift
            popups.pop(i)
            continue
        
        # Change opacity when close to over or just created
        opacity = 255
        if popup["time"] + 1 >= popup_max_time:
            opacity = int((popup_max_time-popup["time"]) * 255)
        elif popup["time"] - 1 <= 0:
            opacity = int(popup["time"] * 255)
            
        # Special case for specifically placed popups
        if popup["position"] is not None:
            
            # Make popup label
            label = pyglet.text.Label(popup["text"],popup["position"][0]+text_padding,popup["position"][1]+text_padding,font_size=30,batch=batch,group=label_group,color=popup["text-color"],anchor_y="bottom")
            label.opacity = opacity
            label_size = (label.content_width,label.content_height)
            
            # Make popup rect
            rect = pyglet.shapes.BorderedRectangle(popup["position"][0],popup["position"][1],label_size[0] + 2 * text_padding, label_size[1] + 2 * text_padding, batch=batch, group=rect_group,color=popup["background-color"],border_color=(0,0,0),border=3)
            rect.opacity = opacity
            rect.border_color = (0,0,0,opacity)
            
            # Add labels to list
            labels.append((rect,label))
            
            # Increment
            i += 1
            
            continue
            
        # Make popup label
        label = pyglet.text.Label(popup["text"],window_padding + text_padding,y,font_size=30,batch=batch,anchor_y="top",group=label_group,color=popup["text-color"])
        label.opacity = opacity
        label_size = (label.content_width,label.content_height)
        
        # Make popup rect
        rect = pyglet.shapes.BorderedRectangle(window_padding,y - text_padding - label_size[1],label_size[0] + 2 * text_padding, label_size[1] + 2 * text_padding, batch=batch, group=rect_group,color=popup["background-color"],border_color=(0,0,0),border=3)
        rect.opacity = opacity
        rect.border_color = (0,0,0,opacity)
        
        # Add labels to list
        labels.append((rect,label))
                
        # Move label                  
        y -= label_size[1] + 2 * text_padding + padding
        
        # Increment
        i += 1
    
    # Push labels to global
    LABELS = labels
    
    return batch

WINDOW_PADDING = settings.POPUP_WINDOW_PADDING
PADDING = settings.POPUP_PADDING
TEXT_PADDING = settings.POPUP_TEXT_PADDING
POPUP_MAX_TIME = settings.POPUP_MAX_TIME
popups:list[dict] = [{"text":"This program is using Enablr","time":0,"text-color":(0,0,0),"background-color":(255,255,255),"position":None}]
LABELS:list = [] # Holds labels and outline rectangles so python doesn't delete them
start_time = time.time()