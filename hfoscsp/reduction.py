# Author : Sonith L.S
# Contact : sonith.ls@iiap.res.in
__version__ = '0.0.9'
# -------------------------------------------------------------------------------------------------------------------- #
# Import required libraries
# -------------------------------------------------------------------------------------------------------------------- #
import os
# import glob
import shutil
# import re
# import shutil
from astropy.io import fits

from hfoscsp.interactive import options
from hfoscsp.airmass import airmass

try:
    from pyraf import iraf
except ImportError as error:
    print(error + "Please install pyraf and iraf")


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
# HFOSC #
# read_noise = 4.87
# ccd_gain   = 1.22
# data_max   = 55000

# HFOSC2 #
# read_noise = 5.75
# ccd_gain = 0.28
# max_count = 700000
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


def ccdsec_removal(file_list, location=''):
    """
    Remove CCDSEC from header to avoid IRAF error in ccdproc etc tasks.
    Argument:
        file_list: List of files need to remove CCDSEC
    Returns :
        none
    """

    task = iraf.hedit
    task.unlearn()

    for file_name in file_list:
        file_name = os.path.join(location, file_name)
        task(images=file_name, fields='CCDSEC', verify='no', delete='yes', show='no', update='yes')


def bias_correction(bias_list, list_file, CCD, location='', prefix_string='b_'):
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
    if CCD.ccd == "HFOSC":
        index = 0
    elif CCD.ccd == "HFOSC2":
        index = 1

    if location != '':               # change location
        pathloc = os.path.join(os.getcwd(), location, 'bias_list')
        master_bias = os.path.join(location, 'master-bias')
    else:
        pathloc = os.path.join(os.getcwd(), 'bias_list')
        master_bias = os.path.join(os.getcwd(), 'master-bias')

    bias_list.sort()
    if len(bias_list) != 0:
        with open(pathloc, 'w') as f:
            for file in bias_list:
                f.write(location+"/"+file+str([index])+'\n')

    remove_file(str(master_bias))

    task = iraf.noao.imred.ccdred.zerocombine
    task.unlearn()
    task(input='@' + pathloc, output=str(master_bias), combine='median', reject='avsigclip',
         ccdtype='', process='no', delete='no', rdnoise=float(CCD.read_noise), gain=float(CCD.ccd_gain))

    task = iraf.images.imutil.imarith
    task.unlearn()

    for file_name in list_file:
        output_file_name = str(prefix_string) + str(file_name)
        output_file_name = os.path.join(location, output_file_name)
        file_name = os.path.join(location, file_name)
        file_name_1 = file_name+str([index])
        remove_file(str(output_file_name))
        task(operand1=str(file_name_1), op='-', operand2=str(master_bias), result=str(output_file_name))
        remove_file(str(file_name))   # removing the older files which is needed to bias correct.

    for file_name in bias_list:
        remove_file(str(os.path.join(location, file_name)))  # removing the older bias files

    pathloc = os.path.join(location, 'Backup')
    os.makedirs(pathloc)
    print("copying master-bias to "+location+"/Backup")
    shutil.move(location+'/'+'master-bias.fits', pathloc)   # backup the master_bias


def cosmic_correction(cosmic_curr_list, location='', prefix_string='c'):
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
        remove_file(str(file_name))   # removing the older files which is needed to bias correct.
    return cr_check_list


