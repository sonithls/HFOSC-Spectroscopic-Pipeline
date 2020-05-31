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
        file_name: file name of the file to remove from directory.
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
        location     : location of the files if it is not in the working directory.
        prefix_string: prefix which add after doing bias correction to files.
    Returns:
        none
        save bias_list in the location provided.
    """

    if location != '':                                                #change location
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
# -------------------------------------------------------------------------------------------------------------------- #

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


def cosmic_correction (cosmic_curr_list, location='', prefix_string='c'):
    """
    Corrects for cosmic rays in the OBJECT image.
    Arguments:
        cosmic_curr_list: List of files which need to do cosmicray correction.
        location        : Location of the files if it is not in the working directory.
        prefix_string   : Prefix to distinguish FITS file from the original FITS file
    Return:
        cr_check_list   : List of files to check how good is the cosmic ray correction.
    """
#     if location != '':
#         pathloc = os.path.join(os.getcwd(), location, 'cosmic_curr_list')
#     else :
#         pathloc = os.path.join(os.getcwd(), 'cosmic_curr_list')

#     cosmic_curr_list.sort()
#     if len(cosmic_curr_list) != 0:
#         with open(pathloc, 'w') as f:
#             for file in cosmic_curr_list:
#                 if location != '':                  #importent change, check with other functions
#                     f.write(location+"/"+file+'\n')
#                 else :
#                     f.write(file+'\n')


    task = iraf.noao.imred.crutil.cosmicrays
    task.unlearn()

    cr_currected_list = []
    for file_name in cosmic_curr_list:

        output_file_name = str(prefix_string) + str(file_name)
        output_file_name = os.path.join(location, output_file_name)
        file_name = os.path.join(location, file_name)
        remove_file(output_file_name)

        task(input=file_name, output=output_file_name, interac='no', train='no')
        cr_currected_list.append(output_file_name)

    task = iraf.images.imutil.imarith
    task.unlearn()

    cr_check_list = []
    for file_name in cosmic_curr_list:

        output_file_name = str(prefix_string) + str(file_name)
        cr_check_file_name = str('chk_') + output_file_name
        output_file_name2 = os.path.join(location, output_file_name)
        file_name = os.path.join(location, file_name)
        cr_check_file_name2 = os.path.join(location, cr_check_file_name)
        cr_check_list.append(cr_check_file_name2)

        task(operand1=str(file_name), op='-', operand2=str(output_file_name2), result=str(cr_check_file_name2))
        remove_file(str(file_name))   #removing the older files which is needed to bias correct.
    return cr_check_list


list_files = search_files(location=list_subdir()[0], keyword='*.fits')
# print list_files
obj_list, obj_list_gr7, obj_list_gr8, passing_list = list_object(list_files,PATH)
flat_list, flat_list_gr7, flat_list_gr8, passing_list = list_flat(list_files,PATH)
comic_curr_list = list(set(obj_list).union(flat_list)) #file which needed to correct for cosmic ray
print len(cosmic_curr_list)
write_list (file_list=cosmic_curr_list, file_name='cosmic_curr_list', location=PATH)
cr_check_list = cosmic_correction (cosmic_curr_list, location=PATH)

# Stop running code for checking the cosmic ray correction
print ("Cosmic ray correction is done. Please check chk files then continue")
raw_input("Press Enter to continue...") #Python 2
for file in cr_check_list:
    remove_file(str(file))


def flat_correction (flat_list, file_list, location='', grism) :
    """
    This fuction do flat correction to object files.
    Arguments:
        flat_list: List of flat files in a perticular grism.
        file_list: List of files which need to do flat correction.
        location : location of the files if it is not in the working directory.
    Returns:
        none
    """
    if location != '':
        pathloc = os.path.join(os.getcwd(), location, 'flat_corr_list'+str(grism))
        master_flat = os.path.join(location, 'master-flat'+str(grism))
        response_file = os.path.join(location, 'nflat'+str(grism))
    else :
        pathloc = os.path.join(os.getcwd(), 'flat_corr_list'+str(grism))
        master_flat = os.path.join(os.getcwd(), 'master-flat'+str(grism))
        response_file = os.path.join(os.getcwd(), 'nflat'+str(grism))

    flat_list.sort()
    if len(flat_list) != 0:
        with open(pathloc, 'w') as f:
            for file in flat_list:
                if location != '':
                    f.write(location+"/"+file+ '\n')
                else:
                    f.write(file+ '\n')

    remove_file(str(master_flat))


    #Make master flat file
    task = iraf.noao.ccdred.flatcombine
    task.unlearn()
    task(input='@' + pathloc, output=str(master_flat), combine = 'average', reject = 'avsigclip',
         ccdtype = 'flat', process = 'no', delete = 'no', rdnoise = float(read_noise), gain = float(ccd_gain))

    #Edit dispersion axis of flat files into 2
    task = iraf.noao.hedit
    task.unlearn()
    task(images=pathloc, fields='dispaxis', value=2, verify = 'no', add = 'yes', show = 'no', update = 'yes' )

    #create response file from master flat
    task = iraf.noao.imred.specred.response
    task.unlearn()
    task(calibrat=str(master_flat), normaliz=str(master_flat), response=str(response_file),
          functio='spline3', order='50')

    #Remove CCDSEC from header to avoid IRAF error
    task = iraf.noao.hedit
    task.unlearn()

    for file in file_list :
        task(images='', fields='CCDSEC', verify = 'no', delete = 'yes', show = 'no', update = 'yes' )

    #Flat fielding of object and standard stars.
    task = iraf.noao.imred.ccdred.ccdproc
    task.unlearn()

    for file in file_list :
        task(images='', output='', ccdtype='', fixpix='no', oversca='no', trim='no', zerocor='no',
              darkcor='no', flatcor='yes')


    #Creating backup files
    pathloc = os.path.join(PATH,'Backup')      #pathlocation changes here caution!!!
    print ("copying master-flat"+str(grism)+"to "+PATH+"/Backup")
    shutil.move (PATH+'/'+'master-flat'+str(grism)+'.fits', pathloc)   #backup the master_flat


def spectral_extraction (file_list, location=''):
    """
    This fuction do spectral extraction and calibration of wavelength.
    Arguments:
        file_list: List of files which need to do spectral extraction
        location : location of the files if it is not in the working directory.
    """
    if location != '':
        pathloc = os.path.join(os.getcwd(), location, 'flat_corr_list')
