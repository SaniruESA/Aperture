"""
Types for settings to use (to make customization easier)
"""

from typing import Literal

Language = Literal["en", "es"]

TTS_Voice = Literal["en-US-EmmaMultilingualNeural"]


class Pixel(int):
    """
    A value of distance in pixels (integer)
    """

    pass


class RGB:
    """
    A value of color in (R,G,B) format (int,int,int)
    """

    pass