def flat_correction(flat_list, file_list, grism, CCD, location='', prefix_string='f'):
    """
    This fuction do flat correction to object files.
    Arguments:
        flat_list     : List of flat files in a perticular grism.
        file_list     : List of files which need to do flat correction.
        location      : Location of the files if it is not in the working directory.
        grism         : Type of grism used.
        prefix_string : Prefix added after flat fielding.
    Returns:
        flat_curr_list: List of flat currected files.
        none
    """
    if location != '':
        pathloc = os.path.join(os.getcwd(), location, 'flat_corr_list'+str(grism))
        master_flat = os.path.join(location, 'master-flat'+str(grism))
        response_file = os.path.join(location, 'nflat'+str(grism))
    else:
        pathloc = os.path.join(os.getcwd(), 'flat_corr_list'+str(grism))
        master_flat = os.path.join(os.getcwd(), 'master-flat'+str(grism))
        response_file = os.path.join(os.getcwd(), 'nflat'+str(grism))

    flat_list.sort()
    if len(flat_list) != 0:
        with open(pathloc, 'w') as f:
            for file in flat_list:
                if location != '':
                    f.write(location+"/"+file+'\n')
                else:
                    f.write(file+'\n')

    remove_file(str(master_flat))

    # Make master flat file
    task = iraf.noao.ccdred.flatcombine
    task.unlearn()
    task(input='@' + pathloc, output=str(master_flat), combine='average', reject='avsigclip',
         ccdtype='', process='no', delete='no', rdnoise=float(CCD.read_noise), gain=float(CCD.ccd_gain))

    for file in flat_list:
        file_name = os.path.join(location, file)
        remove_file(str(file_name))

    # Edit dispersion axis of flat files into 2
    task = iraf.hedit
    task.unlearn()
    task(images=str(master_flat), fields='dispaxis', value=2, verify='no', add='yes', show='no', update='yes')

    # create response file from master flat
    task = iraf.noao.imred.specred.response
    task.unlearn()
    task(calibrat=str(master_flat), normaliz=str(master_flat), response=str(response_file), functio='spline3',
         order='50')

    # # Flat fielding of object and standard stars.
    # task = iraf.noao.imred.ccdred.ccdproc
    # task.unlearn()

    # Flat fielding of object and standard stars.
    task1 = iraf.images.imutil.imarith
    task1.unlearn()

    flat_curr_list = []

    for file_name in file_list:
        output_file_name = str(prefix_string) + str(os.path.splitext(file_name)[0]) + '_'+str(grism)
        output_file_name2 = os.path.join(location, output_file_name)
        file_name = os.path.join(location, file_name)
        flat_curr_list.append(output_file_name2)

        # task(images=file_name, output=output_file_name2, ccdtype='', fixpix='no', oversca='no', trim='no',
        #      zerocor='no', darkcor='no', flatcor='yes', flat=response_file)

        task1(operand1=file_name, op='/', operand2=response_file, result=output_file_name2)

        remove_file(str(file_name))

    # Creating backup files
    backuploc = os.path.join(location, 'Backup')      # pathlocation changes here caution!!!
    print("copying master-flat"+str(grism)+"to "+location+"/Backup")
    shutil.move(location+'/'+'master-flat'+str(grism)+'.fits', backuploc)   # backup the master_flat
    print("copying nflat"+str(grism)+"to "+location+"/Backup")
    shutil.move(location+'/'+'nflat'+str(grism)+'.fits', backuploc)

    return flat_curr_list


