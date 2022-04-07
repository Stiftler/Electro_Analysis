# SetUp CS_Analysis_Tool

import sys
import subprocess
import pip
import tkinter as tk
from tkinter import filedialog


if __name__ == "__main__" :

    """ install standard libaries from web 
    """
    packages = ["numpy", "pandas", "matplotlib"]

    for package in packages :
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])


    """ install dm3-lib from local file (ZIP file)
    """
    link_dm3 = "https://github.com/nanobore/dm3"

    root = tk.Tk()

    label = tk.Label(master = root, text = f"Please select the ZIP file folder of the dm3 libary from {link_dm3}\nPlease download it first.", font = ("Arial", 20))
    label.grid(row = 0, column = 0)

    package = filedialog.askopenfilename(parent = root)
    
    pip.main(["install", "--upgrade", "--no-index", "--find-links=.", package])