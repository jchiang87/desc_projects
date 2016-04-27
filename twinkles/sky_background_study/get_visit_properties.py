import lsst.afw.image as afwImage
import lsst.afw.math as afwMath
import lsst.daf.persistence as dp
from desc.twinkles import get_visits

output_repo = '501'
raft = '2,2'
sensor = '1,1'

visits = get_visits(output_repo)

butler = dp.Butler(output_repo)
for band, visit_list in visits.items():
    for visit in visit_list:
        dataId = dict(visit=visit, raft=raft, sensor=sensor)
        calexp = butler.get('calexp', dataId=dataId)
        calexp_bg = butler.get('calexpBackground', dataId=dataId)
        mi = calexp.getMaskedImage()
        psf = calexp.getPsf()
        pixel_scale = calexp.getWcs().pixelScale().asArcseconds()
        stats_image = calexp_bg[0][0].getStatsImage()

        print visit, \
            psf.computeShape().getDeterminantRadius()*2.35*pixel_scale, \
            afwMath.makeStatistics(stats_image, afwMath.MEDIAN).getValue(), \
            afwMath.makeStatistics(mi, afwMath.VARIANCECLIP).getValue()
