import os
import numpy as np
import matplotlib.pyplot as plt
import astropy.coordinates as coords
import astropy.units as units
import astropy.time
import pandas as pd
import lsst.utils
import lsst.sims.photUtils as sims_photUtils
import desc.monitor

def separation(a, b):
    a_coord = coords.SkyCoord(a[0], a[1], unit=(units.degree, units.degree))
    b_coord = coords.SkyCoord(b[0], b[1], unit=(units.degree, units.degree))
    return a_coord.separation(b_coord)

class SNLightCurve(desc.monitor.LightCurve):
    def __init__(self, params):
        super(SNLightCurve, self).__init__()
        self.params = params

class SNRefLightCurveServer(object):
    def __init__(self):
        obs = pd.read_csv(os.path.join(lsst.utils.getPackageDir('monitor'),
                                       'data', 'SelectedKrakenVisits.csv'),
                          index_col='obsHistID')[['expMJD', 'filter',
                                                  'fiveSigmaDepth']]
        bp_dict = sims_photUtils.BandpassDict.loadBandpassesFromFiles()[0]
        self.ref_lcs = desc.monitor.RefLightCurves(tableName='TwinkSN',
                                                   bandPassDict=bp_dict,
                                                   observations=obs)

    def get_catsim_ids(self, ra, dec, box_size=1, mjd_offset=59580.):
        size = box_size/3600.  # convert from arcsec to degrees
        cos_dec = np.abs(np.cos(dec*np.pi/180.))
        ra_min, ra_max = ra - size/cos_dec, ra + size/cos_dec
        dec_min, dec_max = dec - size, dec + size
        query = """select snid, snra, sndec, t0, redshift from TwinkSN where
                   %(ra_min)12.8f < snra and snra < %(ra_max)12.8f and
                   %(dec_min)12.8f < sndec and sndec < %(dec_max)12.8f"""\
            % locals()
        cursor = self.ref_lcs.dbCursor
        cursor.execute(query)
        data = [list(x) for x in cursor]
        for row in data:
            row.append(separation((ra, dec), row[1:]).arcsec)
            row[3] += mjd_offset
        return pd.DataFrame(data=data,
                            columns='snid RA Dec t0 redshift sep_arcsec'.split())

    def _sourceId(self, catsim_id, nshift):
        return np.left_shift(long(catsim_id), nshift) + self.ref_lcs.objectID

    def get_params(self, catsim_id, nshift=10):
        sourceId = self._sourceId(catsim_id, nshift)
        return self.ref_lcs.astro_object(sourceId)

    def get_SNLightCurve_object(self, sourceId, mjd_offset=59580.):
        df = pd.concat([self.ref_lcs.lightCurve(sourceId, bandName=band)
                        for band in 'ugrizy'])
        params = self.ref_lcs.get_params(sourceId)
        nrows = len(df)
        data = dict(bandpass=['lsst' + band for band in df['band'].tolist()],
                    mjd=np.array(df['time'].tolist()),
                    ra=nrows*[params.get('snra')[0]],
                    dec=nrows*[params.get('sndec')[0]],
                    flux=np.array(df['flux'].tolist()),
                    fluxerr=np.array(df['fluxerr'].tolist()),
                    zp = nrows*[0],
                    zpsys = nrows*['ab'])
        my_lc = SNLightCurve(params)
        my_lc.lightcurve = astropy.table.Table(data=data)
        return my_lc

    def get_light_curve(self, catsim_id, band, nshift=10):
        sourceId = self._sourceId(catsim_id, nshift)
        return self.ref_lcs.lightCurve(sourceId, band)

    def match_catsim_object(self, ra, dec, t0, box_size=1, mjd_offset=59580.,
                            nshift=10, verbose=False):
        catsim_ids = ref_lc_server.get_catsim_ids(ra, dec)
        if verbose:
            print catsim_ids

        id_best = None
        t_best = None
        pars_best = None
        for id_value in catsim_ids['snid']:
            obj_pars = self.get_params(id_value, nshift=nshift)
            time = obj_pars.get('t0')
            if t_best is None or np.abs(time - t0) < np.abs(t_best - t0):
                t_best = time
                id_best = id_value
                pars_best = obj_pars
        return id_best, t_best, pars_best

def chisq(mjd, flux, fluxerr, ref_lc):
    index = np.where((mjd > min(ref_lc['time'])) & (mjd < max(ref_lc['time'])))
    ymodel = np.interp(mjd[index], ref_lc['time'], ref_lc['flux'])*1e9
    chi2 = sum(((ymodel - flux[index])/fluxerr[index])**2)
    dof = len(index[0]) - 1
    nsig = np.sqrt(2*chi2) - np.sqrt(2*dof - 1)
    return chi2, dof, nsig

if __name__ == '__main__':
    plt.ion()

    repo = '/nfs/farm/g/desc/u1/users/jchiang/desc_projects/twinkles/Run1.1/output'
    db_info = dict(database='jc_desc',
                   host='ki-sr01.slac.stanford.edu',
                   port=3307)

    ref_lc_server = SNRefLightCurveServer()
    l2_service = desc.monitor.Level2DataService(repo, db_info=db_info)

    band = 'r'
    results_file = 'sncosmo_results_r.txt'
    results = pd.DataFrame(np.recfromtxt(results_file,
                                         names='objectId chisq ndof z t0 x0 x1 c'.split()))

    for colname in 'z t0 x0 x1 c'.split():
        results[colname+'_model'] = np.zeros(len(results))

    make_plot = False

    for i, objectId in enumerate(results['objectId']):
        t0 = results['t0'][i]
        print i, objectId, t0

        ra, dec = l2_service.get_coords(objectId)
        catsim_id, t0_model, model_pars =\
            ref_lc_server.match_catsim_object(ra, dec, t0, box_size=2,
                                              verbose=False)
        if catsim_id is None:
            continue
        results['z_model'].set_value(i, model_pars.get('z'))
        results['t0_model'].set_value(i, model_pars.get('t0'))
        results['x0_model'].set_value(i, model_pars.get('x0'))
        results['x1_model'].set_value(i, model_pars.get('x1'))
        results['c_model'].set_value(i, model_pars.get('c'))

        if make_plot:
            lc = l2_service.get_light_curve(objectId, band)
            ref_lc = ref_lc_server.get_light_curve(catsim_id, band)
            if len(ref_lc) == 0:
                continue
            #chi2, dof, nsig = chisq(mjd, flux, fluxerr, ref_lc)
            fig = plt.figure()
            plt.errorbar(lc['mjd'], lc['flux'], yerr=lc['fluxerr'],
                         fmt='.', color='black')
            plt.xlabel('MJD')
            plt.ylabel('%(band)s band flux (nmgy)' % locals())
            plt.suptitle('objectId: %i' % objectId)
            plt.errorbar(ref_lc['time'], ref_lc['flux']*1e9,
                         yerr=(ref_lc['fluxerr']*1e9).tolist(), fmt=':.')
            plt.plot((t0, t0), plt.axis()[-2:], 'k:')
            plt.plot((t0_model, t0_model), plt.axis()[-2:], 'r:')

    outfile = 'sncosmo_results_model_comparisons.pkl'
    results.to_pickle(outfile)
