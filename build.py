# --- main window ---
root = tk.Tk()
root.title("Mock Homepage")
root.geometry("900x600")

# --- top navigation bar ---
nav = tk.Frame(root, bg="#2c3e50", height=60)
nav.pack(fill="x")

tk.Label(nav, text="MyApp Homepage", fg="white", bg="#2c3e50",
         font=("Arial", 20, "bold")).pack(side="left", padx=20)

tk.Button(nav, text="Login", bg="#34495e", fg="white").pack(side="right", padx=10)
tk.Button(nav, text="Sign Up", bg="#1abc9c", fg="white").pack(side="right", padx=10)

# --- main content ---
main = tk.Frame(root)
main.pack(fill="both", expand=True)

# --- sidebar ---
sidebar = tk.Frame(main, width=200, bg="#ecf0f1")
sidebar.pack(side="left", fill="y")

tk.Label(sidebar, text="Menu", bg="#ecf0f1",
         font=("Arial", 14, "bold")).pack(pady=10)

buttons = ["Dashboard", "Profile", "Settings", "Help", "Logout"]
for b in buttons:
    tk.Button(sidebar, text=b).pack(fill="x", padx=10, pady=5)

# --- content area ---
content = tk.Frame(main, bg="white")
content.pack(side="left", fill="both", expand=True, padx=10, pady=10)

# Section title
tk.Label(content, text="Welcome to Your Dashboard", bg="white",
         font=("Arial", 18, "bold")).pack(anchor="w")

# --- random UI elements ---
form_frame = tk.Frame(content, bg="white")
form_frame.pack(pady=20, anchor="w")

# Name entry
tk.Label(form_frame, text="Enter your name:", bg="white").grid(row=0, column=0, sticky="w")
name_entry = tk.Entry(form_frame, width=30)
name_entry.grid(row=0, column=1, padx=10)

# Choose option
tk.Label(form_frame, text="Choose a plan:", bg="white").grid(row=1, column=0, sticky="w", pady=5)
plan_combo = ttk.Combobox(form_frame, values=["Free", "Pro", "Enterprise"], width=27)
plan_combo.grid(row=1, column=1, padx=10)

# Checkbox
newsletter_var = tk.BooleanVar()
tk.Checkbutton(form_frame, text="Subscribe to newsletter",
               variable=newsletter_var, bg="white").grid(row=2, column=0, sticky="w", pady=5)

# Submit button
tk.Button(form_frame, text="Submit", bg="#3498db", fg="white").grid(row=3, column=0, columnspan=2, pady=10)

# --- image placeholder ---
img_frame = tk.Frame(content, bg="#bdc3c7", width=300, height=150)
img_frame.pack(pady=10)
tk.Label(img_frame, text="[ Image Placeholder ]", bg="#bdc3c7").place(relx=0.5, rely=0.5, anchor="center")

# --- listbox ---
tk.Label(content, text="Recent Activity", bg="white",
         font=("Arial", 14, "bold")).pack(anchor="w", pady=(20, 5))

activity_list = tk.Listbox(content, height=5, width=50)
activity_list.pack(anchor="w")
for item in ["Logged in", "Changed password", "Viewed dashboard", "Updated