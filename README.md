# Electro_Analysis

Install Python

    -go to https://www.python.org/downloads/release/python-3102/
    
    -download the respective file for your pc (in case for 64-bit Windows: Windows installer (64-bit))
    
    -open the downloaded file
    
    -IMPORTANT: mark the checkbox below for add Python to PATH 
    
    -use the fast installation option (Install Now) 
     includes pip, which is necassary for installing the further depencies of this project


Dependencies (Libary):

    -DM3 Reader for python: https://github.com/nanobore/dm3 (TEM)

    -tkinter (pre-installed with python)

    -pandas (install with console (pip): pip install pandas)

    -matplotlib (install with console (pip): pip install matplotlib)

    -os (usally pre-installed with python)

    -datetime (pre-installed with python)

    -numpy (install with console (pip): pip install numpy)

    -Pillow (pre-installed with python)


How to install DM3 reader:

    -go to https://github.com/nanobore/dm3 
    
    -download the complete project from the GitHub Project
    
    -unzip the file in some arbitrary folder (Destkop recommended)
    
    -open the folder and copy the link (path, e.g. C:\Users\Dieter Reiß\Desktop\piraynal-pydm3reader-d06ab6b3aa0f) 
    
    -open your console (Windows: search for cmd)
    
    -enter following command (path is your copied link): cd path      
     e.g. cd C:\Users\Dieter Reiß\Desktop\piraynal-pydm3reader-d06ab6b3aa0f 
     (changes directory of the command line to the respective folder)
     
    -install the package with the command: python setup.py install
    
    a successful installment yields the following output in the console:
    Finished processing dependencies for dm3-lib==1.2
    

