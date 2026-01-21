import json

with open("../supported.json", "r", encoding="utf-8") as file:
    supported_json = json.load(file)

def insert_ui_element_calls(llm_output: str, original_path: str):

    # TSWO TASKS
    # ONE: CREATE UI ELEMENTS.JSON
    # TWO: INTERSERT SERVER CALS INTO CODE

    with open(original_path, "r", encoding="utf-8") as f:
        original = f.readlines()

    for line, i in enumerate(original):
        pass

# NEED TP UPDATE THI FNCITON
def edit_entry_point(entry_point_path: str):
    file_extension = "." + entry_point_path.split(".")[-1]

    to_insert = supported_json["languages"][file_extension]

    # TODO: add logic to not do duplicate imports
    with open(entry_point_path, "r", encoding="utf-8") as f:
        contents = f.read()
        contents = to_insert + "\n\n" + contents
    
    with open(entry_point_path, "w", encoding="utf-8") as f:
        f.write(contents)


def edit_code_test(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        code = f.read()

    modified_code = code + "1/17/26"

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(modified_code)
