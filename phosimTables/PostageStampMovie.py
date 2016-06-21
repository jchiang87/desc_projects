"""
Use matplotlib.animation tools to make a movie of Twinkles data.
"""
from __future__ import print_function, absolute_import, division
import os
import sys
import copy
import pickle
from collections import OrderedDict
import numpy as np
import astropy.time
import matplotlib.pyplot as plt
from matplotlib import animation
from desc.pserv import DbConnection
from desc.monitor import PostageStampMaker, convert_image_to_hdu, image_norm,\
    render_fits_image
plt.ion()

__all__ = ['PostageStampMovie']

class Level2DataService(object):
    """
    Access to the Twinkles Level 2 data and pserv database.
    """
    def __init__(self, repo, db_info=None):
        """
        Keep track of the Level 2 repository and create a db connection.
        """
        self.repo = repo
        if db_info is None:
            db_info = dict(db='jc_desc', read_default_file='~/.my.cnf')
        self.conn = DbConnection(**db_info)

    def get_pixel_data(self, objectId, band, size=10, pickle_file=None):
        """
        Use PostageStampMaker to extract the pixel data cutout for the
        specified objectId andn band for each visit.
        """
        if pickle_file is None:
            pickle_file = 'pixel_data_%(objectId)i_%(band)s.pkl' % locals()
        if os.path.isfile(pickle_file):
            with open(pickle_file, 'r') as input_:
                pixel_data = pickle.load(input_)
            return pixel_data, pickle_file
        pixel_data = OrderedDict()
        visits = self.get_visits(band)
        ra, dec = self.get_coords(objectId)
        for visit in visits:
            print("working on visit", visit)
            sys.stdout.flush()
            exp_file = os.path.join(repo, 'deepCoadd', band, '0/0,0tempExp',
                                    'v%(visit)i-f%(band)s.fits' % locals())
            maker = PostageStampMaker(exp_file)
            stamp = maker.create(ra, dec, size)
            pixel_data[visit] = \
                copy.deepcopy(stamp.getMaskedImage().getImage().getArray())
        with open(pickle_file, 'w') as output:
            pickle.dump(pixel_data, output)
        return pixel_data, pickle_file

    def get_light_curve(self, objectId, band):
        """
        Get the light curve for the requested objectId and band.
        """
        query = """select cv.obsStart, fs.psFlux, fs.psFlux_Sigma from
               CcdVisit cv join ForcedSource fs on cv.ccdVisitId=fs.ccdVisitId
               join Object obj on fs.objectId=obj.objectId where
               cv.filterName='%(band)s' and fs.objectId=%(objectId)i
               order by cv.obsStart asc""" % locals()
        rows = self.conn.apply(query, lambda curs: np.array([x for x in curs]))
        obsStart, flux, fluxerr = (np.array(col) for col in rows.transpose())
        mjd = astropy.time.Time(obsStart).mjd
        return dict(mjd=mjd, flux=flux, fluxerr=fluxerr)

    def get_visits(self, band):
        """
        Get the visitIds corresponding to the specified band.
        """
        return self.conn.apply('''select visitId from CcdVisit where
                                  filterName='%(band)s' order by visitId'''
                               % locals(),
                               lambda curs: [x[0] for x in curs])

    def get_coords(self, objectId):
        """
        Get the RA, Dec of the requested object from the Object table.
        """
        return self.conn.apply('''select psRA, psDecl from Object where
                                  objectId=%(objectId)i''' % locals(),
                               lambda curs: tuple([x for x in curs][0]))

