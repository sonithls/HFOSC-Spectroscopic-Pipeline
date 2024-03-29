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
import shutil

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
# from hfoscsp.file_management import SetCCD

from hfoscsp.reduction import ccdsec_removal
from hfoscsp.reduction import bias_correction
# from hfoscsp.reduction import cosmic_correction
from hfoscsp.reduction import flat_correction
from hfoscsp.reduction import spectral_extraction
from hfoscsp.reduction import flux_calibrate

from hfoscsp.cosmicray import cosmic_correction_individual
from hfoscsp.cosmicray import cosmic_correction_batch
from hfoscsp.cosmicray import cosmic_correction
from hfoscsp.cosmicray import display_co

from hfoscsp.headercorrection import headercorr
from hfoscsp.headercorrection import headercorr_k
from hfoscsp.interactive import options
from hfoscsp.interactive import multioptions
from hfoscsp.plotspec import spectral_plot

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


def batch_q():
    """Batch processing."""
    logo = """
###############################################################################
###############################################################################
                          HFOSC Spectroscopic Pipeline
                               Batch processing
                                Version: 1.0.0
###############################################################################
###############################################################################
1) Bias correction          2) Cosmic-ray correction    3) Flat correction
4) Wavelength calibration   5) Flux calibration         6) Plot tools
6) Backup                   7) Restore                  8) Header correction
10) Quit
"""
    print(logo)

# --------------------------------------------------------------------------- #


def list_sub(location=''):
    """
    List all sub directories which starts with a digit.

    Parameters
    ----------
        none
    Returns
    -------
        sub_directories: list
            name of sub-directories
    """
    if location != '':
        pathloc = os.path.join(os.getcwd(), location)
    else:
        pathloc = os.getcwd()

    print(pathloc)

    directory_contents = os.listdir(pathloc)
    sub_directories = []
    for item in directory_contents:
        # list directories
        if os.path.isdir(os.path.join(pathloc, item)):
            sub_directories.append(item)
            sub_directories.sort()
    return sub_directories


def b_bias(folder_name, PATH, CCD):
    """Batch-wise bias correction"""

    list_files = search_files(location=folder_name, keyword='*.fits')
    speclist, photlist = spec_or_phot(list_files, PATH, CCD, 'spec')
    # Check [Errno 17] File exists
    bias_list, passing_list = list_bias(speclist, PATH)
    print(bias_list, passing_list)

    bias_correction(bias_list=bias_list, list_file=passing_list, CCD=CCD,
                    location=PATH, prefix_string='b_')
    list_files = search_files(location=folder_name, keyword='*.fits')
    ccdsec_removal(file_list=list_files, location=PATH)


def b_cosmic(folder_name, PATH, CCD):
    """Batch-wise cosmic ray correction"""

    list_files = search_files(location=folder_name, keyword='*.fits')
    # print list_files

    obj_list, obj_l_gr7, obj_l_gr8, pas_list = list_object(list_files, PATH)
    flat_list, f_l_gr7, flat_l_gr8, pas_list = list_flat(list_files, PATH)
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
        cr_check_list = cosmic_correction_individual(cosmic_curr_list,
                                                     CCD=CCD, location=PATH)
    else:
        cr_check_list = cosmic_correction_batch(cosmic_curr_list, CCD=CCD,
                                                location=PATH)
        print(len(cr_check_list))
        # Stop running code for checking the cosmic ray corrected files
        message = """Cosmic ray correction is done.
Do you want to check chk files then continue?"""
        choices = ['Yes', 'No']
        value = options(message, choices)

        if value == "Yes":
            display_co(image_list=cosmic_curr_list, location=PATH)
            # for file in cr_check_list:
            #     remove_file(str(file))
        elif value == "No":
            pass
            # for file in cr_check_list:
            #     remove_file(str(file))


def b_flat(folder_name, PATH, CCD):
    """Batch-wise flat correction."""

    # Making file list for flat-correction
    list_files = search_files(location=folder_name, keyword='*.fits')

    obj_lst, obj_list_gr7, obj_list_gr8, pas_lst = list_object(list_files, PATH)
    flt_lst, flat_list_gr7, flat_list_gr8, pas_lst = list_flat(list_files, PATH)

    # Flat correction using file lists made.
    flat_curr_list = flat_correction(flat_list=flat_list_gr8,
                                     file_list=obj_list_gr8, grism='gr8',
                                     CCD=CCD, location=PATH, prefix_string='f')

    print("Flat correction grism 8 is done.", flat_curr_list)

    flat_curr_list = flat_correction(flat_list=flat_list_gr7,
                                     file_list=obj_list_gr7, grism='gr7',
                                     CCD=CCD, location=PATH, prefix_string='f')
    print("Flat correction grism 7 is done.", flat_curr_list)


