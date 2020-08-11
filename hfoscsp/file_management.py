import os
import glob
import shutil
import re
import shutil
from astropy.io import fits

# -------------------------------------------------------------------------------------------------------------------- #

default_path= os.getcwd()
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

    print (pathloc)
    return file_list


def list_subdir ():
    """
    This function list all sub directories which starts with a digit.
    Arguments:
        none
    Returns:
        sub_directories: name of sub-directories
    """

    directory_contents = os.listdir(os.getcwd())
    sub_directories = []
    for item in directory_contents:
        if os.path.isdir(item) and item[0].isdigit(): #list directories which have first charater a digit
            sub_directories.append(item)
            sub_directories.sort()
    return sub_directories


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


def list_bias (file_list, location=''):
    """
    Identify bias files from file_list provided by looking the header keyword in the
    files.
    Arguments:
        file_list   : List of all files in the directory from which files need to
                      identify.
        location    : location of the files if it is not in the working directory.
    Returns:
        bias_list   : List of bias files from the file_list provided.
        passing_list: Remaining files after removing bias files from the file_list.
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
        elif OBJECT == "Bias_snspec" :
            bias_list.append(file)
        elif OBJECT == "bias_snspec" :
            bias_list.append(file)
        elif OBJECT == "bias" :
            bias_list.append(file)

    passing_list = list(set(file_list).difference(bias_list))
    passing_list.sort()
    return bias_list, passing_list


def remove_file(file_name):
    """
    Removing a file from the directory
    Argument:
        file_name: file name of the file to remove from directory.
    Returns :
        none
    """
    try:
        os.remove(file_name)
    except OSError:
        pass


def write_list (file_list, file_name, location=''):
    """
    This function write file names with complete path in a text file in the destination
    provided, using the input file_list.
    Arguments:
        file_list: List of files need to write into a text file.
        file_name: Name of the text file.
        location : location of the files if it is not in the working directory
    Returns:
        none
        file list with file_file in the given location with file names in it.
    """
    if location != '':
        pathloc = os.path.join(os.getcwd(), location, file_name)

    if len(file_list) != 0:
        with open(pathloc, 'w') as f:
            for file in file_list :
                file = os.path.join(os.getcwd(), location, file)
                f.write(file+ '\n')


def list_flat (file_list, location=''):
    """
    From the file_list provided, sperate files into flat files and further speperate them
    into grism7 and grism8 files.
    Arguments:
        file_list: List of files need to speperate.
        location : location of the files if it is not in the working directory.
    Returns:
        flat_list    : List of all flat files.
        flat_list_gr7: List of gr7 flat files.
        flat_list_gr8: List of gr8 flat files.
        passing_list : List of rest of the files in filelist.
    """
    flat_list = []
    flat_list_gr7= []
    flat_list_gr8= []
    passing_list= []

    for file in file_list :
        file_name = os.path.join(location,file)
        hdul = fits.open(file_name) #HDU_List
        hdr = hdul[0].header        #Primary HDU header
        OBJECT = hdr['OBJECT']
        GRISM = hdr['GRISM']

        if (OBJECT == "Halogen") or (OBJECT == "halogen") or (OBJECT == "flat") :
            flat_list.append(file)
            if GRISM == "4 Grism 7" :
                flat_list_gr7.append(file)
            elif GRISM == "3 Grism 8" :
                flat_list_gr8.append(file)
            else :
                print (file)
                print ("There is error in header term : GRISM")

        else :
            passing_list.append(file)

    return flat_list, flat_list_gr7, flat_list_gr8, passing_list


def list_lamp (file_list, location=''):
    """
    From the file_list provided, sperate files into lamp files and further speperate them
    into grism7 and grism8 files.
    Arguments:
        file_list: List of files need to speperate.
        location : location of the files if it is not in the working directory.
    Returns:
        lamp_list_gr7: List of gr7 lamp files.
        lamp_list_gr8: List of gr8 lamp files.
        passing_list : List of rest of the files in filelist.
    """
    lamp_list_gr7= []
    lamp_list_gr8= []

    for file in file_list :
        file_name = os.path.join(location,file)
        hdul = fits.open(file_name) #HDU_List
        hdr = hdul[0].header        #Primary HDU header
        OBJECT = hdr['OBJECT']
        GRISM = hdr['GRISM']

        if (OBJECT == "FeAr"):
            lamp_list_gr7.append(file)
        elif (OBJECT == "FeNe"):
            lamp_list_gr8.append(file)

    passing_list = list(set(file_list).difference(lamp_list_gr7).difference(lamp_list_gr8))
    return lamp_list_gr7, lamp_list_gr8, passing_list


def list_object (file_list, location=''):
    """
    From the file_list provided, sperate files into object files and further speperate them
    into grism7 and grism8 files.
    Arguments:
        file_list: List of files need to speperate.
        location : location of the files if it is not in the working directory.
    Returns:
        obj_list    : List of all objects.
        obj_list_gr7: List of gr7 object files.
        obj_list_gr8: List of gr8 object files.
        passing_list : List of rest of the files in filelist.
    """
    obj_list = []
    obj_list_gr7= []
    obj_list_gr8= []
    passing_list= []
    for file in file_list :
        file_name = os.path.join(location,file)
        hdul = fits.open(file_name) #HDU_List
        hdr = hdul[0].header        #Primary HDU header
        OBJECT = hdr['OBJECT']
        GRISM = hdr['GRISM']

        if ((OBJECT != "FeAr") and (OBJECT != "FeNe") and (OBJECT != "Halogen") and (OBJECT != "Bias_Snspec")):
            obj_list.append(file)
            if (GRISM == "4 Grism 7") or (GRISM == "Grism 7") or (GRISM == "gr7") or (GRISM == "grism 7") :
                obj_list_gr7.append(file)
            elif (GRISM == "3 Grism 8") or (GRISM == "Grism 8") or (GRISM == "gr8") or (GRISM == "grism 8") :
                obj_list_gr8.append(file)
            else :
                print (file)
                print ("There is error in header term : GRISM")
        else :
            passing_list.append(file)

    #passing_list = list(set(file_list).difference(obj_list_gr7).difference(obj_list_gr8))
    return obj_list, obj_list_gr7, obj_list_gr8, passing_list