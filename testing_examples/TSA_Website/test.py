import tkinter as tk
from tkinter import ttk

root = tk.Tk()
root.title("Modern Homepage")
root.geometry("900x600")
root.configure(bg="#f5f6fa")

# ---------------------------
# Modern ttk theme
# ---------------------------
style = ttk.Style()
style.theme_use("clam")

style.configure("TButton",
                font=("Segoe UI", 11),
                padding=8)
style.configure("TLabel",
                font=("Segoe UI", 11),
                background="#f5f6fa")
style.configure("Card.TFrame",
                background="white",
                relief="ridge",
                borderwidth=1)

# ---------------------------
# Navigation Bar
# ---------------------------
nav = tk.Frame(root, bg="#2d3436", height=60)
nav.pack(fill="x")

tk.Label(nav, text="MyApp Homepage",
         fg="white", bg="#2d3436",
         font=("Segoe UI", 20, "bold")).pack(side="left", padx=20)

ttk.Button(nav, text="Login").pack(side="right", padx=15, pady=10)
ttk.Button(nav, text="Sign Up").pack(side="right", padx=10, pady=10)

# ---------------------------
# Main layout
# ---------------------------
main = tk.Frame(root, bg="#f5f6fa")
main.pack(fill="both", expand=True)

# Sidebar
sidebar = tk.Frame(main, width=200, bg="#dfe6e9")
sidebar.pack(side="left", fill="y")

tk.Label(sidebar, text="Menu",
         font=("Segoe UI", 14, "bold"),
         bg="#dfe6e9").pack(pady=20)

btn_names = ["Dashboard", "Profile", "Settings", "Help", "Logout"]
for name in btn_names:
    ttk.Button(sidebar, text=name).pack(fill="x", padx=20, pady=8)

# ---------------------------
# Content Area
# ---------------------------
content = tk.Frame(main, bg="#f5f6fa")
content.pack(fill="both", expand=True, padx=20, pady=20)

header = tk.Label(content, text="Welcome to Your Dashboard",
                  font=("Segoe UI", 20, "bold"),
                  bg="#f5f6fa")
header.pack(anchor="w")

# Card-like container for form
form_card = ttk.Frame(content, style="Card.TFrame", padding=20)
form_card.pack(anchor="w", pady=20)

ttk.Label(form_card, text="Enter your name:").grid(row=0, column=0, sticky="w", pady=5)
name_entry = ttk.Entry(form_card, width=30)
name_entry.grid(row=0, column=1, padx=10, pady=5)

ttk.Label(form_card, text="Choose a plan:").grid(row=1, column=0, sticky="w", pady=5)
plan_combo = ttk.Combobox(form_card, values=["Free", "Pro", "Enterprise"], width=27)
plan_combo.grid(row=1, column=1, padx=10, pady=5)

newsletter_var = tk.BooleanVar()
ttk.Checkbutton(form_card, text="Subscribe to newsletter",
                variable=newsletter_var).grid(row=2, column=0, columnspan=2, pady=10)

ttk.Button(form_card, text="Submit").grid(row=3, column=0, columnspan=2, pady=10)

# Activity list
ttk.Label(content, text="Recent Activity",
          font=("Segoe UI", 15, "bold")).pack(anchor="w", pady=(20, 8))

activity_box = tk.Listbox(content, height=5, width=50,
                          font=("Segoe UI", 11),
                          bd=0, highlightthickness=1,
                          highlightbackground="#b2bec3")
activity_box.pack(anchor="w")

# for item in ["Logged in", "Changed password", "Viewed dashboard", "Updated profile"]:
#     activity_box.insert("end", "• " + item)

# Footer
footer = tk.Frame(root, bg="#2d3436", height=40)
footer.pack(fill="x", side="bottom")
tk.Label(footer,
         text="© 2025 MyApp — All rights reserved.",
         fg="white", bg="#2d3436",
         font=("Segoe UI", 10)).pack()

if __name__ == "__main__":
    root.mainloop()
