"""
Queries HuggingFace Model (Qwen3-Coder-30B)
with defined prompts for repository code editing.

The majority of the code editing process, when user inputs
a repository into Aperture.
"""

import os
import json
import requests
import hugging_face_auth

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

def prompt_code(code:str, prompt:str, return_code:bool=True):
    """
    Prompts code to be edited
    
    Arguments:  
        code:
            The raw code
    """

    show_code_prompt = ""
    if return_code:
        show_code_prompt = "Return a version of the initially given code with this function added. DO NOT leave out any code in the output."

    # Get the edited code
    response = query({
        "messages": [
            {
                "role":"system",
                "content":f"""Keep all of your messages as short as possible, be straight to the point and only export lines specifically requested.
                {show_code_prompt}

                RULES: {prompt}"""
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
    # print(content)
    
    # Return back code modifications
    return content

def detect_ui_elements(path:str):

    # Make prompt
    prompt = """Extract x,y,width,height, description, type, and find the <Type of UI>, <X>, <Y>, <Width>, <Height>, <Description/Text>, <Line Number of Code> for each UI element in the code.
                Only include elements that would be visible to a user, and ignore layout elements.
                Do not sort the layout elements into categories leave them only as the item that they are.
                The user will send only the original code file to be interpreted.
                Your only output should be in a JSON format following this:
                {
                    "<line number value>": {
                        "x": <the X value>,
                        "y": <the Y value>,
                        "width": <the width value>,
                        "height": <the height value>,
                        "description": <the description value>,
                        "UItype": <the Type of UI value>
                        "shown: false  // always just set to false
                    }, ... // more ui objects for each ui element
                }
                
                
                """
    
    # Load file
    with open(path,"r") as fp:
        orig = fp.read()
        
    # Analyze file with prompt (getting UI elements)
    response = prompt_code(orig, prompt, return_code=False)
    corrected_keys_json = {}

    for key, value in json.loads(response).items():
        corrected_keys_json[f"{os.path.basename(path)}_line{key}"] = value

    # print(corrected_keys_json)
    
    # Sort first response into UI_elements.json file
    # response = sort_response(response)
    
    return corrected_keys_json

def run_aperture_code(path:str):

    # Get language
    language = path.split(".")[-1]

    # Make prompt
    prompt = f"""Generate a {language} function called aperture_runner that runs either an .exe, .app, or extensionless file if the user is on Windows, Mac, or Linux, respectively.
    You must check the OS of the user during the runtime of the code to determine which one to run.
    The path of the will always be in the format "./aperture" followed by the file extension, if applicable."""

    # Load file
    with open(path,"r") as fp:
        orig = fp.read()
        
    # Analyze file with prompt (Aperture runner)
    output = prompt_code(orig, prompt)

    # Write to original file
    with open(path,"w") as fp:
        fp.write(remove_markdown(output))

def generate_server_send_function(path:str):

    # Get language
    language = path.split(".")[-1]

    # Make prompt
    prompt = f"""Generate a {language} function called server_send that does the equivalent of Python's socket.send().
    It should take in two arguments, one called content_type, one called content.
    The function should send this information in a json string formatted like: 
    <bytes_length>\n{{"type":CONTENT_TYPE,"content":CONTENT,...}}
    // where <bytes_length> is the length in bytes of the {{"type":CONTENT_TYPE,"content":CONTENT,...}} section.
    This function should use port 8080 and the user's IP address."""

    # Load file
    with open(path,"r") as fp:
        orig = fp.read()
        
    # Analyze file with prompt (Server sending function)
    output = prompt_code(orig, prompt)

    # Write to original file
    with open(path,"w") as fp:
        fp.write(remove_markdown(output))

def handle_conditional_ui(path:str, ui_elements_json:dict):

    # Make prompt
    prompt = f"""Everywhere there is a conditional showing/hiding or other logic controlling a UI element, call the server_send() function.
    The first argument should be "UI_show" and the second argument should be the key of this UI Element, found in ui_elements.json.
    You have to determine which UI element from ui_elements.json that a section of code corresponds to.

    Information in ui_elements.json:
    {ui_elements_json}
    """

    # Load file
    with open(path,"r") as fp:
        orig = fp.read()
        
    # Analyze file with prompt (detecting UI element changes)
    output = prompt_code(orig, prompt)

    # Write to original file
    with open(path,"w") as fp:
        fp.write(remove_markdown(output))

def eof_server_call(path:str):

    file_name = os.path.basename(path)

    # Make prompt
    prompt = f"""At the end of the file's execution, insert a function call for server_send()
    Put the first argument as "UI_show" and the second argument as "EOF"."""

    # Load file
    with open(path,"r") as fp:
        orig = fp.read()
        
    # Analyze file with prompt (EOF server call)
    output = prompt_code(orig, prompt)

    # Write to original file
    with open(path,"w") as fp:
        fp.write(remove_markdown(output))

def handle_alerts(path:str):

    # Make prompt
    prompt = f"""Every time the code contains a potential audio-based alert or popup, insert a function call for server_send() 
    The first argument should be "add_popup" and the second argument should be the textual content of the alert."""

    # Load file
    with open(path,"r") as fp:
        orig = fp.read()
        
    # Analyze file with prompt (EOF server call)
    output = prompt_code(orig, prompt)

    # Write to original file
    with open(path,"w") as fp:
        fp.write(remove_markdown(output))


# Other functions
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
    Takes in the original response of UI elements and sorts it
    
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

def remove_markdown(output:str):
    important = output.splitlines()[1:-2]

    separator = "\n"
    return separator.join(important)
    
# print("\n".join([str(n) for n in edit_file("../testing_examples/Tkinter/test.py")["button"]]))