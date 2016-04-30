import lsst.afw.image as afwImage
import lsst.afw.math as afwMath
import lsst.daf.persistence as dp

repo = '500'
nmax = 10

butler = dp.Butler(repo)
datarefs = butler.subset('calexp')
for i, dataref in enumerate(datarefs):
    if i > nmax:
        break
    calexp = dataref.get('calexp')
    calexp_bg = dataref.get('calexpBackground')
    mi = calexp.getMaskedImage()
    psf = calexp.getPsf()
    pixel_scale = calexp.getWcs().pixelScale().asArcseconds()
    stats_image = calexp_bg[0][0].getStatsImage()

    print dataref.dataId['visit'], \
        psf.computeShape().getDeterminantRadius()*2.35*pixel_scale, \
        afwMath.makeStatistics(stats_image, afwMath.MEDIAN).getValue(), \
        afwMath.makeStatistics(mi, afwMath.VARIANCECLIP).getValue()
