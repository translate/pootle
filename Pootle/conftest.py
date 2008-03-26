# customization of py.test collection

import py.test.collect

class PootleDirectory(py.test.collect.Directory):
    def recfilter(self, path):
        return super(PootleDirectory, self).recfilter(path) and \
               path.basename not in ('po')

Directory = PootleDirectory

