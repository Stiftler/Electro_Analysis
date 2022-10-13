""" SEM Scale Bar Tool by Pascal Reiß
    Version 1.1.2
"""

from PIL import Image
import pandas as pd

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from mpl_toolkits.axes_grid1.anchored_artists import AnchoredSizeBar
import matplotlib.font_manager as fm
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import os
from datetime import datetime 

from tkinter import filedialog
import tkinter as tk
from tkinter import ttk




class ESEM_Image_Tool :


    def __init__(self) :
        """ initiate SEM_Image_Tool class object with the following attributes:
            - self.frame (tkinter.Frame) and self.feedback_label (tkinter.Label)
              objects are required in the GUI 
            - self.file_paths (tuple: contains the file_paths of the raw data files
              is set under the function self.reset_attributes)
            - self.scale_bar_lengths (list: contains possible length scales (int) for the scale bar added in the images)
        """

        self.program_name = "ESEM Scale Bar Tool"

        self.program_frame = None

        self.reset_attributes()

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


        self.reset_figure_attributes()
        self.reset_scale_bar_attributes()

        """ set up RectangleSelector for rectangle_mode 
        """
        self.rectangle_mode = False

        self.rectangle_selected = None

        self.mouse_pressed = False # required if crop out mode is used and the rectangle is displayed during mouse events

        """ undo step list for undo and redo function of rectangle mode
        """

        self.current_position_undo_list = 0
        self.undo_list = []

        self.undo_redo_state = False

    def reset_attributes(self) :
        """ reset attributes (self.file_paths, self.scale_bar_lengths) to default values 
            and creates the evalution folder if it is not existing
            path_evalution_folder: */Evaluation/**
             * path of this program
             ** current date in the format YYYY-MM-DD
        """

        """ setup path for processed images and create it if not present on the systems 
        """
        self.check_for_evaluation_folder()

        self.file_paths = ()

        """ define possible scale bar lengths for the images 
        """
        self.scale_bar_lengths = [100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000] # in nm


    def reset_figure_attributes(self) :

        self.figure_dpi = 500
        self.figure_type = self.figure_types["TIFF"]


        self.fig, self.ax = plt.subplots()

        self.ax.set_axis_off()
        self.ax.set_title("No Files Selected")


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


    def open_files(self) :
        """ get file_paths from User if files were selected those file_paths are set as self.file_paths
            otherwise an error feedback is given back to the User
        """
        self.file_paths = ()

        root = tk.Tk()
        file_paths = filedialog.askopenfilenames(parent = root, filetypes=[("TIFF files","*.tif")])
        root.destroy()

        if len(file_paths) > 0 :
            self.file_paths = file_paths

            self.preview_index = 0
            self.image_processing_from_path(file_paths[self.preview_index])

            file_name = os.path.basename(file_paths[self.preview_index])
            self.preview_file_label.config(text = f"Displayed File: {file_name}")

            if self.feedback_label != None :
                self.feedback_label.config(text = "Image Processing Can Now Be Started.")

        elif self.feedback_label != None :
            self.feedback_label.config(text = "Please Select Your Raw Images First.")

            self.ax.clear()
            self.ax.set_axis_off()
            self.ax.set_title("No Files Selected")
            print("hello")

            self.preview_file_label.config(text = "Displayed File:")

            self.preview_canvas.draw()


    def get_pixel_size_and_unit(self, series) :
        """ enter a pandas.Series including the pixel size in its values and it is searched by Pixel size 
            returns the pixel size and unit of that pixel
        """
        for value in series :
            value = str(value)

            if "Pixel Size" in value :
           
                value = value.split(" = ")

                if value[0] == "Pixel Size" :

                    pixel_size, unit = float(value[1].split(" ")[0]), value[1].split(" ")[1]

                    return pixel_size, unit


    def get_resolution(self, series) :
        """ enter a pandas.Series including the store resolution in its values and it is searched by Store resolution
            returns the resolution for the x and y axis
        """
        for value in series :
            value = str(value)

            if "Store resolution" in value :
                value = value.split(" = ")[1]
                
                value = value.split(" * ")

                resolution_x, resolution_y = value[0], value[1]

                break

        return resolution_x, resolution_y


    def get_font_properties_for_resolution(self, resolution_x, resolution_y) :
        """ returns the fontproperties 
        """
            
        return fm.FontProperties(size = self.fontsize, fname = self.font_selected)


    def get_cut_off_for_resolution(self, resolution_x, resolution_y) :
        """ returns the y-axis limits for the cut-off point of the SEM images depending on the resolution
            (it cuts off the white box (containing meta data) at the lower edge of the SEM image) 
        """

        if resolution_x == "1024" and resolution_y == "768" :
            return (690, 0)

        elif resolution_x == "2048" and resolution_y == "1536" :
            return (1380, 0)

        elif resolution_x == "1536" and resolution_y == "1024" :
            return (1024, 0)


    def get_vertical_size_scale_bar_for_resolution(self, resolution_x, resolution_y) :
        """ returns the vertical size setting of the scale_bar depending on the resolution
        """

        if self.scale_bar_size_vertical != "automatic" :
            return self.scale_bar_size_vertical

        elif resolution_x == "1024" and resolution_y == "768" :
            return 10

        elif resolution_x == "2048" and resolution_y == "1536" :
            return 20

        elif resolution_x == "1536" and resolution_y == "1024" :
            return 15


    def get_scale_bar_in_pixel_for_resolution(self, resolution_x, resolution_y) :
        """ get length of the scale_bar in pixel depending on the resolution 
        """
        if self.scale_bar_treshold != "automatic" :
            return self.scale_bar_treshold

        elif resolution_x == "1024" and resolution_y == "768" :
            return 75

        elif resolution_x == "2048" and resolution_y == "1536" :
            return 150

        elif resolution_x == "1536" and resolution_y == "1024" :
            return 100


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
                """ open text meta infos of tif files
                    keywords: 
                    - on_bad_lines: skips a line if it does not suit the excepted columns (is toleratable since
                      important data is found in first column)
                    - engine: python since C does not support the keyword on_bad_lines 
                """
                df = pd.read_csv(file_path, encoding = "ANSI", on_bad_lines = "skip", engine = "python")

                """ get name of first column since all relevant informations are saved in that column 
                """
                tif_data = {"PixelWidth" : None,
                            "ResolutionX" : None,
                            "ResolutionY" : None,
                            }
                if type(df.index[0]) == int :
                    content = df[df.columns.to_list()[0]] 
                elif type(df.index[0]) == str :
                    content = df.index

                for idx in content :
                    if "PixelWidth" in idx :
                        tif_data["PixelWidth"] = float(idx.split("=")[1]) * 10**9
                    elif "ResolutionX" in idx :
                        tif_data["ResolutionX"] = idx.split("=")[1]
                    elif "ResolutionY" in idx :
                        tif_data["ResolutionY"] = idx.split("=")[1]



                """ skip the file if the file Thumbs.db is selected 
                """
                if "Thumbs.db" not in file_path :

                    self.ax.clear() 
                    """ find the size of one pixel and resolution in metadata file
                        find resolution of x and y axis 
                    """
                    pixel_size, unit = tif_data["PixelWidth"], "nm"

                    resolution_x, resolution_y = tif_data["ResolutionX"], tif_data["ResolutionY"]

                    print(type(resolution_x))

                    """ gives back a feedback Error if a new and unknown resolution
                        add new resolutions for debuuging: 

                        ends the running code execution so that the User does notice that Error and can report it 
                    """
                    if resolution_x != "1024" or resolution_y != "768" :

                        if resolution_x != "2048" or resolution_y != "1536" :

                            if resolution_x != "1536" or resolution_y != "1024" :

                                print("\nUnknown Resolution REPORT The Following Values And Image To Pascal Reiß\npascal.reiss@uni-bayreuth.de")
                                print(f"File name causing the Error: {file_path}, resolution x: {resolution_x}, resolution y: {resolution_y}")
                                exit()


                    """ get length treshold of scale bar in pixel for automatic scale bar insertion
                        loop through each possible scale bar length from self.scale_bar_lengths
                        calculate the scale bar length in pixel for each position
                        if scale bar length in pixel >= the set scale bar length treshold (in pixel) break the loop and 
                        set this length for the scale bar length 
                    """
                    scale_bar_in_pixel_treshold = self.get_scale_bar_in_pixel_for_resolution(resolution_x, resolution_y)

                    for scale_bar_length in self.scale_bar_lengths :

                        scale_bar_in_pixel = int(round(scale_bar_length / pixel_size))

                        if scale_bar_in_pixel > scale_bar_in_pixel_treshold :

                            break
                    
                    """ get unit of scale bar for scale bar label
                        check existing unit and check if scale_bar_length >= 1000 and divide it by 1000 and set next unit hierachry 
                    """
                    
                    if unit == "pm" :
                        if scale_bar_length >= 1000 :
                            unit = "nm"
                            scale_bar_length = int(scale_bar_length / 1000)

                    elif unit == "nm" :
                        if scale_bar_length >= 1000 :
                            unit = "µm"
                            scale_bar_length = int(scale_bar_length / 1000)

                    elif unit == "µm" :
                        if scale_bar_length >= 1000 :
                            unit = "mm"
                            scale_bar_length = int(scale_bar_length / 1000)

                    """ open the actual image from file_path and adding it a plt.figure 
                    """

                    image = plt.imread(file_path)

                    self.ax.imshow(image, "gray") # add image to figure

                    """ get font and scalbar properties for the determined resolution 
                    """

                    fontprops = self.get_font_properties_for_resolution(resolution_x, resolution_y)

                    size_vertical = self.get_vertical_size_scale_bar_for_resolution(resolution_x, resolution_y)

                    """ create a scale bar object
                    """
                    scalebar = AnchoredSizeBar(self.ax.transData,
                                           scale_bar_in_pixel, 
                                           f"{scale_bar_length} {unit}", self.scale_bar_position, 
                                           pad=0.5,
                                           color= self.scale_bar_color,
                                           frameon= self.frameon,
                                           size_vertical= size_vertical, 
                                           fontproperties = fontprops,
                                           sep = self.scale_bar_label_sep)  

                    """ add scalebar to image
                        set new ylim to cut off image data
                        turn off axis and save processed image as tif file  
                    """
                    self.ax.add_artist(scalebar)

                    ylim = self.get_cut_off_for_resolution(resolution_x, resolution_y)

                    self.ax.set_ylim(ylim)

                    self.ax.set_axis_off()

                    xlim = self.ax.get_xlim()

                    self.undo_list = [(xlim, ylim)]

                    self.preview_canvas.draw()


    def run_image_processing(self) :
        """ this function processes all images selected by the User
            if no files were selectedd an error feedback is given back
        """

        if len(self.file_paths) > 0 :

            """ loop throgh each files individually 
            """

            self.check_for_evaluation_folder()

            for n, file_path in enumerate(self.file_paths) :

                """ get name of file/sample from file_path
                """
                file_name = os.path.basename(file_path)
                sample_name = file_name.split(".tif")[0]

                self.image_processing_from_path(file_path)

                if not self.preview_mode :
                    self.fig.savefig(f"{self.path_evaluation_folder}\{sample_name}{self.figure_type}", dpi = self.figure_dpi, bbox_inches='tight',pad_inches = 0)




                """ feedback for User how for the image processing has been completed
                    known issues:
                    - does not update during evaluation process since the tkinter.Tk window freezes during this process 
                      (since the processing is not disturbed by this issue no bug fixing primarily necassary)
                """
                if self.feedback_label != None :
                    self.feedback_label.config(text = f"Image Processing in Progress. {n + 1} out of {len(self.file_paths)} finished.")

            if self.feedback_label != None :
                self.feedback_label.config(text = "Image Processing Finished")
        
        elif self.feedback_label != None :
            self.feedback_label.config(text = "Please Select Your Raw Images First.")


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
        run_processing_button = tk.Button(master = control_frame, text = "Run Image Processing", comman = self.run_image_processing, font = ("", 14))
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
        self.preview_frame.grid(row = 0, column = 1, padx = 5, pady = 5, rowspan = 2)

        label = tk.Label(master = self.preview_frame, text = "Preview", font = ("Arial", 22))
        label.grid(row = 0, column = 0, padx = 5, pady = 5)

        self.preview_canvas = FigureCanvasTkAgg(self.fig, master = self.preview_frame)
        self.preview_canvas.get_tk_widget().grid(row = 1, column = 0, padx = 5, pady = 5)

        preview_buttons_frame = tk.Frame(master = self.preview_frame)
        preview_buttons_frame.grid(row = 2, column = 0, padx = 5, pady = 5)

        self.preview_canvas.mpl_connect("button_press_event", self.get_xy_coords_mouse_press_event_plt)
        self.preview_canvas.mpl_connect("button_release_event", self.get_xy_coords_mouse_release_event_plt)
        self.preview_canvas.mpl_connect("motion_notify_event", self.create_dynamic_rectangle_in_plt)


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
            if __name__ != "__main__" :
                dic = {"0" : "1", "1" : "0"}
                change_properties_variable.set(dic[setting])


        change_properties_variable = tk.StringVar(value = "0" if __name__ == "__main__" else "1")
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

        label = tk.Label(master = change_properties_figure_frame, text = "Figure Settings",font = ("Arial", 16))
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

            if len(self.file_paths) > 0 :
                self.image_processing_from_path(self.file_paths[self.preview_index])

        settings_control_frame = tk.Frame(master = change_properties_frame, relief = "groove", borderwidth = 2)
        settings_control_frame.grid(row = 3, column = 0, padx = 5, pady = 5)
        
        apply_settings_button = tk.Button(master = settings_control_frame, text = "Apply Settings", command = change_properties, font = ("", 14))
        apply_settings_button.grid(row = 0, column = 0, padx = 5, pady = 5)



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
    """ main program if this program is run directly and is not imported into another python project
    """
    root = tk.Tk()

    sem = SEM_Image_Tool()
    sem.get_gui_frame(root)
    root.mainloop()






""" made by Stiftler (Pascal Reiß)
"""

"""
update list: 
Version 1.0.7 and before

- update list didn´t exist yet (it was a long way until a first working concept existed)

Version 1.0.8 (28.03.2022)
- added filetypes argument for tkinter.filedialog.askopenfilenames function to show only necessary files for the program
  in this case: ["TIFF Files", "*.tif"]

Version 1.1.1 (02.04.2022)
- added FigureCanvasTkAgg object from matplotlib.widgets as SEM_Image_Tool.preview_canvas: display preview picture in GUI
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

Version 1.1.2 (04.04.2022) CTRL is important
- added undo/redo function to cropout function 
  can be accessed by undo_button and redo_button (also CTRL + Z for undo and CTRL + Y for redo)
- added CTRl + S as shortcurt for saving current preview
- addd left and right arrow for switching preview
- added CTRL + K as shortcut for activating cropout function
- added CTRL + R as shortcurt for running image processing (all files)
- added CTRL + O as shortcut for opening files
"""

"""
- location scale bar
- pm conversion to nm
- size scale bar
- deletion of evaluation folder leads to problems during saving of files--> check if evaluation folder exists and if not create it
"""