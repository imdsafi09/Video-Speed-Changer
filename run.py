import os
import platform
import tkinter as tk
from speed_changer.app import VideoSpeedGUI

def main():
    root = tk.Tk()

    # Set icon from assets folder
    base_dir = os.path.dirname(__file__)
    icon_png = os.path.join(base_dir, "speed_changer", "assets", "app_icon.png")
    icon_ico = os.path.join(base_dir, "speed_changer", "assets", "app_icon.ico")

    if platform.system() == "Windows" and os.path.exists(icon_ico):
        root.iconbitmap(icon_ico)
    elif os.path.exists(icon_png):
        root.iconphoto(True, tk.PhotoImage(file=icon_png))

    app = VideoSpeedGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
