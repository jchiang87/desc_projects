from __future__ import print_function
import sys
import csv
from warnings import filterwarnings
import pandas as pd
import numpy as np
import MySQLdb as Database
import desc.pserv

filterwarnings('ignore', category=Database.Warning)

class GetData(object):
    def __init__(self, columns):
        self.columns = columns
    def __call__(self, curs):
        return pd.DataFrame(data=[x for x in curs], columns=self.columns)

def compute_circle(xvalues, yvalues):
    index = np.argsort(xvalues)
    x1 = xvalues[index][0]
    x2 = xvalues[index][len(xvalues)/2]
    x3 = xvalues[index][-1]
    y1 = yvalues[index][0]
    y2 = yvalues[index][len(xvalues)/2]
    y3 = yvalues[index][-1]

    a1 = -(x2 - x1)/(y2 - y1)
    b1 = -a1*(x1 + x2)/2. + (y1 + y2)/2.

    a2 = -(x3 - x2)/(y3 - y2)
    b2 = -a2*(x2 + x3)/2. + (y2 + y3)/2.

    x0 = (b2 - b1)/(a1 - a2)
    y0 = a1*x0 + b1
    r = np.sqrt((x1 - x0)**2 + (y1 - y0)**2)

    phi = np.linspace(0, np.pi*2, 100)
    x = r*np.sin(phi) + x0
    y = r*np.cos(phi) + y0
    return x, y, r

connect = desc.pserv.DbConnection(db='jc_desc',
                                  read_default_file='~/.my.cnf')

connect.apply('drop table if exists PhosimLightCurveStats')
connect.run_script('create_PhosimLightCurveStats.sql', dry_run=False)

# Loop over sourceIds in PhosimObject table and compute light curve stats.
sourceIds = connect.apply("select sourceId from PhosimObject",
                          lambda curs: [x[0] for x in curs])
band = 'u'
csv_file = 'phosim_lc_stats.csv'
with open(csv_file, 'w') as output:
    writer = csv.writer(output, delimiter=',')
    writer.writerow('sourceId meanCounts chisq dof radius xmin xmax ymin ymax filterName'.split())
    for i, sourceId in enumerate(sourceIds):
        if i % (len(sourceIds)/4) == 0:
            sys.stdout.write('!')
        elif i % (len(sourceIds)/20) == 0:
            sys.stdout.write('.')
        sys.stdout.flush()
        query = """select pcc.numPhotons, pcc.avgX, pcc.avgY from
                   CcdVisit cv join PhosimCentroidCounts pcc
                   on cv.ccdVisitId=pcc.ccdVisitId
                   where cv.filterName='%(band)s' and
                   pcc.sourceId=%(sourceId)i""" % locals()
        data = connect.apply(query, GetData('numPhotons avgX avgY'.split()))
        if len(data['numPhotons']) > 1:
            counts = np.array(data['numPhotons'].tolist())
            mean = np.mean(counts)
            chisq = sum((mean - counts)**2/counts)
            x, y, radius = compute_circle(np.array(data['avgX'].tolist()),
                                          np.array(data['avgY'].tolist()))
            writer.writerow((sourceId, mean, chisq, len(counts) - 1,
                             radius, min(data['avgX']), max(data['avgX']),
                             min(data['avgY']), max(data['avgY']), band))
            output.flush()

connect.load_csv('PhosimLightCurveStats', csv_file)
