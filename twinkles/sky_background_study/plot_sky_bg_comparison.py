import os
import numpy as np
import pandas as pd
import galsim
import lsst.afw.image as afwImage
import matplotlib.pyplot as plt
plt.ion()

def bandpasses(exptime=30, effective_diameter=667.):
    """
    Return LSST band passes as GalSim Bandpass objects.
    """
    bands = 'ugrizy'
    bps = dict()
    for band in bands:
        throughput = os.path.join(os.environ['THROUGHPUTS_DIR'], 'baseline',
                                  'total_%s.dat' % band)
        bp = galsim.Bandpass(throughput).thin()
        bps[band] = bp.withZeropoint('AB', effective_diameter, exptime)
    return bps

# Get the pixel scale from one of the calexps.
output_repo = '501'
expfile = os.path.join(output_repo, 'calexp', 'v200-fr', 'R22', 'S11.fits')
wcs = afwImage.ExposureF(expfile).getWcs()
pixel_scale = wcs.pixelScale().asArcseconds()

bps = bandpasses()
df = pd.read_pickle('sky_bg_df.pkl')
#df = pd.read_pickle('sky_bg_df_butler.pkl')

# Compute the sky backgrounds from median background pixel value.
sb = []
for band, flux in zip(df['filter'].values, df['flux'].values):
    sb.append(-2.5*np.log10(flux/pixel_scale**2) + bps[band].zeropoint)
df['sky_bg'] = sb
df.to_pickle('sky_bg_df_sb_calc.pkl')

colors = 'violet green red blue orange yellow'.split()
handles = []
for band, color in zip('ugrizy', colors):
    index = (df['filter']==band)
    marker = '%so' % color
    handles.append(plt.scatter(df[index]['filtSkyBrightness'],
                               df[index]['sky_bg'], color=color,
                               marker='o', label=band))
plt.xlabel('filtSkyBrightness')
plt.ylabel('fitted sky background')
plt.legend(handles=handles, scatterpoints=1, loc=2)
