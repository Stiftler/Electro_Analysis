""" Infrared Analysis Tool by Pascal Reiß
    Version 1.0.1 
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

        self.program_name = "Infrared Analysis"

        self.save_figures = False

        self.reset_attributes()

        self.program_frame = None

        self.feedback_label = None

        self.local_min_setting = False

        self.local_min_frame = None     


    def reset_attributes(self) :

        self.file_paths = ()

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
        
        self.program_frame = tk.Frame(master = master, relief = "groove", borderwidth = 2)
        self.program_frame.grid(row = 1, column = 1, padx = 5, pady = 5)

        control_frame = tk.Frame(master = self.program_frame, relief = "groove", borderwidth = 2)
        control_frame.grid(row = 0, column = 0, padx =5, pady = 5)

        open_files_button = tk.Button(master = control_frame, text = "Open Files", command = self.open_files)
        open_files_button.grid(row = 0, column = 0, padx = 5, pady = 5)

        run_evaluation_button = tk.Button(master = control_frame, text = "Run Evaluation", command = self.run_evaluation)
        run_evaluation_button.grid(row = 0, column = 2, padx = 5, pady = 5)

        self.feedback_label = tk.Label(master = control_frame, text = "Please Select Your Raw Data First.", font = "Arial")
        self.feedback_label.grid(row = 0, column = 1, padx = 5, pady = 5)

        def change_figure_saving_settings() :
            settings = {"1" : True, "0" : False}
            setting = save_figures_variable.get()

            self.save_figures = settings[setting]

        save_figures_variable = tk.StringVar()
        save_figures_checkbox = ttk.Checkbutton(control_frame, text = "automatically save figures", \
            variable = save_figures_variable, command = change_figure_saving_settings)
        save_figures_checkbox.grid(row = 1, column = 0, padx = 5, pady = 5)

        def change_local_min_settings() :
            settings = {"1" : True, "0" : False}
            setting = local_min_variable.get()

            self.local_min_setting = settings[setting]

            if settings[setting] :
                local_min_frame.grid(row = 1, column = 0, padx = 5, pady = 5)
            else :
                local_min_frame.grid_forget()


        local_min_variable = tk.StringVar()
        local_min_checkbox = ttk.Checkbutton(control_frame, text = "automatic local minimas",
            variable = local_min_variable, command = change_local_min_settings)
        local_min_checkbox.grid(row = 2, column = 0, padx = 5, pady = 5)

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

        root = tk.Tk()
        file_paths = filedialog.askopenfilenames(parent = root)
        root.destroy()

        if len(file_paths) > 0 :
            self.file_paths = file_paths

        if self.feedback_label != None :
            self.feedback_label.config(text = "Evaluation Can Now Be Started.")
    

    def run_evaluation(self) :

        if len(self.file_paths) > 0 :

            if self.feedback_label != None :
                self.feedback_label.config(text = "Evaluation in Progress.")

            datas = {}
            for file_path in self.file_paths :
                file_name = os.path.basename(file_path)
                sample_name = file_name.split(".dpt")[0]

                data = pd.read_csv(file_path, delimiter = "\t", names = ["wave_number", "intensity"])

                data["normalized_intensity"] = self.get_normalized_intensity(data["intensity"])                

                datas[sample_name] = data

                if self.local_min_setting :
                    self.get_local_min_pos(data)


                if self.save_figures :

                    fig, ax = plt.subplots()

                    ax.plot(data["wave_number"], data["normalized_intensity"])
                    xlim = ax.get_xlim()
                    ax.set_xlim(xlim[1], xlim[0]) # invert x axis

                    ax.set_xlabel("Wave Number ($cm^{-1}$)")
                    ax.set_ylabel("Intensity (a.u.)")

                    fig.savefig(f"{self.path_evaluation_folder}\{sample_name}.jpg")

                    plt.close(fig)

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

        intensity = (intensity - min(intensity)) / (max(intensity) - min(intensity))

        return intensity


    def get_local_min_pos(self, data) :

        intensity = data["normalized_intensity"]

        count = 0

        for n in range(1, len(intensity) - 1) :

            inte = intensity[n]

            if inte <= self.local_min_threshold :

                if inte <= intensity[n - 1] and inte <= intensity[n + 1] :

                    data.at[n, "local_min"] = inte
                    count +=1





if __name__ == "__main__" :

    ir = Infrared_Analysis()
    ir.open_files()
    ir.run_evaluation()