# --------------------------------------------------------------------------- #
"""
This script is written for HFOSC spectroscopic-Pipeline.

It is containing file management utilities for running the
HFOSC spectroscopic-Pipeline.
"""
__author__ = 'Sonith L.S'
__contact__ = 'sonith.ls@iiap.res.in'
__version__ = '1.0.1'
# --------------------------------------------------------------------------- #
import os
import glob
import shutil
# import re
from astropy.io import fits

# --------------------------------------------------------------------------- #

default_path = os.getcwd()
BACKUP = "HFOSC_PIPELINE_DataBackup"

# Keep every keywords in small letters in the list
KEYWORDS = {'BIAS': ["bias_snspec", "bias_sn", "bias", "bias snspec",
                     "bias-snspec"],
            'FLAT': ["flat", "halogen", "spectral flat", "spectral flats"],
            'LAMP': ["lamp", "fear", "fe-ar", "fene", "fe-ne"],
            'FEAR': ["fear", "fe-ar"],
            'FENE': ["fene", "fe-ne"],
            'GR7': ["grism 7", "4 grism 7", "gr7"],
            'GR8': ["grism 8", "3 grism 8", "gr8"]}


class SetCCD:
    """Set CCD parameters from fits file provided."""

    def __init__(self, file_list, location):
        """Initialise parameters."""
        for file in file_list:
            file_name = os.path.join(location, file)
            hdul = fits.open(file_name)  # HDU_List
            hdr = hdul[0].header
            inst = hdr['INSTRUME'].strip(' ')

            if inst == 'HFOSC2':
                self.ccd = "HFOSC2"  # New HCT CCD # HFOSC2 #
                self.read_noise = 5.75
                self.ccd_gain = 0.28
                self.max_count = 700000
                break
            elif inst == "HFOSC":
                self.ccd = "HFOSC"  # Old HCT CCD # HFOSC #
                self.read_noise = 4.87
                self.ccd_gain = 1.22
                self.max_count = 52000  # 55000 ?
                break
            else:
                print("HEADER ERROR")


def setccd(file_list, location):
    """Select CCD based on header keywords in the fits files."""
    for file in file_list:
        file_name = os.path.join(location, file)
        hdul = fits.open(file_name)  # HDU_List
        hdr = hdul[0].header
        inst = hdr['INSTRUME'].strip(' ')

        if inst == 'HFOSC2':
            ccd = "HFOSC2"  # New HCT CCD # HFOSC2 #
            read_noise = 5.75
            ccd_gain = 0.28
            max_count = 700000
            break
        elif inst == "HFOSC":
            ccd = "HFOSC"  # Old HCT CCD # HFOSC #
            read_noise = 4.87
            ccd_gain = 1.22
            max_count = 52000  # 55000 ?
            break
        else:
            print("HEADER ERROR")
    return read_noise, ccd_gain, max_count, ccd


def Backup(BACKUPDIR):
    """
    Copy all the files in present directory to the  Backup.

    Parameters
    ----------
        BACKUPDIR : str
            Name of the backup directory
    Returns
    -------
        none
    """
    os.makedirs('../'+BACKUPDIR)
    print("Copying files to ../"+BACKUPDIR)
    os.system('cp -r * ../'+BACKUPDIR)


def search_files(keyword, location=''):
    """
    Generate a file_list from assigned folder containing files with specific\
    keyword in it.

    Parameters
    ----------
        location : str
            Location of the files if it is not in the working directory
        keyword  : str
            Keyword in the name of the file e.g.: "*.fits"
    Returns
    -------
        file_list: list
            List of files with the input keyword.
    """
    if location != '':  # changing location
        loc = os.path.join(os.getcwd(), location)
    else:
        loc = os.getcwd()

    if keyword != '':
        file_list = glob.glob1(loc, keyword)

    return file_list


def list_subdir():
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
    directory_contents = os.listdir(os.getcwd())
    sub_directories = []
    for item in directory_contents:
        # list directories which have first charater a digit
        if os.path.isdir(item) and item[0].isdigit():
            sub_directories.append(item)
            sub_directories.sort()
    return sub_directories