def spectral_extraction(obj_list, lamp_list, grism, CCD, location=''):
    """
    This fuction do spectral extraction and calibration of wavelength. After
    running this function a header term "Waveleng" added after succesfully
    finishing this task.

    Parameters
    ----------
    file_list: list
        List of files which need to do spectral extraction
    location: str
        Location of the files if it is not in the working directory.
    """
    if not os.path.isdir(os.path.join(location, 'lamp')):
        if CCD.ccd == "HFOSC":
            gr7_lamp = 'hfosc1_gr7_lamp.fits'
            gr8_lamp = ''
            gr7_lamp_id = 'idhfosc1_gr7_lamp'
            gr8_lamp_id = ''

        elif CCD.ccd == "HFOSC2":
            gr7_lamp = 'feargr7_feige34.fits'
            gr8_lamp = 'fenegr8_feige34.fits'
            gr7_lamp_id = 'idfeargr7_feige34'
            gr8_lamp_id = 'idfenegr8_feige34'

        Databasefilepath = os.path.join(os.getcwd(), 'Database')
        Databasepath = os.path.join(os.getcwd(), 'Database/database')

    else:
        # Only works if lamp folder exists in the main directory and lamp files
        # are named gr7.fits and gr8.fits and lamp id named as idgr7 and idgr8.
        gr7_lamp = 'gr7.fits'
        gr8_lamp = 'gr8.fits'
        gr7_lamp_id = 'idgr7'
        gr8_lamp_id = 'idgr8'

        Databasefilepath = os.path.join(os.getcwd(), 'lamp')
        Databasepath = os.path.join(os.getcwd(), 'lamp')

    # copy reference lamp files
    if not os.path.isdir(os.path.join(location, 'database')):
        os.makedirs(os.path.join(location, 'database'))

    try:
        shutil.copy(os.path.join(Databasefilepath, gr7_lamp),
                    os.path.join(location, gr7_lamp))
        shutil.copy(os.path.join(Databasepath, gr7_lamp_id),
                    os.path.join(location, 'database', gr7_lamp_id))
    except IOError as e:
        print(e)
        print("ERROR: gr7 lamp files are not copied")

    try:
        shutil.copy(os.path.join(Databasefilepath, gr8_lamp),
                    os.path.join(location, gr8_lamp))
        shutil.copy(os.path.join(Databasepath, gr8_lamp_id),
                    os.path.join(location, 'database', gr8_lamp_id))
    except IOError as e:
        print(e)
        print("ERROR: gr8 lamp files are not copied")

    if location != '':
        lamp = os.path.join(os.getcwd(), location, lamp_list[0])
        iraf.cd(os.path.join(os.getcwd(), location))

    for file_name in obj_list:
        # obj_name = os.path.join(os.getcwd(), location, file_name)

        print('''
        Following keys are for aperture selection.
        d - delete trace
        m - set trace
        l - set the lower limit for the aperture
        u - set the upper limit for the aperture
        b - enter background editing
        z - delete background intervals
        s s - mark new fit regions for the backgorund.
              (Press s to select initial point at cursor
               position, press s again for complete the selection)
        f - fit
        q - quit
        ''')

        # Running apall (aperture extract)
        iraf.apall(input=file_name, format='multispec', extras='yes', lower=-15, upper=15, nfind=1,
                   background='fit', weights='none', saturation=int(CCD.max_count), readnoi=CCD.read_noise,
                   gain=CCD.ccd_gain, t_niterate=1, interactive='yes')
        # weights= 'variance' seems to be unstable for our high effective gain
        # t_function=, t_order=,llimit=, ulimit=,ylevel=,b_sample=, background ='fit'
        # saturation=maximum count ?

        # Extracting the lamp (FeAr OR FeNe) for this spectra as obj_name_lamp.fits
        iraf.apall(input=lamp, reference=file_name, out=os.path.splitext(file_name)[0]+'_lamp', recenter='no',
                   trace='no', background='none', interactive='no')

        # Now reidentify the lines lamp files during the observation.
        if grism == 'gr7':
            Lamp = gr7_lamp  # Don't give complete path here. It mess with IRAF.
        elif grism == 'gr8':
            Lamp = gr8_lamp
        else:
            print("ERROR: grism is not specified")

        iraf.reidentify(reference=Lamp, images=os.path.splitext(file_name)[0]+'_lamp',
                        verbose='yes', interactive='yes')
        # interactive='no'

        # Edit the header of obj_name to add ref lamp
        iraf.hedit(os.path.splitext(file_name)[0]+'.ms.fits', "REFSPEC1", os.path.splitext(file_name)[0]+'_lamp.fits',
                   add=1, ver=0)

        file_name_chk = os.path.join(location, file_name)
        hdul = fits.open(file_name_chk)  # HDU_List
        hdr = hdul[0].header             # Primary HDU header
        OBJECT = hdr['OBJECT']
        file_name_out = str(OBJECT)+'_w'+os.path.splitext(file_name)[0]+'.ms.fits'
        # Doing dispersion correction using dispcor (w - wavelength calibration)
        iraf.dispcor(input=os.path.splitext(file_name)[0]+'.ms.fits',
                     output=file_name_out)

        # Add a header indicating that wavelength calibration is done.
        iraf.hedit(file_name_out, "Waveleng", "done", add=1, ver=0)


