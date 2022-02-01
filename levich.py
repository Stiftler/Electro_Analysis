""" Levich Analysis Tool by Pascal Reiß
    Version 1.0.1 
"""

import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import SpanSelector
from datetime import datetime


class Levich_Analysis :


    def __init__(self) :

        self.program_name = "Levich Analysis"

        self.reset_attributes()

        self.change_rpm_button = None

        path_this_programm = os.path.dirname(os.path.realpath(__file__))

        path_evaluation_folder = f"{path_this_programm}\Evaluation"

        if not os.path.exists(path_evaluation_folder) :
            os.mkdir(path_evaluation_folder)

        path_evaluation_folder = f"{path_evaluation_folder}\{self.program_name}"
        
        if not os.path.exists(path_evaluation_folder) :
            os.mkdir(path_evaluation_folder)

        today = datetime.today().strftime("%Y-%m-%d")

        self.path_evaluation_folder = f"{path_evaluation_folder}\{today}"

        if not os.path.exists(self.path_evaluation_folder) :
            os.mkdir(self.path_evaluation_folder)


    def reset_attributes(self) :

        self.save_figures = False
        
        self.file_paths = ()

        self.program_frame = None

        self.rpm_labels, self.rpm_entries = [], []

        self.rpm_values = {}

        self.sample_names = []

        self.start_evaluation = False  

        self.results_levich = pd.DataFrame(index = ["levich_slope", "levich_intersect"])

        self.results_koutecky = pd.DataFrame(index = ["koutecky_slope", "koutecky_intersect", "on_set_current"])     

        self.active_rpm_frames = [] 

        self.active_evaluation_frames = []

        self.active_results_frames = []

        self.data_levich = pd.DataFrame()

        self.data_koutecky = pd.DataFrame()


    def save_levich_results(self) :
        files_in_directory = os.listdir(self.path_evaluation_folder)

        count = 0

        for file in files_in_directory :
            if "Levich_Results" in file :
                count += 1
        
        self.data_levich.to_csv(f"{self.path_evaluation_folder}\Levich_Results_{count}.txt", sep = ";", header = self.data_levich.columns, index = None)


    def save_koutecky_results(self) :
        files_in_directory = os.listdir(self.path_evaluation_folder)

        count = 0

        for file in files_in_directory :
            if "Koutecky_Results" in file :
                count += 1
        
        self.data_koutecky.to_csv(f"{self.path_evaluation_folder}\Koutecky_Results{count}.txt", sep = ";", header = self.data_koutecky.columns, index = None)


    def run_evaluation(self) :
        
        if self.start_evaluation :

            self.change_rpm_button.grid_forget()

            self.feedback_label.config(text = "Evaluation in progress.")

            for evalution_frame in self.active_evaluation_frames :
                evalution_frame.grid_forget()

            def get_results_frame() :
                
                for results_frame in self.active_results_frames :
                    results_frame.grid_forget()

                results_frame = tk.Frame(master = self.program_frame, relief  = "groove", borderwidth =2)
                results_frame.grid(row = 1, column = 1, padx = 5, pady = 5)

                for n, text in enumerate(["Potential (V)", "Levich Slope (mA/ω)", "Levich Intersect (mA)", "Koutecky Slope", "Koutecky Intersect", "On Set Current (mA)"]) : # EINHEITEN ANFÜGEN
                    label = tk.Label(master = results_frame, text = text)
                    label.grid(row = 0, column = n, padx = 5, pady = 5)

                potentials_already_listed = {}

                for n, potential in enumerate(self.results_levich.columns) :
                    label = tk.Label(master = results_frame, text = potential)
                    label.grid(row = n + 1, column = 0, padx = 5, pady = 5)

                    potentials_already_listed[potential] = n + 1
                    for m, index in enumerate(self.results_levich.index) :
                        result = self.results_levich.at[index, potential] * 1000
                        label = tk.Label(master = results_frame, text = round(result, 3))
                        label.grid(row = n + 1, column = m + 1, padx = 5, pady = 5)

                for i, potential in enumerate(self.results_koutecky.columns) :
                    if potential in potentials_already_listed.keys() :
                        row = potentials_already_listed[potential]
                    else :
                        row = n + i + 2
                        label = tk.Label(master = results_frame, text = potential)
                        label.grid(row = row, column = 0, padx = 5, pady = 5)

                    for o, index in enumerate(self.results_koutecky.index) :
                        result = self.results_koutecky.at[index, potential]
                        if index == "on_set_current" :
                            result *= 1000
                        label = tk.Label(master = results_frame, text = round(result, 3))
                        label.grid(row = row, column = o + 3, padx = 5, pady = 5)

                self.active_results_frames.append(results_frame)


            def levich_onselect(xmin, xmax) :   
                
                currents, sqrt_rotation_rates = [], []

                for data in datas.values() :

                    data = data[data["potential"] >= xmin]

                    currents.append(data["current"].tolist()[0])
                    sqrt_rotation_rates.append(data["sqrt_rotation_rate"].tolist()[0])    

                data_levich = pd.DataFrame()
                data_levich["current"] = currents
                data_levich["sqrt_rotation_rate"] = sqrt_rotation_rates

                levich_fit = np.polyfit(data_levich["sqrt_rotation_rate"], data_levich["current"], 1)

                levich_slope, levich_intersect = levich_fit[0], levich_fit[1]

                """ create the eqation of the fit """
                if levich_intersect > 0 :
                    levich_label = f"{round(xmin, 3)} V  j = {round(levich_slope * 1000, 3)}" + " $ω^{0.5}$ + " + f"{round(levich_intersect * 1000, 3)}"
                elif levich_intersect < 0 :
                    levich_label = f"{round(xmin, 3)} V  j = {round(levich_slope * 1000, 3)}" + " $ω^{0.5}$ - " + f"{round(abs(levich_intersect * 1000), 3)}"
                else :
                    levich_label = f"{round(xmin, 3)} V  j = {round(levich_slope * 1000, 3)}" + " $ω^{0.5}$"

                data_levich["levich_fit"] = levich_slope * data_levich["sqrt_rotation_rate"] + levich_intersect

                ax[0,1].scatter(data_levich["sqrt_rotation_rate"], data_levich["current"] * 1000, label = levich_label, marker = "x")
                ax[0,1].plot(data_levich["sqrt_rotation_rate"],data_levich["levich_fit"] * 1000, ls = "--")

                ax[0,1].legend(fontsize = 7, loc = "upper left")

                self.results_levich[str(round(xmin, 3))] = [levich_slope, levich_intersect]

                self.data_levich[f"Current (A) @ {round(xmin, 3)} V"] = data_levich["current"]
                self.data_levich[f"Root of Rotation Rate ((rad/s)^0.5) @ {round(xmin, 3)} V"] = data_levich["sqrt_rotation_rate"]
                self.data_levich[f"Levich Slope (A/(rad/s)^0.5) @ {round(xmin, 3)} V"] = [levich_slope] + [np.nan] * (len(data_levich) - 1)
                self.data_levich[f"Levich Intersect (A) V"] = [levich_intersect] + [np.nan] * (len(data_levich) - 1)

                get_results_frame()


            def koutecky_levich_onselect(xmin, xmax) :
                
                reci_currents, reci_sqrt_rotation_rates = [], []

                for data in datas.values() :

                    data = data[data["potential"] >= xmin]

                    reci_currents.append(data["reci_current"].tolist()[0])
                    reci_sqrt_rotation_rates.append(data["reci_sqrt_rotation_rate"].tolist()[0])

                data_koutecky = pd.DataFrame()
                data_koutecky["reci_current"] = reci_currents
                data_koutecky["reci_sqrt_rotation_rate"] = reci_sqrt_rotation_rates

                koutecky_fit = np.polyfit(data_koutecky["reci_sqrt_rotation_rate"], data_koutecky["reci_current"], 1)

                koutecky_slope, koutecky_intersect = koutecky_fit[0], koutecky_fit[1]

                on_set_current = 1 / koutecky_intersect

                if koutecky_intersect > 0 :
                    koutecky_label = f"{round(xmin, 3)} V " + "$j^{-1}$ " + f"= {round(koutecky_slope)} " + "$ω^{-0.5}$ + " + f"{round(koutecky_intersect, 3)}" 
                elif koutecky_intersect < 0 :
                    koutecky_label = "$j^{-1}$ " + f"= {round(koutecky_slope)} " + "$ω^{-0.5}$ - " + f"{round(abs(koutecky_intersect), 3)}" 
                else :
                    koutecky_label = "$j^{-1}$ " + f"= {round(koutecky_slope)} " + "$ω^{-0.5}$" + f", on set current: {round(on_set_current * 1000, 3)} mA"

                data_koutecky["koutecky_fit"] = koutecky_slope * data_koutecky["reci_sqrt_rotation_rate"] + koutecky_intersect

                ax[1,1].scatter(data_koutecky["reci_sqrt_rotation_rate"], data_koutecky["reci_current"], marker = "x", s = 10, label = koutecky_label)
                ax[1,1].plot(data_koutecky["reci_sqrt_rotation_rate"], data_koutecky["koutecky_fit"], ls = "--")
                ax[1,1].legend(fontsize = 8, loc = "upper left")

                self.results_koutecky[str(round(xmin, 3))] = [koutecky_slope, koutecky_intersect, on_set_current]

                self.data_koutecky[f"Reciprocal Current (A^-1) @ {round(xmin, 3)} V"] = data_koutecky["reci_current"]
                self.data_koutecky[f"Reciprocal Root of Rotation Rate () @ {round(xmin, 3)} V"] = data_koutecky["reci_sqrt_rotation_rate"]
                self.data_koutecky[f"Koutecky Slope () @ {round(xmin, 3)} V"] = [koutecky_slope] + [np.nan] * (len(self.data_koutecky) - 1)
                self.data_koutecky[f"Koutecky Intersect (A^-1) @ {round(xmin, 3)} V"] = [koutecky_intersect]+ [np.nan] * (len(self.data_koutecky) - 1)
                self.data_koutecky[f"On Set Current (mA) @ {round(xmin, 3)} V"] = [round((on_set_current * 1000), 3)] + [np.nan] * (len(self.data_koutecky) - 1)
                
                get_results_frame()


            def get_evaluation_frame() :
                evalution_frame = tk.Frame(master = self.program_frame, relief = "groove", borderwidth = 2)
                evalution_frame.grid(row = 0, column = 1, padx = 5, pady = 5)

                levich_frame = tk.Frame(master = evalution_frame, relief = "groove", borderwidth = 2)
                levich_frame.grid(row = 0, column = 0, padx = 5, pady = 5)

                koutecky_frame = tk.Frame(master = evalution_frame, relief = "groove", borderwidth = 2)
                koutecky_frame.grid(row = 1, column = 0, padx = 5, pady =5)

                label = tk.Label(master = levich_frame, text = "Set Potential for Levich Plot\nEnter Multiple Potentials with ';'")
                label.grid(row = 0, column = 0, padx = 5, pady = 3)

                label = tk.Label(master = koutecky_frame, text = "Set Potential for Koutecky-Levich Plot\nEnter Multiple Potentials with ';'")
                label.grid(row = 0, column = 0, padx = 5, pady = 5)

                levich_entry = tk.Entry(master = levich_frame)
                levich_entry.grid(row = 0, column = 1, padx = 5, pady = 5)

                koutecky_entry = tk.Entry(master = koutecky_frame)
                koutecky_entry.grid(row = 0, column = 1, padx = 5, pady = 5)

                def get_levich_potential() :
                    entries = levich_entry.get()

                    entries = entries.replace(",", ".")

                    entries = entries.split(";")

                    for entry in entries :
                        try :
                            entry = float(entry)
                        except ValueError :
                            self.feedback_label.config(text = f"Failed to convert {entry} to a valid input.")
                            continue
                        levich_onselect(entry, 2) # 2 is for xmax and arbitrarily chosen

                def get_koutecky_potential() :
                    entries = koutecky_entry.get()

                    entries = entries.replace(",", ".")

                    entries = entries.split(";")

                    for entry in entries :
                        try :
                            entry = float(entry)
                        except ValueError :
                            self.feedback_label.config(text = f"Failed to convert {entry} to a valid input.")
                            continue
                        koutecky_levich_onselect(entry, 2) # 2 is for xmax and arbitrarily chosen

                potential_levich_button = tk.Button(master = levich_frame, text = "Set Potential", command = get_levich_potential)
                potential_levich_button.grid(row = 0, column = 2, padx = 5, pady = 5)

                potential_koutecky_button = tk.Button(master = koutecky_frame, text = "Set Potential", command = get_koutecky_potential)
                potential_koutecky_button.grid(row = 0, column = 2, padx = 5, pady = 5)

                def clear_levich_plot() :
                    ax[0,1].clear()
                    ax[0,1].set_xlabel("$ω^{0.5}$ (rad/s$)^{0.5}$")
                    ax[0,1].set_ylabel("Current (mA)")

                    self.results_levich = pd.DataFrame(index = ["levich_slope", "levich_intersect"])

                def clear_koutecky_plot() :
                    ax[1,1].clear()
                    ax[1,1].set_xlabel("$ω^{-0.5}$ (rad/s$)^{-0.5}$")
                    ax[1,1].set_ylabel("Reciprocal Current (A$)^{-1}$")

                    self.results_koutecky = pd.DataFrame(index = ["koutecky_slope", "koutecky_intersect", "on_set_current"])

                clear_levich_button = tk.Button(master = levich_frame, text = "Clear Levich Plot", command = clear_levich_plot)
                clear_levich_button.grid(row = 0, column = 3, padx = 5, pady = 5)

                clear_koutecky_button = tk.Button(master = koutecky_frame, text = "Clear Koutecky Plot", command = clear_koutecky_plot)
                clear_koutecky_button.grid(row = 0, column = 3, padx = 5, pady = 5)

                save_levich_button = tk.Button(master = levich_frame, text = "Save Levich Results", command = self.save_levich_results)
                save_levich_button.grid(row = 0, column = 4, padx = 5, pady = 5)

                save_koutecky_button = tk.Button(master = koutecky_frame, text = "Save Koutecky Results", command = self.save_koutecky_results)
                save_koutecky_button.grid(row = 0, column = 4, padx = 5, pady = 5)

                get_results_frame()

                self.active_evaluation_frames.append(evalution_frame)


            get_evaluation_frame()

            datas = {}

            fig, ax = plt.subplots(2,2)

            for n, file_path in enumerate(self.file_paths) :
                sample_name = self.sample_names[n]
                rpm = self.rpm_values[sample_name]

                """ acutal evalution """
                data = pd.read_csv(file_path, delimiter = ";")
                data.rename(columns = {"WE(1).Potential (V)":"potential", "WE(1).Current (A)" :"current"}, inplace = True)

                ax[0,0].plot(data["potential"], data["current"] * 1000, label = sample_name)
                ax[1,0].plot(data["potential"], data["current"] * 1000)

                rotation_rate = (2 * np.pi) / 60 * rpm
                data["rotation_rate"] = [rotation_rate] * len(data)
                data["sqrt_rotation_rate"] = np.sqrt(data["rotation_rate"])

                data["reci_current"] = 1 / data["current"]
                data["reci_sqrt_rotation_rate"] = 1 / data["sqrt_rotation_rate"]

                data_save = pd.DataFrame()
                data_save["Potential (V)"] = data["potential"]
                data_save["Current (A)"] = data["current"]
                data_save["Rotation Rate (rad/s)"] = data["rotation_rate"]
                data_save["Root Rotation Rate (rad/s)^0.5"] = data["sqrt_rotation_rate"]
                data_save["Reciproce Root Rotation Rate (rad/s)^-0.5"] = data["reci_sqrt_rotation_rate"]

                data_save.to_csv(f"{self.path_evaluation_folder}\{sample_name}.txt", header = data_save.columns, index = None, sep = ";")

                datas[sample_name] = data

            ax[0,0].legend(loc = "upper left", fontsize = 8)

            ax[0,1].set_title("Please select range in the left plot. \nThe lower range limit represents the potential of Levich fit.")
            ax[1,1].set_title("Please select range in the left plot. \nThe lower range limit represents the potential of Koutecky-Levich fit.")
            
            ax[0,0].set_xlabel("Potential vs Ag|AgCl [V]")
            ax[0,0].set_ylabel("Current (mA)")

            ax[1,0].set_xlabel("Potential vs Ag|AgCl [V]")
            ax[1,0].set_ylabel("Current (mA)")

            ax[0,1].set_xlabel("$ω^{0.5}$ (rad/s$)^{0.5}$")
            ax[0,1].set_ylabel("Current (mA)")

            ax[1,1].set_xlabel("$ω^{-0.5}$ (rad/s$)^{-0.5}$")
            ax[1,1].set_ylabel("Reciprocal Current (A$)^{-1}$")

            spanner_levich = SpanSelector(ax[0,0], levich_onselect, "horizontal", useblit = True)
            spanner_koutecky_levich = SpanSelector(ax[1,0], koutecky_levich_onselect, "horizontal", useblit = True)

            plt.show()

            self.change_rpm_button.grid(row =0, column = 2, padx = 5, pady = 5)

            if self.save_figures :

                files_in_directory = os.listdir(self.path_evaluation_folder)

                count = 0
                for file in files_in_directory :
                    if ".jpg" in file :
                        count += 1
                fig.savefig(f"{self.path_evaluation_folder}\Levich_{count}.jpg")


        elif len(self.file_paths) == 0 :
            self.feedback_label.config(text = "Please select your raw data files first.")

        else :
            self.feedback_label.config(text = "Please check the entered RPM values first.")


    def change_rpm_values(self) :
        
        self.start_evaluation = False
        check = -1
        for n, rpm_entry in enumerate(self.rpm_entries) :
            entry = rpm_entry.get()

            entry = entry.replace(",", ".")

            if entry != "" :
                try :
                    entry = float(entry)
                    self.rpm_values[self.sample_names[n]] = entry
                    check += 1
                except ValueError :
                    self.feedback_label.config(text = f"Please enter a valid input for {self.sample_names[n]}.")
                    continue

                self.rpm_labels[n].config(text = f"{entry}")
            else :
                check += 1
                continue

        if n == check :
            self.feedback_label.config(text = "Evaluation can be started.")
            self.start_evaluation = True


    def open_files(self) :

        
        root = tk.Tk()
        self.file_paths = filedialog.askopenfilenames(parent = root)
        root.destroy()

        if len(self.file_paths) > 0 :
            
            self.sample_names = []
            
            for sample_rpm_frame in self.active_rpm_frames :
                sample_rpm_frame.grid_forget()

            for evalution_frame in self.active_evaluation_frames :
                evalution_frame.grid_forget()

            for results_frame in self.active_results_frames :
                results_frame.grid_forget()

            sample_rpm_frame = tk.Frame(master = self.program_frame, relief = "groove", borderwidth = 2)
            sample_rpm_frame.grid(row = 1, column = 0, padx = 5, pady = 5)

            sample_label = tk.Label(master = sample_rpm_frame, text = f"Selected Samples")
            sample_label.grid(row = 0, column = 0, padx = 5, pady = 5)

            rpm_label = tk.Label(master = sample_rpm_frame, text = "RPM")
            rpm_label.grid(row = 0, column = 1, padx = 5, pady = 5)

            self.change_rpm_button = tk.Button(master = sample_rpm_frame, text = "Change RPM Values", command = self.change_rpm_values)
            self.change_rpm_button.grid(row = 0, column = 2)

            self.rpm_labels, self.rpm_entries = [], []

            check = 0
            for n, file_path in enumerate(self.file_paths) :
                file_name = os.path.basename(file_path)
                sample_name = file_name.split(".txt")[0]

                self.sample_names.append(sample_name)

                sample_label = tk.Label(master = sample_rpm_frame, text = f"{sample_name}")
                sample_label.grid(row = n + 1, column = 0, padx = 5, pady = 5)

                rpm = sample_name.split("_")[-1]
                if "rpm" in rpm :
                    rpm = rpm.split("rpm")[0]

                    try :
                        rpm = int(rpm)
                    except ValueError :
                        check += 1
                        rpm = "automatic RPM recognition failed"

                elif "RPM" in rpm :
                    rpm = rpm.split("RPM")[0]

                    try :
                        rpm = int(rpm)
                    except ValueError :
                        check += 1
                        rpm = "automatic RPM recognition failed"

                else :
                    check += 1
                    rpm = "automatic RPM recognition failed"

                rpm_label = tk.Label(master = sample_rpm_frame, text = f"{rpm}")
                rpm_label.grid(row = n + 1, column = 1, padx = 5, pady = 5)

                self.rpm_labels.append(rpm_label)

                rpm_entry = tk.Entry(master = sample_rpm_frame)
                rpm_entry.grid(row = n + 1, column = 2, padx = 5, pady = 5)

                self.rpm_entries.append(rpm_entry)

                self.rpm_values[sample_name] = rpm

                self.active_rpm_frames.append(sample_rpm_frame)

            if check == 0 :
                self.start_evaluation = True
                self.feedback_label.config(text = "Please check the determined RPM values. Evaluation can be started.")
            else :
                self.feedback_label.config(text = "Please check the determined PRM values.")


    def get_gui_frame(self, master) :

        self.reset_attributes()

        self.program_frame = tk.Frame(master = master, relief = "groove", borderwidth = 2)
        self.program_frame.grid(row = 1, column = 1, padx = 5, pady = 5)
        
        control_frame = tk.Frame(master = self.program_frame, relief = "groove", borderwidth = 2)
        control_frame.grid(row = 0, column = 0, padx = 5, pady = 5)

        open_files_button = tk.Button(master = control_frame, text = "Open Files", command = self.open_files)
        open_files_button.grid(row = 0, column = 0, padx = 5, pady = 5)

        self.feedback_label = tk.Label(master = control_frame, text = "Please select your raw data files first.", font = "Arial")
        self.feedback_label.grid(row = 0, column = 1, padx = 5, pady = 5)

        run_evaluation_button = tk.Button(master = control_frame, text = "Start Evaluation", command = self.run_evaluation)
        run_evaluation_button.grid(row = 0, column = 2, padx = 5, pady = 5)

        def change_figure_saving_settings() :
            settings = {"1" : True, "0" : False}
            setting = save_figures_variable.get()

            self.save_figures = settings[setting]


        save_figures_variable = tk.StringVar()
        save_figures_checkbox = ttk.Checkbutton(control_frame, text = "automatically save figures", \
            variable = save_figures_variable, command = change_figure_saving_settings)
        save_figures_checkbox.grid(row = 1, column = 0, padx = 5, pady = 5)

        return self.program_frame




if __name__ == "__main__" :

    levich = Levich_Analysis()
    
    root = tk.Tk()

    frame = levich.get_gui_frame(root)

    root.mainloop()

""" made by Stiftler (Pascal Reiß)
"""