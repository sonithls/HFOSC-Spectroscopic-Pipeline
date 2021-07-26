import os
import glob
from astropy.io import fits
import time


def search_files(location='', keyword=''):
    """
    This function generate filelist from assigned folder with specific keyword in it.
    Arguments:
        location : location of the files if it is not in the working directory
        keyword  : keyword in the name of the file eg: "*.fits"
    Returns:
        file_list: List of files with the input keyword.
    """
    if location != '':      # change -- location
        pathloc = os.path.join(os.getcwd(), location)

    if keyword != '':
        file_list = glob.glob1(pathloc, keyword)
        file_list.sort()

    return file_list


list_files = search_files(os.getcwd(), keyword='*.fits')

count = 0

dash = '-' * 80
print(dash)
print('{:<40s}{:<20s}{:<12s}{:<12s}'.format("FILE NAME", "OBJECT", "GRISM", "APERTURE"))
print(dash)

file = open("file_info", 'w')
for file_name in list_files:
    hdul = fits.open(file_name)
    hdr = hdul[0].header  # the primary HDU header
    try:
        OBJECT = hdr['OBJECT']
        GRISM = hdr['GRISM']
        aperture = hdr['APERTUR']
    except:
        print("No object in header of : ", file_name)
        OBJECT = "none"
        GRISM = "none"
        aperture = "none"
# ----------------------- VBT--------------------------- #
#     OBJECT = hdr['OBJECT']
#     UPPER = hdr['UPPER']
#     LOWER = hdr['LOWER']
#     SLIT = hdr['SLIT']
# ------------------------------------------------------ #
    count += 1
    print('{:<40s}{:<20s}{:<12s}{:<12s}'.format(file_name, OBJECT, GRISM, aperture))
#     print (file_name, OBJECT, UPPER, LOWER, SLIT)
    file.writelines('{:<40s}{:<20s}{:<12s}{:<12s}'.format(file_name, OBJECT, GRISM, aperture)+'\n')
print(dash)

time.sleep(2)
