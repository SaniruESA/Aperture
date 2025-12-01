import tkinter as tk
from tkinter import ttk
from test import root    # your UI file without auto mainloop

def find_all_widgets(parent):
    widgets = parent.winfo_children()
    for w in widgets:
        widgets += find_all_widgets(w)
    return widgets

def is_button(widget):
    return isinstance(widget, (tk.Button, ttk.Button))

def extract_coordinates():
    root.update_idletasks()
    root.update()

    # Offset caused by border + title bar
    offset_x = root.winfo_rootx() - root.winfo_x()
    offset_y = root.winfo_rooty() - root.winfo_y()

    widgets = find_all_widgets(root)

    print("\n--- TRUE BUTTON COORDINATES (WINDOW-RELATIVE) ---\n")

    for w in widgets:
        if is_button(w):
            # Convert absolute → window-relative
            x = w.winfo_rootx() - offset_x
            y = w.winfo_rooty() - offset_y
            width = w.winfo_width()
            height = w.winfo_height()
            text = w.cget("text") or "unnamed"

            print(f"easy_client.add_button([{x}, {y}, {width}, {height}], "
                  f"\"{text} button\")")

    print("\n--- DONE ---\n")

root.after(3000, extract_coordinates)
root.mainloop()
