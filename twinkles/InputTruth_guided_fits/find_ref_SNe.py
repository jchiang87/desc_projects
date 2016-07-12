import sys
sys.path.insert(0, '/u/gl/jchiang/links/desc_projects/twinkles')
sys.path.insert(0, '/u/gl/jchiang/links/desc_projects/phosimTables')
import numpy as np
import astropy.coordinates as coords
import astropy.units as units
import pandas as pd
import sncosmo
import desc.monitor
from light_curve_service import LightCurveFactory
from PhosimDbInterface import PhosimObjects
from refLightCurve_tests import SNRefLightCurveServer

def sep_arcsec(a, b):
    a_coord = coords.SkyCoord(a[0], a[1], unit=(units.degree, units.degree))
    b_coord = coords.SkyCoord(b[0], b[1], unit=(units.degree, units.degree))
    return a_coord.separation(b_coord).arcsec

class GetData(object):
    def __init__(self, columns):
        self.columns = columns
    def __call__(self, cursor):
        data = [x for x in cursor]
        return pd.DataFrame(data=data, columns=self.columns)

class Salt2Model(sncosmo.Model):
    def __init__(self, params, mjd_offset=59580.):
        dust = sncosmo.OD94Dust()
        super(Salt2Model, self).__init__(source='salt2-extended',
                                         effects=[dust, dust],
                                         effect_names=['host', 'mw'],
                                         effect_frames=['rest', 'obs'])
        self.dustmap = sncosmo.SFD98Map()
        self._set_params(params, mjd_offset=mjd_offset)

    def set_ebv(self, ra, dec):
        self.set(mwebv=self.dustmap.get_ebv((ra, dec)))

    def _set_params(self, params, mjd_offset=59580.):
        self.ra = params.get('snra')[0]
        self.dec = params.get('sndec')[0]
        self.x0 = params.get('x0')[0]
        self.x1 = params.get('x1')[0]
        self.c = params.get('c')[0]
        self.t0 = params.get('t0')[0] + mjd_offset
        self.z = params.get('redshift')[0]
        self.set(t0=self.t0, z=self.z, x0=self.x0, x1=self.x1, c=self.c)
        self.set_ebv(self.ra, self.dec)

def get_coadd_object(l2_service, ra, dec, box_size=2):
    size = box_size/3600.  # convert from arcsec to degrees
    cos_dec = np.abs(np.cos(dec*np.pi/180.))
    ra_min, ra_max = ra - size/cos_dec, ra + size/cos_dec
    dec_min, dec_max = dec - size, dec + size
    query = """select obj.objectId, obj.psRA, obj.psDecl from Object obj
               join ObjectNumChildren nc on obj.objectId=nc.objectId where
               nc.numChildren=0 and
               %(ra_min)12.8f < psRA and psRA < %(ra_max)12.8f and
               %(dec_min)12.8f < psDecl and psDecl < %(dec_max)12.8f"""\
            % locals()
    coords = l2_service.conn.apply(query, GetData('objectId ra dec'.split()))
    coords['sep'] = sep_arcsec((coords['ra'], coords['dec']), (ra, dec))
    index = (coords['sep'] == min(coords['sep']))
    return coords[index]

if __name__ == '__main__':
    imin, imax = (int(x) for x in sys.argv[1:3])
    db_info = dict(database='jc_desc',
                   host='ki-sr01.slac.stanford.edu',
                   port=3307)

    l2_service = desc.monitor.Level2DataService(db_info=db_info)
    lc_factory = LightCurveFactory(**db_info)
    SN_objects = PhosimObjects(l2_service, dof_range=(0, 30),
                               chisq_range=(1e3, 1e10))

    sourceIds = SN_objects.data['sourceId'].tolist()
    print len(sourceIds)

    SN_reflc_server = SNRefLightCurveServer()

    columns = """objectId ra dec z t0 x0 x1 c chisq ndof
                 sourceId snra sndec z_model t0_model x0_model x1_model
                 chisq_catsim ndof_catsim""".split()
    results = pd.DataFrame(columns=columns)
    for i in range(imin, imax):
        sourceId = sourceIds[i]
        print i, sourceId
        sys.stdout.flush()

        # Get the catsim light curve and set the salt2 model with the
        # input truth parameters.
        ref_lc = SN_reflc_server.get_SNLightCurve_object(sourceId)
        model = Salt2Model(ref_lc.params)
        # Compute the chisq stats.
        mask = ((ref_lc.lightcurve['bandpass']!='lsstu')
                & (ref_lc.lightcurve['fluxerr']==ref_lc.lightcurve['fluxerr']))
        data = ref_lc.lightcurve[mask]
        ndof = len(data) - 5
        chisq_catsim = sncosmo.chisq(data, model)
        ndof_catsim = ndof

        # Find the nearest object from the Object table within +/-2
        # arcsec of the catsim source coordinates.
        obj = get_coadd_object(l2_service, model.ra, model.dec, box_size=2)
        objectId = obj.objectId.iloc[0]
        # Get the ForcedSource light curves and select the data based
        # on nominal time range of the model (and exclude the u band
        # data).
        lc = lc_factory.create(objectId)
        data_mask = ((lc.data['bandpass'] != 'lsstu')
                     & (model.mintime() < lc.data['mjd'])
                     & (lc.data['mjd'] < model.maxtime()))
        data = lc.data[data_mask]
        # Fit the data using a redshift bounds of +/- 0.03 centered on
        # the input model value.
        res, fitted_model = sncosmo.fit_lc(data, model,
                                           'z t0 x0 x1 c'.split(),
                                           bounds=dict(z=(model.z-0.03,
                                                          model.z+0.03)))
        # Stuff everything into the results DataFrame.
        row = [objectId, obj.ra.iloc[0], obj.dec.iloc[0]]
        foo = sncosmo.flatten_result(res)
        for key in 'z t0 x0 x1 c chisq ndof'.split():
            row.append(foo[key])
        row.extend([sourceId, model.ra, model.dec, model.z, model.t0,
                    model.x0, model.x1, chisq_catsim, ndof_catsim])
        results = results.append(pd.DataFrame(data=[row], columns=columns),
                                 ignore_index=True)
