# -------------------------------------------------------------------------------------------------------------------- #
# This script is to semi-automate basic reduction of HFOSC spectrosopic data
# Author : Sonith L.S
# Contact : sonith.ls@iiap.res.in
__version__ = '0.0.5'
# Code is  written serially to check every functions are working properly
# Adiitional formatting required for running in for multiple number of folder in faster way.
# -------------------------------------------------------------------------------------------------------------------- #

# -------------------------------------------------------------------------------------------------------------------- #
# Import required libraries
# -------------------------------------------------------------------------------------------------------------------- #
import os
import sys
import glob
import shutil
import re
import shutil
from astropy.io import fits

try:
    from pyraf import iraf
except ImportError as error:
    print(error + "Please install pyraf and iraf")

# -------------------------------------------------------------------------------------------------------------------- #
# Import required modules
# -------------------------------------------------------------------------------------------------------------------- #
from hfoscsp.file_management import Backup
from hfoscsp.file_management import search_files
from hfoscsp.file_management import list_subdir
from hfoscsp.file_management import spec_or_phot
from hfoscsp.file_management import list_bias
from hfoscsp.file_management import remove_file
from hfoscsp.file_management import write_list
from hfoscsp.file_management import list_flat
from hfoscsp.file_management import list_lamp
from hfoscsp.file_management import list_object

from hfoscsp.reduction import ccdsec_removal
from hfoscsp.reduction import bias_correction
# from hfoscsp.reduction import cosmic_correction
from hfoscsp.reduction import flat_correction
from hfoscsp.reduction import spectral_extraction
from hfoscsp.reduction import flux_calibrate

from hfoscsp.cosmicray import cosmic_correction_individual
from hfoscsp.cosmicray import cosmic_correction
# -------------------------------------------------------------------------------------------------------------------- #
# Load IRAF Packages
# -------------------------------------------------------------------------------------------------------------------- #
iraf.noao(_doprint=0)
iraf.imred(_doprint=0)
iraf.specred(_doprint=0)
iraf.ccdred(_doprint=0)
iraf.images(_doprint=0)
iraf.astutil(_doprint=0)
iraf.crutil(_doprint=0)
iraf.twodspec(_doprint=0)
iraf.apextract(_doprint=0)
iraf.onedspec(_doprint=0)
iraf.ccdred.instrument = "ccddb$kpno/camera.dat"

# -------------------------------------------------------------------------------------------------------------------- #
"""CCD Information provided for running of IRAF module"""
# HFOSC1 #
# read_noise = 4.87
# ccd_gain   = 1.22
# data_max   = 55000

# HFOSC2 #
read_noise = 5.75
ccd_gain = 0.28
max_count = 700000
# -------------------------------------------------------------------------------------------------------------------- #
default_path = os.getcwd()
BACKUP = "HFOSC_PIPELINE_DataBackup"

bar = """
###############################################################################
###############################################################################
"""


