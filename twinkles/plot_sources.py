import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import astropy.io.fits as fits
import astropy.wcs
from desc.pserv import DbConnection
from light_curve_service import LightCurveFactory
from desc.twinkles import PostageStampMaker, render_fits_image
plt.ion()

try:
    objectId = int(sys.argv[1])
except:
    objectId = 57500

db_info = dict(db='jc_desc', read_default_file='~/.my.cnf')
jc_desc = DbConnection(**db_info)
lc_factory = LightCurveFactory(**db_info)

lc = lc_factory.create(objectId)
lc.plot(figtext='objectId %i' % objectId)

query = 'select psRa, psDecl from Object where objectId=%(objectId)i' % locals()
ra, dec = jc_desc.apply(query, lambda curs : tuple([x for x in curs][0]))
print ra, dec

chisq_min = 0
dof = 0

size_arcsec = 10.

size = size_arcsec/3600. # convert to degrees
cos_dec = np.abs(np.cos(dec*np.pi/180.))
ra_min, ra_max = ra - size/cos_dec, ra + size/cos_dec
dec_min, dec_max = dec - size, dec + size

query = '''select objectId, psRa, psDecl
           from Object obj where
           %(ra_min)12.8f < psRa and psRa < %(ra_max)12.8f and
           %(dec_min)12.8f < psDecl and psDecl < %(dec_max)12.8f''' \
    % locals()

#query = """select objectId, psRa, psDecl from Object
#           where objectId=%(objectId)i or parentObjectId=%(objectId)i""" \
#    % locals()

objects = jc_desc.apply(query, lambda curs : [x for x in curs])
ids, ras, decs = zip(*objects)
print query
print "found", len(ids), "objects"

plt.rcParams['figure.figsize'] = (15, 10)
subplots = (231, 232, 233, 234, 235, 236)
fig = None
for subplot, band in zip(subplots, 'ugrizy'):
    coadd = PostageStampMaker(os.path.join('output_401', 'deepCoadd', band,
                                           '0/0,0.fits'))
    stamp = coadd.create(ra, dec, 2.*size_arcsec)
    outfile = 'stamp_%i.fits' % objectId
    stamp.writeFits(outfile)
    fits_obj = fits.open(outfile)
    fig, axes, norm = render_fits_image(fits_obj[1], title=outfile,
                                        subplot=subplot, fig=fig)
    axes.scatter(ras, decs, transform=axes.get_transform('icrs'), color='red',
                 alpha=0.8)
    axes.scatter([ra], [dec], transform=axes.get_transform('icrs'),
                 color='green')
    axes.set_title('%(objectId)i, %(band)s band coadd' % locals())
