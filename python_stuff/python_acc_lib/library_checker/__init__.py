"""
Ensures libraries exist before importing them
"""
import os
import subprocess
from ..logger.basic_logs import *

def install_pip():
    """
    Ensures pip exists and is updated
    """
    
    # Run update / install command
    os.system("python3 -m ensurepip --upgrade")

# Install queue
PIP_MUST_INSTALL = {}

# Module list
MODULE_LIST = ""

def get_version(library_pip:str):
    """
    Gets the version number of a library from pip
    """
    
    # Run pip show library
    process = subprocess.run(f"pip show {library_pip}",capture_output=True)
    
    # Split the output by lines
    stdout = process.stdout.split(b"\r\n")
    
    # Read each line
    for line in stdout:
        
        # Find version line
        if b"Version" in line:
            return str(line,"utf-8").replace("Version: ","")

def check_library(library_name:str,library_pip:str,version:str=""):
    """
    Makes sure a library exists before importing
    
    Arguments:
        library_name:
            The directory name of the library (what you use to import it)
        library_pip:
            The pip name of the library
        version:
            The version of the library
    """
    global PIP_MUST_INSTALL,MODULE_LIST
    
    # Add to MODULE_LIST
    MODULE_LIST += f"{library_name}{":" if version != "" else ""} {version}\n"
    
    # Try to import
    try:
        
        # Check for library
        info(f"Checking presence: {library_name}",__name__)
        __import__(library_name)
        info(f"Found!: {library_name}",__name__)
        
        # Only check if version is specified in call
        if version != "":
            lib_version = get_version(library_pip)
            
            # Check if version is correct
            if lib_version != version:
                
                # Notify and add to queue
                warn(f"Version: {lib_version} (Incorrect)",__name__)
                PIP_MUST_INSTALL[library_pip] = version
            else:
                
                # Notify that version is corect
                info(f"Version: {lib_version} (Correct)",__name__)
        
    # On failure, queue download
    except ModuleNotFoundError:
        
        warn("Module not found",__name__)
        PIP_MUST_INSTALL[library_pip] = version
    
    # Unknown error, queue download as well
    except Exception as e:
        
        error(f"Module version check failed: {e}")
        PIP_MUST_INSTALL[library_pip] = version
    
        
def install_all():
    """
    Clears the queue of libraries to install and installs them all
    """
    
    # Skip if everything is installed
    if len(PIP_MUST_INSTALL) == 0:
        
        info("No modules needed to download",__name__)
        
        # Print final message
        info(f"\n\nAll modules verified\n{MODULE_LIST}",__name__)
    
        return
        
    # Get packages formatted to install
    package_install:str = ""
    
    for package in PIP_MUST_INSTALL:
        
        #  Get package version
        version = PIP_MUST_INSTALL[package]
        
        # If version specified, download that version
        if version != "":
            
            package_install += f"{package}=={version} "
        
        # Otherwise install latest
        else:
            package_install += f"{package} "
    
    # Run install command (Making sure it works either way)
    os.system(f"pip install {package_install} --break-system-packages")
    
    # Print final message
    info(f"\n\nAll modules verified\n{MODULE_LIST}",__name__)