def b_wave(folder_name, PATH, CCD, default_path):

    # making list for spectral extraction and wavelength calibration
    list_files = search_files(location=folder_name, keyword='*.fits')
    obj_lst, obj_list_gr7, obj_list_gr8, pas_lst = list_object(list_files, PATH)
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
    os.chdir(default_path)


def b_flux(folder_name, PATH, CCD, default_path):

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
    print("OK")


def b_plots(folder_name, PATH, default_path):
    os.chdir(default_path)
    list_files = search_files(location=folder_name, keyword='*ms.fits')

    message = "Select the files to plot"
    choices = list_files
    input_files = multioptions(message, choices)
    spectral_plot(file_list=input_files, location=PATH, type='flux')


def b_backup(pathloc):
    """Back up function."""

    back_up = os.path.join(pathloc, 'Backup')
    if os.path.exists(back_up) is False:
        os.makedirs(back_up)

    files = [f for f in os.listdir(pathloc) if
             os.path.isfile(os.path.join(pathloc, f))]
    # print(files)

    backup_folder = "Test1"  # user_input
    path_new = os.path.join(back_up, backup_folder)
    # print(path_new)

    if os.path.exists(path_new) is False:
        os.makedirs(path_new)

        for f in files:
            f = os.path.join(pathloc, f)
            shutil.copy(f, path_new)
    else:
        print("Backup is already exist with this name")


def b_restore(pathloc):
    """Restore function."""

    back_up = os.path.join(pathloc, 'Backup')
    if os.path.exists(back_up) is True:
        message = "Select folder"
        choices = list_sub(location=back_up)
        input = options(message, choices)
        backup_f = os.path.join(back_up, input)

        files_restore = [f for f in os.listdir(backup_f) if
                         os.path.isfile(os.path.join(backup_f, f))]

        files_safe = [f for f in os.listdir(pathloc) if
                      os.path.isfile(os.path.join(pathloc, f))]

        safe = os.path.join(back_up, 'safe')
        print(safe)
        if not os.path.exists(safe):
            os.mkdir(safe)
        else:
            safe = safe+'1'
            os.mkdir(safe)

        for f in files_safe:
            f_loc = os.path.join(pathloc, f)
            f_move = os.path.join(safe, f)
            print(f, f_move)
            shutil.move(f_loc, f_move)

        for f in files_restore:
            f = os.path.join(backup_f, f)
            shutil.copy(f, pathloc)


def b_headercorr(folder_name):
    """Correcting the header term errors"""
    list_files = search_files(location=folder_name, keyword='*.fits')
    headercorr_k(file_list=list_files, location=folder_name)


def batch_fuc(CCD):
    """Main function of batch operations."""
    batch_q()
    default_path = os.getcwd()
    PATH = os.path.join(os.getcwd(), list_subdir()[0])
    folder_name = list_subdir()[0]
    # print("default_path :", default_path)
    print("folder_name :", folder_name)
    # print("PATH :", PATH)

    A = True

    while A is True:
        message = "Select function"
        choices = ['Bias correction', 'Cosmic-ray correction',
                   'Flat correction', 'Wavelength calibration',
                   'Flux calibration',  'Plot tools', 'Backup',
                   'Restore', 'Header correction', 'Quit']
        input = options(message, choices)

        if input == 'Bias correction':
            b_bias(folder_name, PATH, CCD)
        elif input == 'Cosmic-ray correction':
            b_cosmic(folder_name, PATH, CCD)
        elif input == 'Flat correction':
            b_flat(folder_name, PATH, CCD)
        elif input == 'Wavelength calibration':
            b_wave(folder_name, PATH, CCD, default_path)
        elif input == 'Flux calibration':
            b_flux(folder_name, PATH, CCD, default_path)
        elif input == 'Plot tools':
            b_plots(folder_name, PATH, default_path)
        elif input == 'Backup':
            b_backup(pathloc=PATH)
        elif input == 'Restore':
            b_restore(pathloc=PATH)
        elif input == 'Header correction':
            b_headercorr(folder_name)
        elif input == 'Quit':
            A = False
            sys.exit()
