import select
from ui import popup

def non_blocking_read(filepath):
    with open(filepath, 'r') as f:
        f.seek(0, 2)  # Go to end
        
        while True:
            # Check if data is ready to read (timeout=1 second)
            ready, _, _ = select.select([f], [], [], 1.0)
            
            if ready:
                line = f.readline()
                return line

line = non_blocking_read()     
if line:
    # popup
    pass

# add to server ??



