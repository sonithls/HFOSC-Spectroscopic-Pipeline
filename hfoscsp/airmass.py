"""Calculate airmass."""
from astropy.io import fits
import astropy.units as u
from astropy.time import Time
from astropy.coordinates import SkyCoord, EarthLocation, AltAz, Angle
import datetime
from astropy.utils import iers
import ephem
import math

iers.Conf.iers_auto_url.set('https://datacenter.iers.org/data/9/finals2000A.all')


# HCT location information
latitude = 32.7794
longitude = -281.03583
altitude = 4500.0
hct = EarthLocation.from_geodetic(lat=latitude, lon=longitude, height=altitude)


def airmass(filename, observatory=hct):
    """
    Calculate airmass and adding in the header and retuning value.

    Parameters
    ----------
        filename    : str
            File which need to calculate the airmass.
    Returns
    -------
        airmass     : float
            Airmass value
    """
    hdu = fits.open(filename, mode='update')
    header = hdu[0].header

    # HFOSC
    if 'TM_START' in header.keys():
        date_obs = header['DATE-OBS']
        time_start = header['TM_START']
        object = header['OBJECT']
        print(object)
        ra_ = header['RA']
        dec_ = header['DEC']
        print(ra_, dec_)
        c = SkyCoord(ra_, dec_, unit=(u.hourangle, u.deg))
        ra = c.ra.deg
        dec = c.dec.deg

        time_utc = str(datetime.timedelta(seconds=int(time_start)))
        datetime_utc = date_obs+' '+time_utc
        time = Time(datetime_utc)
        print(time)

    # HFOSC2
    else:
        date_time = header['DATE-AVG'].split('T')
        time_obj = date_time[0]+' '+date_time[1]
        time = Time(time_obj)
        ra = header['RA']
        dec = header['DEC']

    #  calculation of airmass
    coord = SkyCoord(ra, dec, unit='deg')
    altaz_ = coord.transform_to(AltAz(obstime=time, location=observatory))
    airmass = float(altaz_.secz.value)

    # airmass = observer.altaz(time_ut, target).secz
    # altaz = AltAz(obstime=time, location=observatory)
    # altaz_ = coord.transform_to(altaz)
    # airmass = altaz_.secz.value

    # print('The image %s has been observed at an airmass of %f and ra: %r, dec: %d'
    #       % (filename, ra, dec, float(airmass)))

    print("altitude", altaz_.alt.value)
    print("airmass =", airmass)

    list_keywords = ['AIRMASS']
    dict_header = {'AIRMASS': float(airmass)}

    for key in list_keywords:
        if key in header.keys():
            header.remove(key, remove_all=True)
        header.append(card=(key, dict_header[key]))

    hdu.flush()
    hdu.close()
    return airmass
