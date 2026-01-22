# How to user PyInstaller

1. Run pyinstaller in command propmt of the root directory
    * If you get an error about enum34 run `pip uninstall enum34`
    * If it isn't installed use `pip install pyinstaller`
    * If you get a help menu, continue
2. Run pyinstaller with this command
    > pyinstaller aperture.py --onefile -w
    * The -w removes the terminal
3. Wait (be patient mg)
4. Check dist
5. Delete dist and build after you're done (they are already in .gitignore)
