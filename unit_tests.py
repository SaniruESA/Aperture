"""
Tests various methods found within aperture in order to ensure they all work correctly between the client and server
"""

import aperture_library.server as server
import aperture_library.logger as logger
from aperture_library.logger.basic_logs import debug, error, info
import aperture_library.server.easy_client as client
import aperture_library.ui.popup as popup
import threading
import time
import os

# The loaded server
SERVER: server.Server = None

# Statistic about tests
TOTAL_TESTS = 0
TOTAL_PASS = 0
TESTS = []
TOTAL_TIME = 0


def test_stats():
    """
    Prints out final statistics for all tests
    """

    print("\n\nTests\n------------------\n")

    for test in TESTS:

        print(
            f"{("\x1b[32m" if test["pass"] else "\x1b[31m")}{test["name"]}: {("Passed" if test["pass"] else "Fail")} ({test["time"]} ms)\x1b[0m"
        )

    print("------------------")
    print(
        f"{"\x1b[33m" if TOTAL_PASS < TOTAL_TESTS else "\x1b[32m"}({TOTAL_PASS}/{TOTAL_TESTS}) Passed ({TOTAL_TIME} ms)"
    )


def test(func):
    """
    Makes test logging more verbose
    """

    def test_func():
        """
        A single test
        """
        global TOTAL_TESTS, TOTAL_PASS, TESTS, TOTAL_TIME

        # Verbose test logging
        start = time.time()
        debug(f"Starting test: {func.__name__}", __name__)
        TOTAL_TESTS += 1
        test_stats = {"name": func.__name__, "pass": False, "time":-1}

        try:
            debug(f"\x1b[32mTest ({func.__name__}) passed: {func()} ({(time.time()-start)*1000} ms)", __name__)
            end = time.time()
            test_stats["pass"] = True
            test_stats["time"] = (end-start) * 1000
            TOTAL_PASS += 1
            TOTAL_TIME += test_stats["time"]
        except AssertionError as e:
            error(f"Test failed due to assertion: {e}", __name__)
        except Exception as e:
            error(f"Test failed due to unknown reason: {e}", __name__)
        print("\x1b[0m")
        TESTS.append(test_stats)

    return test_func

@test
def test_speed():
    """
    Test server speed
    """
    
    response = client.help()
    
    debug(response, __name__)

@test
def test_1_button():
    """
    Tests adding a single button
    """

    # Add button
    response = client.add_button([0, 0, 50, 50], "test button")

    debug(response, __name__)

    # Check for the correct element
    elements = SERVER.keyboardtab.getUIElements()["button"]

    for element in elements:

        if element["rect"] == [0, 0, 50, 50] and element["ariaText"] == "test button":

            return f"Element {element} found"

    assert False, "Added element was not found"


@test
def test_2_button():
    """
    Checks for created mp3 for button
    """

    # Wait for some time for mp3 to be generated
    time.sleep(5)

    # Check if file in list
    audio_files = os.listdir("temp/")

    assert "output_test button.mp3" in audio_files, "Test button not found in files"

    return "Test button has been found"


@test
def test_3_clear():
    """
    Checks clearing all items
    """

    # Clear items
    response = client.clear_button()

    # Check for items
    debug(response, __name__)

    elements = SERVER.keyboardtab.getUIElements()["button"]

    # Ensure no items
    if len(elements) > 0:
        assert False, f"Items found within elements: {elements}"
    return "No items found after clear"


@test
def test_4_popup():
    """
    Checks adding a popup
    """

    # Add popup
    response = client.add_popup("Hello, World!", (255, 0, 0), (0, 255, 0))

    debug(response, __name__)

    # Check for items
    elements = popup.popups

    for element in elements:

        if (
            element["text"] == "Hello, World!"
            and element["text-color"] == [0, 255, 0]
            and element["background-color"] == [255, 0, 0]
            and element["position"] is None
        ):

            return f"Element {element} found"

    assert False, "Added element was not found"


@test
def test_5_popup():
    """
    Checks the popup removal after time
    """

    # Wait for popup
    time.sleep(10)

    # Check for items
    elements = popup.popups

    # Ensure no items
    if len(elements) > 0:
        assert False, f"Items found within elements: {elements}"
    return "No items found after time"


def test_runner():
    """
    Generates a client and runs all tests
    """
    global SERVER

    # Connect a client
    while not client.client_exists():
        try:
            client.generate_client()
        except Exception:
            pass

    # Wait and get global server
    SERVER = server.MAIN_SERVER
    while SERVER is None:
        info("Attempting to find server", __name__)
        SERVER = server.MAIN_SERVER
        time.sleep(1)

    # Run tests
    test_speed()
    test_1_button()
    test_2_button()
    test_3_clear()
    test_4_popup()
    test_5_popup()

    # Print stats
    test_stats()

    # End program
    client.exit()
    quit()


if __name__ == "__main__":

    # Start the server
    logger.set_stdout()
    logger.clear()
    print("\x1b[2J\x1b[HServer Starting...", end="")

    # Open thread for client
    client_thread = threading.Thread(target=test_runner, daemon=True)
    client_thread.start()

    server.fast_start()
