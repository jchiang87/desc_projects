import os
import sys
import numpy as np
import astropy.io.fits as fits
import matplotlib.pyplot as plt
from desc.twinkles import PostageStampMaker, render_fits_image
from desc.twinkles.db_table_access import LsstDatabaseTable

db_info = dict(db='jc_desc', read_default_file='~/.my.cnf')
jc_desc = LsstDatabaseTable(**db_info)

# Find all of the u band visits.
band = 'u'
visits = jc_desc.apply('''select visitId from CcdVisit
                          where filterName='%(band)s'
                          order by visitId''' % locals(),
                       lambda curs : [x[0] for x in curs])

objectId = 1628

ra, dec = jc_desc.apply('''select psRA, psDecl from Object
                           where objectId=%(objectId)i''' % locals(),
                        lambda curs : tuple([x for x in curs][0]))
size = 10.

# The coadd frame postage stamp.
u_coadd = PostageStampMaker(os.path.join('output', 'deepCoadd/u/0/0,0.fits'))
stamp = u_coadd.create(ra, dec, size)
stamp.writeFits('coadd_stamp.fits')
fits_obj = fits.open('coadd_stamp.fits')
render_fits_image(fits_obj[1])
plt.savefig('coadd_stamp.png')

# Generate the png files for each visit.
for visit in visits:
    print "working on", visit
    sys.stdout.flush()
    maker = PostageStampMaker(os.path.join('output', 'deepCoadd/u/0/0,0tempExp',
                                           'v%i-fu.fits' % visit))
    stamp = maker.create(ra, dec, size)
    outfile = 'stamp_%07i.fits' % visit
    stamp.writeFits(outfile)
    fits_obj = fits.open(outfile)
    render_fits_image(fits_obj[1], title=outfile)
    plt.savefig('stamp_%07i.png' % visit)

# Create the gif movie.
command = 'convert -delay 120 -loop 0 stamp*.png objectId_%i.gif' % objectId
subprocess.call(command, shell=True)
