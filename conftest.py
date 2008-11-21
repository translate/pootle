# customization of py.test collection

import sys, os
import py.test.collect

sys.path.append(os.path.realpath('.'))

class PootleDirectory(py.test.collect.Directory):
    def recfilter(self, path):
        return super(PootleDirectory, self).recfilter(path) and \
               path.basename not in ('po')

Directory = PootleDirectory

