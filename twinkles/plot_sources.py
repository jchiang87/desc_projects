import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import astropy.io.fits as fits
import astropy.wcs
from desc.twinkles.db_table_access import LsstDatabaseTable
from desc.twinkles.lightCurveFactory import LightCurveFactory
from desc.twinkles import PostageStampMaker, render_fits_image
plt.ion()

try:
    objectId = int(sys.argv[1])
except:
    objectId = 57500

print objectId

db_info = dict(db='jc_desc', read_default_file='~/.my.cnf')
jc_desc = LsstDatabaseTable(**db_info)
lc_factory = LightCurveFactory(**db_info)

query = 'select psRa, psDecl from Object where objectId=%(objectId)i' % locals()
ra, dec = jc_desc.apply(query, lambda curs : tuple([x for x in curs][0]))
print ra, dec

chisq_min = 0
dof = 0

size = 5./3600. # 5 arcsec in degrees
cos_dec = np.abs(np.cos(dec*np.pi/180.))
ra_min, ra_max = ra - size/cos_dec, ra + size/cos_dec
dec_min, dec_max = dec - size, dec + size

query = '''select obj.objectId, obj.psRa, obj.psDecl
           from Object obj join Chisq cs
           on obj.objectId=cs.objectId
           where cs.chisq > %(chisq_min)e and cs.dof>=%(dof)i and
           %(ra_min)12.8f < obj.psRa and obj.psRa < %(ra_max)12.8f and
           %(dec_min)12.8f < obj.psDecl and obj.psDecl < %(dec_max)12.8f''' \
    % locals()

objects = jc_desc.apply(query, lambda curs : [x for x in curs])
ids, ras, decs = zip(*objects)
print query
print "found", len(ids), "objects"

plt.rcParams['figure.figsize'] = (20, 30)
subplots = (231, 232, 233, 234, 235, 236)
for subplot, band in zip(subplots, 'ugrizy'):
    coadd = PostageStampMaker(os.path.join('output', 'deepCoadd', band,
                                           '0/0,0.fits'))
    stamp = coadd.create(ra, dec, 10.)
    outfile = 'stamp_%i.fits' % objectId
    stamp.writeFits(outfile)
    fits_obj = fits.open(outfile)
    fig, axes = render_fits_image(fits_obj[1], title=outfile, subplot=subplot)
    axes.scatter(ras, decs, transform=axes.get_transform('icrs'), color='red',
                 alpha=0.8)
    axes.set_title('%(objectId)i, %(band)s band' % locals())

#for my_id in ids:
#    lc = lc_factory.create(my_id)
#    lc.plot(figtext='%i' % my_id)
