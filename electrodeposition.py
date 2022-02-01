""" Electrodeposition Analysis Tool by Pascal Reiß
    Version 1.0.1 
"""

import tkinter as tk
from tkinter import ttk
import pandas as pd
import numpy as np
from tkinter import filedialog
import matplotlib.pyplot as plt
import os
from datetime import datetime

class Electrodeposition_Analysis :
    
    def __init__(self) :

        """ initiate Electrodeposition_Analysis class with the following attributes:
            - self.area_electrode 
                (int/float: contains the value of the area of the electrode in cm²)
            - self.file_paths 
                (tuple: contains the file_paths of the file which shall be evaluated)
            - self.program_frame (tkinter.Frame) and self.feedback_label (tkinter.Label ) 
                are objects required in the GUI interface 
                the interface, which is created in a later function, is no window (tk.Tk)
            - self.save_figures (boolean: contains info if User wants to save a figure created during the evaluation
                default setting : False
                can be changed in the User Interface)
                """

        self.program_name = "Electrodeposition Analysis"

        self.area_electrode = 1 # 

        self.file_paths = ()

        self.program_frame = None

        self.feedback_label = None

        self.save_figures = False

        """ create evaluation folder to save evaluated data and figures (if it does not exist yet)
            created folder is at */Evaluation/Electrodepostion Analysis/**
             * path of this program
             ** current date in format YYYY-MM-DD"""

        path_this_programm = os.path.dirname(os.path.realpath(__file__))

        self.path_evaluation_folder = f"{path_this_programm}\Evaluation\{self.program_name}"

        if not os.path.exists(f"{path_this_programm}\Evaluation") :
            os.mkdir(f"{path_this_programm}\Evaluation")
            
        if not os.path.exists(self.path_evaluation_folder) :
            os.mkdir(self.path_evaluation_folder)

        today = datetime.today().strftime("%Y-%m-%d")

        self.path_evaluation_folder = f"{self.path_evaluation_folder}\{today}"

        if not os.path.exists(self.path_evaluation_folder) :
            os.mkdir(self.path_evaluation_folder)


    def get_seconds_in_min(self, seconds) :
        """ returns a value given in seconds in min 
            expected argument datatypes:
            - seconds: int/float """

        return seconds / 60


    def run_evaluation(self) :
        """ does the actually evaluation of the selected data
            does only trigger if files were selected in the first place """

        if len(self.file_paths) > 0 :

            """ set up figure containing the plots
            """
            fig, ax = plt.subplots()

            current_density_label = "$j_{dep}$" # set up string for y-axis label of plot

            """ loop through each file individually 
            """

            for file_path in self.file_paths :

                """ get name of sample from file name 
                """

                file_name = os.path.basename(file_path)
                sample_name = file_name.split(".txt")[0]

                """ opening actual raw data 
                """

                data = pd.read_csv(file_path, delimiter = ";")

                """ conversion of time in min and calculation of the mean current for the current density calculation 
                """
                data["Time_(min)"] = self.get_seconds_in_min(data["Corrected time (s)"])

                mean_current = np.mean(data["WE(1).Current (A)"])

                current_density = mean_current / self.area_electrode

                """ plot data as scatter plot with x as marker 
                """
                ax.scatter(data["Time_(min)"], data["WE(1).Potential (V)"], \
                    label = f"{sample_name} {current_density_label} = {round(current_density * 1000, 3)} mA/cm²", marker = "x")

                """ create a new DataFrame containg only the relevant data and save those 
                """
                data_save = pd.DataFrame()

                data_save["Time_(min)]"] = data["Time_(min)"]
                data_save["Current_(A)"] = data["WE(1).Current (A)"]
                data_save["Potential_(V)"] = data["WE(1).Potential (V)"]

                data_save.to_csv(f"{self.path_evaluation_folder}\{file_name}", header = data_save.columns, index = None, sep = ";")


            """ finalizing generated plot/figure by adding axis labels and legends
                save the figure in case User wants to save them """
            ax.legend(loc = "lower left", fontsize = 10)
            ax.set_xlabel("Time [min]")
            ax.set_ylabel("$E_{WE}$ vs Ag|AgCl [V]")

            if self.save_figures == True :
                files_in_directory = os.listdir(self.path_evaluation_folder)
                
                count = 0
                for file in files_in_directory :
                    """ counts all saved figures in the evalution folder and saves new figure with count as file name ending
                    """
                    if ".jpg" in file :
                        count += 1
                fig.savefig(f"{self.path_evaluation_folder}\Electrodeposition_{count}.jpg")

            plt.show()


    def open_files(self) :
        """ gets file_paths of raw data files from User which shall be evaluated by this program 
        """
        self.file_paths = () # just in case old files were selected previously, those are overwritten and forgotten

        self.feedback_label.config(text = "Please select your raw data files.")

        root = tk.Tk()
        file_paths = filedialog.askopenfilenames(parent = root)  
        root.destroy()

        self.file_paths = file_paths

        """ if the User Interface is active a feedback is given back if the file selection was succesful 
            since the evalution function is only triggered if len(self.file_paths) > 0 no further safty mechanism is required
        """
        if len(self.file_paths) > 0 and self.feedback_label != None :
            self.feedback_label.config(text = "Evaluation can be started now.")

        elif len(self.file_paths) == 0 and self.feedback_label != None :
            self.feedback_label.config(text = "Please select your raw data files.")


    def get_gui_frame(self, master) :
        """ returns a tkinter.Frame to a master window (tkinter.Tk)
            this Frame needs to contain al necassary widgets/functions required for the evaluation 
            the grid placement was chosen since it is one of the simplest and cleanest options for a tkinter based User Interface
        """

        """ create tkinter.Frame 
            keywords: borderwith and relief for asthetics
            positon in grid row = 1, column = 1 is necassary for the GUI program written by Pascal Reiß (CS_Analysis_Tool.py)
            if new GUI is created these values can be tuned 
        """
        self.program_frame = tk.Frame(master = master, borderwidth = 2, relief = "groove")
        self.program_frame.grid(row = 1, column = 1, padx = 5, pady = 5)

        """ create buttonm which can access the self.open_files function in order to get the file_paths by User
        """
        open_files_button = tk.Button(master = self.program_frame, 
            text = "Open Files", command = self.open_files)
        open_files_button.grid(row = 0, column = 0, padx = 5, pady = 5)

        """ create an Entry field to change area_electrode by User in User Interface 
            the change is done by the change_area_button, which contains the function change_area_electrode
            this function checks if the input by the User was valid (int, float) and if so sets the value as self.area_electrode
        """
        change_area_electrode_entry = tk.Entry(master = self.program_frame, text = f"{self.area_electrode}")
        change_area_electrode_entry.grid(row = 1, column = 0, padx = 5, pady = 5)

        def change_area_electrode() :
            entry = change_area_electrode_entry.get()
            entry = entry.replace(",", ".")
            try :
                entry = float(entry)
                self.area_electrode = entry
                self.feedback_label.config(text = "Conversion of area electrode successful.")
            except ValueError :
                self.feedback_label.config(text = "Conversion of area electrode failed. Please try again.")

        change_area_electrode_button = tk.Button(master = self.program_frame, text = "Change Area Electrode (cm²)", command = change_area_electrode)
        change_area_electrode_button.grid(row = 2, column = 0, padx = 5, pady = 5)

        """ create a tkinter.Label, which contains the feedback for the User if an execution failed or was successful
            (as a attribute of the Electrodepositon_Analysis class itself) 
        """

        self.feedback_label = tk.Label(master = self.program_frame, text = "Please select your raw data files.", font = "Arial")
        self.feedback_label.grid(row = 0, column = 1, pady = 5, padx = 5)

        """ create run_evaluation_button, which contains the function self.run_evalution and starts the evalution
        """
        run_evaluation_button = tk.Button(master = self.program_frame, text = "Start Evaluation", command = self.run_evaluation)
        run_evaluation_button.grid(row = 0, column = 2, padx = 5, pady = 5)

        """ set up a tkinter.StringVar which contains the setting of the tkinter.tkk.Checkbutton
            this Checkbutton acts as checkbox for the automatic save function of the figures 
        """
        def change_figure_saving_settings() :
            setting = save_figures_variable.get()

            if setting == "1" :
                self.save_figures = True

            elif setting == "0" :
                self.save_figures = False

        save_figures_variable = tk.StringVar()
        save_figures_checkbox = ttk.Checkbutton(self.program_frame, text = "automatically save figures",
            variable = save_figures_variable, command = change_figure_saving_settings)
        save_figures_checkbox.grid(column = 0, row = 3, padx = 5, pady = 5)


        return self.program_frame




if __name__ == "__main__" :

    """ main program if this script is run directly and is not imported into another python project
    """

    ed = Electrodeposition_Analysis()
    
    ed.open_files()

    ed.run_evaluation()



""" made by Stiftler (Pascal Reiß) 
"""