def spec_or_phot(file_list, location, CCD, func=''):
    """
    Check whether the file contains spectroscopy of photometry data and make\
    separate list for both spectroscopy and photometry with respective file\
    names.

    Parameters
    ----------
        file_list: list
            List of all files in the directory from which files need to
            identify
        location : str
            Location of the files if it is not in the working directory
        func     : str ('spec' or 'phot')
            type of files need keep in original folder as it is. Remaining
            files will be moved to other directory.
    Returns
    -------
        spec_list: list
            List of spectroscopic files
        phot_list: list
            List of photometric files
    """
    if CCD.ccd == "HFOSC":
        index = 0
    elif CCD.ccd == "HFOSC2":
        index = 1

    spec_list = []
    phot_list = []
    spec_list_fullname = []
    phot_list_fullname = []
    for file in file_list:
        file_name = os.path.join(location, file)
        hdul = fits.open(file_name)  # HDU_List
        hdul[index].header
        hdr = hdul[index].header
        AXIS1 = hdr['NAXIS1']
        AXIS2 = hdr['NAXIS2']
        value = AXIS2/AXIS1
        if value > 2:
            spec_list.append(file)
            spec_list_fullname.append(file_name)
        elif value <= 2:
            phot_list.append(file)
            phot_list_fullname.append(file_name)

    if func == 'spec':
        try:
            pathloc = os.path.join(location, 'phot')
            os.mkdir(pathloc)
            for file in phot_list_fullname:
                shutil.move(file, pathloc)

        except OSError as error:
            print(error)

    elif func == 'phot':
        try:
            pathloc = os.path.join(location, 'spec')
            os.mkdir(pathloc)
            for file in spec_list_fullname:
                shutil.move(file, pathloc)

        except OSError as error:
            print(error)

    return spec_list, phot_list


def list_bias(file_list, location='', keywords=KEYWORDS):
    """
    Identify bias files from file_list provided by looking the header keyword\
    in the files.

    Parameters
    ----------
        file_list   : list
            List of all files in the directory from which files need to
            identify.
        location    : str
            Location of the files if it is not in the working directory.
    Returns
    -------
        bias_list   : list
            List of bias files from the file_list provided.
        passing_list: list
            Remaining files after removing bias files from the file_list.
    """
    bias_list = []
    for file in file_list:
        file_name = os.path.join(location, file)
        hdul = fits.open(file_name)  # HDU_List
        hdr = hdul[0].header        # Primary HDU header
        OBJECT = hdr['OBJECT']

        if OBJECT.lower() in keywords['BIAS']:
            bias_list.append(file)

    passing_list = list(set(file_list).difference(bias_list))
    passing_list.sort()
    return bias_list, passing_list


def remove_file(file_name):
    """
    Remove a file from the directory.

    Parameters
    ----------
        file_name: file name of the file to remove from directory.
    Returns
    -------
        none
    """
    try:
        os.remove(file_name)
    except OSError:
        pass


def write_list(file_list, file_name, location=''):
    """
    Write file names with complete path in a text file in the destination\
    provided, using the input file_list.

    Parameters
    ----------
        file_list: list
            List of files need to write into a text file.
        file_name: str
            Name of the text file.
        location : str
            location of the files if it is not in the working directory.
    Returns
    -------
        none
        file list with file_file in the given location with file names in it.
    """
    if location != '':
        pathloc = os.path.join(os.getcwd(), location, file_name)

    if len(file_list) != 0:
        with open(pathloc, 'w') as f:
            for file in file_list:
                file = os.path.join(os.getcwd(), location, file)
                f.write(file+'\n')


def list_flat(file_list, location='', keywords=KEYWORDS):
    """
    From the file_list provided, separate files into flat files and further\
    separate them into grism7 and grism8 files.

    Parameters
    ----------
        file_list: list
            List of files need to separate.
        location : str
            Location of the files if it is not in the working directory.
    Returns
    -------
        flat_list    : list
            List of all flat files.
        flat_list_gr7: list
            List of gr7 flat files.
        flat_list_gr8: list
            List of gr8 flat files.
        passing_list : list
            List of rest of the files in file-list.
    """
    flat_list = []
    flat_list_gr7 = []
    flat_list_gr8 = []
    passing_list = []

    for file in file_list:
        file_name = os.path.join(location, file)
        hdul = fits.open(file_name)  # HDU_List
        hdr = hdul[0].header         # Primary HDU header
        OBJECT = hdr['OBJECT']
        GRISM = hdr['GRISM']

        try:
            COMMENT = hdr['COMMENT']
        except:
            COMMENT = ''


        if OBJECT.lower() in keywords['FLAT']:
            flat_list.append(file)
            if GRISM.lower() in keywords['GR7']:
                flat_list_gr7.append(file)
            elif GRISM.lower() in keywords['GR8']:
                flat_list_gr8.append(file)
            elif COMMENT != '':
                GRISM = COMMENT[0][3:6]
                if GRISM.lower() in keywords['GR7']:
                    flat_list_gr7.append(file)
                elif GRISM.lower() in keywords['GR8']:
                    flat_list_gr8.append(file)
            else:
                print(file)
                print("There is error in header term : GRISM")

        else:
            passing_list.append(file)

    print('Grism 7 flat files :', flat_list_gr7)
    print('Grism 8 flat files :', flat_list_gr8)

    return flat_list, flat_list_gr7, flat_list_gr8, passing_list


