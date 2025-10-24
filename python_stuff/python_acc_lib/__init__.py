"""
Base library
Checks that all libraries and installed and of the correct version
"""
from . import library_checker
from .logger.basic_logs import *

def verify_lib():
    """
    Checks and downloads all libraries
    """
    
    # Log info message
    info("Checking libraries",__name__)
    
    # Check libraries
    library_checker.check_library("edge_tts","edge-tts","7.2.0")
    library_checker.check_library("pyglet","pyglet","2.1.8")
    library_checker.check_library("pygame","pygame","2.6.1")
    
    # Download libraries
    library_checker.install_all()