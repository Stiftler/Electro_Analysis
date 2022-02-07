""" TEM Scale Bar Tool by Pascal Reiß
    Version 1.0.1 
"""

import os
import pandas as pd
import tkinter as tk
from tkinter import filedialog
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1.anchored_artists import AnchoredSizeBar
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

        self.reset_attributes()

        self.program_frame = None
        self.feedback_label = None


    def reset_attributes(self) :
        """ resets all attributes to default values for the TEM_Image_Tool
            is executed once when a new TEM_Image_Tool class object
            creates the evaluation folder if it is not existing already
            path_evaluation_folder: */Evaluation/**
             * path of this program
             ** current date in the format YYYY-MM-DD
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

        self.scale_bar_lengths = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000]


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
                    scale_bar_pixel = scale_bar_length / pixel_size
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

                fig, ax = plt.subplots()
                ax.imshow(image_array, "gray", vmin = contrast[0], vmax = contrast[1]) 

                """ create the fontproperties of the scale bar
                    create the scale bar with the necessary attributes 
                """
                fontprops = fm.FontProperties(size = 20, fname = r"C:\WINDOWS\Fonts\arial.ttf")

                scale_bar = AnchoredSizeBar(ax.transData,
                                            scale_bar_pixel,
                                            f"{scale_bar_length} {pixel_unit}", "upper left",
                                            pad = 0.7,
                                            color = "white",
                                            frameon = False,
                                            size_vertical = 10,
                                            fontproperties = fontprops,
                                            sep = 10)

                """ add scale bar to image
                    turn off the x and y axis
                    save processed image as tif 
                """
                ax.add_artist(scale_bar)

                ax.set_axis_off()

                fig.savefig(f"{self.path_evaluation_folder}\{sample_name}.tif", dpi = 500, bbox_inches = "tight", pad_inches = 0)
                plt.close(fig)


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
        if pixel_unit == "nm" :
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

    tem = TEM_Image_Tool()
    tem.open_files()
    tem.run_image_processing()
