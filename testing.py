import pyglet
from pyglet.window import mouse

window = pyglet.window.Window(900, 600, caption="Login", resizable=True)

# -----------------------------
# State
# -----------------------------
active_field = None
email_text = ""
password_text = ""
message = ""

# Coordinates (will be set dynamically)
coords = {}


def compute_layout(width, height):
    """Recalculate UI positions based on window size."""
    cx = width // 2

    coords["title_y"] = height - 120
    coords["email_y"] = height - 200
    coords["password_y"] = height - 260
    coords["button_y"] = height - 340

    # Box width scales slightly with window width
    coords["box_width"] = min(400, int(width * 0.4))

    coords["box_x"] = cx - coords["box_width"] // 2
    coords["button_x"] = cx - 70  # button is 140px wide


# Initialize default positions
compute_layout(window.width, window.height)


# -----------------------------
# Drawing labels (dynamic position)
# -----------------------------
def draw_labels():
    pyglet.text.Label(
        "Login",
        font_size=32,
        x=window.width // 2,
        y=coords["title_y"],
        anchor_x="center"
    ).draw()

    pyglet.text.Label("Email:", font_size=16,
                      x=coords["box_x"], y=coords["email_y"] + 10).draw()

    pyglet.text.Label("Password:", font_size=16,
                      x=coords["box_x"], y=coords["password_y"] + 10).draw()

    pyglet.text.Label(
        message,
        font_size=16,
        x=window.width // 2,
        y=coords["button_y"] - 40,
        anchor_x="center",
        color=(255, 60, 60, 255)
    ).draw()


# -----------------------------
# Draw text inputs
# -----------------------------
def draw_text_inputs():
    email_input = pyglet.text.Label(
        email_text,
        font_size=16,
        x=coords["box_x"] + 5,
        y=coords["email_y"] + 5,
        color=(0, 0, 0, 255)
    )

    password_hidden = "*" * len(password_text)
    password_input = pyglet.text.Label(
        password_hidden,
        font_size=16,
        x=coords["box_x"] + 5,
        y=coords["password_y"] + 5,
        color=(0, 0, 0, 255)
    )

    email_input.draw()
    password_input.draw()


# -----------------------------
# Drawing boxes + button
# -----------------------------
def draw_boxes():
    w = coords["box_width"]
    x = coords["box_x"]

    # Input rectangles
    pyglet.shapes.Rectangle(x, coords["email_y"], w, 32, color=(230, 230, 230)).draw()
    pyglet.shapes.Rectangle(x, coords["password_y"], w, 32, color=(230, 230, 230)).draw()

    # Login button
    pyglet.shapes.Rectangle(
        coords["button_x"], coords["button_y"], 140, 40, color=(100, 150, 255)
    ).draw()

    pyglet.text.Label(
        "Login",
        font_size=16,
        x=coords["button_x"] + 70,
        y=coords["button_y"] + 12,
        anchor_x="center",
    ).draw()


# -----------------------------
# Main draw event
# -----------------------------
@window.event
def on_draw():
    window.clear()

    draw_labels()
    draw_boxes()
    draw_text_inputs()


# -----------------------------
# Handle resizing (IMPORTANT)
# -----------------------------
@window.event
def on_resize(width, height):
    compute_layout(width, height)


# -----------------------------
# Mouse click detection
# -----------------------------
@window.event
def on_mouse_press(x, y, button, modifiers):
    global active_field, message

    if button == mouse.LEFT:

        # Email box
        if coords["box_x"] <= x <= coords["box_x"] + coords["box_width"] and \
                coords["email_y"] <= y <= coords["email_y"] + 32:
            active_field = "email"
            message = ""
            return

        # Password box
        if coords["box_x"] <= x <= coords["box_x"] + coords["box_width"] and \
                coords["password_y"] <= y <= coords["password_y"] + 32:
            active_field = "password"
            message = ""
            return

        # Login button
        if coords["button_x"] <= x <= coords["button_x"] + 140 and \
                coords["button_y"] <= y <= coords["button_y"] + 40:

            if "@" not in email_text:
                message = "Invalid email"
            else:
                message = "Login successful!"


# -----------------------------
# Keyboard input
# -----------------------------
@window.event
def on_text(text):
    global email_text, password_text

    if active_field == "email":
        email_text += text
    elif active_field == "password":
        password_text += text


@window.event
def on_key_press(symbol, modifiers):
    global email_text, password_text

    # Backspace
    if symbol == pyglet.window.key.BACKSPACE:
        if active_field == "email":
            email_text = email_text[:-1]
        elif active_field == "password":
            password_text = password_text[:-1]


pyglet.app.run()
