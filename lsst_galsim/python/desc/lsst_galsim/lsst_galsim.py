class lsst_galsim(object):
    '''
    Example class for lsst_galsim package.
    '''
    def __init__(self, message):
        self.message = message

    def run(self, raise_error=False):
        if raise_error:
            raise RuntimeError()
        return self.message
