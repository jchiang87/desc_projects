import os
import sys
import glob
from collections import OrderedDict
import numpy as np
import pandas as pd
import astropy.io.fits as fits
import lsst.afw.math as afwMath
import lsst.daf.persistence as dp
from desc.twinkles import get_visits
from desc.twinkles.sqlite_tools import SqliteDataFrameFactory

def get_calexp_bg(visits, output_repo, raft, sensor):
    butler = dp.Butler(output_repo)
    results = OrderedDict()
    for i, visit in enumerate(visits):
        print "processing %i, %ith of %i visits" % (visit, i, len(visits))
        sys.stdout.flush()
        dataId = dict(visit=visit, raft=raft, sensor=sensor)
        calexp_bg = butler.get('calexpBackground', dataId=dataId)
        image = calexp_bg.getImage()
        results[visit] = afwMath.makeStatistics(image,
                                                afwMath.MEDIAN).getValue()
    return results

def get_calexp_bg_no_butler(visits, output_repo, raft, sensor):
    _raft = 'R%s%s' % tuple(raft.split(','))
    _sensor = 'S%s%s' % tuple(sensor.split(','))
    results = OrderedDict()
    for i, visit in enumerate(visits):
        print "processing %i, %ith of %i visits" % (visit, i, len(visits))
        sys.stdout.flush()
        visit_id = 'v%i-f*' % visit
        pattern = os.path.join(output_repo, 'calexp', visit_id,
                               _raft, 'bkgd-' + _sensor + '.fits')
        bg_file = glob.glob(pattern)[0]
        results[visit] = np.median(fits.open(bg_file)[0].data.ravel())
    return results

if __name__ == '__main__':
    opsim_db = 'kraken_1042_sqlite.db'
    factory = SqliteDataFrameFactory(opsim_db)
    columns = 'obsHistID filtSkyBrightness filter visitExpTime'.split()
    filter_sky_brightness = factory.create(columns, 'Summary',
                                           condition='order by obsHistID asc')

    from get_opsim_db import filter_sky_brightness

#    output_repo = '/nfs/slac/kipac/fs1/g/desc/Twinkles/501'
    output_repo = '/nfs/farm/g/desc/u1/users/jchiang/desc_projects/twinkles/Sky_Background_Study/501'
    raft = '2,2'
    sensor = '1,1'
    visits = get_visits(output_repo)

    all_visits = []
    for visit_list in visits.values():
        all_visits.extend(visit_list)
    all_visits.sort()

    calexp_bgs = get_calexp_bg_no_butler(all_visits, output_repo, raft, sensor)

    data = []
    for visit, flux in calexp_bgs.items():
        sys.stdout.flush()
        row = [visit, flux]
        index = filter_sky_brightness['obsHistID'] == visit
        row.extend(filter_sky_brightness[index].values.tolist()[0])
        data.append(row)

    columns='visit flux obsHistID filtSkyBrightness filter visitExpTime'.split()
    df = pd.DataFrame(data=data, columns=columns)
    df.to_pickle('sky_bg_df.pkl')
