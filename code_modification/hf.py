import os
import requests
import hugging_face_auth

# Get headers and URL
# Get headers and URL
API_URL = "https://router.huggingface.co/v1/chat/completions"
HEADER = {
    "Authorization": f"Bearer {hugging_face_auth.get_token_pipeline()}",
}

def query(payload:dict):
    """
    Requests output from huggingface servers
    
    Arguments:
        payload the JSON payload to POST
    """
    response = requests.post(API_URL, headers=HEADER, json=payload)
    return response.json()

def prompt_code(code:str):
    """
    Prompts code to be edited
    
    Arguments:  
        code:
            The raw code
    """

    # Get the edited code
    response = query({
        "messages": [
            {
                "role":"system",
                "content":"Keep all of your messages as short as possible, be straight to the point and only export lines specifically requested\n\nRULES: Extract x,y,width,height, description, type, and write out the line <Type of UI>, <X>, <Y>, <Width>, <Height>, <Description/Text>, <Line Number of Code> for each UI element in the code.\nOnly include elements that would be visible to a user, and ignore layout elements.\nDo not sort the layout elements into categories leave them only as the item that they are\nThe user will send only the original code file to be interpreted"
            },
            {
                "role": "user",
                "content": code
            }
        ],
        "model": "Qwen/Qwen3-Coder-30B-A3B-Instruct:scaleway"
    })

    # Get the content of the response
    content = response["choices"][0]["message"]["content"]
    
    print(content)
    
    # Return back code modifications
    return content

def edit_file(path:str):
    """
    Loads and builds a file from path
    
    Arguments:
        path:
            The original path of the code
    """
    
    # Load file
    with open(path,"r") as fp:
        
        orig = fp.read()
        
    # Edit file
    response = prompt_code(orig)
    
    # Remove all unnecessary items
    response = sort_response(response)
    
    return response

class Item:
    ui_type:str
    x:int
    y:int
    width:int
    height:int
    text:str
    line_num:int
    def __init__(self,**kwargs):
        for kwarg in kwargs:
            setattr(self,kwarg,kwargs[kwarg])
            
    def __str__(self):
        
        return f"Type: {self.ui_type} X: {self.x} Y: {self.y} Width: {self.width} Height: {self.height} Text: {self.text} Line Num: {self.line_num}"
    
    def __repr__(self):
        
        return self.__str__()

def split_item(item:str) -> Item:
    """
    Takes a single item and splits it into the individual components
    
    Arguments:
        item:
            The original item
    """

    # <Type of UI>, <X>, <Y>, <Width>, <Height>, <Description/Text>, <Line Number of Code>
    separated = [item for item in item.split(",")]
    
    # Format
    return Item(ui_type=separated[0].strip(" <>").lower(),x=int(separated[1]),y=int(separated[2]),width=int(separated[3]),height=int(separated[4]),text=", ".join(separated[5:-1]),line_num=int(separated[-1]))

def sort_response(original_content:str) -> dict:
    """
    Takes in the original response and sorts it
    
    Arguments:
        original_content:
            The original response from the AI
    """
    
    cat:dict[str,list[Item]] = {}
    
    # Sort into categories
    for line in original_content.splitlines():
        
        # Make into an item object
        new_item = split_item(line)
        
        # Sort items into categories
        
        # Add missing categories
        ui_type = new_item.ui_type
        if ui_type not in cat:
            cat[ui_type] = []
            
        # Add item
        cat[ui_type].append(new_item)
        
    # Return final
    return cat
    
print("\n".join([str(n) for n in edit_file("../testing_examples/Tkinter/test.py")["button"]]))