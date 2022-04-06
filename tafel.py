""" Tafel Analysis Tool by Pascal Reiß
    Version 1.0.3
"""

import os
import numpy as np
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.widgets import SpanSelector
from datetime import datetime



class Tafel_Analysis :

    def __init__(self) :

        """ initiate Tafel_Analysis class with the following attributes:
            - self.file_paths 
                (tuple: contains all file_paths for all selected raw data files by the User)
            - self.resistances 
                (dict: contains all resistances (Ω) of the samples as values with the file_paths as keys)
            - self.resistance_entries 
                (list: contains all tkinter.Entry created during the self.get_gui_frame function for entering the resistances
                for each sample by User in GUI)
            - self.resistance_labels
                (list: contains all tkinter.Labels created during the self.get_gui_frame function for displaying the current
                set resistances for each sample in the GUI)
            - self.failed_entries 
                (list: contains all failed entries from the resistance inputs if some entries did not correspond to the 
                expected input)
            - self.start_evaluation
                (boolean: contains state if evaluation can be started or not
                state is set True if for each sample a valid resistance input is set)
            - self.active_frames: 
                (list: contains all active tkinter.Frames created during the evaluation process (like frame which contains
                all results for each sample) so those can be closed if new files are selected)
            - self.program_frame
                (tkinter.Frame: contains all widgets/function necassary for the evaluation with the GUI interface (tkinter.Tk))
            - self.feedback_label
                (tkinter.Label: contains all feedback messages for the User if an execution was successful or failed)
            - self.save_figures
                (boolean: contains state if figures shall be saved or not
                state can be changed by User in the GUI
                default setting: False)
        """

        self.program_name = "Tafel Analysis"

        """ set up basic attributes and parameters necessary for the class and evaluation """
        self.reset_attributes()
        self.reset_parameters()

        self.program_frame = None

        self.feedback_label = None

        self.save_figures = False

        """ create evalution folder if it does not exist yet
        path_evalutation_folder: */Evaluation/Tafel Analysis/**
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



        """ constants necassary for the evaluation 
            can not be changed since those values are constants
        """
        self.gas_constant = 8.314 # kg m²/(s² mol K)
        self.faraday_constant = 9.649 * 10**4 # in A s/mol
        self.standard_potential_KCl = 0.205 # doctor thesis from Miriam Goll (2017) "Maßschneidern von elektroaktiven organischen und anorganischen Funktionsmaterialien elektrochemische Anwendungen"
        self.water_splitting_potential = 1.229 # in V
        self.CD_treshold = 10 # in mA/cm²


    def reset_attributes(self) :
        """ resets all attributes for Tafel_Analysis class object if desired by User or required for opening new files
            is executed once if a new Tafel_Analysis class object is initiated to set those as attributes of the object
        """

        self.file_paths = ()
        self.resistances = {}
        self.resistance_entries = []
        self.resistance_labels = []
        self.start_evaluation = False
        self.failed_entries = []
        self.active_frames = []


    def reset_parameters(self) :
        """ resets all parameters for Tafel_Analysis class object if desired by User
            is executed once if a new Tafel_Analysis class object is initiated to set those as attributes of the 
            Tafel_Analysis class object
        """

        self.area_electrode = 1 # in cm²
        self.pH = 13
        self.number_of_exchanged_electrons = 1
        self.temperature = 298 # in K


    def get_potential_correction(self, potential, current, resistance) :
        """ returns the iR corrected potential of the data set by the formular
            potential = potential - current * resistance

            expected argument datatypes:
            - potential : pandas.Series (V)
            - current : pandas.Series (A)
            - resistance : int/float (Ω)

            returns corrected potential : pandas.Series (V)
        """
        return potential - current * resistance


    def get_SHE_potential(self, potential) :
        """ returns the potential of the standard hydrogen electrode (SHE) by the formular
            potential = potential + 0.059 * pH * E0(KCl-electrode)

            expected argument datatypes:
            - potential : pandas.Series (V)

            returns SHE potential : pandas.Series (V) 
        """
        return potential + 0.059 * self.pH + self.standard_potential_KCl


    def get_current_density(self, current) :
        """ returns the current density of the data set by the formular
            current_density = current / area_electrode
            
            expected argument datatypes:
            - current : pandas.Series (A)

            returns current density : pandas.Series (mA/cm²)
        """
        return current * 1000 / self.area_electrode


    def run_evaluation(self) :
        """ does the actual evaluation of the selected data
            does only trigger if the following conditions are met:
            - len(self.file_paths) > 0 (files have been selected in the first place)
            - len(self.resistances) and len(self.file_paths) identical (for each sample a resistance is given)
            - self.start_evaluation == True (program accepts all inputs as valid and enables the evaluation)

            if not all requirements are met an Error feedback is given back to the User informing him/her if not all samples
            have a resistance set yet or no files were selected in the first place
        """

        if len(self.file_paths) > 0 and len(self.resistances) == len(self.file_paths) and self.start_evaluation == True :
            self.feedback_label.config(text = "Evaluation in progress.")

            def tafel_onselect(xmin, xmax) :
                """ function behind the SpanSelector object in ax[1] (right plot in figure of a single sample plot)
                    accepts a horizont range selection by the User for fitting data with Tafel Fit
                """

                """ clear ax[1] to remove title informing User to select a range for the Tafel Fit
                    scatter data set in ax[1]
                """
                ax[1].clear() 

                ax[1].scatter(data["overpotential"], data["log_current_density"], marker = "x", label = sample_name)

                """ get data from selected range and fit those linear to get the tafel_slope and tafel_intersect
                    get exchange current density by 10**tafel_intersect 
                """
                data_fit = data[data["overpotential"] >= xmin]
                data_fit = data_fit[data_fit["overpotential"] <= xmax]

                """ linear fit"""
                fit = np.polyfit(data_fit["overpotential"], data_fit["log_current_density"], 1)

                tafel_slope, tafel_intersect = fit[0], fit[1]

                exchange_current_density = 10**tafel_intersect

                """ calculate values for displaying the fit in a plot in the graph
                """
                data["tafel_fit"] = tafel_slope * data["overpotential"] + tafel_intersect

                """ generate Tafel equation depending on the value of the intersect for display in ax[1] 
                Tafel equation is displayed as plot label in ax[1] for the calculated fit data"""
                if tafel_intersect > 0 :
                    fit_label = f"lg(j) = {round(tafel_slope, 3)} η + {round(tafel_intersect, 3)}"
                elif tafel_intersect < 0 :
                    fit_label = f"lg(j) = {round(tafel_slope, 3)} η - {round(abs(tafel_intersect), 3)}"
                elif tafel_intersect == 0 :
                    fit_label = f"lg(j) = {round(tafel_slope, 3)} η"

                ax[1].plot(data["overpotential"], data["tafel_fit"], ls = "--", label = fit_label)

                """ set axis label and add legend to ax[1] """
                ax[1].set_xlabel("η [V]")
                ax[1].set_ylabel("lg(j) [mA/cm²]")

                ax[1].legend(loc = "lower right", fontsize = 8)

                """ add calculated fit values to existing DataFrame for saving the evaluated data
                    add calculated fit values to result_frame"""
                data_save["Tafel Fit"] = data["tafel_fit"]
                data_save["Tafel Slope"] = [tafel_slope] + [np.nan] * (len(data_save) - 1)
                data_save["Tafel Intersect"] = [tafel_intersect] + [np.nan] * (len(data_save) - 1)

                results_for_gui.at["exchange_current_density", sample_name] = exchange_current_density
                results_for_gui.at["tafel_slope", sample_name] = tafel_slope
                results_for_gui.at["tafel_intersect", sample_name] = tafel_intersect

                """ add fit_label as value to fit_labels dictionary use the sample_name as key
                """
                fit_labels[sample_name] = fit_label

            """ create lists containing the index and values of datapoints at specific threshold values
                this is necassary to mark those tresholds correctly in the collective figure
            """
            idx_CDs, idx_water_splittings = [], []
            overpotential_Ags, overpotential_SHEs = [], []
            potential_CD_treshold_Ags, potential_CD_treshold_SHEs = [], []

            """ fit_labels dictionary
                contains the fit_label´s of the Tafel fit as values whereas the sample_name is used as key

                datas dictionary
                contains the dataset´s of each sample as value whereas the sample_name is used as key
            """
            fit_labels = {}

            datas = {}

            """ create a DataFrame containing all obtained results for each sample (sample_name as columns) for the result_frame
                in the GUI
            """
            results_for_gui = pd.DataFrame(\
                index = ["overpotential_Ag", "overpotential_SHE", "exchange_current_density", "tafel_slope", "tafel_intersect"])

            """ loop through each file indivdually
            """
            for n, file_path in enumerate(self.file_paths) :
                
                """ get resistance, file_name and sample_name of the sample from the self.resistances dictionary and file_path 
                """
                resistance = self.resistances[file_path]
                file_name = os.path.basename(file_path)
                sample_name = file_name.split(".txt")[0]
                
                """ opening raw data """
                data = pd.read_csv(file_path, delimiter = ";")

                """ calculate potentials vs Ag|AgCl by correction with its current and resistance (in V)
                calculate corrected potentials vs SHE by Ec = Ei + 0.059 * pH + standard_potential_KCl (in V)
                calculate current density by division with the area_electrode (in mA/cm²) 
                """
                
                data["E_vs_Ag"] = self.get_potential_correction(data["WE(1).Potential (V)"], data["WE(1).Current (A)"], resistance) # correction of potential
                data["E_vs_SHE"] = self.get_SHE_potential(data["E_vs_Ag"]) # correction of potential vs SHE

                data["current_density"] = self.get_current_density(data["WE(1).Current (A)"])  # current density in mA/cm²

                """ calculate log10 of current density and overpotential of each data point
                """
                data["log_current_density"] = np.log10(data["current_density"])
                data["overpotential"] = data["E_vs_SHE"] - self.water_splitting_potential

                """ determine datapoint/index of datapoint where the 
                    - current density threshold 
                    - water splitting potential
                    are reached
                    
                    calculate the overpotentials for the Ag and SHE electrode
                    append these values to the respective lists
                """
                data_over_CD_threshold = data[data["current_density"] >= self.CD_treshold]
                data_over_water_splitting_potential = data[data["E_vs_SHE"] >= self.water_splitting_potential]

                idx_treshold_CD = data_over_CD_threshold.index.tolist()[0]
                idx_CDs.append(idx_treshold_CD)

                idx_water_splitting = data_over_water_splitting_potential.index.tolist()[0]
                idx_water_splittings.append(idx_water_splitting)

                overpotential_Ag = data.at[idx_treshold_CD, "E_vs_Ag"] - data.at[idx_water_splitting, "E_vs_Ag"]
                overpotential_Ag = round(overpotential_Ag, 3)
                overpotential_Ags.append(overpotential_Ag)

                overpotential_SHE = data.at[idx_treshold_CD, "E_vs_SHE"] - self.water_splitting_potential
                overpotential_SHE = round(overpotential_SHE, 3)
                overpotential_SHEs.append(overpotential_SHE)

                potential_CD_treshold_Ags.append(data.at[idx_treshold_CD, "E_vs_Ag"])
                potential_CD_treshold_SHEs.append(data.at[idx_treshold_CD, "E_vs_SHE"])

                """ create the figure with two axis
                    - ax[0] (left axis) : current density vs potential SHE (regular axis) or potential Ag (twiny axis)
                    - ax[1] (right axis) : log(current density) vs overpotential

                    ax[0] has a twiny axis (enables displaying Ag and SHE potential as x-axis simultaneously)
                """

                fig, ax = plt.subplots(2)
                ax_twiny = ax[0].twiny()
                ax[0].scatter(data["E_vs_SHE"], data["current_density"], label = f"{file_name} SHE", marker = "x")
                ax_twiny.scatter(data["E_vs_Ag"], data["current_density"], label = f"{file_name} Ag", marker = "+")

                """ add vertical and horizontal lines indicating the positions of the current density threshold and
                    water splitting potential
                """
                ax[0].axvline(self.water_splitting_potential, ls = "--", lw = 0.8, c = "grey")
                ax[0].axhline(self.CD_treshold, ls = "--", lw = 0.8, c = "grey")

                """ add vertical line up to ymax (given as a vector between 0 and 1) representing the value of 
                    self.CD_treshold to indicate reached potential for the sample when the current density threshold is reached
                """
                ylim = ax[0].get_ylim()
                ymax = (self.CD_treshold - ylim[0]) / (ylim[1] - ylim[0])

                ax[0].axvline(data.at[idx_treshold_CD, "E_vs_SHE"], ymax = ymax, ls = "--", lw = 0.8)

                """ add legend and x and y axis label for ax[0] and ax[1]
                    plot data as scatter plot: log(current density) vs overpotential
                """
                ax[0].legend(loc = "upper left")
                ax[0].set_xlabel("$E_{WE}$ vs SHE -iR [V]")
                ax_twiny.set_xlabel("$E_{WE}$ vs Ag|AgCl -iR [V]")
                ax[0].set_ylabel("j [mA/cm²]")

                ax[1].scatter(data["overpotential"], data["log_current_density"], label = file_name, marker = "x")

                """ set title for ax[1], which informs User to select a range in ax[1] to calculate the Tafel Fit for
                the dataset
                """
                ax[1].set_title(label = "Please select the range in the plot below, which shall be fitted.")
                
                ax[1].legend(loc = "lower right")
                ax[1].set_xlabel("η [V]")
                ax[1].set_ylabel("lg(j) [mA/cm²]")

                """ create the tafel_spanner object
                    enables User to select a horizontal range in ax[1] and executes the function tafel_onselect
                    tafel_onselect accepts two arguments (xmin : int/float, xmax : int/float) and calculates
                    the Tafel Fit
                    lower range of selected range is set as xmin, whereas the higher range is set as xmax
                    keyword useblit: no clue what it does but it works
                        in the official documentation the following is stated:
                        'If True, use the backend-dependent blitting features for faster canvas updates.' 
                        (https://matplotlib.org/stable/api/widgets_api.html#matplotlib.widgets.SpanSelector, 01.02.22)
                        don´t know what to do with that information
                """
                
                tafel_spanner = SpanSelector(ax[1], tafel_onselect, "horizontal", useblit = True)

                """ set size of figure, so when figure is saved automatically the right format is used
                    default would save as in small window instead of full screen format"""
                fig.set_size_inches(10,10)

                """ create a new DataFrame, which contains all relevant data from the evaluation
                    data obtained by Tafel Fit is added later in function tafel_onselect
                """
                data_save = pd.DataFrame()
                data_save["Current Density (mA/cm²)"] = data["current_density"]
                data_save["log Current Density"] = data["log_current_density"]
                data_save["Potential Ag-E (V)"] = data["E_vs_Ag"]
                data_save["Potential SHE (V)"] = data["E_vs_SHE"]
                data_save["Overpotential (V)"] = data["overpotential"]
                data_save["Overpotential at Treshold (V)"] = [overpotential_SHE] + [np.nan] * (len(data_save) - 1)

                """ add results to results_for_gui DataFrame
                    results and data obtained by Tafel Fit is added later in function tafel_onselect
                """
                results_for_gui.at["overpotential_Ag", sample_name] = overpotential_Ag
                results_for_gui.at["overpotential_SHE", sample_name] = overpotential_SHE
                
                """ show figure so User can fit data by selecting range in ax[1] (right image)
                """
                plt.show()

                if self.save_figures == True :
                    """ save figure as jpg file if self.save_figures True
                    """
                    path = f"{self.path_evaluation_folder}\{sample_name}.jpg"
                    fig.savefig(path)

                """ save data_save DataFrame as txt file 
                    add data DataFrame to datas dictionary as value and sample_name as key
                """
                data_save.to_csv(f"{self.path_evaluation_folder}\{sample_name}.txt", header = data_save.columns, index = None, sep = ";")

                datas[sample_name] = data

            """ create collective plot with four axis (2 rows and 2 columns, contains all samples)
                - ax[0,0] (upper left axis) : current density vs contains potential SHE (regular axis) or potential Ag (twiny axis) 
                - ax[0,1] (upper right axis) : current density vs potential SHE
                - ax[1,0] (lower left axis) : current density vs potential Ag
                - ax[1,1] (lower right axis) : log(current density) vs overpotential + Tafel-Fit of each sample

            """
            fig, ax = plt.subplots(2,2)

            ax_twiny = ax[0,0].twiny()

            """ add vertical and horizontal lines to indicate the current density thresholds and water splitting potential 
                in ax[0,0], ax[0,1] and ax[1,0] """

            ax[0,0].axvline(self.water_splitting_potential, ls = "--", lw = 0.8, c = "grey")
            ax[0,0].axhline(self.CD_treshold, ls = "--", lw = 0.8, c = "grey")


            ax[0,1].axvline(self.water_splitting_potential, ls = "--", lw = 0.8, c = "grey")
            ax[0,1].axhline(self.CD_treshold, ls = "--", lw = 0.8, c = "grey")


            ax[1,0].axhline(self.CD_treshold, ls = "--", lw = 0.8, c = "grey")

            """ loop through each key and value of the datas dictionary and plot (scatter) the data for each sample
                get for each repetion of the loop an individual color from the matplotlib color pool and save these colors
                in the colors list --> all plots of the same sample have the same color

                matplotlib color pool: https://matplotlib.org/stable/gallery/color/named_colors.html, 01.02.2022
                selected color pool from Tableau Palette
            """
            n = 0
            colors = []
            for sample_name, data in datas.items() :
                color = next(ax[0,0]._get_lines.prop_cycler)['color']
                colors.append(color)
                ax[0,0].scatter(data["E_vs_SHE"], data["current_density"], label = sample_name, marker  = "x", s = 10, c = color)
                ax_twiny.scatter(data["E_vs_Ag"], data["current_density"], marker = "x", s = 10, c = color)
                
                ax[0,1].scatter(data["E_vs_SHE"], data["current_density"], label = sample_name, marker = "x", s = 10, c = color)
                ax[1,0].scatter(data["E_vs_Ag"], data["current_density"], label = sample_name, marker  = "x", s = 10, c = color)

                ax[1,1].scatter(data["overpotential"], data["log_current_density"], label = sample_name, marker = "x", s = 10, c = color)

                try :
                    ax[1,1].plot(data["overpotential"], data["tafel_fit"], label = fit_labels[sample_name], ls = "--", c = color)
                except KeyError :
                    self.feedback_label.config(text = f"Tafel Fit for {sample_name} has not been determined.")
                
                ax[1,0].axvline(data.at[idx_water_splittings[n], "E_vs_Ag"], ls = "--", lw = 0.8, c = "grey")

                n += 1

            """ add x and y axis label and legend to all axis
            """
            ax[0,0].set_xlabel("$E_{WE}$ vs SHE -iR [V]")
            ax[0,0].set_ylabel("j [mA/cm²]")
            ax[0,0].legend(loc = "upper left", fontsize = 8)

            ax_twiny.set_xlabel("$E_{WE}$ vs Ag|AgCl -iR [V]")

            ax[0,1].set_xlabel("$E_{WE}$ vs SHE -iR [V]")
            ax[0,1].set_ylabel("j [mA/cm²]")
            ax[0,1].legend(loc = "upper left", fontsize = 8)

            ax[1,0].set_xlabel("$E_{WE}$ vs Ag|AgCl -iR [V]")
            ax[1,0].set_ylabel("j [mA/cm²]")
            ax[1,0].legend(loc = "upper left", fontsize = 8)

            ax[1,1].set_xlabel("η [V]")
            ax[1,1].set_ylabel("lg(j) [mA/cm²]")
            ax[1,1].legend(loc = "upper left", fontsize = 8)

            """ get the ylim of ax[0,1] 
                calculate the value of the set current density threshold as a vector between 0 and 1
                add a vertical line indicating the reached threshold for each sample by looping through each data_set individauly
                the respective sample colors are chosen from the colors list
            """
            ylim = ax[0,1].get_ylim()
            ymax = (self.CD_treshold - ylim[0]) / (ylim[1] - ylim[0])

            for n, data in enumerate(datas.values()) :
                ax[0,1].axvline(data.at[idx_CDs[n], "E_vs_SHE"], ymax = ymax, ls  = "--", c = colors[n])
                ax[1,0].axvline(data.at[idx_CDs[n], "E_vs_Ag"], ymax = ymax, ls  = "--", c = colors[n])


            """ create a tkinter.Frame which is set into the self.program_frame grid
                this frame contains a table, which displays all obtained results from the Tafel Analysis
                
                loop through all obtained results from the results_for_gui DataFrame and add those in tkinter.Labels 
                in the results frame in form of a table
                table is set up as follows:
                    - rows: samples
                    - columns: results (results labels are added in a later loop)
            """
            results_frame = tk.Frame(master = self.program_frame, relief = "groove", borderwidth = 2)
            results_frame.grid(row = 2, column = 0, pady = 5, padx = 5)

            for n, sample_name in enumerate(results_for_gui) :
                label = tk.Label(master = results_frame, text = f"{sample_name}")
                label.grid(row = n + 1, column = 0, padx = 3, pady = 3)

                for m, result in enumerate(results_for_gui.index) :
                    label = tk.Label(master = results_frame, text = f"{round(results_for_gui.at[result, sample_name], 3)}")
                    label.grid(row = n + 1, column = m + 1, padx = 3, pady = 3)

            for n, result in enumerate(["Overpotential Ag|AgCl (V)", "Overpotential SHE (V)", \
                "Exchange Current Density (mA/cm²)", "Tafel Slope (V/dec)", "Tafel Intersect (mA/cm²)"]) :
                label = tk.Label(master = results_frame, text = f"{result}")
                label.grid(row = 0, column = n + 1, padx = 3, pady = 3)

            """ evaluation finished
                add results_frame to self.active_frames so that at a later point if new files were selected the results_frame can be disabled
                show collective figure to User
            """
            self.feedback_label.config(text = "Evaluation finished.")

            self.active_frames.append(results_frame)

            plt.show()

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
                fig.savefig(f"{self.path_evaluation_folder}\Tafel_{count}.jpg")

        elif len(self.resistances) < len(self.file_paths) or len(self.failed_entries) > 0 :
            self.feedback_label.config(text = "Please enter all resistances first.")

        elif len(self.file_paths) == 0 :
            self.feedback_label.config(text = "Please select your raw data files first.")


    def open_files(self) :
        """ get file_paths from User
            all active_frames in the window are disabled from the self.active_frames list
            during the execution of this function all set attributes of the Tafel_Analysis class object are reseted so no resistances from earlier samples 
            are imported into the new evaluation cycle
            
            if file selection was succesful (len(file_paths) > 0) a new tkinter.Frame is added to the self.program_frame
            the new selected_sample_frame contains a table of all selected samples and their respective resistance values
            next to them are tkinter.Entry´s for entering the resistance by the User
            the created resistance_label´s and resistance_entry´s are added to the resistance_labels and resistance_entries lists
            the selected_sample_frame is added to the self.active_frames list

            set the obtained file_paths as self.file_paths
        """

        for active_frame in self.active_frames :
            active_frame.grid_forget()

        self.reset_attributes()

        root = tk.Tk()
        file_paths = filedialog.askopenfilenames(parent = root, filetypes=[("Text files","*.txt")])
        root.destroy()

        if len(file_paths) > 0 :
            self.feedback_label.config(text = "Please enter the Resistances")

            selected_sample_frame = tk.Frame(master = self.program_frame, borderwidth = 2, relief = "groove")
            selected_sample_frame.grid(row = 1, column = 0, padx = 5, pady = 5)

            sample_label = tk.Label(master = selected_sample_frame, text = "Selected Samples", font = ("Arial", 10))
            sample_label.grid(row = 0, column = 0, padx = 5, pady = 5)

            resistance_label = tk.Label(master = selected_sample_frame, text = "Resistances (Ω)", font = ("Arial", 10))
            resistance_label.grid(row = 0, column = 1, padx = 5, pady = 5)
            
            for n, file_path in enumerate(file_paths) :
                file_name = os.path.basename(file_path)
                sample_name = file_name.split(".txt")[0]

                sample_label = tk.Label(master = selected_sample_frame, text = f"{sample_name}")
                sample_label.grid(row = n + 1, column = 0, padx = 3, pady = 3)

                resistance_label = tk.Label(master = selected_sample_frame, text = "No input yet")
                resistance_label.grid(row = n + 1, column = 1, padx = 3, pady = 3)

                resistance_entry = tk.Entry(master = selected_sample_frame)
                resistance_entry.grid(row = n + 1, column = 2, padx = 3, pady = 3)

                self.resistance_entries.append(resistance_entry)
                self.resistance_labels.append(resistance_label)

            self.active_frames.append(selected_sample_frame)

            self.file_paths = file_paths


    def enter_resistances(self) :
        """ function, which gets the entered resistance entries by User from the self.resistance_entries list and add those in order to the respective
            resistances dictionary as value, whereas the file_path is used as key
            loop through each tkinter.entry from the self.resistance_entries list and get the respective input
            if an entry can not be converted into a valid input (float) an Error Feedback is given back to the User
            the order of the entries represents the order of the samples

            if no entry failed during the conversion the boolean self.start_evaluation state is set to True (it is set to False each time the function
            is exectued (safe switch for the evaluation))
        """

        self.start_evaluation = False 

        if len(self.file_paths) > 0 and len(self.resistance_entries) == len(self.file_paths) :
           
            failed_entries = []
            for n, resistance_entry in enumerate(self.resistance_entries) :
                entry = resistance_entry.get()

                try :
                    entry = float(entry)
                    self.resistances[self.file_paths[n]] = entry
                    self.resistance_labels[n].config(text = f"{entry}")
                except ValueError :
                    self.feedback_label.config(text = f"Could not enter {entry} as a valid resistance.")
                    failed_entries.append(entry)
                    self.resistance_labels[n].config(text = "Failed entering input")
            if len(failed_entries) == 0 :
                self.feedback_label.config(text = "Evaluation can now be started.")
                self.start_evaluation = True

            self.failed_entries = failed_entries

        else :
            self.feedback_label.config(text = "Please select your raw data files first.")


    def get_gui_frame(self, master) :
        """ returns a tkinter.Frame for a master window (tkinter.Tk)
            this frame need to contain all necassary widgets/functions required for the evaluation
            the grid placement was chosen since it is one of the simplest and cleanest options for a clean tkinter based User Interface
        """

        """ reset_attributes in case that this program is imported in another program, where this gui frame is imported twice and old resistance data and so
            are discarded (save switch for wrong inputs)
        """

        self.reset_attributes()

        self.program_frame = tk.Frame(master = master, borderwidth = 2, relief = "groove")
        self.program_frame.grid(row = 0, column = 2, pady = 5, padx = 5, rowspan= 5)

        """ creation of a tkinter.Frame which gives general control over the program for User
            contains general functions/buttons required for the evaluation
        """
        control_frame = tk.Frame(master = self.program_frame, borderwidth = 2, relief = "groove")
        control_frame.grid(row = 0, column = 0, padx = 5, pady = 5)

        """ create a tkinter.Button, which can access the self.open_files function in order to get the file_paths of the raw data files

            create a tkinter.Button, which can access the self.enter_resistances function in order to get the entries from the User for the resistances in 
            the sample/resistance table in the selected_sample_frame (created during the self.open_files function execution)

            create a tkinter.Button, which can access the self.run_evaluation function in order to start the evaluation if the requirements are met
            (see requirements in self.run_evaluation)
        """
        open_files_button = tk.Button(master = control_frame, text = "Open Files", command = self.open_files)
        open_files_button.grid(row = 0, column = 0, padx = 5, pady = 5)

        enter_resistances_button = tk.Button(master = control_frame, text = "Enter Resistances", command = self.enter_resistances)
        enter_resistances_button.grid(row = 0, column = 2, padx = 5, pady = 5)

        run_evaluation_button = tk.Button(master = control_frame, text = "Start Evaluation", command = self.run_evaluation)
        run_evaluation_button.grid(row = 1, column = 2, padx = 5, pady = 5)

        """ create a tkinter.Label, which contains the feedback information of the program
            contains feedback if an execution was successful or failed
            is set as an attribute of the Tafel_Analysis class object so that it can be accessed in different functions
        """

        self.feedback_label = tk.Label(master = control_frame, text = "Please select your raw data files.", font = "Arial")
        self.feedback_label.grid(row = 0, column = 1, padx = 5, pady = 5)
        
        """ create a tkinter.Button, which can access the open_change_parameter_window function
        """
        def open_change_paramter_window() :
            """ function, which creates a new window (is related to the master window, tk.Toplevel(master))
                during its existence commands by the User in the main window (master) are disabled due to the function
                tk.Toplevel.grab_set() gives control only to the new window """
            root = tk.Toplevel(master)
            root.grab_set()
            root.title("Change Parameters for Tafel Analysis")

            """ create a tkinter.Label, which contains the feedback if a change of the parameters was succesful or failed
            """
            parameter_feedback_label = tk.Label(master = root, text = "Please Change Parameters for Tafel Analysis.", font = ("Arial", 10))
            parameter_feedback_label.grid(row = 0, column = 0, columnspan = 2, padx = 5, pady = 5)

            def reset_parameters() :
                """ resets all parameters """
                self.reset_parameters()

                area_electrode_label.config(text = f"{self.area_electrode} cm²")
                pH_label.config(text = f"{self.pH}")
                electrons_label.config(text = f"{self.number_of_exchanged_electrons}")
                temperature_label.config(text = f"{self.temperature} K")

                parameter_feedback_label.config(text = "Parameters have been changed to Default.")

            """ create a tkinter.Button, which can access the function reset_parameters in order to reset all parameters at once and changes the displayed 
                tkinter.Label textes of each parameter
                the button is not connected directly with the self.reset_parameters function since this function does not update the labels in the
                tkinter.Toplevel window
            """

            reset_parameters_button = tk.Button(master = root, text = "Reset to Default", command = reset_parameters)
            reset_parameters_button.grid(row = 0, column = 3, padx = 5, pady = 5)

            """ create a tkinter.Label for each parameter, which can be changed by the User

                create a tkinter.Label for each parameter, which displays the currently set parameter values
                this content of this label is changed if the parameter was changed and displays the new set value

                create a tkinter.Entry for each parameter for changing parameters by User in GUI

                create a tkinter.Button for each parameter, which can access the functions necessary for changing these parameters
                the accessed functions have the following style: change_*
                 * parameter

                the following parameters can be changed by the User:
                - self.area_electrode
                - self.pH
                - self.number_of_exchanged_electrons
                - self.temperature

                all parameters accept a int/float as an input

            """

            def change_area_electrode() :
                entry = area_electrode_entry.get()

                entry = entry.replace(",", ".")

                try :
                    entry = float(entry)
                    self.area_electrode = entry
                    parameter_feedback_label.config(text = "Successful conversion of Area Electrode")
                    area_electrode_label.config(text = f"{self.area_electrode} cm²")
                except :
                    parameter_feedback_label.config(text = "Failed conversion of Area Electrode")

            area_electrode_label = tk.Label(master = root, text = "Area Electrode")
            area_electrode_label.grid(row = 1, column =  0, padx = 5, pady = 5)

            area_electrode_label = tk.Label(master = root, text = f"{self.area_electrode} cm²")
            area_electrode_label.grid(row = 1, column = 1, padx = 5, pady = 5)

            area_electrode_entry = tk.Entry(master = root)
            area_electrode_entry.grid(row = 1, column = 2, padx = 5, pady = 5)

            area_electrode_button = tk.Button(master = root, text = "Change Area Electrode", command = change_area_electrode)
            area_electrode_button.grid(row = 1, column = 3, pady = 5, padx = 5)

            def change_pH() :
                entry = pH_entry.get()

                entry = entry.replace(",", ".")

                try :
                    entry = float(entry)
                    self.pH = entry
                    parameter_feedback_label.config(text = "Successful conversion of pH")
                    pH_label.config(text = f"{self.pH}")
                except :
                    parameter_feedback_label.config(text = "Failed conversion of pH")

            pH_label = tk.Label(master = root, text = "pH")
            pH_label.grid(row = 2, column =  0, padx = 5, pady = 5)

            pH_label = tk.Label(master = root, text = f"{self.pH}")
            pH_label.grid(row = 2, column = 1, padx = 5, pady = 5)

            pH_entry = tk.Entry(master = root)
            pH_entry.grid(row = 2, column = 2, padx = 5, pady = 5)

            pH_button = tk.Button(master = root, text = "Change pH", command = change_pH)
            pH_button.grid(row = 2, column = 3, pady = 5, padx = 5)

            def change_electrons() :
                entry = electrons_entry.get()

                try :
                    entry = int(entry)
                    self.number_of_exchanged_electrons = entry
                    parameter_feedback_label.config(text = "Successful conversion of Number of Exchanged Electrons")
                    electrons_label.config(text = f"{self.number_of_exchanged_electrons}")
                except :
                    parameter_feedback_label.config(text = "Failed conversion of Number of Exchanged Electrons")

            electrons_label = tk.Label(master = root, text = "Number of Exchanged Electrons")
            electrons_label.grid(row = 3, column =  0, padx = 5, pady = 5)

            electrons_label = tk.Label(master = root, text = f"{self.number_of_exchanged_electrons}")
            electrons_label.grid(row = 3, column = 1, padx = 5, pady = 5)

            electrons_entry = tk.Entry(master = root)
            electrons_entry.grid(row = 3, column = 2, padx = 5, pady = 5)

            electrons_button = tk.Button(master = root, text = "Change Number of Exchanged Electrons", command = change_electrons)
            electrons_button.grid(row = 3, column = 3, pady = 5, padx = 5)

            def change_temperature() :
                entry = temperature_entry.get()

                entry = entry.replace(",", ".")

                try :
                    entry = float(entry)
                    self.temperature = entry
                    parameter_feedback_label.config(text = "Successful conversion of Temperature")
                    temperature_label.config(text = f"{self.temperature} K")
                except :
                    parameter_feedback_label.config(text = "Failed conversion of Temperature")

            temperature_label = tk.Label(master = root, text = "Temperature")
            temperature_label.grid(row = 4, column =  0, padx = 5, pady = 5)
            
            temperature_label = tk.Label(master = root, text = f"{self.temperature} K")
            temperature_label.grid(row = 4, column = 1, padx = 5, pady = 5)
            
            temperature_entry = tk.Entry(master = root)
            temperature_entry.grid(row = 4, column = 2, padx = 5, pady = 5)
            
            temperature_button = tk.Button(master = root, text = "Change Temperature", command = change_temperature)
            temperature_button.grid(row = 4, column = 3, pady = 5, padx = 5)
        
        change_parameters_button = tk.Button(master = control_frame, text = "Change Parameters", command = open_change_paramter_window)
        change_parameters_button.grid(row = 1, column = 0, pady = 5, padx = 5)

        """ create a tkinter.StringVar, which contains the setting of the tkinter.tkk.Checkbutton
            this checkbutton act as a checkbox for the automatic save function of the figures
            default is set to False
        """
        def change_figure_saving_settings() :
            setting = save_figures_variable.get()
            
            if setting == "1" :
                self.save_figures = True
            elif setting == "0" :
                self.save_figures = False

            if __name__ != "__main__" :
                save_figures_variable.set("0" if setting == "1" else "1")

            print(self.save_figures)

        save_figures_variable = tk.StringVar(value = "1" if __name__ != "__main__" else "0")
        save_figures_checkbox = ttk.Checkbutton(control_frame, text = "automatically save figures", \
            variable = save_figures_variable, command = change_figure_saving_settings, onvalue = True, offvalue = False)
        save_figures_checkbox.grid(row = 2, column = 0, padx = 5, pady = 5)

        return self.program_frame



if __name__ == "__main__" :

    tafel = Tafel_Analysis()
    root = tk.Tk()
    tafel.get_gui_frame(root)

    root.mainloop()


""" found bugs 
- when the resistances have been entered already and a new input is given, which is invalid the evaluation can still be started
  --> fixed
- when new files are entered the resistances of all the old files are still existing 
  --> fixed
"""

""" made by Stiftler (Pascal Reiß)
"""

"""
update list: 

Version 1.0.2 (28.03.2022)
- added filetypes argument for tkinter.filedialog.askopenfilenames function to show only necessary files for the program
  in this case: ["Text Files", "*.txt"]

Version 1.0.3 (06.04.2022)
- fixed bug were tkinter.StringVar values werent saved if the program was imported
"""