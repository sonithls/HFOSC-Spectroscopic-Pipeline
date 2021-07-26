"""
This script is written for HFOSC spectroscopic-Pipeline.

It is containing cosmic ray correction utilities for running the
HFOSC spectroscopic-Pipeline.
"""
__author__ = 'Sonith L.S'
__contact__ = 'sonith.ls@iiap.res.in'
__version__ = '1.0.0'

# Warning : Please check any variable depends on CCD

import os
import time
import subprocess
import threading
import ccdproc
from astropy.io import fits

from hfoscsp.interactive import options

try:
    from pyraf import iraf
except ImportError as error:
    print(error + "Please install pyraf and iraf")

bar = """
###############################################################################
"""


def remove_file(file_name):
    """
    Remove a file from the directory.

    Parameters
    ----------
        file_name: str
            File name of the file to remove from directory.
    Returns
    -------
        none
    """
    try:
        os.remove(file_name)
    except OSError:
        pass


def irafcosmicrays(input, output, threshold, fluxrate, npasses, window):
    """
    IRAF cosmicray correction module.

    Parameters
    ----------
        input   : str
            File name of file to correct cosmic rays.
        output  : str
            File name of cosmic ray corrected file.
        threshol: float
            Threshold value.
        fluxrate: float
            Flux rate.
        npasses : float
            Number of passes.
        window  :
    Returns
    -------
        none
    """
    iraf.noao.imred.crutil.cosmicrays.unlearn()
    iraf.noao.imred.crutil.cosmicrays(input=input, output=output, thresho=threshold, fluxrat=fluxrate,
                                      npasses=npasses, window=window, interac='no', train='no')


def irafcrmedian(input, output, lsigma, hsigma, ncmed, nlmed, ncsig, nlsig):
    """
    IRAF cosmic-ray correction module.

    Parameters
    ----------
        input   : str
            File name of file to correct cosmic rays.
        output  : str
            File name of cosmic ray corrected file.
        lsigma  : float
            Low Clipping Sigma Factor
        ncsig   : float
            Column Box Size For Sigma Calculation
    Returns
    -------
        none
    """
    iraf.noao.imred.crutil.crmedian.unlearn()
    iraf.noao.imred.crutil.crmedian(input=input, output=output, crmask='', median='', sigma='', residua='',
                                    lsigma=lsigma, hsigma=hsigma, ncmed=ncmed, ncsig=ncsig, nlsig=nlsig)


def la_cosmic(input, output, sigclip, sigfrac, objlim, read_noise, data_max):
    """
    La cosmic cosmic-ray correction module from Astropy.

    Parameters
    ----------
        input   : file name of file to correct cosmic rays.
        output  : file name of cosmic ray corrected file.
        sigclip :
    Returns
    -------
        none
    """
    hdul = fits.open(input)
    gain_corrected = hdul[0].data

    # print (hdul[1].data)
    # print (hdul[0].header)
    cr_cleaned = ccdproc.cosmicray_lacosmic(ccd=gain_corrected, sigclip=4.5, sigfrac=0.3, objlim=5.0, gain=1.0,
                                            readnoise=float(read_noise), satlevel=int(data_max), pssl=0.0, niter=4,
                                            sepmed=True, cleantype='meanmask', fsmode='median', psfmodel='gauss',
                                            psffwhm=2.5, psfsize=7, psfk=None, psfbeta=4.765, verbose=False)
    hdul[0].data = cr_cleaned
    # Write the new HDU structure to outfile
    hdul.writeto(output, overwrite=True)


