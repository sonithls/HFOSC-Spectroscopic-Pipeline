# -------------------------------------------------------------------------------------------------------------------- #
#This script is to semi-automate basic reduction of HFOSC spectrosopic data
#Author : Sonith L.S
#Contact : sonith.ls@iiap.res.in

#Version 0.0.10
#Code is  written serially to check every functions are working properly
#Adiitional formatting required for running in for multiple number of folder in faster way.
# -------------------------------------------------------------------------------------------------------------------- #

# -------------------------------------------------------------------------------------------------------------------- #
# Import required libraries
# -------------------------------------------------------------------------------------------------------------------- #
import os
import glob
import shutil
import re
from astropy.io import fits

try:
    from pyraf import iraf
except ImportError as error:
    print (error + "Please install pyraf and iraf")

BACKUP= "HFOSC_PIPELINE_DataBackup"

def Backup(BACKUPDIR):
    """
    Copies all the files in present directory to the  Backup
    Argument:
        BACKUPDIR : Name of the backup directory
    Returns :
        none
    """
    os.makedirs('../'+BACKUPDIR)
    print("Copying files to ../"+BACKUPDIR)
    os.system('cp -r * ../'+BACKUPDIR)

Backup (BACKUP)



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



def list_subdir ():
    """
    This function list all sub directories.
    Arguments:
        none
    Returns:
        sub_directories: name of sub-directories
    """

    directory_contents = os.listdir(os.getcwd())
    sub_directories = []
    for item in directory_contents:
        if os.path.isdir(item):
            sub_directories.append(item)
    return sub_directories


PATH = os.path.join(os.getcwd(),list_subdir()[0])
#print PATH
list_files = search_files(location=list_subdir()[0], keyword='*.fits')
#print list_files

import shutil

def spec_or_phot (file_list, location, func=''):
    """
    Check whether the file contains spectrosopy of photometry data and make sperate list
    for both spectrosopy and photometry with respective file names.
    Arguments:
        file_list: List of all files in the directory from which files need to identify
        location : location of the files if it is not in the working directory
        func     : type of files need keep in orginal folder as it is. Remaining files
                   will be moved to other directory.
    Returns:
        spec_list: List of spectrosopic files
        phot_list: List of photometric files
    """

    spec_list = []
    phot_list = []
    spec_list_fullname = []
    phot_list_fullname = []
    for file in file_list :
        file_name = os.path.join(location,file)
        hdul = fits.open(file_name) #HDU_List
        hdul[1].header
        hdr = hdul[1].header
        AXIS1 = hdr['NAXIS1']
        AXIS2 = hdr['NAXIS2']
        value = AXIS2/AXIS1
        if value > 2 :
            spec_list.append(file)
            spec_list_fullname.append(file_name)
        elif value <= 2 :
            phot_list.append(file)
            phot_list_fullname.append(file_name)

    if func == 'spec':
        try:
            pathloc = os.path.join(location,'phot')
            os.mkdir(pathloc)
            for file in phot_list_fullname:
                shutil.move (file,pathloc)

        except OSError as error:
            print(error)

    elif func == 'phot':
        try:
            pathloc = os.path.join(location,'spec')
            os.mkdir(pathloc)
            for file in spec_list_fullname:
                shutil.move (file,pathloc)

        except OSError as error:
            print(error)

    return spec_list, phot_list


speclist, photlist = spec_or_phot (list_files, PATH, 'spec')
#file_list is updated from passing list
#print (speclist)


def list_bias (file_list, location=''):
    """
    Identify bias files from file_list provided by looking the header keyword in the files
    Arguments:
        file_list   : List of all files in the directory from which files need to identify
        location    : location of the files if it is not in the working directory
    Returns:
        bias_list   : List of bias files from the file_list provided
        passing_list: Remaining files after removing bias files from the file_list
    """

    bias_list = []
    for file in file_list :
        file_name = os.path.join(location,file)
        hdul = fits.open(file_name) #HDU_List
        hdr = hdul[0].header        #Primary HDU header
        OBJECT = hdr['OBJECT']
        if OBJECT == "Bias_Snspec" :
            bias_list.append(file)
        elif OBJECT == "Bias_Sn" :
            bias_list.append(file)
        elif OBJECT == "bias" :
            bias_list.append(file)

    passing_list = list(set(file_list).difference(bias_list))
    passing_list.sort()
    return bias_list, passing_list


bias_list, passing_list = list_bias (speclist, PATH)
# print (bias_list)
# print (passing_list)

from pyraf import iraf
# -------------------------------------------------------------------------------------------------------------------- #
# Load IRAF Packages
# -------------------------------------------------------------------------------------------------------------------- #
iraf.noao(_doprint=0)
iraf.imred(_doprint=0)
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
read_noise = 4.87
ccd_gain = 1.22
data_max = 55000
# -------------------------------------------------------------------------------------------------------------------- #


def remove_file(file_name):
    """
    Removing a file from the directory
    Argument:
        file_name: file name of the file to remove from directory
    Returns :
        none
    """
    try:
        os.remove(file_name)
    except OSError:
        pass


def bias_correction (bias_list, list_file, location='', prefix_string='b_'):
    """
    From the imput bias_list make master-bias, do bias correction to rest of files in the
    directory, remove all past files and backup master-bias file
    Arguments:
        bias_list    : List of bias files to make master bias.
        list_file    : List of files which need to do bias correction.
        location     : location of the files if it is not in the working directory
        prefix_string: prefix which add after doing bias correction to files.
    Returns:
        none
    """

    if location != '':                                                #change -- location
        pathloc = os.path.join(os.getcwd(), location, 'bias_list')
        master_bias = os.path.join(location, 'master-bias')
    else :
        pathloc = os.path.join(os.getcwd(), 'bias_list')
        master_bias = os.path.join(os.getcwd(), 'master-bias')

    bias_list.sort()
    if len(bias_list) != 0:
        with open(pathloc, 'w') as f:
            for file in bias_list:
                f.write(location+"/"+file+"[1]"+ '\n')


    remove_file(str(master_bias))

    task = iraf.noao.imred.ccdred.zerocombine
    task.unlearn()
    task(input='@' + pathloc, output=str(master_bias), combine = 'median', reject = 'avsigclip',
         ccdtype = '', process = 'no', delete = 'no', rdnoise = float(read_noise),gain = float(ccd_gain))

    task = iraf.images.imutil.imarith
    task.unlearn()

    for file_name in list_file:
        output_file_name = str(prefix_string) + str(file_name)
        output_file_name = os.path.join(location, output_file_name)
        file_name = os.path.join(location, file_name)
        file_name_1 = file_name+"[1]"
        remove_file(str(output_file_name))
        task(operand1=str(file_name_1), op='-', operand2=str(master_bias), result=str(output_file_name))
        remove_file(str(file_name))   #removing the older files which is needed to bias correct.

    for file_name in bias_list:
        remove_file(str(os.path.join(location, file_name))) #removing the older bias files

    pathloc = os.path.join(PATH,'Backup')
    os.makedirs(pathloc)
    print ("copying master-bias to "+PATH+"/Backup")
    shutil.move (PATH+'/'+'master-bias.fits', pathloc)   #backup the master_bias

bias_correction (bias_list, passing_list, PATH)