class PostageStampMovie(object):
    """
    Class to produce an animation of a cutout around a coadd object.
    The forced source light curve is also displayed and cursor events
    on the light curve plot can be used to control the animation.
    """
    def __init__(self, objectId, band, l2_service, size=10,
                 pickle_file=None, figsize=(6, 10), scaling_factor=50):
        """
        Create the figure with the animated cutout and lightcurve.
        """
        self.objectId = objectId
        self.band = band
        self.pixel_data, self.pickle_file = \
            l2_service.get_pixel_data(objectId, band, size=size,
                                      pickle_file=pickle_file)
        self._display_figure(l2_service, size, figsize, scaling_factor)
        self._set_animation_attributes()
        self.fig.canvas.mpl_connect('button_press_event', self.on_click)

    def _display_figure(self, l2_service, size, figsize, scaling_factor):
        """
        Display the image and light curve.
        """
        objectId = self.objectId
        band = self.band

        # Create the coadd postage stamp and use as the initial image.
        coadd = PostageStampMaker(os.path.join(repo, 'deepCoadd', band,
                                               '0/0,0.fits'))
        ra, dec = l2_service.get_coords(objectId)

        # Use the coadd to set the image normalization
        stamp = coadd.create(ra, dec, size)
        hdu = convert_image_to_hdu(stamp)
        norm = image_norm(hdu.data*scaling_factor)

        plt.rcParams['figure.figsize'] = figsize
        self.fig = plt.figure()
        self.fig.suptitle('objectId: %(objectId)i\n%(band)s band' % locals())
        self.image = render_fits_image(hdu, norm=norm, fig=self.fig,
                                       subplot=211)[2]
        self.fig.add_subplot(212)
        self.light_curve = l2_service.get_light_curve(objectId, band)
        plt.errorbar(self.light_curve['mjd'], self.light_curve['flux'],
                     yerr=self.light_curve['fluxerr'], fmt='.')
        self.yrange = plt.axis()[2:]
        self.current_point = plt.plot([self.light_curve['mjd'][0]],
                                      [self.light_curve['flux'][0]],
                                      marker='o', color='red')
        self.current_point.extend(plt.plot([self.light_curve['mjd'][0],
                                            self.light_curve['mjd'][0]],
                                           self.yrange, 'k:'))
        plt.xlabel('MJD')
        plt.ylabel('flux (nmgy)')

    def _set_animation_attributes(self):
        "Set the initial values of the attributes to control the animation."
        self.pause = False
        self.update = False
        self.num = 0
        self.nmax = len(self.light_curve['mjd'])

    def run(self, interval=200):
        """
        Run the animation with a time between frames of interval in
        msec.  The returned FuncAnimation object must exist in the
        top-level context.
        """
        return animation.FuncAnimation(self.fig, self, frames=self.index,
                                       interval=interval)

    def index(self):
        "Generator that returns the frame number to display."
        while True:
            yield self.num
            if not self.pause or self.update:
                self.num += 1
            if self.num >= self.nmax or self.num < 0:
                self.num = 0

    def __call__(self, i):
        "Set the data in the image for the ith frame."
        mjd = self.light_curve['mjd']
        flux = self.light_curve['flux']
        if not self.pause or self.update:
            self.image.set_data(self.pixel_data.values()[i])
            self.current_point[0].set_data([mjd[i]], [flux[i]])
            self.current_point[1].set_data([mjd[i], mjd[i]], self.yrange)
            self.update = False
        return [self.image, self.current_point]

    def on_click(self, event):
        "Call-back to transmit mouse event info."
        if event.button == 3:
            try:
                dt = np.abs(self.light_curve['mjd'] - event.xdata)
                self.num = np.where(dt == min(dt))[0][0] - 1
                self.update = True
            except IndexError:
                pass
        if event.button == 2:
            self.pause ^= True

if __name__ == '__main__':
    repo = '/nfs/farm/g/desc/u1/users/jchiang/desc_projects/twinkles/Run1.1/output'
    band = 'r'
    interval = 200
    level2_service = Level2DataService(repo)
    movies = []
#    for objectId in (6931, 50302, 52429)[:1]:
#        ps = PostageStampMovie(objectId, band, level2_service)
#        movies.append(ps.run(interval))

    objectId = 6931
    for band in 'ur':
        ps = PostageStampMovie(objectId, band, level2_service)
        movies.append(ps.run(interval))
