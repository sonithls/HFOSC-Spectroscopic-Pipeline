"""Header term correction."""
from astropy.io import fits
from file_management import search_files
import os
from astroquery.simbad import Simbad


def headcorr(file_list):
    """Header correction for files in the file list."""
    data = {}

    for filename in file_list:
        hdu = fits.open(filename, mode='update')
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

        data[filename]= [object_name, ra, dec]

    # Finding the RA and DEC using astroquery.
    for i in data.keys():
        try:
            result_table = Simbad.query_object(data[i][0])
            print(result_table)
            obj = result_table[0][0]
            print(obj)
            ra = str(result_table[0][1])
            dec = str(result_table[0][2])
            data[i] = [data[i][0], ra, dec]
            # replace the ra dec here.
        except:
            print("Some problem in astroquery")
            pass

    # Write table in to a csv file.
    if len(data.keys()) != 0:
        location = os.getcwd()+'/object_list.csv'
        with open(location, 'w') as f:
            for i in data.keys():
                f.write(i+','+data[i][0]+','+data[i][1]+','+data[i][2]+'\n')

    return data


def main():
    """Run the code."""
    file_list = search_files(location='', keyword='*.fits')
    headcorr(file_list)


if __name__ == "__main__":
    main()
