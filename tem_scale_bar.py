""" TEM Scale Bar Tool by Pascal Reiß
    Version 1.1.3
"""



import os
import pandas as pd

import tkinter as tk
from tkinter import ttk
from tkinter import filedialog

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from mpl_toolkits.axes_grid1.anchored_artists import AnchoredSizeBar
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.font_manager as fm

from datetime import datetime

import dm3_lib as dm3





class TEM_Image_Tool :

    def __init__(self) :
        """ initiate TEM_Image_Tool class object with the following attributes :
            - self.path_evaluation_folder
                string: contains the path of the evaluation folder of the TEM_Image_Tool class object
            - self.file_paths
                tuple: contains the file_paths of the raw data files
            - self.scale_bar_lengths
                list: contains all possible scale bar lenghts in real units
            - self.program_frame
                tkinter.Frame: contains all functions/widgets necessary for the image processing
            - self.feedback_label
                tkinter.Label: contains Feedback for User if an execution was succesful or failed
        """

        self.program_name = "TEM Scale Bar Tool"



        self.program_frame = None
        self.feedback_label = None

        self.fonts = {"consola" : r"C:\WINDOWS\Fonts\consola.ttf",
                      "arial" : r"C:\Windows\Fonts\arial.ttf", 
                      "times" : r"C:\Windows\Fonts\times.ttf",
                      }

        self.figure_types = {"TIFF" : ".tif",
                             "PNG" : ".png",
                             "EPS" : ".eps",
                             "JPG" : ".jpg"}

        self.colors = ["white", "black", "grey",  "red", "blue", "green", "cyan", "magenta", "yellow"]

        self.scale_bar_positions = ["upper left", "upper right", "lower left", "lower right"]

        self.preview_mode = False

        self.preview_index = 0 # keeps track which file_path is displayed in the SEM_Image_Tool.preview_canvas

        self.reset_attributes()
        self.reset_figure_attributes()
        self.reset_scale_bar_attributes()

        """ set up RectangleSelector for rectangle_mode 
        """
        self.rectangle_mode = False

        self.rectangle_selected = None

        self.mouse_pressed = False

        """ undo step list for undo and redo function of rectangle mode
        """

        self.current_position_undo_list = 0
        self.undo_list = []

        self.undo_redo_state = False


    def reset_attributes(self) :
        """ resets all attributes to default values for the TEM_Image_Tool
            is executed once when a new TEM_Image_Tool class object
            creates the evaluation folder if it is not existing already
            path_evaluation_folder: */Evaluation/**
             * path of this program
             ** current date in the format YYYY-MM-DD
        """

        self.check_for_evaluation_folder()

        self.file_paths = ()

        self.scale_bar_lengths = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000]


    def reset_figure_attributes(self) :

        self.figure_dpi = 500
        self.figure_type = self.figure_types["TIFF"]

        self.fig, self.ax = plt.subplots()

        self.ax.set_axis_off()
        self.ax.set_title("No Files Selected")


    def reset_scale_bar_attributes(self) :
        """ fontproperties of the scale bar
        """
        self.fontsize = 20 # for label
        self.font_selected = self.fonts["arial"]

        self.scale_bar_color = self.colors[0]
        self.scale_bar_position = self.scale_bar_positions[0]
        self.frameon = False
        self.scale_bar_label_sep = 10
        self.scale_bar_size_vertical = "automatic"

        self.scale_bar_treshold = "automatic"


    def check_for_evaluation_folder(self) :

        path_this_programm = os.path.dirname(os.path.realpath(__file__))
        path_evaluation_folder = f"{path_this_programm}\Evaluation"

        if not os.path.exists(path_evaluation_folder) :
            os.mkdir(path_evaluation_folder)

        path_evaluation_folder = f"{path_evaluation_folder}\{self.program_name}"

        if not os.path.exists(path_evaluation_folder) :
            os.mkdir(path_evaluation_folder)

        today = datetime.today().strftime("%Y-%m-%d")
        self.path_evaluation_folder = f"{path_evaluation_folder}" + f"\{today}"


        if not os.path.exists(self.path_evaluation_folder) :
            os.mkdir(self.path_evaluation_folder)


    def get_font_properties_for_resolution(self, resolution_x, resolution_y) :
        """ returns the fontproperties 
        """
            
        return fm.FontProperties(size = self.fontsize, fname = self.font_selected)


    def get_vertical_size_scale_bar_for_resolution(self, resolution_x, resolution_y) :
        """ returns the vertical size setting of the scale_bar depending on the resolution
        """
        resolution_x, resolution_y = str(resolution_x), str(resolution_y)

        if self.scale_bar_size_vertical != "automatic" :
            return self.scale_bar_size_vertical

        elif resolution_x == "4096" and resolution_y == "4095" :
            return 10

        elif resolution_x == "2048" and resolution_y == "2048" :
            return 10

        else :
            print(f"Resolution of {resolution_x}x{resolution_y} unknown. Am using 10 pixels.")
            return 10


    def open_files(self) :
        """ get file_paths from User if files were selected those file_paths are set as self.file_paths
            otherwise an error feedback is given back to the User
        """
        self.file_paths = ()

        root = tk.Tk()
        file_paths = filedialog.askopenfilenames(parent = root, filetypes=[("DM3 files","*.dm3")])
        root.destroy()


        if len(file_paths) > 0 :
            self.file_paths = file_paths

            if self.feedback_label != None :
                self.feedback_label.config(text = "Image Processing Can Now Be Started.")
                
                """ displays first selection with current settings (does of course not save the image) """
            self.preview_index = 0
            self.image_processing_from_path(file_paths[self.preview_index])

            file_name = os.path.basename(file_paths[self.preview_index])
            self.preview_file_label.config(text = f"Displayed File: {file_name}")

        elif self.feedback_label != None :
            self.feedback_label.config(text = "Please Select Your Raw Images First.")

            self.ax.clear()
            self.ax.set_axis_off()
            self.ax.set_title("No Files Selected")
            print("hello")

            self.preview_file_label.config(text = "Displayed File:")

            self.preview_canvas.draw()


    def rectangle_onselect(self, eClick, eRelease) :

        if self.rectangle_mode :

            
            x1, y1 = eClick[0], eClick[1] 
            x2, y2 = eRelease[0], eRelease[1] 

            if x1 > x2 :
                x1, x2 = x2, x1
            if y1 > y2 :
                y1, y2 = y2, y1

            xlim = (x1, x2)
            ylim = (y1, y2)

            self.ax.set_xlim(xlim)
            self.ax.set_ylim(y2, y1)

            if not self.undo_redo_state :
                self.undo_list.append((xlim, ylim))
                self.current_position_undo_list = (len(self.undo_list) - 1)

            self.preview_canvas.draw()


    def get_xy_coords_mouse_press_event_plt(self, event) :

        if self.rectangle_mode :

            self.rectangle_x1_plt, self.rectangle_y1_plt = event.xdata, event.ydata
        
            self.rectangle_selected = Rectangle((self.rectangle_x1_plt, self.rectangle_y1_plt), 
                                                 100, 100, 
                                                 color = "red", fill = False, ls = "--")

            self.ax.add_patch(self.rectangle_selected)
            self.preview_canvas.draw()

            self.mouse_pressed = True


    def create_dynamic_rectangle_in_plt(self, event) :

        if self.rectangle_mode and self.mouse_pressed:
            
            self.rectangle_x2_plt = event.xdata
            self.rectangle_y2_plt = event.ydata


            self.rectangle_selected.set_width(self.rectangle_x2_plt - self.rectangle_x1_plt)
            self.rectangle_selected.set_height(self.rectangle_y2_plt - self.rectangle_y1_plt)

            self.preview_canvas.draw()


    def get_xy_coords_mouse_release_event_plt(self, event) :

        if self.rectangle_mode :

            self.rectangle_x2_plt, self.rectangle_y2_plt = event.xdata, event.ydata


            self.ax.patches = []
            self.preview_canvas.draw()

            self.mouse_pressed = False

            if self.rectangle_x2_plt < self.rectangle_x1_plt :

                self.rectangle_x1_plt, self.rectangle_x2_plt = self.rectangle_x2_plt, self.rectangle_x1_plt

            if self.rectangle_y2_plt < self.rectangle_y1_plt :

                self.rectangle_y1_plt, self.rectangle_y2_plt = self.rectangle_y2_plt, self.rectangle_y1_plt

            self.rectangle_onselect((self.rectangle_x1_plt, self.rectangle_y1_plt), (self.rectangle_x2_plt, self.rectangle_y2_plt))


    def image_processing_from_path(self, file_path) :

        self.ax.clear()
    
        """ open the dm3 file
        """
        file = dm3.DM3(file_path)

        """ get pixel_size, pixel_unit, resolution and contrast of image from image meta data 
            meta data can be accessed via a dictonary (dm3_lib.DM3.tags) where the data is saved as value and the tag as key

            interesting tags with their corresponding values (taken from 2_31k.dm3)
            Tag: root.ImageList.1.ImageData.Calibrations.Dimension.0.Scale Value: 0.303425669670105
            Tag: root.ImageList.1.ImageData.Calibrations.Dimension.0.Units Value: nm
            Tag: root.ImageList.1.ImageData.Dimensions.0 Value: 2048
            Tag: root.ImageList.1.ImageData.Dimensions.1 Value: 2048

            get contrast of image, so that set image via matplotlib.pyplot is in the same grayscale
            contrast can be accessed by dm3_lib.DM3.contrastlimits
        """

        pixel_size = self.get_pixel_size(file)
        pixel_unit = self.get_pixel_unit(file)
        resolution = self.get_resolution(file)
        contrast = self.get_contrast(file)

        """ loop through each possible real scale bar length in the list self.scale_bar_lengths and find the first length with a length of at least 200 in pixels
            if the real scale bar length is larger than 1000 it is divided by 1000 and gets the next unit hierarchy
        """
        for scale_bar_length in self.scale_bar_lengths :
            scale_bar_pixel = int(round(scale_bar_length / pixel_size))
            if scale_bar_pixel > 199 :
                if scale_bar_length >= 1000 :
                    scale_bar_length /= 1000
                    pixel_unit = self.get_next_unit_size(pixel_unit)
                break

        """ get the image as an numpy.ndarray 
            add the array to matplotlib.pyplot via imshow
            set colormap of image to gray and set the contrast limits to vmin and vmax
        """
        image_array = file.imagedata 

        self.ax.imshow(image_array, "gray", vmin = contrast[0], vmax = contrast[1]) 

        """ create the fontproperties of the scale bar
            create the scale bar with the necessary attributes 
        """
        fontprops = self.get_font_properties_for_resolution(resolution[0], resolution[1])

        size_vertical = self.get_vertical_size_scale_bar_for_resolution(resolution[0], resolution[1])

        scale_bar = AnchoredSizeBar(self.ax.transData,
                                    scale_bar_pixel,
                                    f"{scale_bar_length} {pixel_unit}", self.scale_bar_position,
                                    pad = 0.7,
                                    color = self.scale_bar_color,
                                    frameon = self.frameon,
                                    size_vertical = size_vertical,
                                    fontproperties = fontprops,
                                    sep = self.scale_bar_label_sep)

        """ add scale bar to image
            turn off the x and y axis
        """
        self.ax.add_artist(scale_bar)

        self.ax.set_axis_off()

        xlim, ylim = self.ax.get_xlim(), self.ax.get_ylim()

        self.undo_list = [(xlim, ylim)]

        self.preview_canvas.draw()


    def run_image_processing(self) :
        """ this function processes all images selected by the User
            if no files were selected an Error feedback is given back
        """

        if len(self.file_paths) > 0 :

            if self.feedback_label != None :
                self.feedback_label.config(text = "Image Processing In Progress.")

            """ loop through each file indiviually
            """
            for file_path in self.file_paths :
                """ get the file_name and sample_name of the file
                """
                file_name = os.path.basename(file_path)
                sample_name = file_name.split(".dm3")[0]

                self.image_processing_from_path(file_path)

                self.fig.savefig(f"{self.path_evaluation_folder}\{sample_name}{self.figure_type}", dpi = self.figure_dpi, bbox_inches = "tight", pad_inches = 0)

            if self.feedback_label != None :
                self.feedback_label.config(text = "Image Processing Finished.")

        elif self.feedback_label != None :
            self.feedback_label.config(text = "Please Select Your Raw Images First.")


    def get_pixel_size(self, file) :
        """ returns a float that represents the real size equivalent of one pixel 
            expected argument datatyp:
            - file : dm3_lib.DM3
        """
        return float(file.tags["root.ImageList.1.ImageData.Calibrations.Dimension.0.Scale"])


    def get_pixel_unit(self, file) :
        """ returns a string containing the real unit equivalent of one pixel 
            expected argument datatyp:
            - file : dm3_lib.DM3
        """
        return file.tags["root.ImageList.1.ImageData.Calibrations.Dimension.0.Units"]


    def get_resolution(self, file) :
        """ returns a tuple with the x (int) and y (int) resolution of the image 
            expected argument datatyp:
            - file : dm3_lib.DM3
        """
        return (int(file.tags["root.ImageList.1.ImageData.Dimensions.0"]), int(file.tags["root.ImageList.1.ImageData.Dimensions.1"]))


    def get_contrast(self, file) :
        """ returns a tuple with the contrast values of the image
            expectd argument datatyp:
            - file : dm3_lib.DM3
        """
        return file.contrastlimits


    def get_next_unit_size(self, pixel_unit) :
        """ returns a string of the next unit hierarchy

            unit hierarchy: nm --> µm --> mm
            expected argument datatype:
                - pixel_unit : string
        """
        if pixel_unit == "pm" :
            return nm
            
        elif pixel_unit == "nm" :
            return "µm"

        elif pixel_unit == "µm" :
            return "mm"


    def get_gui_frame(self, master) :
        """ returns a tkinter.Frame for a master window (tkinter.Tk)
            this Frame needs to contain all necassary widgets/functions required for the image processing 
            the grid placement was chosen since it is one of the simplest and cleanest options for a clean tkinter based User Interface
        """

        """ create tkinter.Frame 
            keywords: borderwith and relief for asthetics
            positon in grid row = 1, column = 1 is necassary for the GUI program written by Pascal Reiß (CS_Analysis_Tool.py)
            if new GUI is created these values can be tuned 
        """
        self.program_frame = tk.Frame(master = master, relief = "groove", borderwidth = 2)
        self.program_frame.grid(row = 0, column = 1, padx = 5, pady = 5, rowspan = 10)

        main_frame = tk.Frame(master = self.program_frame)
        main_frame.grid(row = 0, column = 0, padx = 5, pady = 5)

        control_frame = tk.Frame(master = main_frame, relief = "groove", borderwidth = 2)
        control_frame.grid(row = 0, column = 0, padx = 5, pady = 5)

        """ create tkinter.Button, which can access the function self.open_files for getting the selected files by the User
        """
        open_files_button = tk.Button(master = control_frame, text = "Open Files", command = self.open_files, font = ("", 14))
        open_files_button.grid(row = 0, column = 0, padx = 5, pady = 5)

        """ create tkinter.Button, which can access the function self.run_image_processing
            for starting the image processing
        """
        run_processing_button = tk.Button(master = control_frame, text = "Run Image Processing", command = self.run_image_processing, font = ("", 14))
        run_processing_button.grid(row = 0, column = 2, padx = 5, pady = 5)

        """ create a tkinter.Label, which contains the feedback for the User if an execution failed or was successful 
            (as a attribute of the SEM_Image_Tool class itself)
        """
        self.feedback_label = tk.Label(master = control_frame, text = "Please Select Your Raw Images First.")
        self.feedback_label.grid(row = 0, column = 1, padx = 5, pady = 5)

        """ create frame for displaying image in gui
            needs to be an object of the TEM object, so that later functions can access it
        """

        self.preview_frame = tk.Frame(master = main_frame, relief = "groove", borderwidth = 2)
        self.preview_frame.grid(row = 0, column = 1, padx = 5, pady = 5, rowspan = 3)

        label = tk.Label(master = self.preview_frame, text = "Preview", font = ("Arial", 22))
        label.grid(row = 0, column = 0, padx = 5, pady = 5)

        self.preview_canvas = FigureCanvasTkAgg(self.fig, master = self.preview_frame)
        self.preview_canvas.get_tk_widget().grid(row = 1, column = 0, padx = 5, pady = 5)

        self.preview_canvas.mpl_connect("button_press_event", self.get_xy_coords_mouse_press_event_plt)
        self.preview_canvas.mpl_connect("button_release_event", self.get_xy_coords_mouse_release_event_plt)
        self.preview_canvas.mpl_connect("motion_notify_event", self.create_dynamic_rectangle_in_plt)


        preview_buttons_frame = tk.Frame(master = self.preview_frame)
        preview_buttons_frame.grid(row = 2, column = 0, padx = 5, pady = 5)

        def goLeft_preview() :

            if self.preview_index > 0 :
                self.preview_index -= 1

                file_path = self.file_paths[self.preview_index]
                file_name = os.path.basename(file_path)

                self.image_processing_from_path(file_path)
                self.preview_file_label.config(text = f"Displayed File: {file_name}")


        def goRight_preview() :

            if self.preview_index < (len(self.file_paths) - 1) :
                self.preview_index += 1

                file_path = self.file_paths[self.preview_index]
                file_name = os.path.basename(file_path)

                self.image_processing_from_path(file_path)
                self.preview_file_label.config(text = f"Displayed File: {file_name}")


        goLeft_preview_button = tk.Button(master = preview_buttons_frame, text = "\u2190", # u2190 arrow pointing to the left
                                          command = goLeft_preview, font = ("", 14)) 
        goLeft_preview_button.grid(row = 0, column = 0, padx = 5, pady = 5)

        goRight_previw_button = tk.Button(master = preview_buttons_frame, text = "\u2192", # u2190 arrow pointing to the right
                                          command = goRight_preview, font = ("", 14)) 
        goRight_previw_button.grid(row = 0, column = 1, padx = 5, pady = 5)


        def set_rectangle_mode() :
            """ controls setting of rectangle mode and therefore if image can be cropped or not
            """
            if self.rectangle_mode :
                self.rectangle_mode = False
                background = preview_buttons_frame.cget("bg") # get standard color of tkinter widgets
                rectangle_control_button.config({"background" : background, "fg" : "black"})
            else :
                self.rectangle_mode = True
                rectangle_control_button.config({"background" : "black", "fg" : "white"})


        rectangle_control_button = tk.Button(master = preview_buttons_frame, text = "\u2702", # u2702 scissor
                                             command = set_rectangle_mode, font = ("", 14))
        rectangle_control_button.grid(row = 0, column = 2, padx = 5, pady = 5)

        def undo () :

            if self.current_position_undo_list > 0 :
                self.current_position_undo_list -= 1

                self.undo_redo_state = True

                xlim = self.undo_list[self.current_position_undo_list][0]
                ylim = self.undo_list[self.current_position_undo_list][1]

                xy1 = (xlim[0], ylim[1])
                xy2 = (xlim[1], ylim[0])

                self.rectangle_onselect(xy1, xy2)

                self.undo_redo_state = False

        undo_button = tk.Button(master = preview_buttons_frame, text = "\u27F2", # curved arrow to the right
                                command = undo, font = ("", 14))
        undo_button.grid(row = 0, column = 3, padx = 5, pady = 5)


        def redo() :
            
            if self.current_position_undo_list < (len(self.undo_list) - 1) :
                self.current_position_undo_list += 1

                self.undo_redo_state = True

                xlim = self.undo_list[self.current_position_undo_list][0]
                ylim = self.undo_list[self.current_position_undo_list][1]

                xy1 = (xlim[0], ylim[1])
                xy2 = (xlim[1], ylim[0])

                self.rectangle_onselect(xy1, xy2)

                self.undo_redo_state = False

        redo_button = tk.Button(master = preview_buttons_frame, text = "\u27F3", # curved arrow to the left
                                command = redo, font = ("", 14))
        redo_button.grid(row = 0, column = 4, padx = 5, pady = 5)

        def save_current_preview() :
            """ saves currently displayed image if files were selected by user len(TEM_Image_Tool.file_paths) > 0
            """

            if len(self.file_paths) > 0 :

                file_path = self.file_paths[self.preview_index]
                file_name = os.path.basename(file_path)
                sample_name = file_name.split(".dm3")[0]

                self.fig.savefig(f"{self.path_evaluation_folder}\{sample_name}_cut_out{self.figure_type}", dpi = self.figure_dpi, bbox_inches = "tight", pad_inches = 0)

        save_current_preview_button = tk.Button(master = preview_buttons_frame, text = "\U0001F4BE", # U0001F4BE save icon
                                                command = save_current_preview, font = ("", 14))
        save_current_preview_button.grid(row = 0, column = 5, padx = 5, pady = 5)



        self.preview_file_label = tk.Label(master = self.preview_frame, text = "Displayed File:", font = ("", 12))
        self.preview_file_label.grid(row = 3, column = 0, padx = 5, pady = 5)




        """ create a tkinter.Frame, which contains all widget necassary for the User if changes to the figures shall be made (compared to the standard process) 
        """
        change_properties_frame = tk.Frame(master = main_frame, relief = "groove", borderwidth = 2)

        def enable_change_properties_frame() :
            setting = change_properties_variable.get()
            if setting == "1" :
                change_properties_frame.grid(row = 1, column = 0, padx = 5, pady = 5)

            elif setting == "0" :
                change_properties_frame.grid_forget()

            """ main programm CS_Analysis_Tool.py does not remember the value for change_properties_variable tk.StringVar
                after integration of the matplotlib canvas FigureCanvasTkAgg
                fix:
                - add recognition if script is imported or not
                  if script is imported change value of variable (works but is not really elegant or intutive)
            """

            dic = {"0" : "1", "1" : "0"}
            change_properties_variable.set(dic[setting])

        change_properties_variable = tk.StringVar(value = "1")
        change_properties_checkbox = ttk.Checkbutton(control_frame, text = "change settings",
                                                        variable = change_properties_variable, command = enable_change_properties_frame)
        change_properties_checkbox.grid(row = 1, column = 0, padx = 5, pady = 5)


        """ tkinter.Frame with all widgets necessary for changing general scale bar settings
        """


        label = tk.Label(master = change_properties_frame, text = "Settings", font = ("Arial", 22))
        label.grid(row = 0, column = 0, padx = 5, pady = 5)

        change_properties_scale_bar_frame = tk.Frame(master = change_properties_frame, relief = "groove", borderwidth = 2)
        change_properties_scale_bar_frame.grid(row = 1, column = 0, padx = 5, pady = 5)

        label = tk.Label(master = change_properties_scale_bar_frame, text = "Scale Bar Settings", font = ("Arial", 16))
        label.grid(row = 0, columnspan = 3, padx = 5, pady = 5)

        fontsize_label = tk.Label(master = change_properties_scale_bar_frame, text = f"Fontsize Scale Bar Label:")
        fontsize_label.grid(row = 1, column = 0, padx = 5, pady = 5)

        fontsize_label = tk.Label(master = change_properties_scale_bar_frame, text = self.fontsize)
        fontsize_label.grid(row = 1, column = 1, padx = 5, pady = 5)

        fontsize_entry = tk.Entry(master = change_properties_scale_bar_frame)
        fontsize_entry.grid(row = 1, column = 2, padx = 5, pady = 5)

        def change_fontsize() :
            entry = fontsize_entry.get()
            fontsize_entry.config({"background" : "white"})
            if entry != "" :
                try :
                    entry = int(entry)
                    self.fontsize = entry
                    fontsize_label.config(text = f"{self.fontsize}")
                except ValueError :
                    fontsize_entry.config({"background" : "red"})

        font_label  = tk.Label(master = change_properties_scale_bar_frame, 
            text = f"Selected Font For Scale Bar Label:")
        font_label.grid(row = 2, column = 0, padx = 5, pady = 5)

        font_label = tk.Label(master = change_properties_scale_bar_frame, 
                              text = list(self.fonts.keys())[list(self.fonts.values()).index(self.font_selected)], # get dictionary key by value
                              ) 
        font_label.grid(row = 2, column = 1, padx = 5, pady = 5)


        font_string_var = tk.StringVar(change_properties_scale_bar_frame)
        font_string_var.set("Fonts")

        font_menu = tk.OptionMenu(change_properties_scale_bar_frame, font_string_var, *self.fonts.keys())
        font_menu.grid(row = 2, column = 2, padx = 5, pady = 5)

        def change_font() :
            var = font_string_var.get()

            if var != "Fonts" :
                self.font_selected = self.fonts[var]

                font_label.config(text = list(self.fonts.keys())[list(self.fonts.values()).index(self.font_selected)])

        color_label = tk.Label(master = change_properties_scale_bar_frame, text = f"Selected Color Scale Bar:")
        color_label.grid(row = 3, column = 0, padx = 5, pady = 5)

        color_label = tk.Label(change_properties_scale_bar_frame, text = self.scale_bar_color)
        color_label.grid(row = 3, column = 1, padx = 5, pady = 5)

        color_string_var = tk.StringVar(change_properties_scale_bar_frame)
        color_string_var.set("Colors")

        color_menu = tk.OptionMenu(change_properties_scale_bar_frame, color_string_var, *self.colors)
        color_menu.grid(row = 3, column = 2, padx = 5, pady = 5)

        def change_color() :
            var = color_string_var.get()

            if var != "Colors" :
                self.scale_bar_color = self.colors[self.colors.index(var)]
                color_label.config(text = f"{self.scale_bar_color}")

        position_label = tk.Label(change_properties_scale_bar_frame, text = f"Selected Positon Scale Bar:")
        position_label.grid(row = 4, column = 0, padx = 5, pady = 5)

        position_label = tk.Label(change_properties_scale_bar_frame, text = self.scale_bar_position)
        position_label.grid(row = 4, column = 1, padx = 5, pady = 5)

        position_string_var = tk.StringVar(change_properties_scale_bar_frame)
        position_string_var.set("Positions")

        position_menu = tk.OptionMenu(change_properties_scale_bar_frame, position_string_var, *self.scale_bar_positions)
        position_menu.grid(row = 4, column = 2, padx = 5, pady = 5)

        def change_position() :
            var = position_string_var.get()

            if var != "Positions" :
                self.scale_bar_position = self.scale_bar_positions[self.scale_bar_positions.index(var)]
                position_label.config(text = f"{self.scale_bar_position}")

        seperation_scale_bar_label = tk.Label(master = change_properties_scale_bar_frame, text = f"Set Seperation Between Scale Bar And Label:")
        seperation_scale_bar_label.grid(row = 5, column = 0, padx = 5, pady = 5)

        seperation_scale_bar_label = tk.Label(master = change_properties_scale_bar_frame, text = f"{self.scale_bar_label_sep}")
        seperation_scale_bar_label.grid(row = 5, column = 1, padx = 5, pady = 5)

        seperation_scale_bar_entry = tk.Entry(master = change_properties_scale_bar_frame)
        seperation_scale_bar_entry.grid(row = 5, column = 2, padx = 5, pady = 5)

        def change_size_vertical() :
            entry = scale_bar_size_vertical_entry.get()
            scale_bar_size_vertical_entry.config({"background" : "white"})

            if entry != "" :
                try :
                    entry = int(entry)
                    self.scale_bar_size_vertical = entry
                    scale_bar_size_vertical_label.config(text = self.scale_bar_size_vertical)
                except ValueError :
                    scale_bar_size_vertical_entry.config({"background" : "red"})

        scale_bar_size_vertical_label = tk.Label(master = change_properties_scale_bar_frame, text = "Set Height of Scale Bar (in pixel):")
        scale_bar_size_vertical_label.grid(row = 6, column = 0, padx = 5, pady = 5)

        scale_bar_size_vertical_label = tk.Label(master = change_properties_scale_bar_frame, text = self.scale_bar_size_vertical)
        scale_bar_size_vertical_label.grid(row = 6, column = 1, padx = 5, pady = 5)

        scale_bar_size_vertical_entry = tk.Entry(master = change_properties_scale_bar_frame)
        scale_bar_size_vertical_entry.grid(row = 6, column = 2, padx = 5, pady = 5)

        def change_seperation() :
            entry = seperation_scale_bar_entry.get() 
            seperation_scale_bar_entry.config({"background" : "white"})
            
            if entry != "" :
                try :
                    entry = float(entry)
                    self.scale_bar_label_sep = entry
                    seperation_scale_bar_label.config(text = f"{self.scale_bar_label_sep}")
                except ValueError :
                    seperation_scale_bar_entry.config({"background" : "red"})

        scale_bar_treshold_label = tk.Label(master = change_properties_scale_bar_frame, text = f"Set Length Treshold Scale Bar (in pixel):")
        scale_bar_treshold_label.grid(row = 7, column = 0, padx = 5, pady = 5)

        scale_bar_treshold_label = tk.Label(master = change_properties_scale_bar_frame, text = f"{self.scale_bar_treshold}")
        scale_bar_treshold_label.grid(row = 7, column = 1, padx = 5, pady = 5)

        scale_bar_treshold_entry = tk.Entry(master = change_properties_scale_bar_frame)
        scale_bar_treshold_entry.grid(row = 7, column = 2, padx = 5, pady = 5)


        def change_treshold() :
            entry = scale_bar_treshold_entry.get()
            scale_bar_treshold_entry.config({"background" : "white"})

            if entry == "automatic" :
                self.scale_bar_treshold = entry
                scale_bar_treshold_label.config(text = f"{self.scale_bar_treshold}")
            elif entry != "" :
                try :
                    entry = int(entry)
                    self.scale_bar_treshold = entry
                    scale_bar_treshold_label.config(text = f"{self.scale_bar_treshold}")
                except ValueError :
                    scale_bar_treshold_entry.config({"background" : "red"})

        def change_frame_scale_bar() :
            var = scale_bar_frame_string_var.get()
            dic = {"0" : False, "1" : True}
            self.frameon = dic[var]

        scale_bar_frame_string_var = tk.StringVar(change_properties_scale_bar_frame)
        scale_bar_frame_string_var.set("0")
        scale_bar_frame_checkbox = ttk.Checkbutton(master = change_properties_scale_bar_frame, text = "Frame For Scale Bar And Label", 
                                                    variable = scale_bar_frame_string_var)
        scale_bar_frame_checkbox.grid(row = 8, column = 0, padx = 5, pady = 5)

        """ add properties of scale bar
        """

        change_properties_figure_frame = tk.Frame(master = change_properties_frame, relief = "groove", borderwidth = 2)
        change_properties_figure_frame.grid(row = 2, column = 0, padx = 5, pady = 5)

        label = tk.Label(master = change_properties_figure_frame, text = "Figure Settings", font = ("Arial", 16))
        label.grid(row = 0, columnspan = 3, padx = 5, pady = 5)

        dpi_label = tk.Label(master = change_properties_figure_frame, text = f"DPI of Figure:")
        dpi_label.grid(row = 1, column = 0, padx = 5, pady = 5)

        dpi_label = tk.Label(master = change_properties_figure_frame, text = f"{self.figure_dpi}")
        dpi_label.grid(row = 1, column = 1, padx = 5, pady = 5)

        dpi_entry = tk.Entry(master = change_properties_figure_frame)
        dpi_entry.grid(row = 1, column = 2, padx = 5, pady = 5)

        def change_dpi() :
            entry = dpi_entry.get()
            dpi_entry.config({"background" : "white"})
            if entry != "" :
                try :
                    entry = int(entry)
                    self.figure_dpi = entry
                    dpi_label.config(text = f"{self.figure_dpi}")
                except ValueError :
                    dpi_entry.config({"background" : "red"})

        figure_type_label = tk.Label(master = change_properties_figure_frame, text = f"Selected File Type For Processed Images:")
        figure_type_label.grid(row = 2, column = 0, padx = 5, pady = 5)

        figure_type_label = tk.Label(change_properties_figure_frame, text = self.figure_type)
        figure_type_label.grid(row = 2, column = 1, padx = 5, pady = 5)

        figure_type_string_var = tk.StringVar(change_properties_figure_frame)
        figure_type_string_var.set("File Types")

        figure_type_menu = tk.OptionMenu(change_properties_figure_frame, figure_type_string_var, *self.figure_types.keys())
        figure_type_menu.grid(row = 2, column = 2, padx = 5, pady = 5)

        def change_figure_type() :
            var = figure_type_string_var.get()

            if var != "File Types" :
                self.figure_type = self.figure_types[var]
                figure_type_label.config(text = f"{self.figure_type}")
        """ add properties of figure
        """

        def change_properties() :
            change_dpi()
            change_fontsize()
            change_font()
            change_color()
            change_position()
            change_seperation()
            change_size_vertical()
            change_treshold()
            change_frame_scale_bar()
            change_figure_type()

            """ display warning if self.frameon = True and self.scale_bar_color = "white" """

            if len(self.file_paths) > 0 :
                self.image_processing_from_path(self.file_paths[0])
                
            if self.frameon and self.scale_bar_color == "white" :
                self.feedback_label.config(text = "Scale Bar and Frame have same color. Please Change the color of the Scale Bar")
            else :
                self.feedback_label.config(text = "Please check your Changes in the Preview")


        settings_control_frame = tk.Frame(master = change_properties_frame, relief = "groove", borderwidth = 2)
        settings_control_frame.grid(row = 3, column = 0, padx = 5, pady = 5)

        apply_settings_button = tk.Button(master = settings_control_frame, text = "Apply Settings", command = change_properties, font = ("", 14))
        apply_settings_button.grid(row = 0, column =0, padx = 5, pady = 5)


        """ hotkey bindings
        """
        master.bind("<Left>", lambda event : goLeft_preview())

        master.bind("<Right>", lambda event : goRight_preview())

        master.bind("<Control-k>", lambda event : set_rectangle_mode())

        master.bind("<Control-z>", lambda event : undo())

        master.bind("<Control-y>", lambda event : redo())

        master.bind("<Control-s>", lambda event : save_current_preview())

        master.bind("<Control-o>", lambda event : self.open_files())

        master.bind("<Control-r>", lambda event : self.run_image_processing())




        return self.program_frame