def flux_calibrate(obj_list, location, default_path, CCD, prefix_string='F_'):
    """
    This function is for flux calibration of the object spectra if standard
    star is also observed in the same night.

    Parameters
    ----------
        obj_list : list
            List of wavelength calibrated object spectra in a perticular grism.
        location : str
            Location of the files if it is not in the working directory.
        default_path :
            Parent directory of the code
        grism : str
            Type of grism used.
        CCD : obj
            CCD object
        prefix_string : str
            Prefix added after flux calibration.
    Returns
    -------
        none
    """
    # This become obsolete
    # if CCD.ccd == "HFOSC":
    #     command_file_path = os.path.join(default_path, 'Database/database', 'setst_HFOSC')
    # elif CCD.ccd == "HFOSC2":
    #     command_file_path = os.path.join(default_path, 'Database/database', 'setst_HFOSC2')

    iaoextinct_path = os.path.join(default_path, 'Database/database', 'iaoextinct.dat')
    if location != '':
        iraf.cd(os.path.join(os.getcwd(), location))

    # Check files are wavelength calibrated and separate object files and standard
    # star files
    obj_stars = []
    std_stars = []
    for file_name in obj_list:
        file_name_chk = os.path.join(location, file_name)
        hdul = fits.open(file_name_chk)  # HDU_List
        hdr = hdul[0].header             # Primary HDU header
        OBJECT = hdr['OBJECT']
        aperture = hdr['APERTUR']
        try:
            Wavelength_cal = hdr['WAVELENG']  # checking weather Wavelength is done
            if Wavelength_cal == 'done':
                if aperture == '2 1340 l':
                    std_stars.append(file_name)
                elif aperture == '8 167 l':
                    obj_stars.append(file_name)
                else:
                    print("Header error for "+str(file_name)+" Please check header term aperture")
            else:
                print("File "+str(file_name)+" is not wavelenght calibrated.")
        except:
            pass
    print("stars :", obj_stars)
    print("standards:", std_stars)

    # Setting Indian Astronomical Observatory, Hanle
    iraf.observatory(command='list', obsid='set', observatory='iao')

    star_list = list(set(obj_stars).union(std_stars))
    # This become obsolete
    # for file_name in star_list:
    #
    #     # Calculating ST and adding in the header
    #     print(file_name, command_file_path)
    #     iraf.astutil.asthedit(images=file_name, commands=command_file_path,
    #                           update='yes')
    #
    #     # Setting Airmass to all files before flux calibration. (ST should be there in the header)
    #     iraf.noao.imred.specred.setairmass(images=file_name, observa='iao')
    #
    # print("Airmass correction is done for all stars")
    for filename in star_list:
        airmass(filename=filename)
    print("Airmass correction is done for all stars")
    # print("Press enter to continue")
    # raw_input()
    message = "Press enter 'Yes' to continue"
    choices = ['Yes']
    options(message, choices)

    # Running standard task in IRAF
    file_name = std_stars[0]

    standard_star_name = raw_input("Type standard star name to continue :")

    # standard_star_name = 'feige34'        # Need to set an option to change this for different std stars
    # mag = 11.18 # Magnitude of standard star.

    standard_data_file = os.path.splitext(file_name)[0]
    iraf.imred.specred.standard(input=file_name, output=standard_data_file, extinct=iaoextinct_path,
                                caldir='onedstds$iidscal/', observa='iao', star_nam=standard_star_name)
    # , mag = float(mag), magband = 'V'
    # fnuzero= ? (Absolute flux zero point), teff= ?
    # mag = float(mag)Magnitude Of The Standard Star
    # magband = 'V' Magnitude Band

    # Running Sensfunc task in IRAF
    iraf.imred.specred.sensfunc(standard=standard_data_file, sensitiv=str(standard_data_file)+'sens',
                                extinct=iaoextinct_path, observa='iao')
    # extinct='onedstds$ctioextinct.dat'

    # Running calibrate task in IRAF
    for file_name in obj_stars:
        iraf.imred.specred.calibrate(input=file_name, output=str(prefix_string)+str(file_name), extinct='yes',
                                     flux='yes', extinction=iaoextinct_path, observa='iao',
                                     sensiti=str(standard_data_file)+'sens')
    # extinct='onedstds$ctioextinct.dat'
