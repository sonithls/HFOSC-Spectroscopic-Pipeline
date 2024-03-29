# --------------------------------------------------------------------------- #
"""This script is to semi-automate basic reduction of HFOSC spectroscopic data.

Additional formatting required for running in for multiple number of folder\
in faster way.

>>>Important header terms which is required for running the HFOSC
Spectroscopic Pipeline

1) 'OBJECT'
2) 'GRISM'
3) 'NAXIS1'
4) 'NAXIS2'
5) 'APERTUR'
6) 'INSTRUME'
7) 'LAMP'       for HFOSC
8) 'DATE-AVG'   for HFOSC2

>>>CCD Information provided for running of IRAF module

HFOSC1
------
# read_noise = 4.87
# ccd_gain   = 1.22
# data_max   = 55000

HFOSC2
------
# read_noise = 5.75
# ccd_gain = 0.28
# max_count = 700000
"""
# --------------------------------------------------------------------------- #
__author__ = 'Sonith L.S'
__contact__ = 'sonith.ls@iiap.res.in'
__version__ = '1.0.0'
# --------------------------------------------------------------------------- #

# --------------------------------------------------------------------------- #
# Import required libraries
# --------------------------------------------------------------------------- #
import os
import sys

try:
    from pyraf import iraf
except ImportError as error:
    print(error + "Please install pyraf and iraf")

# --------------------------------------------------------------------------- #
# Import required modules
# --------------------------------------------------------------------------- #
# from hfoscsp.file_management import Backup
from hfoscsp.file_management import search_files
from hfoscsp.file_management import list_subdir
from hfoscsp.file_management import spec_or_phot
from hfoscsp.file_management import list_bias
from hfoscsp.file_management import remove_file
from hfoscsp.file_management import write_list
from hfoscsp.file_management import list_flat
from hfoscsp.file_management import list_lamp
from hfoscsp.file_management import list_object
# from hfoscsp.file_management import setccd
from hfoscsp.file_management import SetCCD

from hfoscsp.reduction import ccdsec_removal
from hfoscsp.reduction import bias_correction
# from hfoscsp.reduction import cosmic_correction
from hfoscsp.reduction import flat_correction
from hfoscsp.reduction import spectral_extraction
from hfoscsp.reduction import flux_calibrate

from hfoscsp.cosmicray import cosmic_correction_individual
from hfoscsp.cosmicray import cosmic_correction_batch
from hfoscsp.cosmicray import cosmic_correction

from hfoscsp.headercorrection import headercorr
from hfoscsp.interactive import options
from hfoscsp.interactive import multioptions
from hfoscsp.plotspec import spectral_plot
from hfoscsp.batch import batch_fuc
from hfoscsp.headercorrection import headercorr_k

# --------------------------------------------------------------------------- #
# Load IRAF Packages
# --------------------------------------------------------------------------- #
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

# --------------------------------------------------------------------------- #

# --------------------------------------------------------------------------- #
default_path = os.getcwd()
BACKUP = "HFOSC_PIPELINE_DataBackup"

bar = """
###############################################################################
###############################################################################
"""


