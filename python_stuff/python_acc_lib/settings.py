"""
Settings of python acc lib
"""
from .settings_types import *

# SETTINGS

# STT
LANGUAGE:Language = "en" # Language to use (Default: "en")
VOICE_ACTIVATION_KEYWORD:str = "no" # The word to use in text to activate voice assistant. This should always be lowercase (Default: "no")
VOICE_ACTIVATION_CONFIRMATION:str = "Yes?" # The word the voice assistant will respond back to confirm it is listening (Default: "Yes?")

# Window
DEFAULT_WINDOW_WIDTH:Pixel = 1920 # Default window width (Default: 1920)
DEFAULT_WINDOW_HEIGHT:Pixel = 1080 # Default window height (Default: 1080)

# Popups
POPUP_WINDOW_PADDING:Pixel = 10 # Padding from top-left of screen for popups (Default: 10)
POPUP_TEXT_PADDING:Pixel = 10 # Padding for the text within the padding (Default: 10)
POPUP_PADDING:Pixel = 5 # Padding for stacked popups next to each other (Default: 5)
POPUP_MAX_TIME:Pixel = 5 # Max time for popups to exist (Default: 5)
POPUP_DEFAULT_COLOR:RGB = (228,83,76) # Default color for popups to appear as (Default: (228,83,76))

# TTS
TTS_VOICE:TTS_Voice = "en-US-EmmaMultilingualNeural" # TTS Voice to use (Default: "en-US-EmmaMultilingualNeural") 
# Go To: https://gist.github.com/BettyJJ/17cbaa1de96235a7f5773b8690a20462 for a list of voices