def part1(flat_flag):
    # Backing up the whole directory
    # Backup (BACKUP)

    # Selecting the folder for reducing the data
    print(list_subdir())
    raw_input("Press Enter to continue...")  # Python 2
    PATH = os.path.join(os.getcwd(), list_subdir()[0])
    folder_name = list_subdir()[0]
    print(folder_name)
    list_files = search_files(location=folder_name, keyword='*.fits')
    # print list_files

    # Seperating photometric and spectrosopic files
    speclist, photlist = spec_or_phot(list_files, PATH, 'spec')
    # file_list is updated from passing list
    # print (speclist)

    # Running bias corrections
    bias_list, passing_list = list_bias(speclist, PATH)
    # print(bias_list)
    if len(bias_list) == 0:
        sys.exit('Bias list is empty, please check error in header of bias files')
    # print (passing_list)

    # Running bias corrections
    bias_correction(bias_list, passing_list, PATH)
    list_files = search_files(location=folder_name, keyword='*.fits')
    ccdsec_removal(file_list=list_files, location=PATH)

    # Running cosmic ray corrections
    list_files = search_files(location=folder_name, keyword='*.fits')
    # print list_files
    obj_list, obj_list_gr7, obj_list_gr8, passing_list = list_object(list_files, PATH)
    flat_list, flat_list_gr7, flat_list_gr8, passing_list = list_flat(list_files, PATH)
    # cosmic_curr_list = list(set(obj_list).union(flat_list))  # file which needed to correct for cosmic ray
    cosmic_curr_list = obj_list  # file which needed to correct for cosmic ray
    cosmic_curr_list_flats = flat_list
    print(len(cosmic_curr_list))
    write_list(file_list=cosmic_curr_list, file_name='cosmic_curr_list', location=PATH)

    cr_check_list = cosmic_correction(cosmic_curr_list_flats, location=PATH)

    # cosmicray correction manually for individual files or all files automatically
    print("Press Enter for running cosmicray correction with default settings")
    print("Press m and Enter for running cosmicray correction manually")
    input = raw_input()
    if input == 'm':
        cr_check_list = cosmic_correction_individual(cosmic_curr_list, location=PATH)
    else:
        cr_check_list = cosmic_correction(cosmic_curr_list, location=PATH)

    # Stop running code for checking the cosmic ray corrected files
    print("Cosmic ray correction is done. Please check chk files then continue")
    raw_input("Press Enter to continue...")  # Python 2
    for file in cr_check_list:
        remove_file(str(file))

    # ---------------------------flat-correction-------------------------- #
    if flat_flag == 'no' or 'No':
        pass
    else:
        # Making file list for flat-correction
        list_files = search_files(location=folder_name, keyword='*.fits')
        obj_list, obj_list_gr7, obj_list_gr8, passing_list = list_object(list_files, PATH)
        flat_list, flat_list_gr7, flat_list_gr8, passing_list = list_flat(list_files, PATH)
        # Flat correction using file lists made.
        flat_curr_list = flat_correction(flat_list=flat_list_gr8, file_list=obj_list_gr8, location=PATH, grism='gr8',
                                         prefix_string='f')
        print("Flat correction grism 8 is done.")
        flat_curr_list = flat_correction(flat_list=flat_list_gr7, file_list=obj_list_gr7, location=PATH, grism='gr7',
                                         prefix_string='f')
        print("Flat correction grism 7 is done.")

    # making list for spectral extraction and wavelength calibration
    list_files = search_files(location=folder_name, keyword='*.fits')
    obj_list, obj_list_gr7, obj_list_gr8, passing_list = list_object(list_files, PATH)
    lamp_list_gr7, lamp_list_gr8, passing_list = list_lamp(list_files, PATH)

    raw_input("Press Enter for spectral_extraction and wavelength calibration...") #Python 2
    # Running spectral_extraction function using file lists made
    spectral_extraction(obj_list=obj_list_gr7, lamp_list=lamp_list_gr7, location=PATH, grism='gr7')
    spectral_extraction(obj_list=obj_list_gr8, lamp_list=lamp_list_gr8, location=PATH, grism='gr8')

    print("Wavelength calibration of spectra is done")


def part2(folder_name, PATH):
    print(PATH)
    print(folder_name)

    raw_input("Press Enter for Flux_Calibration...") #Python 2

    # Running Flux calibration
    list_files = search_files(location=folder_name, keyword='*.fits')
    print(list_files)
    obj_list, obj_list_gr7, obj_list_gr8, passing_list = list_object(list_files, PATH)
    print(obj_list_gr7)
    flux_calibrate(obj_list=obj_list_gr8, location=PATH, default_path=default_path)
    flux_calibrate(obj_list=obj_list_gr7, location=PATH, default_path=default_path)


def main():
    """Main function of the HFOSC Spectrosopic Pipeline"""
    working_dir_path = os.getcwd()

    logo = """
###############################################################################
###############################################################################
                          HFOSC Spectrosopic Pipeline
                                Version: 0.0.5
###############################################################################
###############################################################################
"""
    print(logo)

    print("Current working directory :", working_dir_path)
    PATH = os.path.join(os.getcwd(), list_subdir()[0])
    folder_name = list_subdir()[0]

    print("If you are not using flats please type -- no -- and enter")
    flat_flag = raw_input()

    print("Press Enter for running complete code")
    print("Press 1 and Entre for running only flux calibration")
    input = raw_input()
    if input == '1':
        part2(folder_name=folder_name, PATH=PATH)
        os.chdir(working_dir_path)
    else:
        part1(flat_flag=flat_flag)
        os.chdir(working_dir_path)
        part2(folder_name=folder_name, PATH=PATH)


if __name__ == "__main__":
    main()
