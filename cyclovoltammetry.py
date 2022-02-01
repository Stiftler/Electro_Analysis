""" Cyclovoltammetry Analysis Tool by Pascal Reiß
    Version 1.0.1 
"""

import os
import numpy as np
import pandas as pd
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from datetime import datetime
import matplotlib.pyplot as plt


class Cyclovoltammetry :

    def __init__(self) :

        self.program_name = "Cyclovoltammetry Analysis"

        self.reset_attributes()

        self.save_figures = False

        self.program_frame = None

        self.feedback_label = None


    def reset_attributes(self) :

        self.area_electrode = 1 # in cm²

        self.file_paths = ()

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
        root = tk.Tk()

        file_paths = filedialog.askopenfilenames(parent = root)

        root.destroy()

        if len(file_paths) > 0 :
            self.file_paths = file_paths
            if self.feedback_label != None :
                self.feedback_label.config(text = "Evaluation Can Now Be Started.")
        elif self.feedback_label != None :
            self.feedback_label.config(text = "Please Select Your Raw Data Files First.")


    def run_evaluation(self) :

        if len(self.file_paths) > 0 :

            if self.feedback_label != None :
                self.feedback_label.config(text = "Evaluation in Progress.")

            fig, ax = plt.subplots()

            for file_path in self.file_paths :

                file_name = os.path.basename(file_path)
                sample_name = file_name.split(".txt")[0]

                data = pd.read_csv(file_path, delimiter = ";")

                data.rename(
                    {"WE(1).Current (A)" : "current", 
                    "WE(1).Potential (V)" : "potential_we"},
                    inplace = True, axis = 1)

                data["current_density"] = data["current"] * 1000 / self.area_electrode
                
                ax.plot(data["potential_we"], data["current_density"], label = sample_name)
                
                for column in ["Potential applied (V)", "Scan", "Index", "Q+", "Q-", "Current range"] :
                    data.drop(column, axis = 1, inplace = True)

                data.to_csv(f"{self.path_evaluation_folder}\{sample_name}.txt", sep = ";", index = None, 
                    header = ["Current (A)", "Potential WE (V)", "Current Density (mA/cm²)"])

            ax.set_xlabel("$E_{WE}$ vs Ag|AgCl [V]")
            ax.set_ylabel("j [mA/cm²)")

            ax.legend(loc = "upper left", fontsize = 8)

            if self.save_figures :
                files_in_directory = os.listdir(self.path_evaluation_folder)

                count = 0
                for file in files_in_directory :
                    if ".jpg" in file :
                        count += 1

                fig.savefig(f"{self.path_evaluation_folder}\Cyclovoltammetry_{count}.jpg")

            if self.feedback_label != None :
                self.feedback_label.config(text = "Evaluation Finished.")
            

            plt.show()


    def get_gui_frame(self, master) :

        self.program_frame = tk.Frame(master = master, relief = "groove", borderwidth = 2)
        self.program_frame.grid(row = 1, column = 1, padx = 5, pady = 5)

        control_frame = tk.Frame(master = self.program_frame, relief = "groove", borderwidth = 2)
        control_frame.grid(row = 0, column = 0, padx = 5, pady = 5)

        open_files_button = tk.Button(master = control_frame, text = "Open Files", command = self.open_files)
        open_files_button.grid(row = 0, column = 0, padx = 5, pady = 5)

        run_evaluation_button = tk.Button(master = control_frame, text = "Start Evaluation", command = self.run_evaluation) 
        run_evaluation_button.grid(row = 0, column = 2, padx = 5, pady = 5)

        self.feedback_label = tk.Label(master = control_frame, text = "Please Select Your Raw Data Files First.", font = "Arial")
        self.feedback_label.grid(row = 0, column = 1, padx = 5, pady = 5)

        def change_figure_saving_settings() :
            settings = {"0" : False, "1" : True}
            setting = save_figures_variable.get()

            self.save_figures = settings[setting]

        save_figures_variable = tk.StringVar()

        save_figures_checkbox = ttk.Checkbutton(master = control_frame, text = "automatically save figures",
            variable = save_figures_variable, command = change_figure_saving_settings)
        save_figures_checkbox.grid(row = 3, column = 0, padx = 5, pady = 5)

        """ add entry for changing area electrode """

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

    cv = Cyclovoltammetry()

    cv.open_files()

    cv.area_electrode = 0.071 # debugging with given raw data files by Jonas

    cv.run_evaluation()