# -------------------------------------------------------------------------------------------------------------------- #
__author__ = 'Sonith L.S'
__contact__ = 'sonith.ls@iiap.res.in'
__version__ = '0.1.1'
# -------------------------------------------------------------------------------------------------------------------- #

# -------------------------------------------------------------------------------------------------------------------- #
# Import required libraries
# -------------------------------------------------------------------------------------------------------------------- #
import os
import sys

try:
    from pyraf import iraf
except ImportError as error:
    print(error + "Please install pyraf and iraf")

# -------------------------------------------------------------------------------------------------------------------- #
# Import required modules
# -------------------------------------------------------------------------------------------------------------------- #
# from hfoscsp.file_management import Backup
from hfoscsp.file_management import search_files
from hfoscsp.file_management import list_subdir
from hfoscsp.file_management import spec_or_phot
from hfoscsp.file_management import list_bias
from hfoscsp.file_management import remove_file
from hfoscsp.file_management import write_list
from hfoscsp.file_management import list_flat
from hfoscsp.file_management import list_lamp
from hfoscsp.file_management import list_object
# from hfoscsp.file_management import setccd
from hfoscsp.file_management import SetCCD

from hfoscsp.reduction import ccdsec_removal
from hfoscsp.reduction import bias_correction
# from hfoscsp.reduction import cosmic_correction
from hfoscsp.reduction import flat_correction
from hfoscsp.reduction import spectral_extraction
from hfoscsp.reduction import flux_calibrate

from hfoscsp.cosmicray import cosmic_correction_individual
from hfoscsp.cosmicray import cosmic_correction_batch
from hfoscsp.cosmicray import cosmic_correction

from hfoscsp.headercorrection import headercorr
from hfoscsp.interactive import options
# from hfoscsp.interactive import multioptions

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

# -------------------------------------------------------------------------------------------------------------------- #


def batch_q():
    """Batch processing."""
    logo = """
###############################################################################
###############################################################################
                          HFOSC Spectroscopic Pipeline
                               Batch processing
                                Version: 0.1.1
###############################################################################
###############################################################################
1) Bias correction          2) Flat correction          3)Cosmic-ray correction

2) Wavelength calibration   3) Flux calibration         6)Backup
"""
    print(logo)

# -------------------------------------------------------------------------------------------------------------------- #


def b_bias(bias_list, list_files, CCD):
    """"""
    bias_correction(bias_list=bias_list, list_file=list_files, CCD=CCD,
                    location='', prefix_string='b_')


def batch_fuc(CCD):
    """Main function of batch operations."""
    batch_q()

    PATH = os.path.join(os.getcwd(), list_subdir()[0])
    folder_name = list_subdir()[0]
    print(folder_name)
    list_files = search_files(location=folder_name, keyword='*.fits')
    speclist, photlist = spec_or_phot(list_files, PATH, CCD, 'spec')  # Check [Errno 17] File exists
    bias_list, passing_list = list_bias(speclist, PATH)
    print(bias_list, passing_list)

    #b_bias(bias_list=bias_list, list_files=passing_list, CCD=CCD)
    #list_files = search_files(location=folder_name, keyword='*.fits')
    #ccdsec_removal(file_list=list_files, location=PATH)
