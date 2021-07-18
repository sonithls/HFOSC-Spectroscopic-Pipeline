"""Header term correction."""
import os
from astropy.io import fits
from astropy.io import ascii
# from hfoscsp.file_management import search_files
from hfoscsp.interactive import options
from astroquery.simbad import Simbad
from tabulate import tabulate


def headcorr(file_list, location=''):
    """Header correction for files in the file list."""
    print (os.getcwd())
    if location != '':  # change location
        loc_object_info = os.path.join(os.getcwd(), location, 'object_info')
    else:
        loc_object_info = os.path.join(os.getcwd(), 'object_info')
    print (loc_object_info)
    data = []
    for filename in file_list:
        if location != '':  # change location
            loc = os.path.join(os.getcwd(), location, filename)
        else:
            loc = os.path.join(os.getcwd(), filename)

        hdu = fits.open(loc)
        header = hdu[0].header

        # HFOSC
        if 'TM_START' in header.keys():
            object_name = header['OBJECT']

            try:
                ra = header['RA']
                dec = header['DEC']
            except:
                ra = 'NaN'
                dec = 'NaN'

        # HFOSC2
        else:
            object_name = header['OBJECT']
            try:
                ra = header['RA']
                dec = header['DEC']
            except:
                ra = 'NaN'
                dec = 'NaN'

        data.append([filename, object_name, ra, dec])

    # Finding the RA and DEC using astroquery.
    data_ = []
    for i in range(0, len(data)):
        try:
            result_table = Simbad.query_object(data[i][1])
            # print(result_table)
            # obj = result_table[0][0]
            # print(obj)
            ra = str(result_table[0][1])
            dec = str(result_table[0][2])
            data_.append([data[i][0], data[i][1], ra, dec])
            # replace the ra dec here.
        except:
            print("Some problem in astroquery")
            data_.append([data[i][0], data[i][1], data[i][2], data[i][3]])
            pass
    data = data_

    # Write table in to a csv file.
    if len(data) != 0:
        with open(loc_object_info, 'w') as f:
            f.write('FILENAME'+','+'OBJECT'+','+'RA'+','+'DEC'+'\n')
            for i in range(0, len(data)):
                f.write(data[i][0]+','+data[i][1]+','+data[i][2]+','+data[i][3]+'\n')
                # print(data[i][1]+','+data[i][2]+','+data[i][3]+','+data[i][0]+'\n')
    print("")
    print(tabulate(data, headers=['FILENAME', 'OBJECT', 'RA', 'DEC']))
    print("")
    return data


def updateheader(data, location=''):
    """Update header."""
    for i in range(0, len(data)):
        filename = data[i][0]
        if location != '':  # change location
            loc = os.path.join(os.getcwd(), location, filename)
        else:
            loc = os.path.join(os.getcwd(), filename)

        hdu = fits.open(loc, mode='update')
        header = hdu[0].header

        ra = data[i][2]
        dec = data[i][3]

        list_keywords = ['RA', 'DEC']
        data_header = {'RA': ra, 'DEC': dec}

        for key in list_keywords:
            if key in header.keys():
                header.remove(key, remove_all=True)
            header.append(card=(key, data_header[key]))

        hdu.flush()
        hdu.close()


def read_info(location=''):
    """Read file information."""
    if location != '':  # change location
        loc_object_info = os.path.join(os.getcwd(), location, 'object_info')
    else:
        loc_object_info = os.path.join(os.getcwd(), 'object_info')
    obj_info = ascii.read(loc_object_info)

    # print(obj_info)

    data = []
    for i in range(0, len(obj_info)):
        # print(i)
        filename = obj_info['FILENAME'][i]
        object_name = obj_info['OBJECT'][i]
        ra = obj_info['RA'][i]
        dec = obj_info['DEC'][i]
        # print(filename)
        data.append([filename, object_name, ra, dec])
    # print(data)

    # Finding the RA and DEC using astroquery.
    data_ = []
    for i in range(0, len(data)):
        # print(i)
        try:
            result_table = Simbad.query_object(data[i][1])
            # print(result_table)
            obj = result_table[0][0]
            # print(obj)
            ra = str(result_table[0][1])
            dec = str(result_table[0][2])
            data_.append([data[i][0],data[i][1], ra, dec])
            # replace the ra dec here.
        except:
            print("Some problem in astroquery")
            data_.append([data[i][0], data[i][1], data[i][2], data[i][3]])
            pass
    data = data_

    # Write table in to a csv file.
    if len(data) != 0:
        with open(loc_object_info, 'w') as f:
            f.write('FILENAME'+','+'OBJECT'+','+'RA'+','+'DEC'+'\n')
            for i in range(0, len(data)):
                f.write(data[i][0]+','+data[i][1]+','+data[i][2]+','+data[i][3]+'\n')
                # print(data[i][1]+','+data[i][2]+','+data[i][3]+','+data[i][0]+'\n')
    print("")
    print(tabulate(data, headers=['FILENAME', 'OBJECT', 'RA', 'DEC']))
    print("")
    return data


def headercorr(file_list, location=''):
    """Run the code."""
    data = headcorr(file_list, location=location)

    print("Check the object_list.csv before updating the header.")
    message = "Do you want to continue updating header ?"
    choices = ['Yes', 'No']
    answer = options(message, choices)

    while answer != 'Yes':
        data = read_info(location=location)

        print("object_list.csv is updated, check it before updating the header.")
        message = "Do you want to continue updating header ?"
        choices = ['Yes', 'No']
        answer = options(message, choices)

    updateheader(data, location=location)

    # while True:
    # do_something()
    # if answer == 'Yes':
    # break


# if __name__ == "__main__":
#     file_list = search_files(location='', keyword='*.fits')
#     headercorr(file_list, location='')