def part1(CCD):
    """Part one - wavelength calibration."""
    # Backing up the whole directory
    # Backup (BACKUP)

    message = "Do you want to do flat-fielding ?"
    choices = ['Yes', 'No']
    flat_flag = options(message, choices)
    # Question for flat-fielding using flat_flag

    # Selecting the folder for reducing the data
    print(list_subdir())
    # raw_input("Press Enter to continue...")  # Python 2

    message = "Do you want to continue ? Please press Enter"
    choices = ['Yes']
    options(message, choices)

    PATH = os.path.join(os.getcwd(), list_subdir()[0])
    folder_name = list_subdir()[0]
    print(folder_name)
    list_files = search_files(location=folder_name, keyword='*.fits')
    # print list_files

    # Separating photometric and spectroscopic files
    speclist, photlist = spec_or_phot(list_files, PATH, CCD, 'spec')
    # file_list is updated from passing list
    # print (speclist)

    # Running bias corrections
    bias_list, passing_list = list_bias(speclist, PATH)
    # print(bias_list)
    if len(bias_list) == 0:
        sys.exit('Bias list is empty, please check header of bias files')
    # print (passing_list)

    # Running bias corrections
    bias_correction(bias_list, passing_list, CCD, PATH)
    list_files = search_files(location=folder_name, keyword='*.fits')
    ccdsec_removal(file_list=list_files, location=PATH)

    # Running cosmic ray corrections
    list_files = search_files(location=folder_name, keyword='*.fits')
    # print list_files
    obj_list, obj_list_gr7, obj_list_gr8, passing_list = list_object(list_files,
                                                                     PATH)
    flat_list, flat_list_gr7, flat_list_gr8, passing_list = list_flat(list_files,
                                                                      PATH)
    # cosmic_curr_list = list(set(obj_list).union(flat_list))
    # file which needed to correct for cosmic ray
    cosmic_curr_list = obj_list  # file which needed to correct for cosmic ray
    cosmic_curr_list_flats = flat_list
    print(len(cosmic_curr_list))
    write_list(file_list=cosmic_curr_list, file_name='cosmic_curr_list',
               location=PATH)

    cr_check_list = cosmic_correction(cosmic_curr_list_flats, location=PATH)

    for file in cr_check_list:
        remove_file(str(file))

    # cosmic-ray correction manually for individual files
    # or all files automatically
    message = "How do you like to proceed Cosmic ray correction?"
    choices = ['Default', 'Manually']
    input = options(message, choices)

    if input.lower() == 'manually':
        cr_check_list = cosmic_correction_individual(cosmic_curr_list, CCD=CCD,
                                                     location=PATH)
    else:
        cr_check_list = cosmic_correction_batch(cosmic_curr_list, CCD=CCD,
                                                location=PATH)

    # Stop running code for checking the cosmic ray corrected files
    print("Cosmic ray correction is done. Please check chk files then continue")

    # raw_input("Press Enter to continue...")  # Python 2
    message = "Do you want to continue ?"
    choices = ['Yes']
    options(message, choices)

    for file in cr_check_list:
        remove_file(str(file))

    # ---------------------------flat-correction----------------------------- #
    if str(flat_flag).lower() == 'no':
        print("flat_flag :", flat_flag)
        print("No flat fielding")
    elif str(flat_flag).lower() == 'yes':
        # Making file list for flat-correction
        list_files = search_files(location=folder_name, keyword='*.fits')
        obj_list, obj_list_gr7, obj_list_gr8, passing_list = list_object(list_files, PATH)
        flat_list, flat_list_gr7, flat_list_gr8, passing_list = list_flat(list_files, PATH)
        # Flat correction using file lists made.

        flat_curr_list = flat_correction(flat_list=flat_list_gr8,
                                         file_list=obj_list_gr8, grism='gr8',
                                         CCD=CCD,
                                         location=PATH, prefix_string='f')
        print("Flat correction grism 8 is done.", flat_curr_list)

        flat_curr_list = flat_correction(flat_list=flat_list_gr7,
                                         file_list=obj_list_gr7, grism='gr7',
                                         CCD=CCD,
                                         location=PATH, prefix_string='f')
        print("Flat correction grism 7 is done.", flat_curr_list)

    # making list for spectral extraction and wavelength calibration
    list_files = search_files(location=folder_name, keyword='*.fits')
    obj_list, obj_list_gr7, obj_list_gr8, passing_list = list_object(list_files,
                                                                     PATH)
    lamp_list_gr7, lamp_list_gr8, passing_list = list_lamp(list_files, PATH)

    message = "Press Enter for spectral_extraction and wavelength calibration.."
    choices = ['Yes']
    options(message, choices)

    # Running spectral_extraction function using file lists made
    spectral_extraction(obj_list=obj_list_gr7, lamp_list=lamp_list_gr7,
                        location=PATH, CCD=CCD, grism='gr7')

    spectral_extraction(obj_list=obj_list_gr8, lamp_list=lamp_list_gr8,
                        location=PATH, CCD=CCD, grism='gr8')

    print("Wavelength calibration of spectra is done")


def part2(folder_name, PATH, CCD):
    print(PATH)
    print(folder_name)

    # raw_input("Press Enter for Flux_Calibration...") # Python 2
    message = "Press Enter for Flux_Calibration..."
    choices = ['Yes']
    options(message, choices)

    # Header correction
    list_files = search_files(location=folder_name, keyword='*.ms.fits')
    headercorr(file_list=list_files, location=folder_name)

    # Running Flux calibration
    list_files = search_files(location=folder_name, keyword='*.fits')
    print(list_files)

    obj_lst, obj_list_gr7, obj_list_gr8, pas_lst = list_object(list_files, PATH)
    print(obj_list_gr7)
    flux_calibrate(obj_list=obj_list_gr8, location=PATH,
                   default_path=default_path, CCD=CCD)

    flux_calibrate(obj_list=obj_list_gr7, location=PATH,
                   default_path=default_path, CCD=CCD)


def b_headercorr(folder_name):
    """Correcting the header term errors"""
    list_files = search_files(location=folder_name, keyword='*.fits')
    headercorr_k(file_list=list_files, location=folder_name)


def main():
    """Run the HFOSC Spectroscopic Pipeline."""
    working_dir_path = os.getcwd()

    logo = """
###############################################################################
###############################################################################
                          HFOSC Spectroscopic Pipeline
                                Version: 1.0.0
###############################################################################
###############################################################################
"""
    print(logo)

    print("Current working directory :", working_dir_path)
    PATH = os.path.join(os.getcwd(), list_subdir()[0])
    folder_name = list_subdir()[0]

    list_files_ccdcheck = search_files(location=folder_name, keyword='*.fits')

    CCD = SetCCD(file_list=list_files_ccdcheck, location=PATH)

    A = True
    while A is True:

        message = "Select the mode of running the Pipeline"
        choices = ['Batch-wise operation', 'Complete Code',
                   'Only Flux Calibration',
                   'Plot spectra', 'Header correction', 'Quit']
        input = options(message, choices)

        if input == 'Batch-wise operation':
            batch_fuc(CCD=CCD)

        elif input == 'Complete Code':
            part1(CCD=CCD)
            os.chdir(working_dir_path)
            part2(folder_name=folder_name, PATH=PATH, CCD=CCD)

        elif input == 'Only Flux Calibration':
            part2(folder_name=folder_name, PATH=PATH, CCD=CCD)
            os.chdir(working_dir_path)

        elif input == 'Plot spectra':
            os.chdir(working_dir_path)
            list_files = search_files(location=folder_name, keyword='*ms.fits')

            message = "Select the files to plot"
            choices = list_files
            input_files = multioptions(message, choices)
            spectral_plot(file_list=input_files, location=PATH, type='flux')

        elif input == 'Header correction':
            b_headercorr(folder_name)

        elif input == 'Quit':
            A = False


if __name__ == "__main__":
    main()
