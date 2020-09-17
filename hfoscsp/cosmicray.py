import os
import time
import subprocess
import threading

try:
    from pyraf import iraf
except ImportError as error:
    print(error + "Please install pyraf and iraf")


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


def irafcosmicrays(input, output, threshold, fluxrate, npasses, window):
    """
    Function utilise IRAF cosmicray correction module.
    Argument:
        input   : file name of file to correct cosmic rays.
        output  : file name of cosmic ray corrected file.
        threshol:
        fluxrate:
        npasses :
        window  :
    Returns :
        none
    """
    iraf.noao.imred.crutil.cosmicrays.unlearn()
    iraf.noao.imred.crutil.cosmicrays(input=input, output=output, thresho=threshold, fluxrat=fluxrate,
                                      npasses=npasses, window=window, interac='no', train='no')


def irafcrmedian(input, output, lsigma, hsigma, ncmed, nlmed, ncsig, nlsig):
    """
    Function utilise IRAF cosmicray correction module.
    Argument:
        input   : file name of file to correct cosmic rays.
        output  : file name of cosmic ray corrected file.

    Returns :
        none
    """
    iraf.noao.imred.crutil.crmedian.unlearn()
    iraf.noao.imred.crutil.crmedian(input=input, output=output, lsigma=lsigma, hsigma=hsigma, ncmed=ncmed,
                                    ncsig=ncsig, nlsig=nlsig)


def cosmic_correction_individual(cosmic_curr_list, location='', prefix_string='c'):
    """
    Corrects for cosmic rays in the individually for each OBJECT images and allow to adjust the
    parameters manually
    Arguments:
        cosmic_curr_list: List of files which need to do cosmicray correction.
        location        : Location of the files if it is not in the working directory.
        prefix_string   : Prefix to distinguish FITS file from the original FITS file
    Return:
        cr_check_list   : List of files to check how good is the cosmic ray correction.
    """
    print(cosmic_curr_list)
    cr_currected_list = []
    cr_check_list = []

    # opening ds9 for manually inspecting images
    subprocess.Popen('ds9')
    time.sleep(4)

    # Default method for cr currection curresponds to cosmicray task in IRAF
    cr_currection_method = 1
    # cosmic ray correction task default parameters
    threshold = 25
    fluxrate = 2
    npasses = 5
    window = 5

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

        if cr_currection_method == 1:
            thread = threading.Thread(target=irafcosmicrays(input=file_name, output=output_file_name2,
                                                            threshold=threshold, fluxrate=fluxrate,
                                                            npasses=npasses, window=window))
        elif cr_currection_method == 2:
            thread = threading.Thread(target=irafcosmicrays(input=file_name, output=output_file_name2,
                                                            threshold=threshold, fluxrate=fluxrate,
                                                            npasses=npasses, window=window))
        elif cr_currection_method == 3:
            thread = threading.Thread(target=irafcosmicrays(input=file_name, output=output_file_name2,
                                                            threshold=threshold, fluxrate=fluxrate,
                                                            npasses=npasses, window=window))
        thread.start()
        # wait here for the result to be available before continuing
        thread.join()

        iraf.images.imutil.imarith.unlearn()
        iraf.images.imutil.imarith(operand1=str(file_name), op='-', operand2=str(output_file_name2),
                                   result=str(cr_check_file_name2))
        time.sleep(1)
        # try:
            # iraf.display(cr_check_file_name2, 2)
        iraf.display(output_file_name2, 1)
        iraf.display(cr_check_file_name2, 2)
        iraf.display(file_name, 3)
        print("Try ds9>>>Frame>>>Blink to check how good is the cosmic ray correction")

        # except iraf.IrafError as error:
        #     # ds9 might not be open, hence open it and try again
        #     print('DS9 window is not active. Opening a DS9 window please wait')
        #     subprocess.Popen('ds9')
        #     time.sleep(3)  # Wait 3 seconds
        #     # iraf.display(cr_check_file_name2, 2)
        #     iraf.display(output_file_name2)

        print(file_name)

        check = ''
        check = raw_input('Enter "y" accept, "n" reject:')

        if check == 'n':  # Should redo
            print(x)
            print("Entre new cosmic-ray correction method (1/2/3)")
            cr_currection_method = raw_input()
            if cr_currection_method == 1:
                print("Entre new cosmic-ray correction parameters")
                print("threshold = ", threshold, "Enter new threshold =")
                threshold = raw_input()
                print("fluxrate = ", fluxrate, "Enter new fluxrate = ")
                fluxrate = raw_input()
                print("npasses = ", npasses, "Enter new npasses = ")
                npasses = raw_input()
                print("window = ", window, "Enter new window (5/7) = ")
                window = raw_input()
            # elif cr_currection_method == 2:
            # elif cr_currection_method == 3:
            continue

        if check == 'y':  # Should continue
            print(x)
            x = next(iterobj, sentinel)  # Explicitly advance loop for continue case
            cr_check_list.append(cr_check_file_name)
            cr_currected_list.append(output_file_name)
            # remove_file(str(file_name))   # removing the older files which is needed to bias correct.
            continue

        if check == 'b':  # Should break
            break

        # Advance loop
        x = next(iterobj, sentinel)
        print("Error in loop")
        break

    return cr_check_list
