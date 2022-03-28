""" SEM Scale Bar Tool by Pascal Reiß
    Version 1.0.8
"""

from PIL import Image
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1.anchored_artists import AnchoredSizeBar
import matplotlib.font_manager as fm
import os
from datetime import datetime 

from tkinter import filedialog
import tkinter as tk
from tkinter import ttk




class SEM_Image_Tool :

    def __init__(self) :
        """ initiate SEM_Image_Tool class object with the following attributes:
            - self.frame (tkinter.Frame) and self.feedback_label (tkinter.Label)
              objects are required in the GUI 
            - self.file_paths (tuple: contains the file_paths of the raw data files
              is set under the function self.reset_attributes)
            - self.scale_bar_lengths (list: contains possible length scales (int) for the scale bar added in the images)
        """

        self.program_name = "SEM Scale Bar Tool"

        self.program_frame = None

        self.reset_attributes()

        self.feedback_label = None


        self.fonts = {"consola" : r"C:\WINDOWS\Fonts\consola.ttf",
                      "arial_1" : r"C:\Windows\Fonts\arial.ttf", 
                      "arial_2" : r"C:\WINDOWS\Fonts\ARIALN.TTF",
                      "times" : r"C:\Windows\Fonts\times.ttf",
                      }

        self.figure_types = {"TIFF" : ".tif",
                             "PNG" : ".png",
                             "EPS" : ".eps",
                             "JPG" : ".jpg"}

        self.colors = ["white", "black", "grey",  "red", "blue", "green", "cyan", "magenta", "yellow"]

        self.scale_bar_positions = ["upper left", "upper right", "lower left", "lower right"]

        self.preview_mode = False


        self.reset_figure_attributes()
        self.reset_scale_bar_attributes()


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
        self.font_selected = self.fonts["arial_1"]

        self.scale_bar_color = self.colors[0]
        self.scale_bar_position = self.scale_bar_positions[0]
        self.frameon = False
        self.scale_bar_label_sep = 10

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

            if self.feedback_label != None :
                self.feedback_label.config(text = "Image Processing Can Now Be Started.")

        elif self.feedback_label != None :
            self.feedback_label.config(text = "Please Select Your Raw Images First.")


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


    def get_vertical_size_scale_bar_for_resolution(self, resolution_x, resolution_y) :
        """ returns the vertical size setting of the scale_bar depending on the resolution
        """

        if resolution_x == "1024" and resolution_y == "768" :
            return 10

        elif resolution_x == "2048" and resolution_y == "1536" :
            return 20


    def get_scale_bar_in_pixel_for_resolution(self, resolution_x, resolution_y) :
        """ get length of the scale_bar in pixel depending on the resolution 
        """
        if self.scale_bar_treshold != "automatic" :
            return self.scale_bar_treshold

        elif resolution_x == "1024" and resolution_y == "768" :
            return 75

        elif resolution_x == "2048" and resolution_y == "1536" :
            return 150


    def run_image_processing(self) :
        """ this function processes all images selected by the User
            if no files were selectedd an error feedback is given back
        """

        if len(self.file_paths) > 0 :

            """ loop throgh each files individually 
            """

            self.check_for_evaluation_folder()

            for n, file_path in enumerate(self.file_paths) :

                """ open text meta infos of tif files
                    keywords: 
                    - on_bad_lines: skips a line if it does not suit the excepted columns (is toleratable since
                      important data is found in first column)
                    - engine: python since C does not support the keyword on_bad_lines 
                """
                df = pd.read_csv(file_path, encoding = "ANSI", on_bad_lines = "skip", engine = "python")

                """ get name of first column since all relevant informations are saved in that column 
                """
                column = df.columns.tolist()[0]

                """ get name of file/sample from file_path
                """
                file_name = os.path.basename(file_path)
                sample_name = file_name.split(".tif")[0]

                """ skip the file if the file Thumbs.db is selected 
                """
                if file_name == "Thumbs.db" :
                    continue

                print(file_name)

                """ find the size of one pixel and resolution in metadata file
                    find resolution of x and y axis 
                """
                pixel_size, unit = self.get_pixel_size_and_unit(df[column])

                resolution_x, resolution_y = self.get_resolution(df[column])

                """ gives back a feedback Error if a new and unknown resolution
                    add new resolutions for debuuging: 

                    ends the running code execution so that the User does notice that Error and can report it 
                """
                if resolution_x != "1024" or resolution_y != "768" :

                    if resolution_x != "2048" or resolution_y != "1536" :

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

                fig, ax = plt.subplots()

                ax.imshow(image) # add image to figure

                """ get font and scalbar properties for the determined resolution 
                """

                fontprops = self.get_font_properties_for_resolution(resolution_x, resolution_y)

                size_vertical = self.get_vertical_size_scale_bar_for_resolution(resolution_x, resolution_y)

                """ create a scale bar object
                """
                scalebar = AnchoredSizeBar(ax.transData,
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
                ax.add_artist(scalebar)

                ylim = self.get_cut_off_for_resolution(resolution_x, resolution_y)

                ax.set_ylim(ylim)

                ax.set_axis_off()

                if not self.preview_mode :
                    fig.savefig(f"{self.path_evaluation_folder}\{sample_name}{self.figure_type}", dpi = self.figure_dpi, bbox_inches='tight',pad_inches = 0)

                if self.preview_mode :
                    plt.show()

                plt.close(fig) # close figure for improved ram usage

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
        self.program_frame.grid(row = 1, column = 1, padx = 5, pady = 5)

        control_frame = tk.Frame(master = self.program_frame, relief = "groove", borderwidth = 2)
        control_frame.grid(row = 0, column = 0, padx = 5, pady = 5)

        """ create tkinter.Button, which can access the function self.open_files for getting the selected files by the User
        """
        open_files_button = tk.Button(master = control_frame, text = "Open Files", command = self.open_files)
        open_files_button.grid(row = 0, column = 0, padx = 5, pady = 5)

        """ create tkinter.Button, which can access the function self.run_image_processing
            for starting the image processing
        """
        run_processing_button = tk.Button(master = control_frame, text = "Run Image Processing", comman = self.run_image_processing)
        run_processing_button.grid(row = 0, column = 2, padx = 5, pady = 5)

        """ create a tkinter.Label, which contains the feedback for the User if an execution failed or was successful 
            (as a attribute of the SEM_Image_Tool class itself)
        """
        self.feedback_label = tk.Label(master = control_frame, text = "Please Select Your Raw Images First.")
        self.feedback_label.grid(row = 0, column = 1, padx = 5, pady = 5)

        """ create a tkinter.Frame, which contains all widget necassary for the User if changes to the figures shall be made (compared to the standard process) 
        """
        change_properties_frame = tk.Frame(master = self.program_frame, relief = "groove", borderwidth = 2)

        def enable_change_properties_frame() :
            setting = change_properties_variable.get()
            if setting == "1" :
                change_properties_frame.grid(row = 1, column = 0, padx = 5, pady = 5)

            elif setting == "0" :
                change_properties_frame.grid_forget()

        change_properties_variable = tk.StringVar()
        change_properties_checkbox = ttk.Checkbutton(control_frame, text = "change settings",
                                                        variable = change_properties_variable, command = enable_change_properties_frame)
        change_properties_checkbox.grid(row = 1, column = 0, padx = 5, pady = 5)

        """ tkinter.Frame with all widgets necessary for changing general scale bar settings
        """

        change_properties_scale_bar_frame = tk.Frame(master = change_properties_frame, relief = "groove", borderwidth = 2)
        change_properties_scale_bar_frame.grid(row = 0, column = 0, padx = 5, pady = 5)

        label = tk.Label(master = change_properties_scale_bar_frame, text = "Scale Bar Settings")
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
        scale_bar_treshold_label.grid(row = 6, column = 0, padx = 5, pady = 5)

        scale_bar_treshold_label = tk.Label(master = change_properties_scale_bar_frame, text = f"{self.scale_bar_treshold}")
        scale_bar_treshold_label.grid(row = 6, column = 1, padx = 5, pady = 5)

        scale_bar_treshold_entry = tk.Entry(master = change_properties_scale_bar_frame)
        scale_bar_treshold_entry.grid(row = 6, column = 2, padx = 5, pady = 5)

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
        scale_bar_frame_checkbox.grid(row = 7, column = 0, padx = 5, pady = 5)

        """ add properties of scale bar
        """

        change_properties_figure_frame = tk.Frame(master = change_properties_frame, relief = "groove", borderwidth = 2)
        change_properties_figure_frame.grid(row = 0, column = 1, padx = 5, pady = 5)

        label = tk.Label(master = change_properties_figure_frame, text = "Figure Settings")
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
            change_treshold()
            change_frame_scale_bar()
            change_figure_type()

        settings_control_frame = tk.Frame(master = change_properties_frame, relief = "groove", borderwidth = 2)
        settings_control_frame.grid(row = 0, column = 3, padx = 5, pady = 5)
        apply_settings_button = tk.Button(master = settings_control_frame, text = "Apply Settings", command = change_properties)
        apply_settings_button.grid(row = 0, column =0, padx = 5, pady = 5)

        def get_preview() :
            if len(self.file_paths) > 0 :
                file_paths = self.file_paths 
                self.file_paths = (self.file_paths[0],)
                self.preview_mode = True
                self.run_image_processing()
                self.preview_mode = False
                self.file_paths = file_paths
            else :
                self.feedback_label.config(text = "Please Select At Least One File First.")
        preview_button = tk.Button(master = settings_control_frame, text = "Preview Of Current Settings", command = get_preview)
        preview_button.grid(row = 1, column = 0, padx = 5, pady = 5)

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
"""

"""
- location scale bar
- pm conversion to nm
- size scale bar
- deletion of evaluation folder leads to problems during saving of files--> check if evaluation folder exists and if not create it
"""