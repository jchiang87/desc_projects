import os
import sys
import subprocess
import numpy as np
import astropy.io.fits as fits
import matplotlib.pyplot as plt
from desc.twinkles import PostageStampMaker, render_fits_image
from desc.twinkles.Display import image_norm
from desc.twinkles.db_table_access import LsstDatabaseTable

try:
    objectId = int(sys.argv[1])
    tempdir = sys.argv[2]
except:
    print "usage: %s <objectId> <tempdir>" % sys.argv[0]
    sys.exit(0)

def output_dir(filename):
    return os.path.join(tempdir, filename)

band = 'u'
size = 10.
scaling_factor = 50.

db_info = dict(db='jc_desc', read_default_file='~/.my.cnf')
jc_desc = LsstDatabaseTable(**db_info)

# Find all of the visits for the specified band.
visits = jc_desc.apply('''select visitId from CcdVisit
                          where filterName='%(band)s'
                          order by visitId''' % locals(),
                       lambda curs : [x[0] for x in curs])

# Find the coordinates of the object.
ra, dec = jc_desc.apply('''select psRA, psDecl from Object
                           where objectId=%(objectId)i''' % locals(),
                        lambda curs : tuple([x for x in curs][0]))

# Create the coadd postage stamp to get the normalization for the
# individual stamp images.
coadd = PostageStampMaker(os.path.join('output', 'deepCoadd', band,
                                       '0/0,0.fits'))
coadd_file = output_dir('coadd_%(objectId)i.fits' % locals())
if not os.path.isfile(coadd_file):
    stamp = coadd.create(ra, dec, size)
    stamp.writeFits(coadd_file)
fits_obj = fits.open(coadd_file)
norm = image_norm(fits_obj[1].data*scaling_factor)

render_fits_image(fits_obj[1])
plt.savefig('coadd_%(objectId)i.png' % locals())

# Generate the png files for each visit.
for visit in visits:
    print "working on", visit
    sys.stdout.flush()
    fitsfile = output_dir('stamp_%07i.fits' % visit)
    if not os.path.isfile(fitsfile):
        maker = PostageStampMaker(os.path.join('output', 'deepCoadd', band,
                                               '0/0,0tempExp',
                                               'v%i-fu.fits' % visit))
        stamp = maker.create(ra, dec, size)
        stamp.writeFits(fitsfile)
    fits_obj = fits.open(fitsfile)
    title = 'objectId: %(objectId)i; visit: %(visit)7i' % locals()
    render_fits_image(fits_obj[1], title=title, norm=norm)
    plt.savefig(output_dir('stamp_%07i.png' % visit))

# Create the gif movie.
command = 'convert -delay 20 -loop 0 %(tempdir)s/stamp*.png objectId_%(objectId)i.gif' % locals()
subprocess.call(command, shell=True)
