""" SEM Scale Bar Tool by Pascal Reiß
    Version 1.0.6
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


    def reset_attributes(self) :
        """ reset attributes (self.file_paths, self.scale_bar_lengths) to default values 
            and creates the evalution folder if it is not existing
            path_evalution_folder: */Evaluation/**
             * path of this program
             ** current date in the format YYYY-MM-DD
        """

        """ setup path for processed images and create it if not present on the systems 
        """
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

        self.file_paths = ()

        """ define possible scale bar lengths for the images 
        """
        self.scale_bar_lengths = [100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000] # in nm


    def open_files(self) :
        """ get file_paths from User if files were selected those file_paths are set as self.file_paths
            otherwise an error feedback is given back to the User
        """
        self.file_paths = ()

        root = tk.Tk()
        file_paths = filedialog.askopenfilenames(parent = root)
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
            
        return fm.FontProperties(size = 20, fname = r"C:\WINDOWS\Fonts\arial.ttf")


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

        if resolution_x == "1024" and resolution_y == "768" :
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
                if unit == "nm" :

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
                                       f"{scale_bar_length} {unit}", 'upper left', 
                                       pad=0.7,
                                       color='white',
                                       frameon=False,
                                       size_vertical= size_vertical, 
                                       fontproperties = fontprops,
                                       sep = 10)  

                """ add scalebar to image
                    set new ylim to cut off image data
                    turn off axis and save processed image as tif file  
                """
                ax.add_artist(scalebar)

                ylim = self.get_cut_off_for_resolution(resolution_x, resolution_y)

                ax.set_ylim(ylim)

                ax.set_axis_off()

                fig.savefig(f"{self.path_evaluation_folder}\{file_name}", dpi = 500, bbox_inches='tight',pad_inches = 0)

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

        """ create tkinter.Button, which can access the function self.open_files for getting the selected files by the User
        """
        open_files_button = tk.Button(master = self.program_frame, text = "Open Files", command = self.open_files)
        open_files_button.grid(row = 0, column = 0, padx = 5, pady = 5)

        """ create tkinter.Button, which can access the function self.run_image_processing
            for starting the image processing
        """
        run_processing_button = tk.Button(master = self.program_frame, text = "Run Image Processing", comman = self.run_image_processing)
        run_processing_button.grid(row = 0, column = 2, padx = 5, pady = 5)

        """ create a tkinter.Label, which contains the feedback for the User if an execution failed or was successful 
            (as a attribute of the SEM_Image_Tool class itself)
        """
        self.feedback_label = tk.Label(master = self.program_frame, text = "Please Select Your Raw Images First.")
        self.feedback_label.grid(row = 0, column = 1, padx = 5, pady = 5)

        return self.program_frame



if __name__ == "__main__" :
    """ main program if this program is run directly and is not imported into another python project
    """
    
    sem = SEM_Image_Tool()

    sem.open_files()
    sem.run_image_processing()





""" made by Stiftler (Pascal Reiß)
"""
