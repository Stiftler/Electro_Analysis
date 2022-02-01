# Electro analysis 
import os
import tkinter as tk
from datetime import datetime

import levich as la
import tafel as ta
import electrodeposition as ed
import sem_scale_bar as sem
import infrared as ir
import cyclovoltammetry as cv


""" adds method to the dictionary which contain the name and the execution function"""
def add_method_to_program_dictionary(method, gui_program_dictionary) :
    gui_program_dictionary[method.program_name] = method

    return gui_program_dictionary




class User_Interface :


    def __init__(self, gui_program_dictionary) :

        self.gui_program_dictionary = gui_program_dictionary

        """ create a window for the user interface """
        
        self.root = tk.Tk()
        self.root.title("Colloidal Systems Bayreuth Analysis Tool")

        """ create a frame in the window, which contains all available programs in a dropdown menu"""

        self.programs_frame = tk.Frame(master = self.root, relief = "groove", borderwidth = 2)
        self.programs_frame.grid(column = 0, row = 1, padx = 5, pady = 5)

        """ the following label is not changed during the running process therefore no special assignment has been chosen """

        label = tk.Label(master = self.root, text = "Colloidal Systems Bayreuth\nAnalysis Tool", font = ("Arial", 20))
        label.grid(column =  0, row = 0, padx = 5, pady = 5)

        """ the following label contains the selected method from the dropdown menu self.program_menu """
        self.selected_program_label = tk.Label(master = self.programs_frame, text = "Please select a evaluation method", font = "Arial")
        self.selected_program_label.grid(column = 0, row = 0, padx = 5, pady = 5)

        self.program_variable = tk.StringVar(self.programs_frame)
        self.program_variable.set("Methods")

        self.program_menu = tk.OptionMenu(self.programs_frame, self.program_variable, *list(gui_program_dictionary.keys()))
        self.program_menu.grid(column = 0, row = 1, padx = 5, pady = 5)

        self.active_program_frame = tk.Frame(master = self.root, relief = "groove", borderwidth = 2)
        self.active_program_frame.grid(row = 1, column = 1, padx = 5, pady = 5)



        """ the following button starts the selected program """
        def select_programm() :

            self.active_program_frame.grid_forget()
            selected_programm = self.program_variable.get()

            self.selected_program_label.config(relief = "flat")

            if selected_programm != "Methods" :
                self.selected_program_label.config(text = f"Selection: {selected_programm}" )

                self.active_program_frame = self.gui_program_dictionary[selected_programm].get_gui_frame(self.root)
                
            else :
                print("Hello")
                self.selected_program_label.config(text = "Please select a evaluation method", borderwidth = 2, relief = "solid", font = "Arial")

        run_program_button = tk.Button(self.programs_frame, text = "Select Method", command = select_programm)
        run_program_button.grid(column = 0, row = 2, padx = 5, pady = 5)






if __name__ == "__main__" :

    """ create a list, which is filled with available program names for the dropdown menu in the gui 
    the program names have to be set in the classes of the evalution methods 
    the program names can be accessed by creating a object of the evalution method and adding the string from class.program_name (e.g. Levich_Analysis.program_name) to the gui_program_list by the function add_method_to_program_dictionary() 
    alternative create an instance of the class and add the class to the list in the "create gui_program_list" loop
    """

    gui_program_dictionary = {}

    """ addd analysis methods """

    levich = la.Levich_Analysis()
    tafel = ta.Tafel_Analysis()
    electrodeposition = ed.Electrodeposition_Analysis()
    infrared = ir.Infrared_Analysis()
    cyclovolt = cv.Cyclovoltammetry()

    """ add imaging processes """

    sem_tool = sem.SEM_Image_Tool()

    path_main_program = os.path.dirname(os.path.realpath(__file__))

    path_evaluation_folder = path_main_program + "\Evaluation"

    if not os.path.exists(path_evaluation_folder) :
        os.mkdir(path_evaluation_folder)

    program_list = [levich, tafel, electrodeposition, sem_tool, infrared, cyclovolt]

    today = datetime.today().strftime("%Y-%m-%d")
    """ "create gui_program_list" loop """
    for method in program_list : 
        gui_program_dictionary = add_method_to_program_dictionary(method, gui_program_dictionary)




    gui = User_Interface(gui_program_dictionary)
    
    gui.root.mainloop()


    """ """