"""Header term correction."""
from astropy.io import fits
from file_management import search_files
import os
from astroquery.simbad import Simbad


def headcorr(file_list):
    """Header correction for files in the file list."""
    dicts = {}

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

        dicts.setdefault(filename, [])
        dicts[filename].extend([object_name, ra, dec])

    # Finding the RA and DEC using astroquery.
    for i in dicts.keys():
        try:
            result_table = Simbad.query_object(dicts[i][0])
            obj = result_table[0]
            ra = result_table[1]
            dec = result_table[2]
            # replace the ra dec here.
        except:
            pass
        print(obj, ra, dec)
        # print(result_table)

    # Write table in to a csv file.
    if len(dicts.keys()) != 0:
        location = os.getcwd()+'/object_list.csv'
        with open(location, 'w') as f:
            for i in dicts.keys():
                f.write(i+','+dicts[i][0]+','+dicts[i][1]+','+dicts[i][2]+'\n')

    return dicts


def main():
    """Run the code."""
    file_list = search_files(location='', keyword='*.fits')
    headcorr(file_list)


if __name__ == "__main__":
    main()