def list_lamp(file_list, location='', keywords=KEYWORDS):
    """
    From the file_list provided, separate files into lamp files and further\
    separate them into grism7 and grism8 files.

    Parameters
    ----------
        file_list: list
            List of files need to separate.
        location : str
            Location of the files if it is not in the working directory.
    Returns
    -------
        lamp_list_gr7: list
            List of gr7 lamp files.
        lamp_list_gr8: list
            List of gr8 lamp files.
        passing_list : list
            List of rest of the files in file-list.
    """
    lamp_list_gr7 = []
    lamp_list_gr8 = []

    for file in file_list:
        file_name = os.path.join(location, file)
        hdul = fits.open(file_name)  # HDU_List
        hdr = hdul[0].header         # Primary HDU header
        OBJECT = hdr['OBJECT']
        GRISM = hdr['GRISM']
        LAMP = hdr['LAMP']

        if OBJECT.lower() in keywords['FEAR']:
            lamp_list_gr7.append(file)
        elif OBJECT.lower() in keywords['FENE']:
            lamp_list_gr8.append(file)
        # For HFOSC1 old CCD, not kept using from KEYWORDS
        elif (OBJECT.lower() == "lamp"):
            if LAMP.lower() in keywords['FEAR']:
                lamp_list_gr7.append(file)
            elif LAMP.lower() in keywords['FENE']:
                lamp_list_gr8.append(file)

    passing_list = list(set(file_list).difference(lamp_list_gr7).difference(lamp_list_gr8))
    return lamp_list_gr7, lamp_list_gr8, passing_list


def list_object(file_list, location='', keywords=KEYWORDS):
    """
    From the file_list provided, separate files into object files and further\
    separate them into grism7 and grism8 files.

    Parameters
    ----------
        file_list: list
            List of files need to separate.
        location : str
            Location of the files if it is not in the working directory.
    Returns
    -------
        obj_list    : list
            List of all objects.
        obj_list_gr7: list
            List of gr7 object files.
        obj_list_gr8: list
            List of gr8 object files.
        passing_list : list
            List of rest of the files in file-list.
    """
    obj_list = []
    obj_list_gr7 = []
    obj_list_gr8 = []
    passing_list = []
    for file in file_list:
        file_name = os.path.join(location, file)
        hdul = fits.open(file_name)  # HDU_List
        hdr = hdul[0].header         # Primary HDU header
        OBJECT = hdr['OBJECT']
        print(file)
        GRISM = hdr['GRISM']

        try:
            COMMENT = hdr['COMMENT']
        except:
            COMMENT = ''

        if OBJECT.lower() not in (
                keywords['BIAS'] + keywords['FLAT'] + keywords['LAMP']):
            obj_list.append(file)
            if GRISM.lower() in keywords['GR7']:
                obj_list_gr7.append(file)
            elif GRISM.lower() in keywords['GR8']:
                obj_list_gr8.append(file)

            elif COMMENT != '':
                GRISM = COMMENT[0][3:6]
                print("GRISM from comment term : ",GRISM)
                if GRISM.lower() in keywords['GR7']:
                    obj_list_gr7.append(file)
                elif GRISM.lower() in keywords['GR8']:
                    obj_list_gr8.append(file)

            else:
                print(file)
                print("There is error in header term : GRISM")
        else:
            passing_list.append(file)

    # passing_list = list(set(file_list).difference(obj_list_gr7).difference(obj_list_gr8))
    return obj_list, obj_list_gr7, obj_list_gr8, passing_list

# -------------------------------------------------------------------------------------------------------------------- #
