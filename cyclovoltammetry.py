""" Cyclovoltammetry Analysis Tool by Pascal Reiß
    Version 1.0.3
"""

import os
import numpy as np
import pandas as pd
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from datetime import datetime
import matplotlib.pyplot as plt


class Cyclovoltammetry_Analysis :

    def __init__(self) :
        """ initiate Cyclovoltammetry_Analysis with the following attributes:
            - self.area_electrode
                (int/float: contains the area of the electrode in cm²)
            - self.file_paths
                (tuple: contains the file_paths of the raw data files)
            - self.path_evaluation_folder
                (string: contains the path of the evaluation folder)
            - self.save_figures
                (boolean: contains the state if created figures shall be saved automatically)
            - self.program_frame
                (tkinter.Frame: is an object required if the program is run in an GUI application)
            - self.feedback_label
                (tkinter.Label: contains Feedback for User in GUI if an execution was succesful or failed)
        """ 
        self.program_name = "Cyclovoltammetry Analysis"

        self.reset_attributes()

        self.save_figures = False

        self.program_frame = None

        self.feedback_label = None


    def reset_attributes(self) :
        """ resets all attributes for the Infrared_Analysis class object
            this function is executed once, when a new Infrared_Analysis class object is initiated
        """
        self.area_electrode = 1 # in cm²

        self.file_paths = ()

        """ create evaluation folder to save evaluated data and figures (if it does not exist yet)
            created folder is at */Evaluation/Infrared Analysis/**
             * path of this program
             ** current date in format YYYY-MM-DD
        """
        path_of_this_program = os.path.dirname(os.path.realpath(__file__))

        path_evaluation_folder = f"{path_of_this_program}\Evaluation"

        if not os.path.exists(path_evaluation_folder) :
            os.mkdir(path_evaluation_folder)

        path_evaluation_folder = f"{path_evaluation_folder}\{self.program_name}"

        if not os.path.exists(path_evaluation_folder) :
            os.mkdir(path_evaluation_folder)

        today = datetime.today().strftime("%Y-%m-%d")

        path_evaluation_folder = f"{path_evaluation_folder}\{today}"

        if not os.path.exists(path_evaluation_folder) :
            os.mkdir(path_evaluation_folder)

        self.path_evaluation_folder = path_evaluation_folder


    def open_files(self) :
        """ get selected files by User and add those to self.file_paths if files were selected 
            if no files were selected an Error Message is displayed in the self.feedback_label in the GUI
        """
        root = tk.Tk()
        file_paths = filedialog.askopenfilenames(parent = root, filetypes=[("Text files","*.txt")])
        root.destroy()

        if len(file_paths) > 0 :
            self.file_paths = file_paths
            if self.feedback_label != None :
                self.feedback_label.config(text = "Evaluation Can Now Be Started.")
        elif self.feedback_label != None :
            self.feedback_label.config(text = "Please Select Your Raw Data Files First.")


    def run_evaluation(self) :
        """ does the actual evaluation if files were selected in the firs place
        """
        if len(self.file_paths) > 0 :

            if self.feedback_label != None :
                self.feedback_label.config(text = "Evaluation in Progress.")

            """ create a figure and axis
                loop through each selected file in self.file_paths individually
            """
            fig, ax = plt.subplots()

            for file_path in self.file_paths :
                """ get the sample_name from the file_path
                """
                file_name = os.path.basename(file_path)
                sample_name = file_name.split(".txt")[0]

                """ open the files and rename columns
                    calculate the current density (mA/cm²) by the formular:
                     current density = current / area electrode
                """
                data = pd.read_csv(file_path, delimiter = ";")

                data.rename(
                    {"WE(1).Current (A)" : "current", 
                    "WE(1).Potential (V)" : "potential_we"},
                    inplace = True, axis = 1)

                data["current_density"] = data["current"] * 1000 / self.area_electrode
                """ plot the current density vs potential
                """ 
                ax.plot(data["potential_we"], data["current_density"], label = sample_name)
                
                """ drop unnecassary columns and save data DataFrame in evaluation folder 
                """
                for column in ["Potential applied (V)", "Scan", "Index", "Q+", "Q-", "Current range"] :
                    data.drop(column, axis = 1, inplace = True)

                data.to_csv(f"{self.path_evaluation_folder}\{sample_name}.txt", sep = ";", index = None, 
                    header = ["Current (A)", "Potential WE (V)", "Current Density (mA/cm²)"])

            """ add legend, x and y axis label
            """
            ax.set_xlabel("$E_{WE}$ vs Ag|AgCl [V]")
            ax.set_ylabel("j [mA/cm²)")

            ax.legend(loc = "upper left", fontsize = 8)

            """ automatically save figure if self.save_figures state True
                program counts all figures in the evaluation order and adds the count at the end of the file name
            """
            if self.save_figures :
                files_in_directory = os.listdir(self.path_evaluation_folder)

                count = 0
                for file in files_in_directory :
                    if ".jpg" in file :
                        count += 1

                fig.savefig(f"{self.path_evaluation_folder}\Cyclovoltammetry_{count}.jpg")

            """ evaluation finished
            """
            if self.feedback_label != None :
                self.feedback_label.config(text = "Evaluation Finished.")

            plt.show()


    def get_gui_frame(self, master) :
        """ returns a tkinter.Frame to a master window (tkinter.Tk)
            this frame needs to contain all necassyry widgets/functions required for the evalution
            the grid placement was chosen since it is one of the simplest and cleanest options for a clean tkinter based User Interface
        """
        self.program_frame = tk.Frame(master = master, relief = "groove", borderwidth = 2)
        self.program_frame.grid(row = 1, column = 1, padx = 5, pady = 5)

        """ create an additional tkinter.Frame acting as a control panel with access to the following functions via tkinter.Buttons
            - self.open_files
                get file_paths from selected files by User
            - self.run_evaluation
                executes the evaluation

            create a tkinter.Label acting as a feedback label for Error Messages for the User
        """
        control_frame = tk.Frame(master = self.program_frame, relief = "groove", borderwidth = 2)
        control_frame.grid(row = 0, column = 0, padx = 5, pady = 5)

        open_files_button = tk.Button(master = control_frame, text = "Open Files", command = self.open_files)
        open_files_button.grid(row = 0, column = 0, padx = 5, pady = 5)

        run_evaluation_button = tk.Button(master = control_frame, text = "Start Evaluation", command = self.run_evaluation) 
        run_evaluation_button.grid(row = 0, column = 2, padx = 5, pady = 5)

        self.feedback_label = tk.Label(master = control_frame, text = "Please Select Your Raw Data Files First.", font = "Arial")
        self.feedback_label.grid(row = 0, column = 1, padx = 5, pady = 5)

        """ create a tkinter.ttk.Checkbutton, which contains the state of the self.save_figures
            it controls if created figures are saved automatically
            default state: False
        """
        def change_figure_saving_settings() :
            settings = {"0" : False, "1" : True}
            setting = save_figures_variable.get()

            self.save_figures = settings[setting]

        save_figures_variable = tk.StringVar()
        save_figures_checkbox = ttk.Checkbutton(master = control_frame, text = "automatically save figures",
            variable = save_figures_variable, command = change_figure_saving_settings)
        save_figures_checkbox.grid(row = 3, column = 0, padx = 5, pady = 5)

        """ create a tkinter.Entry for changing area electrode by User Input 
            valid inputs are int/float
            create a tkinter.Button for User to enter his/her entries for the new changed area of the electrode

            feedback if the input was succesful or failed are displayed in self.feedback_label
        """

        def change_area_electrode() :
            entry = change_area_electrode_entry.get()

            if entry != "" :
                entry = entry.replace(",", ".")

                try :
                    entry = float(entry)
                    self.area_electrode = entry
                    self.feedback_label.config(text = f"Set Area Electrode to {self.area_electrode}")
                except ValueError :
                    self.feedback_label.config(text = "Changing Area Electrode Failed. Please Enter a valid Input.")

        change_area_electrode_entry = tk.Entry(master = control_frame)
        change_area_electrode_entry.grid(row = 1, column = 0, padx = 5, pady = 5)

        change_area_electrode_button = tk.Button(master = control_frame, text = "Change Area Electrode (cm²)", command = change_area_electrode)
        change_area_electrode_button.grid(row = 2, column = 0, padx = 5, pady = 5)

        return self.program_frame





if __name__ == "__main__" :

    cv = Cyclovoltammetry_Analysis()

    cv.open_files()

    cv.area_electrode = 0.071 # debugging with given raw data files by Jonas

    cv.run_evaluation()


""" made by Stiftler (Pascal Reiß)
"""

"""
update list: 
Version 1.0.2 

- update list didn´t exist yet 

Version 1.0.3 (28.03.2022)
- added filetypes argument for tkinter.filedialog.askopenfilenames function to show only necessary files for the program
  in this case: ["Text Files", "*.txt"]
"""