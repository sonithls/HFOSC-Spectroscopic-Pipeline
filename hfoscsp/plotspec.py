import os
from astropy.io import fits
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
from hfoscsp.file_management import search_files
from hfoscsp.interactive import options
from hfoscsp.interactive import multioptions


def load_fits(file_name, location=''):
    """
    Convert IRAF written fits files to flux and wavelength. Other fits files\
    are not compatible. Please check CRVAL1 and CD1_1 is available in the\
    header.

    Parameters
    ----------
        file_name : str
            File_name of .fits file to covert into text file.
        location : str
            Location of the files if it is not in the working directory
    Returns
    -------
        wave: array
            Spectral axis in absolute value. (with out units)
        flux: array
            Flux value (with out units)
        telluric: array
            Flux value (with out units)
        uncert: array
            Flux value (with out units)
    """
    if location != '':      # change -- location
        loc = os.path.join(os.getcwd(), location, file_name)
    else:
        loc = file_name

    spectrum = fits.open(loc)

    if spectrum[0].header['NAXIS'] == 3:
        # Create flux and wavelength array
        data = np.array(spectrum[0].data)
        flux = data[0][0]
        telluric = data[2][0]
        uncert = data[3][0]
        wave = np.ones(spectrum[0].header['NAXIS1'], dtype=float)
        for i in range(spectrum[0].header['NAXIS1']):
            wave[i] = spectrum[0].header['CRVAL1'] + i*spectrum[0].header['CD1_1']
            # for Himalayan Chandra telescope before combining the Grism7 and Grism8 spectra

    elif spectrum[0].header['NAXIS'] == 1:
        # Create flux and wavelength array
        flux = np.array(spectrum[0].data)
        wave = np.ones(spectrum[0].header['NAXIS1'], dtype=float)
        for i in range(spectrum[0].header['NAXIS1']):
            wave[i] = spectrum[0].header['CRVAL1'] + i*spectrum[0].header['CDELT1']
            # for Himalayan Chandra telescope after combining the Grism7 and Grism8 spectra

    return flux, wave, telluric, uncert


def spectral_plot(file_list, location, type):
    """
    """
    # left = 3600
    # right = 9400
    # left = 5000
    # right = 6000

    # bottom = -0.2*10**-14
    # top = 5*10**-14
    # plt.figure(figsize=(14, 10))
    fig = plt.figure(figsize=(13, 9))  # setting the figure size

    # file_list = search_files(keyword='*.fits')
    print("All fits files in the folder :", file_list)

    ax = fig.add_subplot(111)
    for file_name in file_list:
        flux, wave, telluric, uncert = load_fits(file_name=file_name, location=location)
        # data = np.array([wave, flux])
        # data = data.T

        # datafile_path = os.path.splitext(file_name)[0]+'.txt'
        # print(datafile_path)
        if type.lower() == 'flux':
            plt.plot(wave, flux, label=file_name, linewidth=0.6)
        elif type.lower() == 'telluric':
            plt.plot(wave, telluric, label=file_name, linewidth=0.6)

    # plt.xlim(left, right)
    # plt.ylim(bottom, top)

    ax.xaxis.set_ticks_position('both')
    ax.yaxis.set_ticks_position('both')
    # ax.xaxis.set_major_locator(MultipleLocator(500))
    # ax.xaxis.set_minor_locator(MultipleLocator(100))
    # ax.yaxis.set_major_locator(MultipleLocator(top/10))
    # ax.yaxis.set_minor_locator(MultipleLocator(top/5))
    ax.tick_params(which='major', direction='in', length=8, width=1, labelsize=12)
    ax.tick_params(which='minor', direction='in', length=4, width=1, labelsize=12)
    plt.legend()
    plt.savefig('test_fig', dpi=100, format='png', bbox_inches='tight')
    plt.show()
    # raw_input("Press Enter for continue")
    plt.close()


def plotspectra():
    """
    """

    # Select folder from the list.

    file_list = search_files('*.fits')

    message = "Which spectrum file you need to plot?"
    choices = file_list
    file_list = multioptions(message, choices, default='')
    print(file_list)
    spectral_plot(file_list=file_list, location='', type='flux')

    message = "Do you need to plot telluric lines if available?"
    choices = ["Yes", "No"]
    Ans = options(message, choices)

    if Ans == "Yes":
        spectral_plot(file_list=file_list, location='', type='telluric')


if __name__ == "__main__":
    plotspectra()