def cosmic_correction_individual(cosmic_curr_list, CCD, location='', prefix_string='c'):
    """
    Corrects for cosmic rays in the individually for each OBJECT images and\
    allow to adjust the parameters manually.

    Parameters
    ----------
        cosmic_curr_list: list
            List of files which need to do cosmic-ray correction.
        location        : str
            Location of the files if it is not in the working directory.
        prefix_string   : str
            Prefix to distinguish FITS file from the original FITS file
    Returns
    -------
        cr_check_list   : list
            List of files to check how good is the cosmic ray correction.
    """
    print(cosmic_curr_list)
    cr_currected_list = []
    cr_check_list = []

    # opening ds9 for manually inspecting images
    subprocess.Popen('ds9')
    # process_ds9open.wait()
    ds9_time_delay = 2  # Depends upon how fast your system opens up ds9
    ds9_waiting = threading.Thread(time.sleep(ds9_time_delay))
    ds9_waiting.start()

    # Default method for cr currection curresponds to cosmicray task in IRAF
    # cr_currection_method = raw_input("Enter new cosmic-ray correction method (1/2/3) :")
    message = "Select the cosmic ray correction module"
    choices = ['irafcrmedian', 'irafcosmicrays', 'la_cosmic']
    cr_currection_method = options(message, choices)
    # cosmicray correction task default parameters
    threshold = 25
    fluxrate = 2
    npasses = 5
    window = 5

    # crmedian
    lsigma = 25       # Low Clipping Sigma Factor
    ncsig = 10        # Column Box Size For Sigma Calculation

    # la_cosmic parameters
    sigclip = 15.0
    sigfrac = 0.5
    objlim = 5.0
    data_max = CCD.max_count  # 700000  # Depend up on CCD
    read_noise = CCD.read_noise  # 5.75  # Depend up on CCD

    # Create guaranteed unique sentinel (can't use None since iterator might produce None)
    sentinel = object()
    iterobj = iter(cosmic_curr_list)    # Explicitly get iterator from iterable (for does this implicitly)
    x = next(iterobj, sentinel)         # Get next object or sentinel
    while x is not sentinel:            # Keep going until we exhaust iterator

        file_name = x

        output_file_name = str(prefix_string) + str(file_name)
        output_file_name2 = os.path.join(location, output_file_name)

        cr_check_file_name = str('chk_') + output_file_name
        cr_check_file_name2 = os.path.join(location, cr_check_file_name)

        file_name = os.path.join(location, file_name)

        print(output_file_name)
        print(cr_check_file_name)

        remove_file(output_file_name2)
        remove_file(cr_check_file_name2)

        if cr_currection_method == 'irafcosmicrays':
            irafcosmicrays(input=file_name, output=output_file_name2, threshold=threshold, fluxrate=fluxrate,
                           npasses=npasses, window=window)
        elif cr_currection_method == 'irafcrmedian':
            irafcrmedian(input=file_name, output=output_file_name2, lsigma=lsigma, hsigma=3, ncmed=5, nlmed=5,
                         ncsig=ncsig, nlsig=25)
        elif cr_currection_method == 'la_cosmic':
            la_cosmic(input=file_name, output=output_file_name2, sigclip=sigclip, sigfrac=sigfrac, objlim=objlim,
                      read_noise=read_noise, data_max=data_max)

        iraf.images.imutil.imarith.unlearn()
        iraf.images.imutil.imarith(operand1=str(file_name), op='-', operand2=str(output_file_name2),
                                   result=str(cr_check_file_name2))
        # time.sleep(3)
        ds9_waiting.join()
        # try:
        #     iraf.display(cr_check_file_name2, 2)
        iraf.display(output_file_name2, 1)
        iraf.display(cr_check_file_name2, 2)
        iraf.display(file_name, 3)
        print(bar)
        print("Try ds9>>>Frame>>>Blink to check how good is the cosmic ray correction")
        print(bar)
        # except iraf.IrafError as error:
        #     # ds9 might not be open, hence open it and try again
        #     print('DS9 window is not active. Opening a DS9 window please wait')
        #     subprocess.Popen('ds9')

        print(file_name)

        check = ''
        message = "Enter Yes accept, No for reject"
        choices = ['Yes', 'No']
        check = options(message, choices)
        # check = raw_input('Enter "y" accept, "n" reject:')

        if check == 'No':  # Should redo
            print(x)
            # cr_currection_method = raw_input("Enter new cosmic-ray correction method (1/2/3) :")
            message = "Enter Yes accept, No for reject"
            choices = ['irafcrmedian', 'irafcosmicrays', 'la_cosmic']
            cr_currection_method = options(message, choices)
            if cr_currection_method == 'irafcosmicrays':
                print("Enter new cosmicray correction parameters")
                threshold = raw_input('threshold='+str(threshold)+'; Enter new threshold :')
                fluxrate = raw_input('fluxrate ='+str(fluxrate)+'; Enter new fluxrate :')
                npasses = raw_input('npasses ='+str(npasses)+'; Enter new npasses :')
                window = raw_input('window'+str(window)+'Enter new window (5/7) :')
            if cr_currection_method == 'irafcrmedian':
                print("Enter new crmedian correction parameters")
                lsigma = raw_input('lsigma='+str(lsigma)+'; Enter new lsigma :')  # Low Clipping Sigma Factor
                ncsig = raw_input('ncsig='+str(ncsig)+'; Enter new ncsig (minimum=10):')
                # Column Box Size For Sigma Calculation
            if cr_currection_method == 'la_cosmic':
                print("Enter new la_cosmic cosmic-ray correction parameters")
                sigclip = raw_input('sigclip='+str(sigclip)+'; Enter new sigclip :')
                sigfrac = raw_input('sigfrac='+str(sigfrac)+'; Enter new sigfrac :')
                objlim = raw_input('objlim='+str(objlim)+'; Enter new objlim :')
            continue

        if check == 'Yes':  # Should continue
            print(x)
            x = next(iterobj, sentinel)  # Explicitly advance loop for continue case
            cr_check_list.append(cr_check_file_name)
            cr_currected_list.append(output_file_name)
            remove_file(str(file_name))
            remove_file(cr_check_file_name2)
            # remove_file(str(file_name))   # removing the older files which is needed to bias correct.
            continue

        if check == 'b':  # Should break
            break
            print("Error in loop")

        # Advance loop
        x = next(iterobj, sentinel)
        break

    return cr_check_list


