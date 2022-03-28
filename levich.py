""" Levich Analysis Tool by Pascal Reiß
    Version 1.0.2
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
        """ initiate Levich_Analysis class with the following attributes
            - self.save_figures
                (boolean: contains the state if User wants to save the created figures automatically
                default state: False)
            - self.start_evaluation
                (boolean: safety switch if not all required parameters are known, the evaluation can not be started)
            - self.file_paths 
                (tuple: contains the file_paths of the raw data files selected by the User)
            - self.sample_names
                (list: contains all sample_names of the selected files)
            - self.program_frame (tkinter.Frame)
                is an object required in the GUI interface
                the interface, which is created in a later function (self.get_gui_frame)
            - self.active_rpm_frames, self.active_evaluation_frames and self.active_results_frames
                (list: contains all active frames created during the execution of this program)
            - self.rpm_labels and self.rpm_entries
                (list: contains the tkinter.Label´s and tkinter.Entry´s created in the sample_rpm_frame (see function self.open_files)
                these tkinter.Label´s and tkinter.Entry´s list the current set RPM values and gives User the possibility to change those)
            - self.change_rpm_button
                (tkinter.Button: has the function to change the set rpm values for each sample. It is set as an attribute of the Levich_Analysis class object so
                that it can be removed during the evaluation process (if not User could change rpm values during the evaluation and that would kill the 
                running evaluation process))
            - self.rpm_values
                (dict: contains the set rpm values for each sample as value and the sample_name as the key)
            - self.results_levich and self.results_koutecky
                (pandas.DataFrame: contains all evaluated data from the levich and levicht-koutecky fit)
            - self.data_levich and self.data_koutecky
                (pandas.DataFrame: contains the data set of each selected potential for the levich and levich-koutecky fit)
        """


        """ set up basic attributes and paramteters necessary for the class and evalution 
        """
        self.program_name = "Levich Analysis"

        self.reset_attributes()

        self.change_rpm_button = None

        """ create evaluation folder to save evaluated data and figures (if this folder does not exist already)
            created folder is at */Levich Analysis/**
             * path of this program
             ** current date in format YYYY-MM-DD
        """

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
        """ resets all attributes for the Levich_Analysis class object or required for opening new files
            this function is exectued once during the initiation of the Levich_Analysis class object to set
            those attributes of the object
        """

        self.save_figures = False
        self.start_evaluation = False  

        self.file_paths = ()
        self.sample_names = [] 

        self.program_frame = None        
        self.active_rpm_frames = [] 
        self.active_evaluation_frames = []
        self.active_results_frames = []
        
        self.rpm_labels, self.rpm_entries = [], []
        self.rpm_values = {}   

        self.data_levich = pd.DataFrame()
        self.data_koutecky = pd.DataFrame()

        self.results_levich = pd.DataFrame(index = ["levich_slope", "levich_intersect"])
        self.results_koutecky = pd.DataFrame(index = ["koutecky_slope", "koutecky_intersect", "on_set_current"]) 


    def save_levich_results(self) :
        """ saves the self.data_levich DataFrame if User desires to save the evaluated data
            is deployed on tkinter.Button event (save_levich_button (see function get_evaluation frame in self.run_evaluation))
            it loops through all files in the evaluation folder and counts the existing Levich_Results files
            the new file is saved with the count at the end of the file_name
        """
        files_in_directory = os.listdir(self.path_evaluation_folder)

        count = 0

        for file in files_in_directory :
            if "Levich_Results" in file :
                count += 1
        
        self.data_levich.to_csv(f"{self.path_evaluation_folder}\Levich_Results_{count}.txt", sep = ";", header = self.data_levich.columns, index = None)


    def save_koutecky_results(self) :
        """ saves the self.data_koutecky DataFrame if User desires to save the evaluated data
            is deployed on tkinter.Button event (save_koutecky_button (see function get_evaluation frame in self.run_evaluation))
            it loops through all files in the evaluation folder and counts the existing Koutecky_Results files
            the new file is saved with the count at the end of the file_name
        """
        files_in_directory = os.listdir(self.path_evaluation_folder)

        count = 0

        for file in files_in_directory :
            if "Koutecky_Results" in file :
                count += 1
        
        self.data_koutecky.to_csv(f"{self.path_evaluation_folder}\Koutecky_Results{count}.txt", sep = ";", header = self.data_koutecky.columns, index = None)


    def run_evaluation(self) :
        """ does the acutal evaluation of the selected data
            does only trigger if the self.start_evaluation state is True
            the state switches to True if the following conditions are met:
            - raw data files have been selected in the first place
            - every selected sample has a rpm value assigned
        """
        
        if self.start_evaluation :
            """ remove self.change_rpm_button from grid (if the User pushes the Button during the evaluation process, the evalution process is killed)
                remove all active evaluation_frames from grid (new data does not interfere with old data in GUI)
            """

            self.change_rpm_button.grid_forget()

            self.feedback_label.config(text = "Evaluation in progress.")

            for evalution_frame in self.active_evaluation_frames :
                evalution_frame.grid_forget()

            def get_results_frame() :
                """ after the execution of a levich or koutecky-levich fit a results_frame is generated, which contains all determined results from those fits
                    the results are listed in a table with the following format:
                    - rows: list of the potential selected by User for fit 
                        (each potential is represented once. the potentials_already_listed dict contains the row as value and the set potential as key
                        the dict keeps track if a potential was added prior 
                        the order is that at first the levich results are added and the koutecky afterwards)
                    - columns: results at that potential 

                    at first all active results_frame in the self.active_results_frames list are removed from the grid
                    afterwards a new results_frame is generated with the new available data and added to self.active_results_frames
                """
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
                """ function exectued if the User selects a horizontal range in ax[0,0] or sets a value in GUI
                    deployes a levich-fit at xmin
                    xmax is not required for a levich-fit but since this function can be accessed by a SpanSelector (spanner levich) a hihger range 
                    is necassary
                    xmax has no further influence on the evalutation
                """

                """ loop through all dataset and get the first current and square root rotation rate of each sample, which is >= xmin
                    add those values to corresponding lists
                """
                currents, sqrt_rotation_rates = [], []
                for data in datas.values() :
                    data = data[data["potential"] >= xmin]

                    currents.append(data["current"].tolist()[0])
                    sqrt_rotation_rates.append(data["sqrt_rotation_rate"].tolist()[0])    

                """ add isolated currents and square root rotation rate of each sample to a pandas.DataFrame
                    fit those data linearly and isolate the 
                    - levich slope
                    - levich intersect
                """
                data_levich = pd.DataFrame()
                data_levich["current"] = currents
                data_levich["sqrt_rotation_rate"] = sqrt_rotation_rates

                levich_fit = np.polyfit(data_levich["sqrt_rotation_rate"], data_levich["current"], 1)

                levich_slope, levich_intersect = levich_fit[0], levich_fit[1]

                """ create the Levich fit equation for the plot label 
                    calculate data for the fit to represent it in the plot
                """
                if levich_intersect > 0 :
                    levich_label = f"{round(xmin, 3)} V  j = {round(levich_slope * 1000, 3)}" + " $ω^{0.5}$ + " + f"{round(levich_intersect * 1000, 3)}"
                elif levich_intersect < 0 :
                    levich_label = f"{round(xmin, 3)} V  j = {round(levich_slope * 1000, 3)}" + " $ω^{0.5}$ - " + f"{round(abs(levich_intersect * 1000), 3)}"
                else :
                    levich_label = f"{round(xmin, 3)} V  j = {round(levich_slope * 1000, 3)}" + " $ω^{0.5}$"

                data_levich["levich_fit"] = levich_slope * data_levich["sqrt_rotation_rate"] + levich_intersect

                """ add isolated data and data fit to ax[0,1]
                    add data to self.data_levich DataFrame for saving later
                """

                ax[0,1].scatter(data_levich["sqrt_rotation_rate"], data_levich["current"] * 1000, label = levich_label, marker = "x")
                ax[0,1].plot(data_levich["sqrt_rotation_rate"],data_levich["levich_fit"] * 1000, ls = "--")

                ax[0,1].legend(fontsize = 7, loc = "upper left")

                self.results_levich[str(round(xmin, 3))] = [levich_slope, levich_intersect]

                self.data_levich[f"Current (A) @ {round(xmin, 3)} V"] = data_levich["current"]
                self.data_levich[f"Root of Rotation Rate ((rad/s)^0.5) @ {round(xmin, 3)} V"] = data_levich["sqrt_rotation_rate"]
                self.data_levich[f"Levich Slope (A/(rad/s)^0.5) @ {round(xmin, 3)} V"] = [levich_slope] + [np.nan] * (len(data_levich) - 1)
                self.data_levich[f"Levich Intersect (A) @ {round(xmin, 3)} V"] = [levich_intersect] + [np.nan] * (len(data_levich) - 1)

                """ display results obtained Levich fit in GUI
                """
                get_results_frame()


            def koutecky_levich_onselect(xmin, xmax) :
                """ function exectued if the User selects a horizontal range in ax[1,0] or sets a value in GUI
                    deployes a koutecky-levich-fit at xmin
                    xmax is not required for a levich-fit but since this function can be accessed by a SpanSelector (spanner_koutecky_levich) a hihger range 
                    is necassary
                    xmax has no further influence on the evalutation
                """     

                """ loop through all datasets and get the first reciprocal current and reciprocal square root roation rate of each sample, which is >= xmin
                    add those values to corresponding lists
                """           
                reci_currents, reci_sqrt_rotation_rates = [], []
                for data in datas.values() :
                    data = data[data["potential"] >= xmin]

                    reci_currents.append(data["reci_current"].tolist()[0])
                    reci_sqrt_rotation_rates.append(data["reci_sqrt_rotation_rate"].tolist()[0])
                
                """ add isolated reciprocal currents and reciprocal sqaure root rotation rates of each sample to a pandas.DataFrame
                    fit those data linearly and isolate the
                    - koutecky-levich slope
                    - koutecky-levich intersect

                    determine the on set current by the reciprocal kotekcy-levich intersect
                """
                data_koutecky = pd.DataFrame()
                data_koutecky["reci_current"] = reci_currents
                data_koutecky["reci_sqrt_rotation_rate"] = reci_sqrt_rotation_rates

                koutecky_fit = np.polyfit(data_koutecky["reci_sqrt_rotation_rate"], data_koutecky["reci_current"], 1)

                koutecky_slope, koutecky_intersect = koutecky_fit[0], koutecky_fit[1]

                on_set_current = 1 / koutecky_intersect

                """ create the koutecky-levich-fit equation for the plot label
                    calculate data for the fit to represent it in the plot
                """
                if koutecky_intersect > 0 :
                    koutecky_label = f"{round(xmin, 3)} V " + "$j^{-1}$ " + f"= {round(koutecky_slope)} " + "$ω^{-0.5}$ + " + f"{round(koutecky_intersect, 3)}" 
                elif koutecky_intersect < 0 :
                    koutecky_label = "$j^{-1}$ " + f"= {round(koutecky_slope)} " + "$ω^{-0.5}$ - " + f"{round(abs(koutecky_intersect), 3)}" 
                else :
                    koutecky_label = "$j^{-1}$ " + f"= {round(koutecky_slope)} " + "$ω^{-0.5}$" + f", on set current: {round(on_set_current * 1000, 3)} mA"

                data_koutecky["koutecky_fit"] = koutecky_slope * data_koutecky["reci_sqrt_rotation_rate"] + koutecky_intersect

                """ add isolated data and data fit to ax[1,0]
                    add data to self.data_koutecky DataFrame for saving later
                """
                ax[1,1].scatter(data_koutecky["reci_sqrt_rotation_rate"], data_koutecky["reci_current"], marker = "x", s = 10, label = koutecky_label)
                ax[1,1].plot(data_koutecky["reci_sqrt_rotation_rate"], data_koutecky["koutecky_fit"], ls = "--")
                ax[1,1].legend(fontsize = 8, loc = "upper left")

                self.results_koutecky[str(round(xmin, 3))] = [koutecky_slope, koutecky_intersect, on_set_current]

                self.data_koutecky[f"Reciprocal Current (A^-1) @ {round(xmin, 3)} V"] = data_koutecky["reci_current"]
                self.data_koutecky[f"Reciprocal Root of Rotation Rate () @ {round(xmin, 3)} V"] = data_koutecky["reci_sqrt_rotation_rate"]
                self.data_koutecky[f"Koutecky Slope () @ {round(xmin, 3)} V"] = [koutecky_slope] + [np.nan] * (len(self.data_koutecky) - 1)
                self.data_koutecky[f"Koutecky Intersect (A^-1) @ {round(xmin, 3)} V"] = [koutecky_intersect]+ [np.nan] * (len(self.data_koutecky) - 1)
                self.data_koutecky[f"On Set Current (mA) @ {round(xmin, 3)} V"] = [round((on_set_current * 1000), 3)] + [np.nan] * (len(self.data_koutecky) - 1)
                
                """ display results obtained by Koutecky-Levich fit in GUI
                """
                get_results_frame()


            def get_evaluation_frame() :
                """ when the evaluation is exectuted a tkinter.Frame is created in the self.program_frame, which acts as a control panel for the evaluation
                    it contains two further tkinter.Frame´s, which represent the
                    - levich fit control panel (upper frame)
                    - koutecky-levich fit control (lower frame)

                    one of those control panels contains
                    - tkinter.Label 
                        for labeling each frame for the User, which is represented by which
                    - tkinter.Entry´s 
                        for entering potentials for the fits
                        multiple entries at once are possible by seperating the entries with ;
                        decimals can be entered either by . or , 
                    - tkinter.Button´s 
                        for executing the following functions:
                            - get_levich_potential: 
                                gets the entered potentials by User in the entry field for the levich fit
                                exectutes the function levich_onselect directly afterwards
                                if an entry fails, this position is skipped and an Error Feedback is displayed informing the User
                                the remaining valid position are still executed
                                multiple positions can be entered by seperation with ;
                            - get_koutecky_potential: 
                                gets the entered potentials by User in the entry field for the koutecky-levich fit
                                executes the function koutecky_levich_onselect directly afterward
                                if an entry fails, this position is skipped and an Error Feedback is displayed informing the User
                                the remaining valid positions are still executed
                                multiple positions can be entered by seperation with ;
                            - clear_levich_plot and clear_koutecky_plot:
                                clears levich plot ax[0,1] and koutecky plot ax[1,1] (removes existing fits and title)
                                clears the self.results_levich and self.results_koutecky DataFrame´s
                            - self.save_levich_results and self.save_koutecky_results:
                                saves the existing version of the self.results_levich and self.results_koutecky DataFrame´s to txt file
                """
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
                    """ gets the set potentials for the levich fit and executes the function levich_onselect for each entry afterwards
                        invalid entry´s are skipped and an Error Feedback is displayed
                        multiple entries can be entered by seperation with ;
                    """
                    entries = levich_entry.get()
                    entries = entries.replace(",", ".")
                    entries = entries.split(";")

                    for entry in entries :
                        try :
                            entry = float(entry)
                        except ValueError :
                            self.feedback_label.config(text = f"Failed to convert {entry} to a valid input.")
                            continue
                        levich_onselect(entry, 2) # 2 is for xmax (is arbitrarily chosen)

                def get_koutecky_potential() :
                    """ gets the set potentials for the koutecky-levich fit and executes the function koutecky_levich_onselect for each entry afterwards
                        invalid entry´s are skipped and an Error Feedback is displayed
                        multiple entries can be entered by seperation with ;
                    """
                    entries = koutecky_entry.get()

                    entries = entries.replace(",", ".")

                    entries = entries.split(";")

                    for entry in entries :
                        try :
                            entry = float(entry)
                        except ValueError :
                            self.feedback_label.config(text = f"Failed to convert {entry} to a valid input.")
                            continue
                        koutecky_levich_onselect(entry, 2) # 2 is for xmax (is arbitrarily chosen)

                potential_levich_button = tk.Button(master = levich_frame, text = "Set Potential", command = get_levich_potential)
                potential_levich_button.grid(row = 0, column = 2, padx = 5, pady = 5)

                potential_koutecky_button = tk.Button(master = koutecky_frame, text = "Set Potential", command = get_koutecky_potential)
                potential_koutecky_button.grid(row = 0, column = 2, padx = 5, pady = 5)

                def clear_levich_plot() :
                    """ clears the levich plot ax[0,1] (removes existing fits and title)
                        clears the self.result_levich DataFrame
                    """
                    ax[0,1].clear()
                    ax[0,1].set_xlabel("$ω^{0.5}$ (rad/s$)^{0.5}$")
                    ax[0,1].set_ylabel("Current (mA)")

                    self.results_levich = pd.DataFrame(index = ["levich_slope", "levich_intersect"])

                def clear_koutecky_plot() :
                    """ clears the koutecky-levich plot ax[1,1] (removes existing fits and title)
                        clears the self.result_levich DataFrame
                    """
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

                """ get an results_frame for the evalution_frame
                    append the evalution_frame to the self.active_evaluation_frames list """
                get_results_frame()

                self.active_evaluation_frames.append(evalution_frame)

            """ create a frame, which acts as a control panel for the evaluation 
            """
            get_evaluation_frame()

            """ create a datas dic with the data of each sample as value and the sample name as key

                create the figure for the evaluation wíth two rows and two columns
                - ax[0,0] (upper left) and ax[1,0] (lower left) display the same current vs potential 
                - ax[1,0] (upper right) display the levich fit data currents vs square root rotation rates
                - ax[1,1] (lower right) display the koutecky fit dada reciprocal currents vs reciprocal square root rotation rates
            """
            datas = {}
            fig, ax = plt.subplots(2,2)

            """ loop through each dataset individually
            """
            for n, file_path in enumerate(self.file_paths) :
                """ get the sample_name and rpm value of each sample
                 """
                sample_name = self.sample_names[n]
                rpm = self.rpm_values[sample_name]

                """ open raw data set and rename columns
                """
                data = pd.read_csv(file_path, delimiter = ";")
                data.rename(columns = {"WE(1).Potential (V)":"potential", "WE(1).Current (A)" :"current"}, inplace = True)

                """ plot current (in mA) vs potential (V) in ax[0,0] and ax[1,0]
                """
                ax[0,0].plot(data["potential"], data["current"] * 1000, label = sample_name)
                ax[1,0].plot(data["potential"], data["current"] * 1000)

                """ calculate rotation rate from rpm by the fomular: 
                    rotation_rate = 2 * pi / (60 * rpm) 
                    calculate square root of the rotation rate

                    calculate reciprocal current and reciprocal square root rotation rate
                """
                rotation_rate = (2 * np.pi) / 60 * rpm
                data["rotation_rate"] = [rotation_rate] * len(data)
                data["sqrt_rotation_rate"] = np.sqrt(data["rotation_rate"])

                data["reci_current"] = 1 / data["current"]
                data["reci_sqrt_rotation_rate"] = 1 / data["sqrt_rotation_rate"]

                """ create a new DataFrame containing the processed data
                    save data_save as a txt file

                    append data to datas dictionary as value and use the sample_name as key
                """
                data_save = pd.DataFrame()
                data_save["Potential (V)"] = data["potential"]
                data_save["Current (A)"] = data["current"]
                data_save["Rotation Rate (rad/s)"] = data["rotation_rate"]
                data_save["Root Rotation Rate (rad/s)^0.5"] = data["sqrt_rotation_rate"]
                data_save["Reciproce Root Rotation Rate (rad/s)^-0.5"] = data["reci_sqrt_rotation_rate"]

                data_save.to_csv(f"{self.path_evaluation_folder}\{sample_name}.txt", header = data_save.columns, index = None, sep = ";")

                datas[sample_name] = data

            """ add title, legend, x and y axis label to axis in figure
            """
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

            """ create SpanSelector´s in ax[0,0] and ax[1,0] for levich-fit in ax[0,1] and koutecky-levich fit in ax[1,1]
                both SpanSelector´s accept an horizontal range selection by User and uses the lower range for the fits (the upper range is discarded)
                keyword useblit: no clue what it does but it works
                    in the official documentation the following is stated:
                    'If True, use the backend-dependent blitting features for faster canvas updates.' 
                    (https://matplotlib.org/stable/api/widgets_api.html#matplotlib.widgets.SpanSelector, 01.02.22)
                    don´t know what to do with that information

                show figure to User for evaluation and range selection
            """

            spanner_levich = SpanSelector(ax[0,0], levich_onselect, "horizontal", useblit = True)
            spanner_koutecky_levich = SpanSelector(ax[1,0], koutecky_levich_onselect, "horizontal", useblit = True)

            plt.show()

            """ evaluation finished
                set self.change_rpm_button back on grid
            """
            self.change_rpm_button.grid(row =0, column = 2, padx = 5, pady = 5)

            if self.save_figures :
                """ save figure automatically if state True
                    counts all files in the evaluation folder with an .jpg ending
                    adds the count at the end of the file_name
                """
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
        """ gets entered rpm values in tkinter.Entry´s in sample_rpm_frame
            sets at start of execution the safty switch self.start_evaluation to False

            loops through all tkinter.Entry´s in self.rpm_entries and count successful conversion/entering
            if count equal to number of repetions the safty switch self.start_evaluation to True
            otherwise an Error Feedback is given back

            valid inputs are int/float
            decimals can be entered by . or ,
            the respective labels displaying the current set rpm value for each sample are updated after a successful conversion

            count is started at -1 since enumerate start at 0 
        """
        
        self.start_evaluation = False
        count = -1
        for n, rpm_entry in enumerate(self.rpm_entries) :
            entry = rpm_entry.get()

            entry = entry.replace(",", ".")

            if entry != "" :
                try :
                    entry = float(entry)
                    self.rpm_values[self.sample_names[n]] = entry
                    count += 1
                except ValueError :
                    self.feedback_label.config(text = f"Please enter a valid input for {self.sample_names[n]}.")
                    continue

                self.rpm_labels[n].config(text = f"{entry}")
            else :
                count += 1
                continue

        if n == count :
            self.feedback_label.config(text = "Evaluation can be started.")
            self.start_evaluation = True


    def open_files(self) :
        """ gets selected files by User and add those to self.file_paths

        """
        
        root = tk.Tk()
        file_paths = filedialog.askopenfilenames(parent = root, filetypes=[("Text files","*.txt")])
        root.destroy()

        if len(file_paths) > 0 :
            """ close all active frames in the lists if new were selected:
            - self.active_rpm_frames
            - self.active_evaluation_frames
            - self.active_resutls_frame

            set state of safty switch self.start_evaluation to False

            clear the existing list self.sample_names

            create a new tkinter.Frame containing:
            - tkinter.Label´s:
                representing the selected samples and currently set rpm values
            - tkinter.Entry´s:
                for entering new rpm value by User for each respective sample 
            - tkinter.Button:
                to get the enterd rpm values by the User

            clear existing lists self.rpm_labels and self.rpm_entries
            """
            self.start_evaluation = False
            
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

            """ loop through each file_path and count all failed automatic rpm recognitions
            """
            count = 0
            for n, file_path in enumerate(file_paths) :
                """ get the sample_name and append it to the list self.sample_names
                    create a tkinter.Label with the content of sample_name as text
                """
                file_name = os.path.basename(file_path)
                sample_name = file_name.split(".txt")[0]

                self.sample_names.append(sample_name)

                sample_label = tk.Label(master = sample_rpm_frame, text = f"{sample_name}")
                sample_label.grid(row = n + 1, column = 0, padx = 5, pady = 5)
                """ try to find a rpm value at the end the sample_name
                    in order for the automatic rpm value recognintion to work the following format for the file_name has to be chosen:
                    *_100RPM.txt or *_100rpm.txt
                     * name of the sample

                    the recognition works by splitting the sample_name at each '_' and using the last fragment/element
                    searching for 'rpm' or 'RPM' in the fragment and splitting it
                    it uses the first fragment and tries to convert it into an int
                    if that mechanism fails an Error Feedback is given back

                    let´s use an example: 
                     sample_name = "example_file_100RPM"
                     after the first split: rpm = ["example", "file", "100RPM"]
                     use last fragment/element : rpm = "100RPM"
                     after the second split rpm = ["100"]
                     try to convert first fragment/element into an int
                """
                rpm = sample_name.split("_")[-1]
                if "rpm" in rpm :
                    rpm = rpm.split("rpm")[0]

                    try :
                        rpm = int(rpm)
                    except ValueError :
                        count += 1
                        rpm = "automatic RPM recognition failed"

                elif "RPM" in rpm :
                    rpm = rpm.split("RPM")[0]

                    try :
                        rpm = int(rpm)
                    except ValueError :
                        count += 1
                        rpm = "automatic RPM recognition failed"

                else :
                    count += 1
                    rpm = "automatic RPM recognition failed"

                """ add determined rpm value in a tkinter.Label and display it in the sample_rpm_frame
                    add tkinter.Entry´s to the sample_rpm_frame for changing the rpm values

                    add the tkinter.Label and tkinter.Entry to the list self.rpm_labels and self.rpm_entries

                    add the rpm value to dict self.rpm_values as value and the sample_name as key
                    add the sample_rpm_frame to the self.active_rpm_frames list

                    add file_paths to self.file_paths
                """
                rpm_label = tk.Label(master = sample_rpm_frame, text = f"{rpm}")
                rpm_label.grid(row = n + 1, column = 1, padx = 5, pady = 5)

                self.rpm_labels.append(rpm_label)

                rpm_entry = tk.Entry(master = sample_rpm_frame)
                rpm_entry.grid(row = n + 1, column = 2, padx = 5, pady = 5)

                self.rpm_entries.append(rpm_entry)

                self.rpm_values[sample_name] = rpm

                self.active_rpm_frames.append(sample_rpm_frame)

                self.file_paths = file_paths

            if count == 0 :
                self.start_evaluation = True
                self.feedback_label.config(text = "Please check the determined RPM values. Evaluation can be started.")
            else :
                self.feedback_label.config(text = "Please check the determined PRM values.")


    def get_gui_frame(self, master) :
        """ returns a tkinter.Frame for a master window (tkinter.Tk)
            this frame needs to contain all necassyry widgets/functions required for the evalution
            the grid placement was chosen since it is one of the simplest and cleanest options for a clean tkinter based User Interface
        """

        """ reset atrributes in order to clean existing dictionaries and lists with previous data
        """
        self.reset_attributes()

        self.program_frame = tk.Frame(master = master, relief = "groove", borderwidth = 2)
        self.program_frame.grid(row = 1, column = 1, padx = 5, pady = 5)
        
        """ create a tkinter.Frame, which gives general control over the program by containing:
            - tkinter.Label as Feedback label for Error Messages
            - tkinter.Buttons with access to the following functions:
                - self.open_files 
                    gets file_paths from User Selection
                - self.run_evaluation
                    executes the evaluation if the safty switch state is True
        """
        control_frame = tk.Frame(master = self.program_frame, relief = "groove", borderwidth = 2)
        control_frame.grid(row = 0, column = 0, padx = 5, pady = 5)

        open_files_button = tk.Button(master = control_frame, text = "Open Files", command = self.open_files)
        open_files_button.grid(row = 0, column = 0, padx = 5, pady = 5)

        self.feedback_label = tk.Label(master = control_frame, text = "Please select your raw data files first.", font = "Arial")
        self.feedback_label.grid(row = 0, column = 1, padx = 5, pady = 5)

        run_evaluation_button = tk.Button(master = control_frame, text = "Start Evaluation", command = self.run_evaluation)
        run_evaluation_button.grid(row = 0, column = 2, padx = 5, pady = 5)

        """ create a tkinter.ttk.Checkbutton, which contains the state of the self.save_figure variable
            default state: False
        """
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

"""
update list: 
Version 1.0.2 (28.03.2022)

- added filetypes argument for tkinter.filedialog.askopenfilenames function to show only necessary files for the program
  in this case: ["Text Files", "*.txt"]
"""