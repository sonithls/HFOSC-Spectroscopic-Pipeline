import os
import re
import glob
import numpy as np
from astropy.io import fits


def search_files (location='', keyword=''):
    """
    This function generate filelist from assigned folder with specific keyword in it.
    Arguments:
        location : location of the files if it is not in the working directory
        keyword  : keyword in the name of the file eg: "*.fits"
    Returns:
        file_list: List of files with the input keyword.
    """
    if location != '':                                                #change -- location
        pathloc = os.path.join(os.getcwd(), location)

    if keyword != '':
        file_list = glob.glob1(pathloc, keyword)

    return file_list


list_files = search_files(os.getcwd(),keyword='*.fits')

count =0

file = open("file_info", 'w')
for file_name in list_files :
    hdul = fits.open(file_name)
    hdr = hdul[0].header  # the primary HDU header
    OBJECT =hdr['OBJECT']
    GRISM =hdr['GRISM']
#     OBJECT = hdr['OBJECT']
#     UPPER = hdr['UPPER']
#     LOWER = hdr['LOWER']
#     SLIT = hdr['SLIT']
    count +=1
    print (file_name, OBJECT, GRISM)
#     print (file_name, OBJECT, UPPER, LOWER, SLIT)
    file.writelines(file_name+"  "+OBJECT+"  "+GRISM+ '\n')

print ("Done")
