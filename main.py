# main.py
import tkinter as tk
from ui.display import VRDisplayApp

if __name__ == "__main__":
    root = tk.Tk()
    app = VRDisplayApp(root)
    root.mainloop()