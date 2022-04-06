""" Infrared Analysis Tool by Pascal Reiß
    Version 1.0.3
"""

import tkinter as tk
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from tkinter import filedialog
from tkinter import ttk
from datetime import datetime
from matplotlib.widgets import SpanSelector

class Infrared_Analysis :

    def __init__(self) :
        """ initiate Infrared_Analysis class with the following attributes:
            - self.save_figures
                (boolean: contains the state if the User wants to save the created figures automatically
                default state: False)
            - self.file_paths
                (tuple: contains the file_paths of the selected raw data files by the User)
            - self.local_min_threshold
                (float: value between 0 and 1
                sets the threshold for the automatic local minima determination
                default setting: 0.4)
            - self.path_evaluation_folder
                (string: contains the path of the evalution folder)
            - self.program_frame
                (tkinter.Frame: is an object required in the GUI if a GUI is desired in a seperate program)
            - self.feedback_label 
                (tkinter.Label: contains Feedback for the User if a process was succesful or failed)
            - self.local_min_setting
                (boolean: state if local minima shall be determined automatically
                default state: False)
            - self.local_min_frame
                (tkinter.Frame: is an object required in the self.program_frame if the User wants to determine the local minima automatically)
        """

        """ set up basic attributes required for the Infrared_Analysis
        """
        self.program_name = "Infrared Analysis"

        self.save_figures = False

        self.reset_attributes()

        self.program_frame = None

        self.feedback_label = None

        self.local_min_setting = False

        self.local_min_frame = None     


    def reset_attributes(self) :
        """ resets all atttributes for the Infrared_Analysis class object 
            this function is executed once when a new Infrared_Analysis class object is initiated 
        """
        self.file_paths = ()

        """ create evaluation folder to save evaluated data and figures (if it does not exist yet)
            created folder is at */Evaluation/Infrared Analysis/**
             * path of this program
             ** current date in format YYYY-MM-DD
        """
        path_of_this_program = os.path.dirname(os.path.realpath(__file__))

        path_evaluation_folder = f"{path_of_this_program}\Evaluation"

        today = datetime.today().strftime("%Y-%m-%d")

        if not os.path.exists(path_evaluation_folder) :
            os.mkdir(path_evaluation_folder)

        path_evaluation_folder = f"{path_evaluation_folder}\{self.program_name}"

        if not os.path.exists(path_evaluation_folder) :
            os.mkdir(path_evaluation_folder)

        path_evaluation_folder = f"{path_evaluation_folder}\{today}"

        if not os.path.exists(path_evaluation_folder) :
            os.mkdir(path_evaluation_folder)

        self.path_evaluation_folder = path_evaluation_folder

        self.local_min_threshold = 0.4


    def get_gui_frame(self, master) :
        """ returns a tkinter.Frame to a master window (tkinter.Tk)
            this frame needs to contain all necassyry widgets/functions required for the evalution
            the grid placement was chosen since it is one of the simplest and cleanest options for a clean tkinter based User Interface
        """
        self.program_frame = tk.Frame(master = master, relief = "groove", borderwidth = 2)
        self.program_frame.grid(row = 0, column = 1, padx = 5, pady = 5, rowspan= 5)

        """ create an additional tkinter.Frame acting as a control panel with access to the following functions via tkinter.Buttons
            - self.open_files
                get file_paths from selected files by User
            - self.run_evaluation
                executes the evaluation

            create a tkinter.Label acting as a Feedback Label for Error Messages for the User
        """
        control_frame = tk.Frame(master = self.program_frame, relief = "groove", borderwidth = 2)
        control_frame.grid(row = 0, column = 0, padx =5, pady = 5)

        open_files_button = tk.Button(master = control_frame, text = "Open Files", command = self.open_files)
        open_files_button.grid(row = 0, column = 0, padx = 5, pady = 5)

        run_evaluation_button = tk.Button(master = control_frame, text = "Run Evaluation", command = self.run_evaluation)
        run_evaluation_button.grid(row = 0, column = 2, padx = 5, pady = 5)

        self.feedback_label = tk.Label(master = control_frame, text = "Please Select Your Raw Data First.", font = "Arial")
        self.feedback_label.grid(row = 0, column = 1, padx = 5, pady = 5)

        """ create a tkinter.tkk.Checkbutton, which contains the state of the self.save_figures
            it controls if created figures are saved automatically
            default state: False 
        """
        def change_figure_saving_settings() :
            settings = {"1" : True, "0" : False, "" : True}
            setting = save_figures_variable.get()


            self.save_figures = settings[setting]

            if __name__ != "__main__" :
                save_figures_variable.set(value = "0" if setting in ["", "1"] else "1")


        save_figures_variable = tk.StringVar(value = "1" if __name__ != "__main__" else "0")
        save_figures_checkbox = ttk.Checkbutton(control_frame, text = "automatically save figures", \
            variable = save_figures_variable, command = change_figure_saving_settings)
        save_figures_checkbox.grid(row = 1, column = 0, padx = 5, pady = 5)

        def change_local_min_settings() :
            settings = {"1" : True, "0" : False, "" : True}
            setting = local_min_variable.get()

            self.local_min_setting = settings[setting]
            if settings[setting] :
                local_min_frame.grid(row = 1, column = 0, padx = 5, pady = 5)
            else :
                local_min_frame.grid_forget()

            if __name__ != "__main__" :
                local_min_variable.set(value = "0" if setting in ["", "1"] else "1")

            
        """ create a tkinter.tkk.Checkbutton, which contains the state of the self.local_min_setting
            it controls if local minima positons shall be determined automatically
            default state: False 
        """
        local_min_variable = tk.StringVar(value = "1" if __name__ != "__main__" else "0")

        print(local_min_variable.get())
        local_min_checkbox = ttk.Checkbutton(control_frame, text = "automatic local minimas",
            variable = local_min_variable, command = change_local_min_settings)
        local_min_checkbox.grid(row = 2, column = 0, padx = 5, pady = 5)

        """ create a tkinter.Frame, which contains
            - tkinter.Labels
                displaying the currently set local minima treshold
            - tkinter.Entry
                enabling entering new local minima tresholds
                valid inputs are float in the range between 0 and 1
            - tkinter.Button
                with access to change self.local_min_treshold
        """
        local_min_frame = tk.Frame(self.program_frame, relief = "groove", borderwidth = 2)

        local_min_label = tk.Label(local_min_frame, text = "Please Enter A Treshold for the\nAutomatic Local Minima Determination", font = ("Arial", 10))
        local_min_label.grid(row = 0, column = 0, padx = 5, pady = 5)

        local_min_label = tk.Label(local_min_frame, text = f"Current Threshold: {self.local_min_threshold}")
        local_min_label.grid(row = 1, column = 0, padx = 5, pady = 5)

        local_min_entry = tk.Entry(local_min_frame)
        local_min_entry.grid(row = 1, column = 1, padx = 5, pady = 5)

        def set_local_min() :
            entry = local_min_entry.get()

            if entry != "" :
                entry = entry.replace(",", ".")
                try :
                    entry = float(entry)
                    success = True
                except ValueError :
                    success = False

                if success and entry > 0 and entry < 1 :
                    self.local_min_threshold = entry
                    
                    local_min_label.config(text = f"Current Threshold: {self.local_min_threshold}")

                else :
                    self.feedback_label.config(text = "Please Enter a Valid Treshold Between 0 and 1.")

        local_min_button = tk.Button(master = local_min_frame, text = "Enter Treshold", command = set_local_min)
        local_min_button.grid(row = 1, column = 2, padx = 5, pady = 5)

        return self.program_frame


    def open_files(self) :
        """ get selected files by User and add those to self.file_paths if files were selected
            if no files were selected an Error Message is displayed in self.feedback_label
        """
        root = tk.Tk()
        file_paths = filedialog.askopenfilenames(parent = root, filetypes=[("DPT files","*.dpt")])
        root.destroy()

        if len(file_paths) > 0 :
            self.file_paths = file_paths

        if self.feedback_label != None :
            self.feedback_label.config(text = "Evaluation Can Now Be Started.")
    

    def run_evaluation(self) :
        """ does the actual evaluation of the selected data
            does only trigger if files were selected in the first place 
            otherwise an Error Message is raised for the User in the self.feedback_label
        """

        if len(self.file_paths) > 0 :

            """ if statement required if the program is used in a GUI
            """
            if self.feedback_label != None :
                self.feedback_label.config(text = "Evaluation in Progress.")

            """ loop through each selected file in self.file_paths
                process data and save data for later use in datas dictionary as value and sample_name as key
            """
            datas = {}
            for file_path in self.file_paths :
                """ get the sample_name from the file_path
                """
                file_name = os.path.basename(file_path)
                sample_name = file_name.split(".dpt")[0]

                """ open data of sample 
                    get normalized intensity between 0 and 1 
                    add data DataFrame to datas dict as value and sample_name as key
                """
                data = pd.read_csv(file_path, delimiter = "\t", names = ["wave_number", "intensity"])

                data["normalized_intensity"] = self.get_normalized_intensity(data["intensity"])                

                datas[sample_name] = data

                """ determine local minima position if selected the automatic local minma determination 
                """
                if self.local_min_setting :
                    self.get_local_min_pos(data)

                """ plot normalized intenstiy vs wave number in figure if User wants to save the figures automatically
                    invert x axis
                    add x and y axis label 
                """
                if self.save_figures :

                    fig, ax = plt.subplots()

                    ax.plot(data["wave_number"], data["normalized_intensity"])
                    xlim = ax.get_xlim()
                    ax.set_xlim(xlim[1], xlim[0]) # invert x axis

                    ax.set_xlabel("Wave Number ($cm^{-1}$)")
                    ax.set_ylabel("Intensity (a.u.)")

                    fig.savefig(f"{self.path_evaluation_folder}\{sample_name}.jpg")

                    plt.close(fig)

                """ drop column intensity in data DataFrame and save it in the evaluation folder
                """
                data.drop("intensity", axis = 1, inplace = True)

                if self.local_min_setting :
                    data.to_csv(f"{self.path_evaluation_folder}\{sample_name}.txt", header = ["wave_number (cm^-1)", "Normalized Intensity (a.u)", "Local Min"], index = None, sep = ";")
                else :
                    data.to_csv(f"{self.path_evaluation_folder}\{sample_name}.txt", header = ["wave_number (cm^-1)", "Normalized Intensity (a. u.)"], index = None, sep = ";")


            fig, ax = plt.subplots()

            for sample_name, data in datas.items() :
                color = next(ax._get_lines.prop_cycler)['color']
                ax.plot(data["wave_number"], data["normalized_intensity"], label = sample_name, c = color)
                
                if self.local_min_setting :
                    ax.scatter(data["wave_number"], data["local_min"], marker = "x", s = 10, c = color)
                

            xlim = ax.get_xlim()
            ax.set_xlim(xlim[1], xlim[0]) # invert x axis

            ax.set_xlabel("Wave Number ($cm^{-1}$)")
            ax.set_ylabel("Intensity (a.u.)")
            ax.legend(loc = "upper left", fontsize = 8)


            if self.feedback_label != None :
                self.feedback_label.config(text = "Evaluation Finished.")

            plt.show()

            if self.save_figures :

                files_in_directory = os.listdir(self.path_evaluation_folder) 

                count = 0
                for file in files_in_directory :
                    if "Infrared_Analysis" in file :
                        count += 1

                fig.savefig(f"{self.path_evaluation_folder}\Infrared_Analysis_{count}.jpg")
                

    def get_normalized_intensity(self, intensity) :
        """ returns an normalized data set between 0 and 1 by the formular
            intensity = (intensity - min-intensity) / (max-intensity - min-intensity)

            expected argument datatype:
            - intensity: pandas.Series
        """

        intensity = (intensity - min(intensity)) / (max(intensity) - min(intensity))

        return intensity


    def get_local_min_pos(self, data) :
        """ searches for local minima in the column normalized_intensity from the data DataFrame by comparing each position with its direct neighbor if it
            represents an local minima

            known issues:
            - detects every minima position (can by fine tuned by setting right self.local_min_treshold)
        """
        intensity = data["normalized_intensity"]

        count = 0

        for n in range(1, len(intensity) - 1) :

            inte = intensity[n]

            if inte <= self.local_min_threshold :

                if inte <= intensity[n - 1] and inte <= intensity[n + 1] :

                    data.at[n, "local_min"] = inte
                    count +=1





if __name__ == "__main__" :

    root = tk.Tk()

    ir = Infrared_Analysis()
    ir.get_gui_frame(root)

    root.mainloop()



""" made by Stiftler (Pascal Reiß)
"""

"""
update list: 

Version 1.0.2 (28.03.2022)
- added filetypes argument for tkinter.filedialog.askopenfilenames function to show only necessary files for the program
  in this case: ["DPT Files", "*.dpt"]

Version 1.0.3 (06.04.2022)
- fixed bug were tkinter.StringVar values werent saved if the program was imported
"""