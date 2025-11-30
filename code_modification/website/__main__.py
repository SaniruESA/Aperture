import socket
from typing import Literal
import webbrowser
from pathlib import Path

Data_Type = Literal["GET"] # List of possible data types

class DecodedData:
    
    data_type:Data_Type
    data:str
    split_data:list[str]
    tags:dict[dict]={}
    tabs:list[str]
    
    def __init__(self,data:str):
        """
        Splits the data into multiple different parts that are easier to access
        """
        
        # Ignore blank data
        if data == "":
            print("Empty packet sent")
            self.tabs = []
            self.tags = {}
            self.data = ""
            self.data_type = "GET"
            self.split_data = []
            
            return
        
        # Set data
        self.data = data
        
        # Split the data by line
        self.split_data = data.split("\n")
        
        # Get rid of HTTP version
        self.split_data[0] = self.split_data[0].replace(" HTTP/1.1\r","")
        
        # Get header
        header = self.split_data[0]
        split_header = header.split("/")
        
        # Split the start of the header
        self.data_type = split_header[0][:-1]
        
        # Get tabs
        self.tabs = split_header[1:]
        
        # Get tab count
        tab_count = len(self.tabs)
        
        # Get the tags
        if "?" in self.tabs[tab_count-1]:
            unprocessed_tags = self.tabs[tab_count-1].split("?")[1].split("&")
        else:
            unprocessed_tags = []
        
        # Get rid of tags at last tab
        self.tabs[tab_count-1] = self.tabs[tab_count-1].split("?")[0]
        
        # Get rid of blank tags
        while '' in unprocessed_tags:
            unprocessed_tags.remove('')
        
        # Get each tag
        for tag in unprocessed_tags:
            
            # Split the tag
            split_tag = tag.split("=")
            
            name = split_tag[0]
            value = split_tag[1]
            
            # Fix value characters
            value = value.replace("+"," ")
            value = value.replace(r"%3A",":")
            value = value.replace(r"%2F","/")
            value = value.replace(r"%2B","+")
            value = value.replace(r"%3F","?")
            
            # Add to tags
            self.tags[name] = value
        
    def __str__(self):
        
        return self.data
        
# Get default IP
DEFAULT_COMPUTER_IP = socket.gethostbyname(socket.gethostname())
PORT = 5739 # The port to host on

# Make server
server_socket = socket.create_server(("",PORT),family=socket.AF_INET)

# Open website
webbrowser.open(f"http://localhost:{PORT}",new=1,autoraise=True)

# Get connection to website
conn,addr = server_socket.accept()

def format_data(content:str,code:str="200 OK",type:str="text/html") -> bytes:
    """
    Formats and returns html data
    
    Arguments:
        code:
            The html return code
        content:
            The content to send
        type:
            The content type
    """
    
    # Make header
    data = f"HTTP/1.1 {code}\nContent-Length: {len(content)}\nContent-Type: {type}; charset=UTF-8\n\n{content}"
    
    return data.encode()

    
def get_html() -> DecodedData:
    """
    Gets request made by web browser to server
    """
    
    return DecodedData(conn.recv(2048).decode())

def run():
    
    # Get data
    decode_data:DecodedData = get_html()
    
    # Do process based on gotten html tag
    match decode_data.data_type:
        
        case "GET":
            
            print(decode_data)
            load_html(HTML_ROOT_PATH,decode_data)
            conn.send(format_data(HTML))
        
        case "POST":
            
            print(decode_data)
            
        case _:
            
            # Error for unhandled data types
            raise Exception(f"Unknown data type: {decode_data.data_type}")
        
    return decode_data

def load_html(path:str,decode_data:DecodedData):
    """
    Loads an HTML from path and stores in global HTML
    
    Arguments:
        path:
            The path to load from
    """
    global HTML
    
    try:
        
        # Load whilst adding the script path and current tab path
        with open(ABS_PATH+path+"/".join(decode_data.tabs)+".html","r",encoding="utf-8") as fp:
            
            HTML = fp.read()
    except:
        
        # Notify that error has occurred
        print(f"Failure to read \"{ABS_PATH+path+'/'.join(decode_data.tabs)}.html\"")
        
        # On failure, go to main page
        with open(ABS_PATH+path+"/.html","r",encoding="utf-8") as fp:
            
            HTML = fp.read()
        
    
# Get absolute path
ABS_PATH = str(Path(__file__).parent.absolute())+"/"

# Load main html
HTML_ROOT_PATH = "pages/"

while True:
    
    try:
        run()
    except:
        # On failure, make a new website server
        server_socket.close()
        
        # Make server
        server_socket = socket.create_server(("",PORT),family=socket.AF_INET)

        # Get connection to website
        conn,addr = server_socket.accept()