def cosmic_correction(cosmic_curr_list, location='', prefix_string='c'):
    """
    Corrects for cosmic rays in the OBJECT image.

    Parameters
    ----------
        cosmic_curr_list: list
            List of files which need to do cosmic-ray correction.
        location        : str
            Location of the files if it is not in the working directory.
        prefix_string   : str
            Prefix to distinguish FITS file from the original FITS file
    Returns
    -------
        cr_check_list   : list
            List of files to check how good is the cosmic ray correction.
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


def cosmic_correction_batch(cosmic_curr_list, CCD, location='',  prefix_string='c'):
    """
    Corrects for cosmic rays in the OBJECT image.

    Parameters
    ----------
        cosmic_curr_list: list
            List of files which need to do cosmic-ray correction.
        location        : str
            Location of the files if it is not in the working directory.
        prefix_string   : str
            Prefix to distinguish FITS file from the original FITS file
    Returns
    -------
        cr_check_list   : list
            List of files to check how good is the cosmic ray correction.
    """
    print(cosmic_curr_list)
    cr_currected_list = []
    cr_check_list = []

    message = "Select the cosmic ray correction module"
    choices = ['irafcrmedian', 'irafcosmicrays', 'la_cosmic']
    cr_currection_method = options(message, choices)

    message = "Do you need to keep verification files for cosmic-ray correction ?"
    choices = ['Yes', 'No']
    verify = options(message, choices)

    # cosmicray correction task default parameters
    threshold = 25
    fluxrate = 2
    npasses = 5
    window = 5

    # crmedian
    lsigma = 25       # Low Clipping Sigma Factor
    ncsig = 10        # Column Box Size For Sigma Calculation

    # la_cosmic parameters
    sigclip = 15.0
    sigfrac = 0.5
    objlim = 5.0
    data_max = CCD.max_count  # 700000  # Depend up on CCD
    read_noise = CCD.read_noise  # 5.75  # Depend up on CCD

    # Cosmic ray correction loop
    for file_name in cosmic_curr_list:

        output_file_name = str(prefix_string) + str(file_name)
        output_file_name2 = os.path.join(location, output_file_name)

        file_name = os.path.join(location, file_name)

        print(output_file_name)

        remove_file(output_file_name2)

        if cr_currection_method == 'irafcosmicrays':
            irafcosmicrays(input=file_name, output=output_file_name2, threshold=threshold, fluxrate=fluxrate,
                           npasses=npasses, window=window)
        elif cr_currection_method == 'irafcrmedian':
            irafcrmedian(input=file_name, output=output_file_name2, lsigma=lsigma, hsigma=3, ncmed=5, nlmed=5,
                         ncsig=ncsig, nlsig=25)
        elif cr_currection_method == 'la_cosmic':
            la_cosmic(input=file_name, output=output_file_name2, sigclip=sigclip, sigfrac=sigfrac, objlim=objlim,
                      read_noise=read_noise, data_max=data_max)

        cr_currected_list.append(output_file_name)

        if verify == 'No':
            cr_check_file_name = str('chk_') + output_file_name
            cr_check_file_name2 = os.path.join(location, 'CR_Check', cr_check_file_name)
            cr_check_folder = os.path.join(location, 'CR_Check')
            try:
                os.makedirs(cr_check_folder)
            except OSError:
                pass

            remove_file(cr_check_file_name2)

            iraf.images.imutil.imarith.unlearn()
            iraf.images.imutil.imarith(operand1=str(file_name), op='-', operand2=str(output_file_name2),
                                       result=str(cr_check_file_name2))

            print(cr_check_file_name)
            cr_check_list.append(cr_check_file_name)
            # it will not remove files

        elif verify == 'Yes':
            cr_check_file_name = str('chk_') + output_file_name
            cr_check_file_name2 = os.path.join(location, cr_check_file_name)

            remove_file(cr_check_file_name2)

            iraf.images.imutil.imarith.unlearn()
            iraf.images.imutil.imarith(operand1=str(file_name), op='-',
                                       operand2=str(output_file_name2),
                                       result=str(cr_check_file_name2))

            print(cr_check_file_name)
            cr_check_list.append(cr_check_file_name2)  # it will remove files

        remove_file(str(file_name))
        # remove_file(cr_check_file_name2)
    return cr_check_list


def display_co(image_list, location='', prefix_string='c'):
    """Function for displaying the image files in ds9"""

    # opening ds9 for manually inspecting images
    subprocess.Popen('ds9')
    # process_ds9open.wait()
    ds9_time_delay = 3  # Depends upon how fast your system opens up ds9
    # time.sleep(4)
    ds9_waiting = threading.Thread(time.sleep(ds9_time_delay))
    ds9_waiting.start()
    ds9_waiting.join()
    # Create guaranteed unique sentinel
    # (can't use None since iterator might produce None)
    sentinel = object()
    iterobj = iter(image_list)   # Explicitly get iterator from iterable
    # (for does this implicitly)
    x = next(iterobj, sentinel)  # Get next object or sentinel
    while x is not sentinel:     # Keep going until we exhaust iterator

        file_name = x
        print(file_name)

        output_file_name = str(prefix_string) + str(file_name)
        output_file_name2 = os.path.join(location, output_file_name)

        cr_check_file_name = str('chk_') + output_file_name
        cr_check_file_name2 = os.path.join(location, cr_check_file_name)

        # file_name = os.path.join(location, file_name)

        print(output_file_name)
        print(cr_check_file_name)

        try:
            iraf.display(output_file_name2, 1)
            iraf.display(cr_check_file_name2, 2)
        except:
            time.sleep(2)
            iraf.display(output_file_name2, 1)
            iraf.display(cr_check_file_name2, 2)
        # iraf.display(file_name, 3)
        print(bar)
        print("Try ds9>>>Frame>>>Blink to check how good is the cosmic ray correction")
        print(bar)
        # except iraf.IrafError as error:
        #     # ds9 might not be open, hence open it and try again
        #     print('DS9 window is not active. Opening a DS9 window please wait')
        #     subprocess.Popen('ds9')

        check = ''
        message = "Continue to next image"
        choices = ['Yes']
        check = options(message, choices)

        if check == 'Yes':  # Should continue
            x = next(iterobj, sentinel)
            #  Explicitly advance loop for continue case
            continue
