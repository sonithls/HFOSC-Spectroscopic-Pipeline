import os

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
    # for file_name in cosmic_curr_list:
    #
    #     output_file_name = str(prefix_string) + str(file_name)
    #     output_file_name2 = os.path.join(location, output_file_name)
    #
    #     cr_check_file_name = str('chk_') + output_file_name
    #     cr_check_file_name2 = os.path.join(location, cr_check_file_name)
    #
    #     file_name = os.path.join(location, file_name)
    #
    #     task(operand1=str(file_name), op='-', operand2=str(output_file_name2), result=str(cr_check_file_name2))
    #
    #     iraf.display(cr_check_file_name2)
    #     print(cr_check_file_name2)
    #     check = ''
    #     check = raw_input('Enter "r" to reject, "a" accept:')
    #
    #
    #
    #     cr_check_list.append(cr_check_file_name2)
    #
    #     remove_file(str(file_name))   # removing the older files which is needed to bias correct.

    # Create guaranteed unique sentinel (can't use None since iterator might produce None)
    sentinel = object()
    iterobj = iter(cosmic_curr_list)  # Explicitly get iterator from iterable (for does this implicitly)
    x = next(iterobj, sentinel)  # Get next object or sentinel
    while x is not sentinel:     # Keep going until we exhaust iterator

        file_name = x
        output_file_name = str(prefix_string) + str(file_name)
        output_file_name2 = os.path.join(location, output_file_name)

        cr_check_file_name = str('chk_') + output_file_name
        cr_check_file_name2 = os.path.join(location, cr_check_file_name)

        file_name = os.path.join(location, file_name)

        task(operand1=str(file_name), op='-', operand2=str(output_file_name2), result=str(cr_check_file_name2))

        iraf.display(cr_check_file_name2)
        print(cr_check_file_name2)

        check = ''
        check = raw_input('Enter "y" accept, "n" reject:')

        if check == 'n':  # Should redo
            print(x)
            continue

        if check == 'y':  # Should continue
            print(x)
            x = next(iterobj, sentinel)  # Explicitly advance loop for continue case

            cr_check_list.append(cr_check_file_name2)
            remove_file(str(file_name))   # removing the older files which is needed to bias correct.

            continue

        if check == 'b':  # Should break
            break

        # Advance loop
        x = next(iterobj, sentinel)

    return cr_check_list