if __name__ == "__main__" :

    root = tk.Tk()

    tem = TEM_Image_Tool()
    tem.get_gui_frame(root)

    root.mainloop()



""" made by Stiftler (Pascal Reiß)
"""

"""
update list: 
Version 1.0.2

- added features for customising given graphs and scale bar

Version 1.0.3 (28.03.2022)
- added filetypes argument for tkinter.filedialog.askopenfilenames function to show only necessary files for the program
  in this case: ["DM3 Files", "*.dm3"]

Version 1.1.1 (29.03.2022)
- added feature for cutting out rectangles in the image (known issue: new customization of scale bar necessary)

Version 1.1.2 (02.04.2022)
- added FigureCanvasTkAgg object from matplotlib.widgets as TEM_Image_Tool.preview_canvas: display preview picture in GUI
  for some reason the change_properties_variable tk.StringVar did not remember its value when the script is imported
  fix: change value of change_properties_variable by checking if sript is imported or not ---> fixed it
- removed preview button and merged function into apply_settings_button 
  changed settings for scale_bar are directly displayed in the FigureCanvasTkAgg object
- reworked general GUI Layout
- added goLeft_preview_button and goRight_preview_button to switch displayed image from selected files
- added cropout function which can be activated by rectangle_control_button:
  function displays a rectangle (matplotlib.patches.Rectangle) which shows selected area 
  rectangle is drawn by holding MouseButton-1 (left) and after releasing the selected area is cropped out
- added save_current_preview_button, which saves the currently displayed image locally

Version 1.1.3 (04.04.2022) CTRL is important
- added undo/redo function to cropout function 
  can be accessed by undo_button and redo_button (also CTRL + Z for undo and CTRL + Y for redo)
- added CTRl + S as shortcurt for saving current preview
- addd left and right arrow for switching preview
- added CTRL + K as shortcut for activating cropout function
- added CTRL + R as shortcurt for running image processing (all files)
- added CTRL + O as shortcut for opening files
"""